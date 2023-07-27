/// Container for Logs on the Python side
/// @todo future work on logs
/* 
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
*/