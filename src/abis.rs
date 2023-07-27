use ethers::abi::{Abi, Function, StateMutability};
use pyo3::prelude::*;

#[pyclass]
pub struct ContractInfo {
    #[pyo3(get)]
    pub functions: Vec<ContractFunction>,
    #[pyo3(get)]
    pub constructor_params: Option<Vec<String>>,
}

#[pymethods]
impl ContractInfo {
    #[staticmethod]
    pub fn load(raw: &str) -> Self {
        Self::from(raw)
    }

    /// Load inline ABI information for example...
    #[staticmethod]
    pub fn parse_abi(human: Vec<&str>) -> Self {
        Self::from(human)
    }
}

fn build_contract_info(abi: Abi) -> ContractInfo {
    let funcs = abi.functions().map(|f| map_function(f.clone())).collect();
    let const_params = abi.constructor.as_ref().and_then(|c| {
        Some(
            c.inputs
                .iter()
                .map(|entry| entry.kind.to_string())
                .collect::<Vec<String>>(),
        )
    });
    ContractInfo {
        functions: funcs,
        constructor_params: const_params,
    }
}

impl From<&str> for ContractInfo {
    fn from(abi: &str) -> Self {
        let abi = serde_json::from_str::<Abi>(&abi).unwrap();
        build_contract_info(abi)
    }
}

impl From<Vec<&str>> for ContractInfo {
    fn from(abi: Vec<&str>) -> Self {
        let abi = ethers::abi::parse_abi(&abi).unwrap();
        build_contract_info(abi)
    }
}

#[pyclass]
#[derive(Clone, Debug, Default)]
pub struct ContractFunction {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub signature: [u8; 4],
    #[pyo3(get)]
    pub ins: Vec<String>,
    #[pyo3(get)]
    pub outs: Vec<String>,
    #[pyo3(get)]
    pub is_transact: bool,
    #[pyo3(get)]
    pub is_payable: bool,
}

#[pymethods]
impl ContractFunction {
    pub fn __str__(_self: PyRef<'_, Self>) -> String {
        return _self.name.clone();
    }
}

fn map_function(f: Function) -> ContractFunction {
    let mut func_out = ContractFunction::default();
    func_out.name = f.name.clone();
    func_out.signature = f.short_signature();
    match f.state_mutability {
        StateMutability::Pure | StateMutability::View => {
            func_out.is_transact = false;
            func_out.is_payable = false;
        }
        StateMutability::Payable => {
            func_out.is_transact = true;
            func_out.is_payable = true;
        }
        _ => {
            func_out.is_transact = true;
            func_out.is_payable = false;
        }
    }

    func_out.ins = f
        .inputs
        .iter()
        .map(|entry| entry.kind.to_string())
        .collect::<Vec<String>>();

    func_out.outs = f
        .outputs
        .iter()
        .map(|entry| entry.kind.to_string())
        .collect::<Vec<String>>();

    return func_out;
}
