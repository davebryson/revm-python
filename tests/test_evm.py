import pytest
from eth_utils import is_address, to_wei

from revm_py import load_contract_meta_from_file, Provider


def test_setup_accounts():
    provider = Provider()
    actors = provider.create_accounts_with_balance(10, 2)
    assert len(actors) == 10

    # Check a random balance
    assert provider.balance_of(actors[4]) == to_wei(2, "ether")


def test_balance_and_transfers():
    transfer_amt = to_wei(1, "ether")
    provider = Provider()

    [bob, alice] = provider.create_accounts_with_balance(2, 5)

    # Bob sends eth to alice
    provider.transfer(bob, alice, transfer_amt)
    assert provider.balance_of(bob) == to_wei(4, "ether")
    assert provider.balance_of(alice) == to_wei(6, "ether")

    ## Test simple transfer to contract
    abi, bytecode = load_contract_meta_from_file(
        "./example/contracts/SimplePayable.json"
    )

    contract_address, _ = provider.deploy(bob, abi, bytecode, [bob])
    assert provider.balance_of(contract_address) == 0

    provider.transfer(alice, contract_address, transfer_amt)

    assert provider.balance_of(contract_address) == transfer_amt
    assert provider.balance_of(alice) == to_wei(5, "ether")


def test_deploy_contract_with_no_arg():
    abi, bytecode = load_contract_meta_from_file("./example/contracts/Counter.json")
    provider = Provider()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    # Doesn't expect any args
    with pytest.raises(BaseException):
        # try with wrong number of args
        provider.deploy(deployer, abi, bytecode, [1, 2])

    ca, gas_used = provider.deploy(deployer, abi, bytecode)
    assert is_address(ca)
    assert gas_used > 0


def test_deploy_contract_with_args():
    abistr, bytecode = load_contract_meta_from_file(
        "./example/contracts/MockERC20.json"
    )

    provider = Provider()
    actors = provider.create_accounts_with_balance(1, 2)
    deployer = actors[0]

    with pytest.raises(BaseException):
        # try with wrong number of args
        provider.deploy(deployer, abistr, bytecode, [])

    with pytest.raises(BaseException):
        # try with wrong args
        provider.deploy(deployer, abistr, bytecode, [1, 10])

    # now do it right...
    contract_address, deploy_cost = provider.deploy(
        deployer, abistr, bytecode, ["hello", "HEO", 18]
    )
    assert is_address(contract_address)
    assert deploy_cost > 0

    # call the public state variable 'name' on the contract
    ((result,), _gas, _) = provider.read_contract(
        abi=abistr,
        caller=deployer,
        address=contract_address,
        function="name",
        args=[],
    )
    assert result == "hello"


def test_deploy_with_inline_abi():
    _, bytecode = load_contract_meta_from_file("./example/contracts/MockERC20.json")

    provider = Provider()
    actors = provider.create_accounts_with_balance(1, 3)
    deployer = actors[0]

    inline = [
        "constructor(string, string, uint8)",
    ]
    contract_address, deploy_cost = provider.deploy(
        deployer, inline, bytecode, ["hello", "HEO", 18]
    )
    assert is_address(contract_address)
    assert deploy_cost > 0


def test_deploy_with_value():
    _, bytecode = load_contract_meta_from_file("./example/contracts/SimplePayable.json")
    provider = Provider()
    actors = provider.create_accounts_with_balance(2, 3)
    deployer = actors[0]

    value = to_wei(1, "ether")
    inline = [
        "constructor(address) payable",
    ]

    contract_address, deploy_cost = provider.deploy(
        deployer, inline, bytecode, [deployer], value
    )

    assert is_address(contract_address)
    assert deploy_cost > 0

    bal = provider.balance_of(contract_address)
    assert bal == value


def test_calling_counter_contract():
    abi, bytecode = load_contract_meta_from_file("./example/contracts/counter.json")
    provider = Provider()
    [deployer] = provider.create_accounts_with_balance(1, 3)
    contract_address, _ = provider.deploy(deployer, abi, bytecode, [])

    provider.write_contract(
        caller=deployer,
        address=contract_address,
        abi=abi,
        function="addAndSet",
        args=[2, 3],
    )

    ((v,), _, _) = provider.read_contract(
        caller=deployer, address=contract_address, abi=abi, function="number"
    )
    assert v == 5


def test_calling_contracts():
    abi, bytecode = load_contract_meta_from_file("./example/contracts/MockERC20.json")

    provider = Provider()
    [deployer, bob, alice] = provider.create_accounts_with_balance(3, 3)
    contract_address, _ = provider.deploy(
        deployer, abi, bytecode, ["hello123", "HEO", 18]
    )

    assert is_address(contract_address)

    # deployer mints 3 to bob
    provider.write_contract(
        caller=deployer,
        address=contract_address,
        abi=abi,
        function="mint",
        args=[bob, 3],
    )

    ((v0,), _, _) = provider.read_contract(
        caller=bob, address=contract_address, abi=abi, function="name", args=[]
    )
    assert v0 == "hello123"

    ((v,), _, _) = provider.read_contract(
        caller=bob, address=contract_address, abi=abi, function="balanceOf", args=[bob]
    )
    assert v == 3

    # bob transfers 1 to alice
    (_, _, logs) = provider.write_contract(
        caller=bob,
        address=contract_address,
        abi=abi,
        function="transfer",
        args=[alice, 1],
    )

    assert len(logs) == 1

    ((b0,), _, _) = provider.read_contract(
        caller=bob, address=contract_address, abi=abi, function="balanceOf", args=[bob]
    )
    assert b0 == 2

    ((b1,), _, _) = provider.read_contract(
        caller=alice,
        address=contract_address,
        abi=abi,
        function="balanceOf",
        args=[alice],
    )
    assert b1 == 1


def test_events():
    pass
