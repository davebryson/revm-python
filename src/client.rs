use revm::{
    db::{CacheDB, EmptyDB},
    primitives::{AccountInfo, Address, ExecutionResult, Log, Output, ResultAndState, TxEnv, U256},
    Database, EVM,
};
use std::cell::RefCell;

/// Revm Client
#[derive(Clone)]
pub struct BasicClient {
    evm: RefCell<EVM<CacheDB<EmptyDB>>>,
}

impl BasicClient {
    pub fn new() -> Self {
        let mut evm = EVM::new();
        let db = CacheDB::new(EmptyDB::default());
        evm.env.block.gas_limit = U256::MAX.into();
        evm.database(db);
        Self {
            evm: RefCell::new(evm),
        }
    }

    pub fn create_account(&self, address: Address, amount: Option<U256>) -> eyre::Result<()> {
        let mut info = AccountInfo::default();
        if amount.is_some() {
            info.balance = amount.unwrap();
        }
        self.evm
            .borrow_mut()
            .db()
            .and_then(|db| Some(db.insert_account_info(address, info)));

        Ok(())
    }

    /// Get the account balance of the given account
    pub fn get_balance(&self, account: Address) -> U256 {
        match self.evm.borrow_mut().db().expect("evm db").basic(account) {
            Ok(Some(account)) => account.balance.into(),
            _ => U256::ZERO,
        }
    }

    pub fn deploy(&self, tx: TxEnv) -> eyre::Result<Address> {
        self.evm.borrow_mut().env.tx = tx;
        let (output, _, _) = self
            .evm
            .borrow_mut()
            .transact_commit()
            .map_err(|e| eyre::eyre!("error on deploy: {:?}", e))
            .and_then(|r| process_execution_result(r))?;

        match output {
            Output::Create(_, Some(address)) => Ok(address),
            _ => eyre::bail!("expected a create call"),
        }
    }

    // This is invoked in contract::call:FunctionCall
    pub fn call(&self, tx: TxEnv) -> eyre::Result<Vec<u8>> {
        self.evm.borrow_mut().env.tx = tx;
        match self.evm.borrow_mut().transact_ref() {
            Ok(ResultAndState { result, .. }) => {
                let (r, _, _) = process_result_with_value(result)?;
                Ok(r)
            }
            _ => eyre::bail!("error with read..."),
        }
    }

    // This is invoked in contract::call:FunctionCall
    pub fn send_transaction(&self, tx: TxEnv) -> eyre::Result<(Vec<u8>, u64, Vec<Log>)> {
        self.evm.borrow_mut().env.tx = tx;
        match self.evm.borrow_mut().transact_commit() {
            Ok(result) => {
                let (b, gas, logs) = process_result_with_value(result)?;
                //let rlogs = into_ether_raw_log(logs);
                Ok((b, gas, logs))
            }
            _ => eyre::bail!("error with write..."),
        }
    }
}

/// helper to extract results
fn process_execution_result(result: ExecutionResult) -> eyre::Result<(Output, u64, Vec<Log>)> {
    match result {
        ExecutionResult::Success {
            output,
            gas_used,
            logs,
            ..
        } => Ok((output, gas_used, logs)),
        ExecutionResult::Revert { output, .. } => eyre::bail!("Failed due to revert: {:?}", output),
        ExecutionResult::Halt { reason, .. } => eyre::bail!("Failed due to halt: {:?}", reason),
    }
}

fn process_result_with_value(result: ExecutionResult) -> eyre::Result<(Vec<u8>, u64, Vec<Log>)> {
    let (output, gas_used, logs) = process_execution_result(result)?;
    let bits = match output {
        Output::Call(value) => value,
        _ => eyre::bail!("expected call output"),
    };

    Ok((bits.to_vec(), gas_used, logs))
}
