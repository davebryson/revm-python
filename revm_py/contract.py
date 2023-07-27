import secrets
from .revm_py import ContractInfo, EVM

from eth_abi import encode, decode
from eth_utils import to_wei


def generate_random_address():
    return "0x" + secrets.token_hex(20)


class Revm:
    def __init__(self):
        self.evm = EVM()

    def create_account(self, initial_bal=0):
        """
        Create a single account with an optional balance in ether
        Return the account address
        """
        bal = to_wei(initial_bal, "ether")
        address = generate_random_address()
        self.evm.create_account(address, bal)
        return address

    def create_accounts_with_balance(self, num, bal_in_eth=0):
        """
        Create 'num' of accounts with given balance in eth.
        Default bal == 0
        Returns List[address]
        """
        output = []
        for _ in range(0, num):
            address = self.create_account(bal_in_eth)
            output.append(address)
        return output

    def balance_of(self, address):
        """
        Return the balance for the given address
        """
        return self.evm.get_balance(address)

    def transfer(self, sender, receiver, amt):
        """
        Transfer eth between accounts
        """
        self.evm.transfer(sender, receiver, amt)

    def transact(self, caller, contract_address, encoded, value=0):
        bits, _, _ = self.evm.transact(caller, contract_address, encoded, value)
        return bits

    # @todo remove 'caller' not needed in a view/pure
    def call(self, caller, contract_address, encoded):
        bits, _, _ = self.evm.call(caller, contract_address, encoded)
        return bits


class Function:
    def __init__(self, signature, ins, outs, is_transact, is_payable):
        self.ins = ins
        self.outs = outs
        self.is_payable = is_payable
        self.is_transact = is_transact
        self.selector = signature

        self.provider = None
        self.contract_address = None

    def __call__(self, *args, **kwargs):
        value = kwargs.get("value", 0)
        caller = kwargs.get("caller", None)
        if not self.contract_address:
            raise Exception("missing contract address")

        # @todo move this to transact only
        if not caller:
            raise Exception("missing caller address")

        if len(args) != len(self.ins):
            raise Exception(
                f"input args do not match contract inputs. requires: {self.ins}"
            )

        self.encoded = self.selector + encode(self.ins, args)
        if self.is_transact:
            # it's a write call
            bits = self.provider.transact(
                caller, self.contract_address, self.encoded, value
            )
        else:
            # it's a read call
            bits = self.provider.call(caller, self.contract_address, self.encoded)

        return decode(self.outs, bytes(bits))


class Contract:
    def __init__(self, provider, abi):
        self.address = None
        self.provider = provider
        self.constructor_params = []
        self.__fns = {}

        info = None
        if isinstance(abi, (list, tuple)):
            info = ContractInfo.parse_abi(abi)
        elif isinstance(abi, str):
            info = ContractInfo.load(abi)
        else:
            raise Exception("unrecognized abi format")

        self.constructor_params = info.constructor_params

        for fo in info.functions:
            f = Function(
                bytes(fo.signature),
                fo.ins,
                fo.outs,
                fo.is_transact,
                fo.is_payable,
            )
            self.__fns[fo.name] = f

    def __getattr__(self, n):
        if n in self.__fns:
            fn = self.__fns[n]
            fn.contract_address = self.address
            fn.provider = self.provider
            return fn

    def at(self, address):
        self.address = address
        return self

    @classmethod
    def deploy(cls, provider, caller, abi, bytecode, args=[], value=0):
        c = cls(provider, abi)
        if c.constructor_params:
            if len(c.constructor_params) != len(args):
                raise Exception("wrong number of args for the constructor")
            bytecode += encode(c.constructor_params, args)
        addr, _ = provider.evm.deploy(caller, bytecode, value)
        c.address = addr
        return c

    def show(self):
        print("contract functions: ")
        for k, v in self.__dict__.items():
            if isinstance(v, Function):
                print(f" - {k}")
