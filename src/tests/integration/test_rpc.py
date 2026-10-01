from __future__ import annotations

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
DEBUG_ACTUAL_OUTPUT: Final = False


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
        if type(payload) is not list:
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
        if type(payload) is not list:
            payload = [payload]
        if type(payload) is list:
            request_result = execute_json_rpc(server, payload)

        assert_or_update_output(
            request_result, OUTPUT_FILES / f'{test_id}.expected.json', update=update_expected_output
        )


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
