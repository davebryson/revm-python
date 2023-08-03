import pytest
from eth_utils import is_address, to_wei

from revm_py import Revm, Contract


def test_contract_deploy_no_args():
    with open("./tests/fixtures/counter.json") as f:
        counterabi = f.read()

    provider = Revm()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    counter = Contract(provider, counterabi)
    address = counter.deploy(deployer)

    assert is_address(address)
    assert address == counter.address

    val = counter.number()
    assert val == 0

    with pytest.raises(BaseException):
        # constructor doesn't accept args
        counter.deploy(deployer, args=(1, 2))


def test_contract_deploy_with_args():
    with open("./tests/fixtures/erc20.json") as f:
        ercabi = f.read()

    provider = Revm()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    erc = Contract(provider, ercabi)
    erc.deploy(deployer, args=("hello", "H", 6))

    assert is_address(erc.address)

    with pytest.raises(BaseException):
        # missing args
        erc.deploy(deployer)

    name = erc.name()
    assert name == "hello"

    sym = erc.symbol()
    assert sym == "H"


def test_contract_deploy_with_value():
    with open("./tests/fixtures/simplepayable.json") as f:
        simpleabi = f.read()

    provider = Revm()
    actors = provider.create_accounts_with_balance(2, 2)
    deployer = actors[0]
    alice = actors[1]

    amount = to_wei(1, "ether")
    simple = Contract(provider, simpleabi)

    simple.deploy(deployer, args=[alice], value=amount)
    assert is_address(simple.address)

    assert provider.balance_of(simple.address) == amount
    assert provider.balance_of(deployer) == amount


def test_read_write_contract():
    with open("./tests/fixtures/counter.json") as f:
        counterabi = f.read()

    provider = Revm()
    actors = provider.create_accounts_with_balance(2, 2)
    deployer = actors[0]
    bob = actors[1]

    counter = Contract(provider, counterabi)
    counter.deploy(deployer)

    # make 99 calls to the number
    for i in range(1, 100):
        counter.setNumber(i, caller=bob)

    b = counter.number()
    assert b == 99

    with pytest.raises(BaseException):
        # can't call functions that don't exist
        counter.nope()
