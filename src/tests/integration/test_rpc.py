from __future__ import annotations

import gzip
import json
from typing import TYPE_CHECKING, Final

import pytest
import requests

from .conftest import SERVER_HOST
from .utils import INPUT_FILES, OUTPUT_FILES, TEST_DATA_DIR, assert_or_update_output

if TYPE_CHECKING:
    from kontrol_node.rpc import KontrolNodeServer


def execute_json_rpc(port: int, payload: dict) -> str:
    server_url = f'http://{SERVER_HOST}:{port}'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(payload), headers=headers)
    return json.dumps(response.json())


RPC_TESTS_ALL: Final = tuple((TEST_DATA_DIR / 'rpc-tests-all').read_text().splitlines())
RPC_TESTS_SKIPPED: Final = tuple((TEST_DATA_DIR / 'rpc-tests-skipped').read_text().splitlines())


@pytest.mark.parametrize('test_id', RPC_TESTS_ALL)
def test_rpc_file(
    test_id: str,
    server: KontrolNodeServer,
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
                request_result = execute_json_rpc(server.port(), request)
                request_result = json.loads(request_result)
                if request['method'] == 'anvil_dumpState':
                    snapshot = decode_snapshot(request_result['result'], compressed=True)
                    uncompressed = encode_snapshot(snapshot, compressed=False)
                    request_result['result'] = uncompressed

                response_list.append(request_result)
            result = json.dumps(response_list, indent=2, sort_keys=True)
        assert_or_update_output(result, OUTPUT_FILES / f'{test_id}.expected.json', update=update_expected_output)

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