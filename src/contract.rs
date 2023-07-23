use ethers::abi::Abi;
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone, Debug)]
pub struct ContractParser {
    abi: ethers::abi::Abi,
}

#[pymethods]
impl ContractParser {
    #[staticmethod]
    pub fn load(raw: &str) -> Self {
        Self::from(raw)
    }

    #[staticmethod]
    pub fn parse_abi(human: Vec<&str>) -> Self {
        Self::from(human)
    }

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

    /// Parse ABI and return the input and out parameters for use with python eth_utils
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

#[cfg(test)]
mod tests {

    #[test]
    fn parse_stuff() {
        //let abi =
        //    parse_abi(&["function x(address, uint256) external view returns (uint256)"]).unwrap();

        //let contract = ContractParser::parse_abi(
        //    ["function x(address, uint256) external view returns (uint256)"].to_vec(),
        //);

        //let (i, o) = contract.function_params("x");
        /*
        let func = abi.function("x").unwrap();
        let ins = func
            .inputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();

        let outs = func
            .outputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();
        */

        //println!("input: {:?}", i);
        //println!("output: {:?}", o);
    }
}
