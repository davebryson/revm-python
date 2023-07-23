from .revm_py import EVM, ContractParser

"""
First use of the evm module
"""
import secrets

from eth_abi import encode, decode
from eth_utils import function_signature_to_4byte_selector, decode_hex, to_wei


def load_contract_meta_from_file(path):
    """
    Load a contract metadata json file
    """
    import json

    with open(path) as f:
        meta = json.loads(f.read())
        abi = meta["abi"]
        bytcode = decode_hex(meta["bytecode"]["object"])

    return (json.dumps(abi), bytcode)


def generate_random_address():
    return "0x" + secrets.token_hex(20)


class Provider:
    def __init__(self):
        self.evm = EVM()

    def __validate(self, kvargs):
        # Minimal validation
        if not "address" in kvargs:
            raise Exception("missing address")
        if not "caller" in kvargs:
            raise Exception("missing caller (from) address")
        if not "abi" in kvargs:
            raise Exception("missing abi")
        if not "function" in kvargs:
            raise Exception("missing function name")

    def create_accounts_with_balance(self, num=1, bal_in_eth=1):
        bal = to_wei(bal_in_eth, "ether")
        output = []
        for _ in range(0, num):
            address = generate_random_address()
            output.append(address)
            self.evm.create_account(address, bal)
        return output

    def balance_of(self, address):
        return self.evm.get_balance(address)

    def transfer(self, sender, receiver, amt):
        self.evm.transfer(sender, receiver, amt)

    def deploy(self, address, bytecode, args=None, value=None):
        ## @todo handle constructor args and value
        return self.evm.deploy(address, bytecode)

    def write_contract(self, **kvargs):
        caller = kvargs["caller"]
        contract_address = kvargs["address"]
        abi = kvargs["abi"]
        func = kvargs["function"]
        args = kvargs.get("args", [])
        contract = ContractParser.load(abi)

        ins, outs = contract.function_params(func)
        if len(ins) == 1:
            full_function = f"{func}({ins[0]})"
        else:
            full_function = f"{func}{tuple(ins)}"

        encoded_call = function_signature_to_4byte_selector(full_function) + encode(
            ins, args
        )
        bits, gas_used = self.evm.transact(caller, contract_address, encoded_call)

        return (decode(outs, bytes(bits)), gas_used)

    def read_contract(self, **kvargs):
        self.__validate(kvargs)
        caller = kvargs["caller"]
        contract_address = kvargs["address"]
        abi = kvargs["abi"]
        func = kvargs["function"]
        args = kvargs.get("args", [])
        contract = ContractParser.load(abi)

        ins, outs = contract.function_params(func)
        full_function = f"{func}{tuple(args)}"

        encoded_call = function_signature_to_4byte_selector(full_function) + encode(
            ins, args
        )
        bits, gas_used = self.evm.call(caller, contract_address, encoded_call)

        return (decode(outs, bytes(bits)), gas_used)
