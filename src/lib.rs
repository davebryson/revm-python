use pyo3::{
    exceptions::{PyRuntimeError, PyTypeError},
    prelude::*,
};
use revm::primitives::{TransactTo, TxEnv, B160};
use ruint::aliases::U256;
use std::fmt::Debug;

mod abis;
mod contract;
mod evm;

use contract::{ContractParser, FuncOutput};

// adapted from https://github.com/gakonst/pyrevm/tree/master
pub fn pyerr<T: Debug>(err: T) -> pyo3::PyErr {
    PyRuntimeError::new_err(format!("{:?}", err))
}

pub fn addr(addr: &str) -> Result<B160, PyErr> {
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

/// Container for Logs on the Python side
/// @todo handle parsing correctly
#[pyclass]
#[derive(Debug, Clone)]
pub struct LogInfo(revm::primitives::Log);

#[pymethods]
impl LogInfo {
    #[getter]
    fn address(_self: PyRef<'_, Self>) -> String {
        let bits: &[u8] = _self.0.address.as_bytes();
        format!("0x{}", hex::encode(bits))
    }

    #[getter]
    fn topics(_self: PyRef<'_, Self>) -> Vec<Vec<u8>> {
        _self
            .0
            .topics
            .iter()
            .map(|i| i.to_vec())
            .collect::<Vec<Vec<u8>>>()
    }

    #[getter]
    fn data(_self: PyRef<'_, Self>) -> Vec<u8> {
        _self.0.data.to_vec()
    }

    fn __str__(&self) -> PyResult<String> {
        Ok(format!("{:?}", self))
    }
}

impl From<revm::primitives::Log> for LogInfo {
    fn from(log: revm::primitives::Log) -> Self {
        LogInfo(log)
    }
}

fn convert_logs(ins: Vec<revm::primitives::Log>) -> Vec<LogInfo> {
    ins.iter()
        .map(|entry| entry.clone().into())
        .collect::<Vec<LogInfo>>()
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
    ) -> PyResult<(Vec<u8>, u64, Vec<LogInfo>)> {
        let (ca, ta) = address_helper(caller, Some(to));
        let mut write_tx = TxEnv::default();
        write_tx.caller = ca;
        write_tx.transact_to = TransactTo::Call(ta.unwrap());
        write_tx.data = data.into();
        if value.is_some() {
            write_tx.value = value.unwrap();
        }

        let (b, g, rlogs) = _self.0.transact(write_tx)?;

        //let (b, g, rlogs) = _self.0.send(ca, ta.unwrap(), value, Some(data))?;
        let plogs = convert_logs(rlogs);
        Ok((b, g, plogs))
    }

    fn call(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        to: &str,
        data: Vec<u8>,
    ) -> PyResult<(Vec<u8>, u64, Vec<LogInfo>)> {
        let (ca, ta) = address_helper(caller, Some(to));
        let mut read_tx = TxEnv::default();
        read_tx.caller = ca;
        read_tx.transact_to = TransactTo::Call(ta.unwrap());
        read_tx.data = data.into();

        let (b, g, rlogs) = _self.0.call(read_tx).map_err(pyerr)?;

        let plogs = convert_logs(rlogs);
        Ok((b, g, plogs))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn revm_py(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<EVM>()?;
    m.add_class::<ContractParser>()?;
    m.add_class::<LogInfo>()?;
    m.add_class::<FuncOutput>()?;

    //m.add_class::<abis::ContractFunction>()?;
    m.add_class::<abis::ContractInfo>()?;

    //m.add_function(wrap_pyfunction!(convert_types, m)?)?;

    Ok(())
}
