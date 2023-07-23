use anyhow::bail;
use revm::{
    db::{CacheDB, DatabaseRef, EmptyDB},
    primitives::{AccountInfo, Address, ExecutionResult, Log, Output, ResultAndState, TransactTo},
    EVM,
};
use ruint::aliases::U256;

pub struct Executor {
    // @todo future should handle other DBs
    evm: EVM<CacheDB<EmptyDB>>,
}

impl Executor {
    pub fn new() -> Self {
        let mut evm = EVM::new();
        let db = CacheDB::new(EmptyDB {});
        evm.env.block.gas_limit = U256::MAX;
        //evm.env.block.basefee = U256::from(2000);

        // @todo make configurable to include base fee,etc...
        // evm.env.block.basefee = parse_ether(0.000001).unwrap().into();
        evm.database(db);
        Self { evm }
    }

    pub fn create_account(
        &mut self,
        address: Address,
        balance: Option<U256>,
    ) -> anyhow::Result<()> {
        let mut info = AccountInfo::default();
        if balance.is_some() {
            info.balance = balance.unwrap();
        }

        self.evm
            .db()
            .and_then(|db| Some(db.insert_account_info(address, info)));

        Ok(())
    }

    pub fn deploy(
        &mut self,
        deployer: Address,
        bincode: Vec<u8>,
        value: Option<U256>,
    ) -> anyhow::Result<(Address, u64)> {
        self.evm.env.tx.caller = deployer;
        self.evm.env.tx.transact_to = TransactTo::create();
        self.evm.env.tx.data = bincode.into();
        //self.evm.env.tx.gas_price = U256::from(3000);
        if value.is_some() {
            self.evm.env.tx.value = value.unwrap();
        }

        let result = match self.evm.transact_commit() {
            Ok(r) => r,
            Err(e) => bail!(format!("error with deploy tx: {:?}", e)),
        };
        let (output, gas, _) = process_execution_result(result)?;
        match output {
            Output::Create(_, Some(address)) => Ok((address.into(), gas)),
            _ => bail!("expected a create call"),
        }
    }

    pub fn send(
        &mut self,
        caller: Address,
        to: Address,
        value: Option<U256>,
        data: Option<Vec<u8>>,
    ) -> anyhow::Result<(Vec<u8>, u64, Vec<Log>)> {
        self.evm.env.tx.caller = caller;
        self.evm.env.tx.transact_to = TransactTo::Call(to);
        //let gas = self.evm.env.effective_gas_price();
        //self.evm.env.tx.gas_price = U256::from(3000);
        if value.is_some() {
            self.evm.env.tx.value = value.unwrap();
        }
        if data.is_some() {
            self.evm.env.tx.data = data.unwrap().into();
        }
        let result = match self.evm.transact_commit() {
            Ok(r) => r,
            Err(e) => bail!(format!("error with send: {:?}", e)),
        };
        process_result_with_value(result)
    }

    pub fn call(
        &mut self,
        caller: Address,
        to: Address,
        data: Vec<u8>,
    ) -> anyhow::Result<(Vec<u8>, u64, Vec<Log>)> {
        self.evm.env.tx.caller = caller;
        self.evm.env.tx.transact_to = TransactTo::Call(to);
        self.evm.env.tx.data = data.into();
        let result = match self.evm.transact_ref() {
            Ok(ResultAndState { result, .. }) => result,
            _ => bail!("call: error with simulate write..."),
        };
        process_result_with_value(result)
    }

    pub fn get_balance(&mut self, address: Address) -> U256 {
        let db = self.evm.db().expect("evm db");
        match db.basic(address) {
            Ok(Some(account)) => account.balance,
            _ => U256::ZERO,
        }
    }
}

fn process_execution_result(result: ExecutionResult) -> anyhow::Result<(Output, u64, Vec<Log>)> {
    match result {
        ExecutionResult::Success {
            output,
            gas_used,
            logs,
            ..
        } => Ok((output, gas_used, logs)),
        ExecutionResult::Revert { output, .. } => bail!("Failed due to revert: {:?}", output),
        ExecutionResult::Halt { reason, .. } => bail!("Failed due to halt: {:?}", reason),
    }
}

fn process_result_with_value(result: ExecutionResult) -> anyhow::Result<(Vec<u8>, u64, Vec<Log>)> {
    let (output, gas_used, logs) = process_execution_result(result)?;
    let bits = match output {
        Output::Call(value) => value,
        _ => bail!("expected call output"),
    };

    Ok((bits.into(), gas_used, logs))
}

#[cfg(test)]
mod tests {
    use super::Executor;
    use revm::primitives::Address;
    use ruint::aliases::U256;

    #[test]
    fn basics() {
        let bob = Address::from_low_u64_be(1);
        let alice = Address::from_low_u64_be(2);
        let bal = U256::from(1000000);

        let mut evm = Executor::new();
        assert!(evm.create_account(bob, Some(bal)).is_ok());
        assert!(evm.create_account(alice, Some(bal)).is_ok());

        assert_eq!(bal, evm.get_balance(bob));
        assert_eq!(bal, evm.get_balance(alice));

        evm.send(bob, alice, Some(U256::from(50)), None).unwrap();
        let result = evm.get_balance(alice);

        println!("{:}", result);
        println!("{:}", evm.get_balance(bob));
    }
}
