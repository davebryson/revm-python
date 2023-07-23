use ethers::abi::Abi;
use pyo3::prelude::*;

/// Utility to parse ABI. Primarily used to extract information needed
/// to encode/decode inputs, outputs, and log events.
#[pyclass]
#[derive(Clone, Debug)]
pub struct ContractParser {
    abi: ethers::abi::Abi,
}

#[pymethods]
impl ContractParser {
    /// Load and ABI from string format
    #[staticmethod]
    pub fn load(raw: &str) -> Self {
        Self::from(raw)
    }

    /// Load inline ABI information for example...
    #[staticmethod]
    pub fn parse_abi(human: Vec<&str>) -> Self {
        Self::from(human)
    }

    /// Get required constructor input if any
    pub fn constructor_params(_self: PyRef<'_, Self>) -> Option<Vec<String>> {
        if _self.abi.constructor.is_none() {
            return None;
        }
        let constructor = _self.abi.constructor.as_ref().unwrap();
        let r = constructor
            .inputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();
        Some(r)
    }

    /// Parse ABI and return the input and out parameters to encode/decode with python eth_utils
    pub fn function_params(_self: PyRef<'_, Self>, name: &str) -> (Vec<String>, Vec<String>) {
        let ins = _self
            .abi
            .function(name)
            .unwrap()
            .inputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();

        let outs = _self
            .abi
            .function(name)
            .unwrap()
            .outputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();
        (ins, outs)
    }
}

impl From<&str> for ContractParser {
    fn from(abi: &str) -> Self {
        let abi = serde_json::from_str::<Abi>(&abi).unwrap();
        Self { abi }
    }
}

impl From<Vec<&str>> for ContractParser {
    fn from(abi: Vec<&str>) -> Self {
        let abi = ethers::abi::parse_abi(&abi).unwrap();
        Self { abi }
    }
}
