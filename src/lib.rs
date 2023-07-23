use pyo3::{
    exceptions::{PyRuntimeError, PyTypeError},
    prelude::*,
};
use revm::primitives::B160;
use ruint::aliases::U256;
use std::fmt::Debug;

mod contract;
mod evm;

use contract::ContractParser;

pub fn pyerr<T: Debug>(err: T) -> pyo3::PyErr {
    PyRuntimeError::new_err(format!("{:?}", err))
}

pub fn addr(addr: &str) -> Result<B160, PyErr> {
    addr.parse::<B160>()
        .map_err(|_| PyTypeError::new_err("failed to parse address from str"))
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
        value: Option<U256>,
    ) -> PyResult<(String, U256)> {
        let deployer = addr(caller).map_err(pyerr).expect("valid address");
        let (addy, gas) = _self.0.deploy(deployer, bincode, value)?;
        let address = format!("{:?}", addy);
        Ok((address, U256::from(gas)))
    }

    fn create_account(mut _self: PyRefMut<'_, Self>, address: &str, balance: U256) -> PyResult<()> {
        let addy = addr(address).map_err(pyerr).expect("valid address");
        _self.0.create_account(addy, Some(balance.into()))?;
        Ok(())
    }

    fn get_balance(mut _self: PyRefMut<'_, Self>, address: &str) -> U256 {
        let addy = addr(address).map_err(pyerr).expect("valid address");
        let r = _self.0.get_balance(addy);
        r
    }

    fn transfer(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        to: &str,
        amount: U256,
    ) -> PyResult<u64> {
        let ca = addr(caller).map_err(pyerr).expect("valid address");
        let ta = addr(to).map_err(pyerr).unwrap();
        let (_, g, _) = _self.0.send(ca, ta, Some(amount), None)?;
        Ok(g)
    }

    fn transact(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        to: &str,
        data: Vec<u8>,
        value: Option<U256>,
    ) -> PyResult<(Vec<u8>, u64)> {
        let ca = addr(caller).map_err(pyerr).expect("valid address");
        let ta = addr(to).map_err(pyerr).unwrap();
        let (b, g, _) = _self.0.send(ca, ta, value, Some(data))?;
        Ok((b, g))
    }

    fn call(
        mut _self: PyRefMut<'_, Self>,
        caller: &str,
        to: &str,
        data: Vec<u8>,
    ) -> PyResult<(Vec<u8>, u64)> {
        let ca = addr(caller).map_err(pyerr).expect("valid address");
        let ta = addr(to).map_err(pyerr).unwrap();
        let (b, g, _) = _self.0.call(ca, ta, data).map_err(pyerr)?;
        Ok((b, g))
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn revm_py(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<EVM>()?;
    m.add_class::<ContractParser>()?;

    Ok(())
}
