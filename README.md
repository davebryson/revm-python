# revmup-python
A Python smart-contract API and blazingly fast (embedded) Ethereum Virtual Machine (EVM).

**DEPRECATED** see [Simular](https://github.com/simular-fi/simular)

How is this different than Brownie, Ganache, Anvil?
- It's only an EVM, no blocks or minings
- No HTTP/JSON-RPC. You talk directly to the EVM (and it's fast)
- Provides low-level access to storage
- You can still do all the ethereum stuff: account transfers, contract interaction, etc...
- Fork and interact with main chain historical data (coming soon...)

The primary motivation for this work was to be able to model smart-contract interaction in an Agent Based Modeling environment like [Mesa](https://mesa.readthedocs.io/en/main/). To do that, we needed a fast, flexible, EVM with a Python API.

## Standing on the shoulders of giants
Thanks to the following projects for making this work easy!
- [pyO3](https://github.com/PyO3)
- [revm](https://github.com/bluealloy/revm)
- [alloy-rs](https://github.com/alloy-rs/core/tree/main)
- [eth_utils/eth_abi](https://eth-utils.readthedocs.io/en/stable/) 

## Get Started
- You need `Rust`, `Python/Poetry`. Will be available on PyPi soon.
- Run `make build`
- See `revm_py/__init__.py` for the main python api

## Example
Deploy and interact with the classic `counter` smart contract

```python
    # load contract abi
    with open("./tests/fixtures/counter.json") as f:
        counterabi = f.read()
    
    # create the EVM client
    client = Revm()

    # Create 2 accounts and fund them with 2 ether
    [deployer, alice] = client.create_accounts_with_balance(2, 2)

    # Create and instance of the contract and deploy it to the EVM
    counter = Contract(client, counterabi)
    address = counter.deploy(deployer)
    assert is_address(counter.address)

    # Contract functions are dynamically built from the ABI and
    # attached to the 'Contract.
    #
    # Call the 'setNumber' function from the contract
    # Alice is the 'from' address...setting the number to 10
    counter.setNumber(10, caller=alice)

    # Now call the 'number' function in the contract to 
    # check the state of the contract
    result = counter.number()
    assert result == 10
```
## What's next
- Mesa examples
- Fork chain support

