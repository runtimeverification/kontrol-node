from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
from typing import Final

import pytest
import requests

TEST_DATA_DIR: Final = (Path(__file__).parent / 'test-data').resolve(strict=True)
INPUT_FILES: Final = TEST_DATA_DIR / 'input'
OUTPUT_FILES: Final = TEST_DATA_DIR / 'output'
RPC_TESTS_ALL: Final = tuple((TEST_DATA_DIR / 'rpc-tests-all').read_text().splitlines())
RPC_TESTS_SKIPPED: Final = tuple((TEST_DATA_DIR / 'rpc-tests-skipped').read_text().splitlines())
DEBUG_ACTUAL_OUTPUT: Final = True


def execute_json_rpc(server_url: str, payload: dict | list) -> str:
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(payload), headers=headers)
    return json.dumps(response.json(), indent=2, sort_keys=True)


@pytest.mark.parametrize('test_id', RPC_TESTS_ALL)
def test_rpc_file(
    test_id: str,
    server: str,
    update_expected_output: bool,
) -> None:
    if test_id in RPC_TESTS_SKIPPED:
        pytest.skip()

    with open(INPUT_FILES / f'{test_id}.in.json') as test_file:
        payload = json.loads(test_file.read())
        if type(payload) is dict:
            payload = [payload]
        if type(payload) is list:
            response_list = []
            for request in payload:
                request_result = execute_json_rpc(server, request)
                request_result = json.loads(request_result)
                response_list.append(request_result)
            result = json.dumps(response_list, indent=2, sort_keys=True)
        assert_or_update_output(result, OUTPUT_FILES / f'{test_id}.expected.json', update=update_expected_output)


@pytest.mark.parametrize('test_id', RPC_TESTS_ALL)
def test_rpc_file_batched(
    test_id: str,
    server: str,
    update_expected_output: bool,
) -> None:
    if test_id in RPC_TESTS_SKIPPED:
        pytest.skip()

    with open(INPUT_FILES / f'{test_id}.in.json') as test_file:
        payload = json.loads(test_file.read())
        if type(payload) is dict:
            payload = [payload]
        if type(payload) is list:
            request_result = execute_json_rpc(server, payload)

        assert_or_update_output(
            request_result, OUTPUT_FILES / f'{test_id}.expected.json', update=update_expected_output
        )


@pytest.mark.skip(reason='Disabled')
@pytest.mark.parametrize('test_id', RPC_TESTS_ALL)
def test_anvil_compatibility(
    test_id: str,
    server: str,
    anvil: str,
) -> None:
    """
    Test the JSON-RPC server by comparing its responses to those of an Anvil instance for a set of predefined test cases.
    """

    if test_id in RPC_TESTS_SKIPPED:
        pytest.skip()

    with open(INPUT_FILES / f'{test_id}.in.json') as test_file:
        payload = json.loads(test_file.read())
        if type(payload) is dict:
            payload = [payload]
        if type(payload) is list:
            for request in payload:
                kontrol_result = execute_json_rpc(server, request)
                kontrol_result = json.loads(kontrol_result)
                anvil_result = execute_json_rpc(anvil, request)
                anvil_result = json.loads(anvil_result)
                if request['method'] == 'anvil_dumpState':
                    print('Kontrol Node Result')
                    print(json.dumps(kontrol_result['result'], indent=2, sort_keys=True))
                    print('Anvil Result')
                    anvil_snapshot = decode_snapshot(anvil_result['result'], compressed=True)
                    anvil_uncompressed = encode_snapshot(anvil_snapshot, compressed=False)
                    anvil_result['result'] = anvil_uncompressed
                    print(json.dumps(anvil_snapshot, indent=2, sort_keys=True))
                assert kontrol_result == anvil_result


### Snapshot utilities


def normalize_snapshot(hex_data: str) -> str:
    """
    Normalize the snashot data for comparison.
    1. The RPC method `anvil_dumpState` compresses `result` with gzip, whose
    output is flaky therefore decompress the result prior to comparing with
    saved output, whose result was also decompressed.
    2. Additionally, json.dumps is unstable for dictionary entries therefore
    sort the encoded json text dict entries
    """
    snapshot_data = decode_snapshot(hex_data, compressed=True)
    normalized_hex = encode_snapshot(snapshot_data, compressed=True)
    return normalized_hex


def decode_snapshot(hex_data: str, compressed: bool = True) -> dict:
    """Decode the hex-encoded gzip-compressed snapshot data."""
    if hex_data.startswith('0x'):
        hex_data = hex_data[2:]
    compressed_data = bytes.fromhex(hex_data)
    decompressed_data = gzip.decompress(compressed_data) if compressed else compressed_data
    snapshot_data = json.loads(decompressed_data.decode('utf-8'))
    return snapshot_data


def encode_snapshot(snapshot_data: dict, compressed: bool = True) -> str:
    """Encode the snapshot data as hex-encoded gzip-compressed data."""
    json_data = json.dumps(snapshot_data, sort_keys=True).encode('utf-8')
    compressed_data = gzip.compress(json_data) if compressed else json_data
    hex_data = '0x' + compressed_data.hex()
    return hex_data


def assert_or_update_output(actual_text: str, expected_file: Path, *, update: bool) -> None:
    if update:
        expected_file.write_text(actual_text)
    else:
        assert expected_file.is_file()
        expected_text = expected_file.read_text()
        if DEBUG_ACTUAL_OUTPUT:
            with open(f'{os.getcwd()}/ACTUAL.json', 'w') as f:
                f.write(actual_text)
            with open(f'{os.getcwd()}/EXPECTED.json', 'w') as f:
                f.write(expected_text)
        assert actual_text == expected_text
