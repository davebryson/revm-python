import pytest
from eth_utils import is_address, to_wei

from revm_py import load_contract_meta_from_file, Provider


def test_gas_limit():
    provider = Provider()

    bob = provider.create_account(10)
    deployer = provider.create_account(2)

    abi, bytecode = load_contract_meta_from_file(
        "./abm/bank_reserve/contract/BankReserve.json"
    )
    contract_address, _ = provider.deploy(deployer, abi, bytecode, [5000])
    amount = to_wei(1, "ether")

    (_, gas, _) = provider.write_contract(
        abi=abi,
        caller=bob,
        address=contract_address,
        function="depositToSavings",
        value=amount,
    )

    print(f"GAS: {gas}")

    (result, _, _) = provider.read_contract(
        abi=abi,
        caller=bob,
        address=contract_address,
        function="savings",
        args=[bob],
    )
    (value,) = result
    assert value == amount

    # Can we get the gas limit error?
    """
    for _ in range(0, 1000):
        provider.read_contract(
            abi=abi,
            caller=bob,
            address=contract_address,
            function="loans",
            args=[bob],
        )
    """
