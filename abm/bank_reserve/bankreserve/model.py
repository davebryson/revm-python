"""
The following code was adapted from the Bank Reserves model included in Netlogo
Model information can be found at:
http://ccl.northwestern.edu/netlogo/models/BankReserves
Accessed on: November 2, 2017
Author of NetLogo code:
    Wilensky, U. (1998). NetLogo Bank Reserves model.
    http://ccl.northwestern.edu/netlogo/models/BankReserves.
    Center for Connected Learning and Computer-Based Modeling,
    Northwestern University, Evanston, IL.
"""

import mesa
import numpy as np
import random

from bankreserve.agents import Consumer

from revm_py import Provider, AbiParser, load_contract_meta_from_file
from eth_utils import to_wei, from_wei

"""
If you want to perform a parameter sweep, call batch_run.py instead of run.py.
For details see batch_run.py in the same directory as run.py.
"""

# Start of datacollector functions


def to_ether(value):
    return from_wei(value, "ether")


def get_num_rich_agents(model):
    """return number of rich agents"""
    rich_agents = [
        a for a in model.schedule.agents if to_ether(a.savings) > model.rich_threshold
    ]
    return len(rich_agents)


def get_num_poor_agents(model):
    """return number of poor agents"""
    poor_agents = [a for a in model.schedule.agents if to_ether(a.loans) > 10]
    return len(poor_agents)


def get_num_mid_agents(model):
    """return number of middle class agents"""
    mid_agents = [
        a
        for a in model.schedule.agents
        if to_ether(a.loans) < model.rich_threshold
        and to_ether(a.savings) < model.rich_threshold
    ]
    return len(mid_agents)


def get_total_savings(model):
    """sum of all agents' savings"""

    agent_savings = [to_ether(a.savings) for a in model.schedule.agents]
    # return the sum of agents' savings
    return np.sum(agent_savings)


def get_total_wallets(model):
    """sum of amounts of all agents' wallets"""

    agent_wallets = [to_ether(a.balance) for a in model.schedule.agents]
    # return the sum of all agents' wallets
    return np.sum(agent_wallets)


def get_total_money(model):
    # sum of all agents' wallets
    wallet_money = get_total_wallets(model)
    # sum of all agents' savings
    savings_money = get_total_savings(model)
    # return sum of agents' wallets and savings for total money
    return wallet_money + savings_money


def get_total_loans(model):
    # list of amounts of all agents' loans
    agent_loans = [to_ether(a.loans) for a in model.schedule.agents]
    # return sum of all agents' loans
    return np.sum(agent_loans)


class BankModel(mesa.Model):
    # grid height
    grid_h = 20
    # grid width
    grid_w = 20

    """init parameters "init_people", "rich_threshold", and "reserve_percent"
       are all set via Slider"""

    def __init__(
        self,
        height=grid_h,
        width=grid_w,
        init_people=2,
        rich_threshold=10,
        reserve_percent=50,
    ):
        self.height = height
        self.width = width
        self.init_people = init_people
        self.schedule = mesa.time.RandomActivation(self)
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=True)
        # rich_threshold is the amount of savings a person needs to be considered "rich"
        self.rich_threshold = rich_threshold
        # self.reserve_percent = reserve_percent
        # see datacollector functions above
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Rich": get_num_rich_agents,
                "Poor": get_num_poor_agents,
                "Middle Class": get_num_mid_agents,
                "Savings": get_total_savings,
                "Wallets": get_total_wallets,
                "Money": get_total_money,
                "Loans": get_total_loans,
            },
            agent_reporters={"Wealth": lambda x: x.wealth},
        )

        """
        Create provider
        Deploy contract
        Generate wallets below
        Update logic to calculate 'reserve_percent' below
        """
        abi, bytecode = load_contract_meta_from_file(
            "./abm/bank_reserve/contract/BankReserve.json"
        )
        self.provider = Provider()

        # Load and deploy the BankReserve contract
        deployer = self.provider.create_account(1)
        # adjust percentage for basis points
        resv_percent = reserve_percent * 100
        (bank_address, _) = self.provider.deploy(
            deployer, abi, bytecode, [resv_percent]
        )

        # create a single bank for the model
        # self.bank = Bank(1, self, self.reserve_percent)

        # create people for the model according to number of people set by user
        for i in range(self.init_people):
            # set x, y coords randomly within the grid
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)

            initial_balance = random.randint(1, rich_threshold + 1)
            address = self.provider.create_account(initial_balance)
            c = Consumer(i, address, (x, y), self, True, bank_address, abi)

            # p = Person(i, (x, y), self, True, self.bank, self.rich_threshold)
            # place the Person object on the grid at coordinates (x, y)
            self.grid.place_agent(c, (x, y))
            # add the Person object to the model schedule
            self.schedule.add(c)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        # tell all the agents in the model to run their step function
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self):
        for i in range(self.run_time):
            self.step()
