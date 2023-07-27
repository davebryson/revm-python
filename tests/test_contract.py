import pytest
from eth_utils import is_address

from revm_py import load_contract_meta_from_file, Revm, Contract


def test_contract_from_abi():
    abi, bytecode = load_contract_meta_from_file("./example/contracts/Counter.json")

    provider = Revm()
    actors = provider.create_accounts_with_balance(2, 2)
    deployer = actors[0]
    bob = actors[1]

    c = Contract.deploy(provider, deployer, abi, bytecode)
    assert is_address(c.address)

    for i in range(2, 100):
        c.setNumber(i, caller=bob)

    (b,) = c.number(caller=bob)
    assert b == 99

    # with pytest.raises(BaseException):
    #    c.setNumber(1)

    with pytest.raises(BaseException):
        c.nope()

    c1 = Contract(provider, abi=["function number() view returns (uint256)"])
    with pytest.raises(BaseException):
        c1.number(caller=bob)

    (b1,) = c1.at(c.address).number(caller=bob)
    assert b1 == 99

    with pytest.raises(BaseException):
        Contract(provider, "bad api input")
