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

from bankreserve.random_walk import RandomWalker

from eth_utils import to_wei, from_wei


class Consumer(RandomWalker):
    def __init__(self, unique_id, my_address, pos, model, use_moore, bank_address, abi):
        """
        uid:          id to track the consumer
        my_address    consumers wallet address
        pos:          in the grid
        model:        handle to the model
        use_moore:    specifies the number of neighbors (cells) in the grid
        bank_address: deployed address of the bank
        provider:     needed to call contracts
        abi:          bank contract ABI
        """
        super().__init__(unique_id, pos, model, moore=use_moore)
        self.abi = abi
        self.address = my_address
        self.bank_address = bank_address

        # when doing business, if the agent runs short this is the diff between
        # what the intended to pay and how much they were short. This value determines
        # how much they take from savings and get a loan for
        self.short_balance = 0

    def update_agent_state(self):
        # self.balance = self.model.provider.balance_of(self.address)
        # self.loans = ...
        pass

    def take_loan(self, amount):
        try:
            self.model.provider.write_contract(
                abi=self.abi,
                caller=self.address,
                address=self.bank_address,
                function="takeLoan",
                args=[amount],
            )
            # use local accounting
            self.loans += amount
        except Exception as e:
            print(f"ERROR: {e}")

    @property
    def balance(self):
        return self.model.provider.balance_of(self.address)

    @property
    def loans(self):
        """
        Call bank to get my loan balance
        """
        (result, _, _) = self.model.provider.read_contract(
            abi=self.abi,
            caller=self.address,
            address=self.bank_address,
            function="loans",
            args=[self.address],
        )
        (value,) = result
        return value

    @property
    def savings(self):
        """
        Call bank to get my savings balance
        """
        (result, _, _) = self.model.provider.read_contract(
            abi=self.abi,
            caller=self.address,
            address=self.bank_address,
            function="savings",
            args=[self.address],
        )
        (value,) = result
        return value

    @property
    def wealth(self):
        """
        Call my net worth (savings - loans)
        """
        savings = from_wei(self.savings, "ether")
        loans = from_wei(self.loans, "ether")
        return savings - loans

    def __send_what_i_can_afford(self, recipient_address, my_balance, value_in_eth):
        val_in_wei = to_wei(value_in_eth, "ether")
        if my_balance == 0:
            # nothing I can do with now
            self.short_balance = val_in_wei
            return

        # trade with what you have
        amount_to_send = 0
        if my_balance >= val_in_wei:
            amount_to_send = val_in_wei
        else:
            # diff of what I owe
            self.short_balance = val_in_wei - my_balance
            # send what I can afford
            amount_to_send = my_balance

        self.model.provider.transfer(self.address, recipient_address, amount_to_send)

    def do_business(self):
        print("RUNNING: do_business")
        # Check to see if I have any funds available to exchange
        savings = self.savings
        my_balance = self.balance
        print(f"agent: {self.unique_id}, bal: {my_balance}  sav: {savings}")
        (result, _, _) = self.model.provider.read_contract(
            abi=self.abi,
            caller=self.address,
            address=self.bank_address,
            function="availableToLoan",
        )
        (availableToLoan,) = result

        if savings > 0 or my_balance > 0 or availableToLoan > 0:
            # I have money to play...

            # create list of consumers at my location (includes self)
            my_cell = self.model.grid.get_cell_list_contents([self.pos])

            # check if other people are at my location
            if len(my_cell) > 1:
                # set customer to self for while loop condition
                customer = self
                while customer == self:
                    """select a random person from the people at my location
                    to trade with"""
                    customer = self.random.choice(my_cell)
                # 50% chance of trading with customer
                if self.random.randint(0, 1) == 0:
                    # 50% chance of trading 5 eth
                    if self.random.randint(0, 1) == 0:
                        # give customer 5 eth from my wallet
                        # or if my balance is less send what I have
                        self.__send_what_i_can_afford(customer.address, my_balance, 5)
                    # 50% chance of trading $2
                    else:
                        # give customer 2 eth from my wallet
                        # or if my balance is less send what I have
                        self.__send_what_i_can_afford(customer.address, my_balance, 2)

    def balance_books(self):
        """
        What's the best way to handle this logic??

        if I'm broke, tap savings
           - try to withdrawn enough to zero our shortage
           - either take savings to fill shortage OR use savings and a loan to cover debt
        else
           deposit surplus wallet balance in savings

        if I have any savings
          try to reduce any loan debt
        """
        wallet_balance = self.balance
        # if my wallet is empty, try to re-fill from savings and/or loan
        if wallet_balance == 0:
            current_savings = self.savings
            if current_savings >= self.short_balance:
                # withdraw from savings to clear debt
                self.model.provider.write_contract(
                    abi=self.abi,
                    caller=self.address,
                    address=self.bank_address,
                    function="withdrawFromSavings",
                    args=[current_savings],
                )
                self.short_balance = 0
            else:
                # if any savings, withdraw what I have and try to get loan for the diff
                if current_savings > 0:
                    self.model.provider.write_contract(
                        abi=self.abi,
                        caller=self.address,
                        address=self.bank_address,
                        function="withdrawFromSavings",
                        args=[current_savings],
                    )
                    # deduct shortage by withdraw
                    self.short_balance -= current_savings

                # attempt a loan for remaining shortage.
                # check how much the bank can loan
                ((loan_amt_available,), _, _) = self.model.provider.read_contract(
                    abi=self.abi,
                    caller=self.address,
                    address=self.bank_address,
                    function="availableToLoan",
                )

                if loan_amt_available >= self.short_balance:
                    # Take out a loan for the amount short
                    self.model.provider.write_contract(
                        abi=self.abi,
                        caller=self.address,
                        address=self.bank_address,
                        function="takeLoan",
                        args=[self.short_balance],
                    )
                    # clear my shortage
                    self.short_balance = 0
                else:
                    # Get a loan for what we can to reduce short_balance
                    self.model.provider.write_contract(
                        abi=self.abi,
                        caller=self.address,
                        address=self.bank_address,
                        function="takeLoan",
                        args=[loan_amt_available],
                    )
                    self.short_balance -= loan_amt_available

        else:
            # I have money in my wallet (maybe from trading) so deposit in savings
            self.model.provider.write_contract(
                abi=self.abi,
                caller=self.address,
                address=self.bank_address,
                function="depositToSavings",
                value=wallet_balance,
            )

        # Now, let's deal with any loan?
        current_loans = self.loans
        my_savings = self.savings

        if current_loans > 0 and my_savings > 0:
            # try to payoff loans
            if my_savings >= current_loans:
                # with draw enough savings to payoff loans
                # repay loan for full amount
                self.model.provider.write_contract(
                    abi=self.abi,
                    caller=self.address,
                    address=self.bank_address,
                    function="withdrawFromSavings",
                    args=[current_loans],
                )
                # repay loan and clear debt
                self.model.provider.write_contract(
                    abi=self.abi,
                    caller=self.address,
                    address=self.bank_address,
                    function="repayLoan",
                    value=current_loans,
                )
            else:
                # withdraw what I have
                self.model.provider.write_contract(
                    abi=self.abi,
                    caller=self.address,
                    address=self.bank_address,
                    function="withdrawFromSavings",
                    args=[my_savings],
                )
                # repay what I can
                self.model.provider.write_contract(
                    abi=self.abi,
                    caller=self.address,
                    address=self.bank_address,
                    function="repayLoan",
                    value=my_savings,
                )

    def step(self):
        # move to a cell in my Moore neighborhood
        self.random_move()
        # trade
        self.do_business()
        # deposit money or take out a loan
        self.balance_books()
