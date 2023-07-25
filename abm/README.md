# Smart Contract Agent Based Modeling

One of the main motivations for developing `revm-python` is the ability to use smart contract enabled Agents with the [Mesa Agent Based Modeling Enviroment](https://github.com/projectmesa/mesa)

## Early experiments
- Boltzmann Wealth Model:  A direct port of the implementation from [Mesa Examples](https://github.com/projectmesa/mesa-examples). However this version replaces the wealth transfer in the orginal model with EVM transfers of Ethereum. To run the experiment: `python boltzmann/run.py`
- Bank Reserve: Another port of a Mesa example. `...in progress...`