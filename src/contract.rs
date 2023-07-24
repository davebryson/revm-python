use ethers::abi::Abi;
use pyo3::prelude::*;

/// Utility to parse ABI. Primarily used to extract information needed
/// to encode/decode inputs, outputs, and log events.
#[pyclass(name = "AbiParser")]
#[derive(Clone, Debug)]
pub struct ContractParser {
    inner: AbiHelperInner,
}

#[pymethods]
impl ContractParser {
    /// Load and ABI from string format
    #[staticmethod]
    pub fn load(raw: &str) -> Self {
        Self {
            inner: AbiHelperInner::from(raw),
        }
    }

    /// Load inline ABI information for example...
    #[staticmethod]
    pub fn parse_abi(human: Vec<&str>) -> Self {
        Self {
            inner: AbiHelperInner::from(human),
        }
    }

    /// Get required constructor input if any
    pub fn constructor_params(_self: PyRef<'_, Self>) -> Option<Vec<String>> {
        _self.inner.constructor_params()
    }

    /// Parse ABI and return the input and out parameters to encode/decode with python eth_utils
    pub fn function_params(_self: PyRef<'_, Self>, name: &str) -> (Vec<String>, Vec<String>) {
        _self.inner.function_params(name)
    }
}

/// We implement this separately so we can test it independently of the Python version above
#[derive(Debug, Clone)]
pub(crate) struct AbiHelperInner {
    abi: ethers::abi::Abi,
}

impl AbiHelperInner {
    /// Get required constructor input if any
    pub(crate) fn constructor_params(&self) -> Option<Vec<String>> {
        if self.abi.constructor.is_none() {
            return None;
        }
        let constructor = self.abi.constructor.as_ref().unwrap();
        let r = constructor
            .inputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();
        Some(r)
    }

    /// Parse ABI and return the input and out parameters to encode/decode with python eth_utils
    pub(crate) fn function_params(&self, name: &str) -> (Vec<String>, Vec<String>) {
        let ins = self
            .abi
            .function(name)
            .unwrap()
            .inputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();

        let outs = self
            .abi
            .function(name)
            .unwrap()
            .outputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>();
        (ins, outs)
    }

    // @todo decide how to use for log parsing
    #[allow(dead_code)]
    pub(crate) fn event_params(&self, name: &str) -> Vec<String> {
        // @note Can get the event signature from Event
        self.abi
            .event(name)
            .unwrap()
            .inputs
            .iter()
            .map(|entry| entry.kind.to_string())
            .collect::<Vec<String>>()
    }

    /*
     * Explore for log parsing
    pub(crate) fn parse_log(
        &self,
        name: &str,
        topics: Vec<Vec<u8>>,
        data: Vec<u8>,
    ) -> anyhow::Result<()> {
        let event = self.abi.event(name)?;
        // event.inputs.
        // event.signature();

        let tokens = event
            .parse_log(RawLog {
                topics,
                data: data.to_vec(),
            })?
            .params
            .into_iter()
            .map(|param| param.value)
            .collect::<Vec<_>>();

        Ok(())
    }
    */
}

impl From<&str> for AbiHelperInner {
    fn from(abi: &str) -> Self {
        let abi = serde_json::from_str::<Abi>(&abi).unwrap();
        Self { abi }
    }
}

impl From<Vec<&str>> for AbiHelperInner {
    fn from(abi: Vec<&str>) -> Self {
        let abi = ethers::abi::parse_abi(&abi).unwrap();
        Self { abi }
    }
}

impl From<serde_json::Value> for AbiHelperInner {
    fn from(abi_value: serde_json::Value) -> Self {
        let abi = serde_json::from_value::<Abi>(abi_value["abi"].clone()).unwrap();
        Self { abi }
    }
}

#[cfg(test)]
mod tests {
    use crate::contract::AbiHelperInner;

    fn extract_abi_helper(rabi: &str) -> String {
        let abijson: serde_json::Value = serde_json::from_str(rabi).unwrap();
        serde_json::to_string(&abijson["abi"]).unwrap()
    }

    #[test]
    fn parse_erc20() {
        let raw = include_str!("../example/contracts/mockERC20.json");
        let abistr: &str = &extract_abi_helper(&raw);

        let abi = AbiHelperInner::from(abistr);

        let (i, o) = abi.function_params("transfer");
        assert_eq!(vec!["address", "uint256"], i);
        assert_eq!(vec!["bool"], o);

        let args = abi.constructor_params();
        assert!(args.is_some());
        assert_eq!(vec!["string", "string", "uint8"], args.unwrap());

        let evts = abi.event_params("Transfer");
        println!("{:?}", evts);
    }
}
