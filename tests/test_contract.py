import pytest
from eth_utils import is_address, to_wei

from revm_py import load_contract_meta_from_file, Revm, Contract


def test_contract_deploy_no_args():
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/counter.json")

    provider = Revm()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    c = Contract.deploy(provider, deployer, abi, bytecode)
    assert is_address(c.address)

    with pytest.raises(BaseException):
        # constructor doesn't accept args
        Contract.deploy(provider, deployer, abi, bytecode, args=(1, 2))


def test_contract_deploy_with_args():
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/erc20.json")
    provider = Revm()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    c = Contract.deploy(provider, deployer, abi, bytecode, args=("hello", "H", 6))
    assert is_address(c.address)

    with pytest.raises(BaseException):
        # missing args
        Contract.deploy(provider, deployer, abi, bytecode)

    (name,) = c.name()
    assert name == "hello"

    (sym,) = c.symbol()
    assert sym == "H"


def test_contract_deploy_with_value():
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/simplepayable.json")
    provider = Revm()
    actors = provider.create_accounts_with_balance(2, 2)
    deployer = actors[0]
    alice = actors[1]

    amount = to_wei(1, "ether")
    c = Contract.deploy(provider, deployer, abi, bytecode, args=[alice], value=amount)
    assert is_address(c.address)

    assert provider.balance_of(c.address) == amount
    assert provider.balance_of(deployer) == amount


def test_contract_with_inline_abi():
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/erc20.json")
    provider = Revm()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    c = Contract.deploy(provider, deployer, abi, bytecode, args=("hello", "H", 6))
    assert is_address(c.address)

    # try calling with inline abi
    cabi = Contract(provider, ["function name() view returns (string)"])
    (r,) = c.at(c.address).name()
    assert r == "hello"


def test_read_write_contract():
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/counter.json")

    provider = Revm()
    actors = provider.create_accounts_with_balance(2, 2)
    deployer = actors[0]
    bob = actors[1]

    c = Contract.deploy(provider, deployer, abi, bytecode)
    assert is_address(c.address)

    # make 99 calls to the number
    for i in range(1, 100):
        c.setNumber(i, caller=bob)

    (b,) = c.number()
    assert b == 99

    with pytest.raises(BaseException):
        # can't call functions that don't exist
        c.nope()
