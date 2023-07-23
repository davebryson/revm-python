from revm_py import ContractParser
import json
import pytest

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


def test_human_readable_parser():
    abi = ContractParser.parse_abi(
        [
            "function hello(address, uint256) external returns (uint256)",
            "function another() returns (bool)",
        ]
    )
    ins, outs = abi.function_params("hello")
    assert len(ins) == 2
    assert len(outs) == 1
    assert ["address", "uint256"] == ins
    assert ["uint256"] == outs

    ins1, outs1 = abi.function_params("another")
    assert [] == ins1
    assert ["bool"] == outs1

    with pytest.raises(BaseException):
        # Bad input
        ContractParser.parse_abi(
            [
                "function another returns (bool)",
            ]
        )


def test_json_file():
    raw = json.dumps(ABI)
    abi = ContractParser.load(raw)
    ins, outs = abi.function_params("number")
    assert len(ins) == 0
    assert len(outs) == 1
    assert [] == ins
    assert ["uint256"] == outs

    ins1, outs1 = abi.function_params("setNumber")
    assert ["uint256"] == ins1
    assert [] == outs1

    with pytest.raises(BaseException):
        abi.function_params("nope")

    with pytest.raises(BaseException):
        ContractParser.load("abcd")
