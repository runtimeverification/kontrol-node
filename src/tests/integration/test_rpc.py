from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

import pytest
import requests

from .conftest import SERVER_HOST
from .utils import INPUT_FILES, OUTPUT_FILES, TEST_DATA_DIR, assert_or_update_output

if TYPE_CHECKING:
    from kontrol_node.rpc import StatefulKJsonRpcServer


def json_rpc_request_payload(port: int, payload: dict) -> str:
    server_url = f'http://{SERVER_HOST}:{port}'
    headers = {'Content-Type': 'application/json'}
    response = requests.post(server_url, data=json.dumps(payload), headers=headers)
    return json.dumps(response.json())


RPC_TESTS_ALL: Final = tuple((TEST_DATA_DIR / 'rpc-tests-all').read_text().splitlines())
RPC_TESTS_SKIPPED: Final = tuple((TEST_DATA_DIR / 'rpc-tests-skipped').read_text().splitlines())


@pytest.mark.parametrize('test_id', RPC_TESTS_ALL)
def test_rpc_file(
    test_id: str,
    server_instance: tuple[StatefulKJsonRpcServer, int],
    update_expected_output: bool,
) -> None:
    _, port = server_instance
    if test_id in RPC_TESTS_SKIPPED:
        pytest.skip()

    with open(INPUT_FILES / f'{test_id}.in.json', 'r') as test_file:
        payload = json.loads(test_file.read())
        result = json_rpc_request_payload(port, payload)
        assert_or_update_output(result, OUTPUT_FILES / f'{test_id}.expected.json', update=update_expected_output)
