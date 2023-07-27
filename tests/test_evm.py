import pytest
from eth_utils import is_address, to_wei

from revm_py import load_contract_meta_from_file, Revm, Contract


def test_evm_setup_accounts():
    provider = Revm()
    actors = provider.create_accounts_with_balance(10, 2)
    assert len(actors) == 10

    # Check a random balance
    assert provider.balance_of(actors[4]) == to_wei(2, "ether")


def test_balance_and_transfers():
    transfer_amt = to_wei(1, "ether")
    provider = Revm()

    [bob, alice] = provider.create_accounts_with_balance(2, 5)

    # Bob sends eth to alice
    provider.transfer(bob, alice, transfer_amt)
    assert provider.balance_of(bob) == to_wei(4, "ether")
    assert provider.balance_of(alice) == to_wei(6, "ether")

    ## Test simple transfer to contract
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/simplepayable.json")

    c = Contract.deploy(provider, bob, abi, bytecode, [bob])
    assert is_address(c.address)
    assert provider.balance_of(c.address) == 0

    provider.transfer(alice, c.address, transfer_amt)

    assert provider.balance_of(c.address) == transfer_amt
    assert provider.balance_of(alice) == to_wei(5, "ether")
