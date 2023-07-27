use anyhow::bail;
use revm::{
    db::{CacheDB, DatabaseRef, EmptyDB},
    primitives::{AccountInfo, Address, ExecutionResult, Log, Output, ResultAndState, TxEnv},
    EVM,
};
use ruint::aliases::U256;

pub struct Executor {
    // @todo handle forks
    evm: EVM<CacheDB<EmptyDB>>,
}

impl Executor {
    pub fn new() -> Self {
        let mut evm = EVM::new();
        let db = CacheDB::new(EmptyDB {});
        evm.env.block.gas_limit = U256::MAX;
        // @todo make configurable to include base fee?
        evm.database(db);
        Self { evm }
    }

    /// Create and account with an optional balance
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

    /// Get the balance for the given address
    pub fn get_balance(&mut self, address: Address) -> U256 {
        let db = self.evm.db().expect("evm db");
        match db.basic(address) {
            Ok(Some(account)) => account.balance,
            _ => U256::ZERO,
        }
    }

    /// Deploy an contract
    pub fn deploy(&mut self, tx: TxEnv) -> anyhow::Result<(Address, u64)> {
        self.evm.env.tx = tx;

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

    /// Write transaction
    pub fn transact(&mut self, tx: TxEnv) -> anyhow::Result<(Vec<u8>, u64, Vec<Log>)> {
        self.evm.env.tx = tx;
        let result = match self.evm.transact_commit() {
            Ok(r) => r,
            Err(e) => bail!(format!("error with send: {:?}", e)),
        };
        process_result_with_value(result)
    }

    /// Read call
    pub fn call(&mut self, tx: TxEnv) -> anyhow::Result<(Vec<u8>, u64, Vec<Log>)> {
        self.evm.env.tx = tx;
        let result = match self.evm.transact_ref() {
            Ok(ResultAndState { result, .. }) => result,
            Err(e) => bail!("call: error: {:?}", e),
        };
        process_result_with_value(result)
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
        ExecutionResult::Revert { output, .. } => {
            bail!("Called failed due to revert: {:?}", output)
        }
        ExecutionResult::Halt { reason, .. } => bail!("Called failed due to halt: {:?}", reason),
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
    use revm::primitives::{Address, TransactTo, TxEnv};
    use ruint::aliases::U256;

    use ethers::abi::{Abi, JsonAbi};
    use ethers::prelude::*;

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

        let mut tx = TxEnv::default();
        tx.caller = bob;
        tx.transact_to = TransactTo::Call(alice);
        tx.value = U256::from(50);

        let r = evm.transact(tx);
        assert!(r.is_ok());

        let result = evm.get_balance(alice);
        assert_eq!(U256::from(1000050u32), result);

        let result2 = evm.get_balance(bob);
        assert_eq!(U256::from(999950u32), result2);
    }

    #[test]
    fn contract_read_write() {
        let raw = include_str!("../abm/bank_reserve/contract/BankReserve.json");
        let (a, b) = match serde_json::from_str::<JsonAbi>(raw) {
            Ok(JsonAbi::Object(o)) => {
                let abi1 = serde_json::to_string(&o.abi).unwrap();
                let abi = serde_json::from_str::<Abi>(&abi1).unwrap();
                if o.bytecode.is_none() {
                    panic!("missing bytecode")
                }
                (abi, o.bytecode.unwrap().to_vec())
            }
            _ => panic!("expected a full contract metadata json file"),
        };

        let contract = BaseContract::from(a);

        let bob = Address::from_low_u64_be(1);
        let deployer = Address::from_low_u64_be(2);
        let bal = U256::from(5000000000000000000u64);

        let mut evm = Executor::new();
        assert!(evm.create_account(bob, Some(bal)).is_ok());
        assert!(evm.create_account(deployer, Some(bal)).is_ok());

        // Encode deploy bytecode
        let bincode = contract
            .abi()
            .constructor()
            .unwrap()
            .encode_input(b, &[ethers::abi::Token::Uint(5000usize.into())])
            .unwrap();
        let mut tx = TxEnv::default();
        tx.caller = deployer;
        tx.transact_to = TransactTo::create();
        tx.data = bincode.into();

        let (ca, _) = evm.deploy(tx).unwrap();
        println!("{:?}", ca);

        // Do Write
        let encoded_write = contract.encode("depositToSavings", ()).unwrap();
        let mut write_tx = TxEnv::default();
        write_tx.caller = bob;
        write_tx.transact_to = TransactTo::Call(ca);
        write_tx.value = U256::from(1000000000000000000u64);
        write_tx.data = encoded_write.to_vec().into();

        let (_, g0, _) = evm.transact(write_tx).unwrap();

        // Do Read
        // encode
        let encoded_read = contract.encode::<H160>("savings", bob.into()).unwrap();
        let mut read_tx = TxEnv::default();
        read_tx.caller = bob;
        read_tx.transact_to = TransactTo::Call(ca);
        read_tx.data = encoded_read.to_vec().into();

        let (r, _, _) = evm.call(read_tx).unwrap();

        // decode
        let b = contract.decode_output::<u128, _>("savings", r).unwrap();
        assert_eq!(1000000000000000000u128, b);

        // Do Read
    }
}
