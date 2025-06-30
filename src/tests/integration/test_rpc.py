from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

import pytest
import requests
import gzip

from .conftest import SERVER_HOST
from .utils import INPUT_FILES, OUTPUT_FILES, TEST_DATA_DIR, assert_or_update_output

if TYPE_CHECKING:
    from kontrol_node.rpc import StatefulKJsonRpcServer


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
    server: StatefulKJsonRpcServer,
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

                # method `anvil_dumpState` compresses `result` with gzip, whose output is flaky
                # therefore decompress the result prior to comparing with saved output, whose result was also decompressed
                if request["method"]=='anvil_dumpState':
                    result = request_result["result"][2:]
                    result = bytes.fromhex(result)
                    result = gzip.decompress(result).hex()
                    request_result['result'] = '0x' + result
                
                response_list.append(request_result)
            result = json.dumps(response_list, indent=2)
        assert_or_update_output(result, OUTPUT_FILES / f'{test_id}.expected.json', update=update_expected_output)
