import mesa

from revm_py import *
from eth_utils import to_wei


def compute_gini(model):
    agent_wealths = [agent.get_balance() for agent in model.schedule.agents]
    x = sorted(agent_wealths)
    N = model.num_agents
    B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x))
    return 1 + (1 / N) - 2 * B


class BoltzmannWealthModel(mesa.Model):
    """A simple model of an economy where agents exchange currency at random.

    All the agents begin with one unit of currency, and each time step can give
    a unit of currency to another agent. Note how, over time, this produces a
    highly skewed distribution of wealth.
    """

    def __init__(self, N=100, width=10, height=10):
        self.num_agents = N
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(
            model_reporters={"Gini": compute_gini},
            agent_reporters={"Wealth": "get_balance"},
        )

        # Create the EVM provider
        self.provider = Provider()
        # Generate wallets for N actors with a balance of 2 eth
        actors = self.provider.create_accounts_with_balance(N, 2)

        # Create agents
        for i in range(self.num_agents):
            # note we assign and agent and ethereum address
            addy = actors[i]
            a = MoneyAgent(i, addy, self)
            self.schedule.add(a)
            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self, n):
        for i in range(n):
            self.step()


class MoneyAgent(mesa.Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, unique_id, address, model):
        super().__init__(unique_id, model)
        self.address = address

    def get_balance(self):
        # note we get an agent's balance from the EVM
        return self.model.provider.balance_of(self.address)

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def give_money(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        cellmates.pop(
            cellmates.index(self)
        )  # Ensure agent is not giving money to itself
        if len(cellmates) > 0:
            other = self.random.choice(cellmates)
            # Agent transfers ether via the EVM
            self.model.provider.transfer(
                self.address, other.address, to_wei(1, "ether")
            )

    def step(self):
        self.move()
        if self.get_balance() > 0:
            self.give_money()
