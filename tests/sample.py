from revm_py import (
    load_contract_meta_from_file,
    generate_random_address,
    ContractInfo,
)

from eth_abi import encode, decode


class Function:
    def __init__(self, provider, signature, ins, outs, is_transact, is_payable):
        self.ins = ins
        self.outs = outs
        self.is_payable = is_payable
        self.is_transact = is_transact
        self.provider = provider
        self.selector = signature

    def __call__(self, *args):
        if len(args) != len(self.ins):
            raise Exception(
                f"input args do not match contract inputs. requires: {self.ins}"
            )
        self.encoded = self.selector + encode(self.ins, args)
        print(f"call encoded: {self.encoded.hex()}")
        if self.is_transact:
            print("transact")
        else:
            print("call")
        return self


class Contract:
    def __init__(self, abi, provider=None):
        self.provider = provider
        self.address = None
        # if isinstance(abi, (list, tuple)):
        #    return AbiParser.parse_abi(abi)

        info = ContractInfo.load(abi)

        # Note: ethers returns the signature with the 'return value':
        # functionName():(uint256). So we split(":") to get the sig for 4-byte.
        # print(f"{funcs}")
        for fo in info.functions:
            setattr(
                self,
                fo.name,
                Function(
                    self.provider,
                    bytes(fo.signature),
                    fo.ins,
                    fo.outs,
                    fo.is_transact,
                    fo.is_payable,
                ),
            )

    def at(self, address):
        self.address = address
        return self

    def deploy(cls):
        # self.address = ...
        pass

    def show(self):
        print("contract functions: ")
        for k, v in self.__dict__.items():
            if isinstance(v, Function):
                print(f" - {k}")


if __name__ == "__main__":
    abistr, bytecode = load_contract_meta_from_file(
        "./example/contracts/MockERC20.json"
    )

    addy = generate_random_address()
    contract = Contract(abistr)
    contract.show()
    contract.mint(addy, 1)
