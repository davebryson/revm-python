import json
import pytest

from revm_py import ContractInfo

ABI = [
    {
        "inputs": [],
        "name": "increment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "number",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "newNumber", "type": "uint256"}],
        "name": "setNumber",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def test_fails_parse_on_bad_input():
    with pytest.raises(BaseException):
        ContractInfo.load("")

    with pytest.raises(BaseException):
        # Expects full meta (w/bytecode)
        raw = json.dumps(ABI)
        ContractInfo.parse_abi(raw)


def test_abi_parser_from_file():
    with open("./tests/fixtures/erc20.json") as f:
        ercabi = f.read()
    info = ContractInfo.load(ercabi)
    assert len(info.functions) == 14

    # Check the mint function
    result = filter(lambda f: f.name == "mint", info.functions)
    func = list(result)
    assert len(func) == 1
    assert func[0].ins == ["address", "uint256"]
    assert func[0].is_transact

    cp = info.constructor_params
    assert len(cp) == 3
    assert ["string", "string", "uint8"] == cp

    assert len(info.bytecode) > 0
