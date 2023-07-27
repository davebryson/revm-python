import json
import pytest

from revm_py import ContractInfo, load_contract_meta_from_file

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

    info = ContractInfo.parse_abi([])
    assert len(info.functions) == 0

    with pytest.raises(BaseException):
        ContractInfo.parse_abi("")


def test_abi_parse_from_str():
    raw = json.dumps(ABI)
    info = ContractInfo.load(raw)
    assert len(info.functions) == 3


def test_abi_parser_from_file():
    abistr, _ = load_contract_meta_from_file("./tests/fixtures/erc20.json")
    info = ContractInfo.load(abistr)
    assert len(info.functions) == 14
    result = filter(lambda f: f.name == "mint", info.functions)
    func = list(result)
    assert len(func) == 1
    assert func[0].ins == ["address", "uint256"]
    assert func[0].is_transact

    cp = info.constructor_params
    assert len(cp) == 3
    assert ["string", "string", "uint8"] == cp


def test_human_readable_parser():
    info = ContractInfo.parse_abi(
        [
            "function hello(address, uint256) external returns (uint256)",
            "function another() returns (bool)",
        ]
    )
    assert len(info.functions) == 2
    assert info.constructor_params == None
