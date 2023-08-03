use alloy_json_abi::{ContractObject, Function, JsonAbi, StateMutability};
use pyo3::prelude::*;

///
/// Abi utilities using ethers to parse abi and extract contract
/// function information used in the python contract class
///

#[pyclass]
pub struct ContractInfo {
    #[pyo3(get)]
    pub functions: Vec<ContractFunction>,
    #[pyo3(get)]
    pub constructor_params: Option<Vec<String>>,
    #[pyo3(get)]
    pub bytecode: Option<Vec<u8>>,
}

#[pymethods]
impl ContractInfo {
    #[staticmethod]
    pub fn load(raw: &str) -> Self {
        Self::from(raw)
    }
}

impl From<&str> for ContractInfo {
    fn from(abi: &str) -> Self {
        let co = serde_json::from_str::<ContractObject>(&abi).unwrap();
        let (fns, cp) = build_contract_info(co.abi);
        Self {
            functions: fns,
            constructor_params: cp,
            bytecode: co.bytecode.and_then(|i| Some(i.to_vec())),
        }
    }
}

fn build_contract_info(abi: JsonAbi) -> (Vec<ContractFunction>, Option<Vec<String>>) {
    let funcs = abi.functions().map(|f| map_function(f.clone())).collect();
    let const_params = abi.constructor.as_ref().and_then(|c| {
        Some(
            c.inputs
                .iter()
                .map(|entry| entry.ty.to_string())
                .collect::<Vec<String>>(),
        )
    });
    (funcs, const_params)
}

/*
impl From<Vec<&str>> for ContractInfo {
    fn from(abi: Vec<&str>) -> Self {
        let abi = ethers::abi::parse_abi(&abi).unwrap();
        build_contract_info(abi)
    }
}
*/

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
    func_out.signature = f.selector();
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
        .map(|entry| entry.ty.to_string())
        .collect::<Vec<String>>();

    func_out.outs = f
        .outputs
        .iter()
        .map(|entry| entry.ty.to_string())
        .collect::<Vec<String>>();

    return func_out;
}

#[cfg(test)]
mod tests {

    use alloy_json_abi::ContractObject;

    use super::ContractInfo;

    #[test]
    fn parse_contract_object() {
        let raw = include_str!("../tests/fixtures/counter.json");
        let co = serde_json::from_str::<ContractObject>(raw).unwrap();
        assert!(co.bytecode.is_some());
        assert_eq!(4, co.abi.functions.len());
        assert_eq!(0, co.abi.events.len());
    }

    #[test]
    fn parse_contract_info() {
        let raw = include_str!("../tests/fixtures/counter.json");
        let ci = ContractInfo::load(raw);
        assert_eq!(4, ci.functions.len());
        assert!(ci.constructor_params.is_none());
        assert!(ci.bytecode.is_some());

        let a = &ci.functions[0];
        println!("sig: {:?}", a);
    }
}
