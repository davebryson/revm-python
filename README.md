# Revm-Python
A Python api for a blazingly fast Ethereum Virtual Machine (EVM). Also includes a contract api to deploy and interact with smart contracts.

How is this different than Brownie, Ganache, Anvil?
- It's only an EVM, no blocks or minings
- No HTTP/JSON-RPC. You talk directly to the EVM (and it's fast)
- Provides low-level access to storage
- You can still do all the ethereum stuff: accounts, transfers, contract interaction, etc...
- Fork and interact with main chain historical data 

The primary motivation for this work was to be able to model smart contract interaction in an Agent Based Modeling environment like [Mesa](https://mesa.readthedocs.io/en/main/). To do that, we needed a fast, flexible, EVM with a Python api (of course).   More to come on this...

## Standing on the shoulders of giants
Thanks to the following projects for making this work easy!
- [pyO3](https://github.com/PyO3)
- [revm](https://github.com/bluealloy/revm)
- [ethers](https://docs.rs/ethers/latest/ethers/index.html)
- [eth_utils/eth_abi](https://eth-utils.readthedocs.io/en/stable/) 

## Get Started
- You need `Rust`, `Python/Poetry`. Will be available on PyPi soon.
- Run `make build`
- See `revm_py/__init__.py` for the main python api

## Example
Deploy and interact with the classic `counter` smart contract

```python
    # load contract meta from the json abi
    abi, bytecode = load_contract_meta_from_file("./tests/fixtures/counter.json")
    
    # create the EVM
    provider = Revm()

    # Create some accounts and fund them with 2 ether
    actors = provider.create_accounts_with_balance(3, 2)
    deployer = actors[0]
    alice = actors[2]

    # Deploy the contract
    counter = Contract.deploy(provider, deployer, abi, bytecode)
    assert is_address(counter.address)

    # Call the 'setNumber' function on the contract
    # Alice is the 'from' address...setting the number to 10
    counter.setNumber(10, caller=alice)

    # Now check the (state) value in the contract
    (val,) = counter.number()
    assert val == 10
```
See [tests](./tests/) for more examples

