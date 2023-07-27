// SPDX-License-Identifier: Apache-2.0
// SPDX-FileCopyrightText: 2023 Dave Bryson for the MITRE Corp
pragma solidity ^0.8.13;

///
/// A port of the Bank Reserve Mesa Model Example.
contract BankReserve {
    /// Track total loans (overtime)
    uint256 public outstandingLoans;

    /// Loans
    mapping(address => uint256) public loans;
    /// Savings by accounts. The total of this == the balance of this contract
    mapping(address => uint256) public savings;

    /// configurable value in basis points
    uint16 public reservePercentage;

    /// Set the reserve percentage with basis points:
    ///  percentage   :  1% ..... 100%
    ///  basis point  : 100 ..... 10_000
    constructor(uint16 rp) {
        reservePercentage = rp;
    }

    /// helper for clarity
    /// OR maybe bankBalance()
    function bankBalance() public view returns (uint256) {
        return address(this).balance;
    }

    ///
    /// Calculate the reserve as a percentage of the total deposits
    ///
    function reserve() public view returns (uint256) {
        return (reservePercentage * bankBalance()) / 10_000;
    }

    function availableToLoan() public view returns (uint256) {
        return bankBalance() - (reserve() - outstandingLoans);
    }

    /// Caller makes a deposit to their savings
    function depositToSavings() public payable {
        require(msg.value > 0, "you can't deposit 0");
        savings[msg.sender] = msg.value;
    }

    /// Caller can withdraw from their account
    function withdrawFromSavings(uint256 amount) public {
        uint256 bal = savings[msg.sender];
        require(bal >= amount, "you don't have enough savings");
        require(address(this).balance >= amount, "the bank is insolvent!");

        savings[msg.sender] = bal - amount;

        safeTransfer(msg.sender, amount);
    }

    function takeLoan(uint256 amountRequested) public {
        require(
            availableToLoan() >= amountRequested,
            "bank is unable to loan at this time..."
        );

        loans[msg.sender] = amountRequested;
        outstandingLoans += amountRequested;

        safeTransfer(msg.sender, amountRequested);
    }

    /// Caller repays a load
    function repayLoan() public payable {
        require(msg.value > 0, "you can't repay 0");
        require(
            loans[msg.sender] > 0,
            "you don't have an outstanding loan balance"
        );
        require(
            loans[msg.sender] <= msg.value,
            "you can't pay more than you owe"
        );

        // decrease callers loan debt
        loans[msg.sender] -= msg.value;
        // decrease outstanding loans
        outstandingLoans -= msg.value;
    }

    /// Adapted from the excellent solmate lib:  SafeTransferLib
    function safeTransfer(address to, uint256 amount) internal {
        bool success;
        /// @solidity memory-safe-assembly
        assembly {
            // Transfer the ETH and store if it succeeded or not.
            success := call(gas(), to, amount, 0, 0, 0, 0)
        }
        require(success, "ETH_TRANSFER_FAILED");
    }
}
