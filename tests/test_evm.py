from revm_py import Revm
from eth_utils import to_wei


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
