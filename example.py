"""
Simple example of using the API
"""
from revm_py import Revm, Contract
from eth_utils import to_wei


def accounts_and_transfers():
    print("Running accounts and transfers")
    # Create the EVM client
    provider = Revm()

    # Create two wallets with a balance of 5 eth
    [bob, alice] = provider.create_accounts_with_balance(2, 5)

    # Check Bob's balance
    assert provider.balance_of(bob) == to_wei(5, "ether")

    # Transfer 1 eth from Bob to Alice
    transfer_amt = to_wei(1, "ether")
    provider.transfer(bob, alice, transfer_amt)

    # Check the balances
    assert provider.balance_of(bob) == to_wei(4, "ether")
    assert provider.balance_of(alice) == to_wei(6, "ether")

    print("Done!")


def do_contract():
    print("Interact with Counter contract")
    # Load the ABI information needed to deploy and interact with the contract
    with open("./tests/fixtures/counter.json") as f:
        counterabi = f.read()

    # Create the EVM client
    provider = Revm()

    # Create 1 wallet to deploy and interact with the contract
    [deployer] = provider.create_accounts_with_balance(1, 2)

    counter = Contract(provider, counterabi)
    address = counter.deploy(deployer)
    print(f"Contract address: {address}")

    # Interact with the contract. Methods are from the contract
    current_value = counter.number()
    print(f"initial value: {current_value}")

    # Note we have to pass the 'from/caller' address
    counter.setNumber(3, caller=deployer)

    print(f"updated value: {counter.number()}")
    print("Done!")


if __name__ == "__main__":
    accounts_and_transfers()
    print("--------")
    do_contract()
