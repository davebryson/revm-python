use pyo3::{
    exceptions::{PyRuntimeError, PyTypeError},
    prelude::*,
};
use revm::primitives::{TransactTo, TxEnv, B160};
use ruint::aliases::U256;
use std::fmt::Debug;

mod abis;
mod evm;

// adapted from https://github.com/gakonst/pyrevm/tree/master
pub(crate) fn pyerr<T: Debug>(err: T) -> pyo3::PyErr {
    PyRuntimeError::new_err(format!("{:?}", err))
}

pub(crate) fn addr(addr: &str) -> Result<B160, PyErr> {
    addr.parse::<B160>()
        .map_err(|_| PyTypeError::new_err("failed to parse address from str"))
}

fn address_helper(caller: &str, receiver: Option<&str>) -> (B160, Option<B160>) {
    let caller = addr(caller)
        .map_err(pyerr)
        .expect("valid address for caller");
    if receiver.is_some() {
        let rec = addr(receiver.unwrap())
            .map_err(pyerr)
            .expect("valid address for receiver");
        return (caller, Some(rec));
    }
    return (caller, None);
}

#[pyclass]
pub struct EVM(evm::Executor);

#[pymethods]
impl EVM {
    #[new]
    fn new() -> PyResult<Self> {
        let m = evm::Executor::new();
        Ok(EVM(m))
    }

    fn deploy(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        bincode: Vec<u8>,
        value: U256,
    ) -> PyResult<(String, U256)> {
        let (deployer, _) = address_helper(caller, None);
        let mut tx = TxEnv::default();
        tx.caller = deployer;
        tx.transact_to = TransactTo::create();
        tx.data = bincode.into();
        tx.value = value;

        let (addy, gas) = _self.0.deploy(tx)?;

        let address = format!("{:?}", addy);
        Ok((address, U256::from(gas)))
    }

    fn create_account(mut _self: PyRefMut<'_, Self>, address: &str, balance: U256) -> PyResult<()> {
        let (caller, _) = address_helper(address, None);
        _self.0.create_account(caller, Some(balance.into()))?;
        Ok(())
    }

    fn get_balance(mut _self: PyRefMut<'_, Self>, address: &str) -> U256 {
        let (caller, _) = address_helper(address, None);
        let r = _self.0.get_balance(caller);
        r
    }

    /// Convienence helper for just sending eth
    fn transfer(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        to: &str,
        amount: U256,
    ) -> PyResult<u64> {
        let (ca, ta) = address_helper(caller, Some(to));
        let mut tx = TxEnv::default();
        tx.caller = ca;
        tx.transact_to = TransactTo::Call(ta.unwrap());
        tx.value = amount;

        let (_, g, _) = _self.0.transact(tx)?;
        Ok(g)
    }

    fn transact(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        to: &str,
        data: Vec<u8>,
        value: Option<U256>,
    ) -> PyResult<(Vec<u8>, u64)> {
        let (ca, ta) = address_helper(caller, Some(to));
        let mut write_tx = TxEnv::default();
        write_tx.caller = ca;
        write_tx.transact_to = TransactTo::Call(ta.unwrap());
        write_tx.data = data.into();
        if value.is_some() {
            write_tx.value = value.unwrap();
        }

        // note: ignoring logs for now...add later
        let (b, g, _) = _self.0.transact(write_tx)?;

        Ok((b, g))
    }

    ///
    fn call(mut _self: PyRefMut<'_, Self>, to: &str, data: Vec<u8>) -> PyResult<(Vec<u8>, u64)> {
        let (ta, _) = address_helper(to, None);
        let mut read_tx = TxEnv::default();
        read_tx.transact_to = TransactTo::Call(ta);
        read_tx.data = data.into();

        let (b, g, _) = _self.0.call(read_tx).map_err(pyerr)?;

        Ok((b, g))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn revm_py(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<EVM>()?;
    m.add_class::<abis::ContractInfo>()?;

    Ok(())
}
