import secrets
from eth_abi import encode, decode
from eth_utils import to_wei

from .revm_py import ContractInfo, EVM


def generate_random_address():
    """
    Generate a random account address
    """
    return "0x" + secrets.token_hex(20)


class Revm:
    """
    Thin Python wrapper around a Rust EVM.
    """

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
        """
        Make a 'write' call to a contract
        Returns any result byte encoded
        """
        bits, _ = self.evm.transact(caller, contract_address, encoded, value)
        return bits

    def call(self, contract_address, encoded):
        """
        Make a 'read' call to a contract
        Returns any result byte encoded
        """
        bits = self.evm.call(contract_address, encoded)
        return bits


class Function:
    """
    Contains all the information needed to encode and decode calls
    to the EVM
    """

    def __init__(self, signature, ins, outs, is_transact, is_payable):
        self.ins = ins
        self.outs = outs
        self.selector = signature
        self.is_payable = is_payable
        self.is_transact = is_transact

        self.provider = None
        self.contract_address = None

    def __call__(self, *args, **kwargs):
        if not self.contract_address:
            raise Exception("missing contract address. see at() method")

        value = kwargs.get("value", 0)
        caller = kwargs.get("caller", None)

        if len(args) != len(self.ins):
            raise Exception(
                f"input args do not match contract inputs. requires: {self.ins}"
            )

        self.encoded = self.selector + encode(self.ins, args)
        if self.is_transact:
            if not caller:
                raise Exception("missing caller address")
            # it's a write call
            bits = self.provider.transact(
                caller, self.contract_address, self.encoded, value
            )
        else:
            # it's a read call
            bits = self.provider.call(self.contract_address, self.encoded)

        decoded = decode(self.outs, bytes(bits))
        if len(decoded) == 1:
            return decoded[0]
        else:
            return decoded


class Contract:
    def __init__(self, provider, abi):
        """
        Create a contract from the given provider and ABI. Maps contract function
        names to the class and automatically determines if a method call should be
        a contract transaction or a read-only call based on the ABI.
        """
        self.address = None
        self.provider = provider
        self.constructor_params = []
        self.__contract_functions = {}
        self.bytecode = None

        info = None
        if isinstance(abi, str):
            info = ContractInfo.load(abi)
        else:
            raise Exception("unrecognized abi format")

        self.bytecode = info.bytecode
        self.constructor_params = info.constructor_params

        for fo in info.functions:
            f = Function(
                bytes(fo.signature),
                fo.ins,
                fo.outs,
                fo.is_transact,
                fo.is_payable,
            )
            self.__contract_functions[fo.name] = f

    def __getattr__(self, n):
        """
        Make contract methods available as calls
        For example, if the ABI has the contract function 'function hello(uint256)',
        you can invoke it by name: contract.hello(10)
        """
        if n in self.__contract_functions:
            fn = self.__contract_functions[n]
            fn.contract_address = self.address
            fn.provider = self.provider
            return fn

    def at(self, address):
        """
        Set the contract address, if not already set on deploy
        """
        self.address = address
        return self

    def deploy(self, caller, args=[], value=0):
        if not self.constructor_params and len(args) > 0:
            raise Exception("constructor doesn't take any args")
        if self.constructor_params:
            if len(self.constructor_params) != len(args):
                raise Exception("wrong number of args for the constructor")
            self.bytecode += encode(self.constructor_params, args)

        addr = self.provider.evm.deploy(caller, self.bytecode, value)
        self.address = addr
        return addr
