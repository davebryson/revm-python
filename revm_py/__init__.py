from .revm_py import EVM, AbiParser
from .contract import Contract, Revm

"""
Provider and utilities for interacting with the EVM
"""
import secrets

from eth_abi import encode, decode
from eth_utils import function_signature_to_4byte_selector, decode_hex, to_wei


def load_contract_meta_from_file(path):
    """
    Load a contract metadata json file.

    Returns a tuple with the abi section (as a string), and the bytecode
    """
    import json

    with open(path) as f:
        meta = json.loads(f.read())
        abi = meta["abi"]
        bytcode = decode_hex(meta["bytecode"]["object"])

    return (json.dumps(abi), bytcode)


def generate_random_address():
    return "0x" + secrets.token_hex(20)


def format_args(name, params):
    """
    Format a function name and input args needed for 4-byte selector. Ex:
    Given
        function name  : add
        function params: ["uint256", "address"]

    Returns "add(uint256,uint256)"
    """
    result = ""
    for i in params:
        result += f"{i},"
    # remove trailing ","
    t = result.strip(",")
    return f"{name}({t})"


class Provider:
    def __init__(self):
        self.evm = EVM()

    def __validate(self, kvargs):
        # Minimal validation on input to read/write
        # @todo Maybe map to a namedtuple for use inside calls below
        if not "address" in kvargs:
            raise Exception("missing address")
        if not "caller" in kvargs:
            raise Exception("missing caller (from) address")
        if not "abi" in kvargs:
            raise Exception("missing abi")
        if not "function" in kvargs:
            raise Exception("missing function name")

    def __get_contract_from_abi(self, abi):
        """
        Parse the incoming abi depending on if it's an inline entry, or
        the fill json abi as a string
        """
        if isinstance(abi, (list, tuple)):
            return AbiParser.parse_abi(abi)
        return AbiParser.load(abi)

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
        Create 'num' of account with given balance in eth.
        Default bal == 0
        Returns List[address]
        """
        output = []
        for _ in range(0, num):
            address = self.create_account(bal_in_eth)
            # address = generate_random_address()
            output.append(address)
            # self.evm.create_account(address, bal)
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

    def __encode_deploy_bytecode_with_args(self, abi, bytecode, args):
        contract = self.__get_contract_from_abi(abi)
        params = contract.constructor_params()
        if len(params) != len(args):
            raise Exception("wrong number of constructor params")
        return bytecode + encode(params, args)

    def deploy(self, caller, abi, bytecode, args=[], value=0):
        if len(args) > 0:
            bytecode_with_args = self.__encode_deploy_bytecode_with_args(
                abi, bytecode, args
            )
            return self.evm.deploy(caller, bytecode_with_args, value)
        return self.evm.deploy(caller, bytecode, value)

    def __make_encoded_call(self, fn_name, expected_input, args):
        """
        Encode function signature and args for evm tx
        """
        if len(expected_input) != len(args):
            raise Exception("input args do not match contract inputs")

        fn_definition = format_args(fn_name, expected_input)

        return function_signature_to_4byte_selector(fn_definition) + encode(
            expected_input, args
        )

    def write_contract(self, **kvargs):
        """
        Make a transaction call that commits
        """
        self.__validate(kvargs)
        caller = kvargs["caller"]
        contract_address = kvargs["address"]
        abi = kvargs["abi"]
        func = kvargs["function"]
        args = kvargs.get("args", [])
        value = kvargs.get("value", 0)

        contract = self.__get_contract_from_abi(abi)
        ins, outs = contract.function_params(func)
        encoded_call = self.__make_encoded_call(func, ins, args)

        bits, gas_used, logs = self.evm.transact(
            caller, contract_address, encoded_call, value
        )

        return (decode(outs, bytes(bits)), gas_used, logs)

    def read_contract(self, **kvargs):
        """
        Make a read-only call that does not commit
        """
        self.__validate(kvargs)
        caller = kvargs["caller"]
        contract_address = kvargs["address"]
        abi = kvargs["abi"]
        func = kvargs["function"]
        args = kvargs.get("args", [])

        contract = self.__get_contract_from_abi(abi)
        ins, outs = contract.function_params(func)
        encoded_call = self.__make_encoded_call(func, ins, args)

        bits, gas_used, logs = self.evm.call(caller, contract_address, encoded_call)

        return (decode(outs, bytes(bits)), gas_used, logs)
