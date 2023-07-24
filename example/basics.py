from eth_utils import to_wei, from_wei
from revm_py import Provider, load_contract_meta_from_file

if __name__ == "__main__":
    info = """
    ~~~  Demonstrates basic functionality scripting with the embedded EVM ~~~
    """
    print(info)

    abi, bytecode = load_contract_meta_from_file("./example/contracts/counter.json")

    provider = Provider()
    actors = provider.create_accounts_with_balance(2, 2)
    print("generated actor addresses")
    print("preloaded each with a balance of 2 eth in the EVM")

    bob = actors[0]
    alice = actors[1]

    print(" deploying contract...")
    contract_address, deploy_cost = provider.deploy(bob, abi, bytecode)
    print(f"deployed address: {contract_address}")

    print(" ~~ interacting with the contract ~~~")
    r1 = provider.read_contract(
        abi=abi,
        caller=bob,
        address=contract_address,
        function="number",
        args=[],
    )

    # note: using inline abi
    w1 = provider.write_contract(
        abi=[
            "function setNumber(uint256) returns ()",
        ],
        caller=bob,
        address=contract_address,
        function="setNumber",
        args=[10],
    )

    print(f"write call {w1}")

    r1 = provider.read_contract(
        abi=abi,
        caller=bob,
        address=contract_address,
        function="number",
    )

    print(f"final: {r1}")

    # Balance and transfer
    bal = provider.balance_of(bob)

    print(f"bob's balance: {bal} in wei")
    print(f"bob's balance: {from_wei(bal, 'ether')} in ether")

    g = provider.transfer(alice, bob, to_wei(0.5, "ether"))
    print(f"transfer gas: {g}")

    print(f"bob's balance: {from_wei(provider.balance_of(bob), 'ether')} in ether")
    print(f"alice's balance: {from_wei(provider.balance_of(alice), 'ether')} in ether")
