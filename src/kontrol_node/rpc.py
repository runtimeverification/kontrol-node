from __future__ import annotations

import atexit
import cProfile
import gzip
import json
import logging
import os
import shutil
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pyk.kdist import kdist
from pyk.konvert._utils import munge
from pyk.kore.prelude import BOOL, INT, SORT_K_ITEM, bool_dv, inj, int_dv, str_dv, top_cell_initializer
from pyk.kore.syntax import App, SortApp
from pyk.ktool.krun import llvm_interpret

if TYPE_CHECKING:
    from pyk.kore.syntax import Pattern

    from kontrol_node.options import VMOptions

_LOGGER: Final = logging.getLogger(__name__)

_PROFILING: Final[bool] = False

_DEBUG_KORE: Final[bool] = False

# Simbolik needs at minimum the following RPC methods
# eth_sendTransaction
# eth_getTransactionByHash
# eth_getTransactionReceipt
# eth_getCode
# eth_getBlockByNumber
# eth_getBlockByHash
# eth_getTransactionCount
# eth_getStorageAt
# anvil_stateDump
# debug_traceTransaction

# requests.json                                <- JSON-RPC requests
# blocks/block_0.json                          <- The initial StateDump (genesis state)
# blocks/block_<block number>.json             <- StateDump
# transactions/traces/trace_<tx hash>.jsonl    <- JSON lines consisting of TraceItems
# transactions/receipts/receipt_<tx hash>.json <- TransactionReceipt
# transactions/results/result_<tx hash>.json   <- TransactionResult


class KontrolNodeServer:
    options: VMOptions

    def __init__(self, options: VMOptions) -> None:
        self.options = options
        print(f'Initialized KontrolNodeServer with options: {self.options}')

    def serve(self) -> None:
        _LOGGER.info(f'Starting JSON-RPC server at {self.options.host}:{self.options.port}')
        self.handler, self.interpreter = create_handler()
        self.http_server = HTTPServer((self.options.host, int(self.options.port)), self.handler)
        self.http_server.serve_forever()
        _LOGGER.info(f'JSON-RPC server at {self.options.host}:{self.options.port} shut down.')

    def shutdown(self) -> None:
        if self.http_server:
            self.http_server.shutdown()
        if self.interpreter:
            self.interpreter.shutdown()

    def port(self) -> int:
        return self.http_server.server_port


class InterpreterProcess:
    """
    The Python server and K semantics communicate with each other via two files
    `requests.json` and `response.json`.
    The Python sever writes the request to the `requests.json` file.
    It then runs the K interpreter.
    The interpreter reads the `requests.json` file, proccesses the request, and writes
    the response to the `response.json` file.
    """

    io_dir: Path

    def __init__(self) -> None:
        self._setup_io_dir()
        atexit.register(self.shutdown)

    def _setup_io_dir(self) -> None:
        self.io_dir = Path(tempfile.mkdtemp(prefix='io_dir', dir=os.getcwd()))
        (self.io_dir / 'blocks').mkdir(parents=True, exist_ok=True)
        (self.io_dir / 'transactions').mkdir(parents=True, exist_ok=True)
        genesis_src = Path(__file__).resolve().parent / 'genesis.json'
        genesis_dst = self.io_dir / 'blocks' / 'block_0.json'
        shutil.copyfile(genesis_src, genesis_dst)
        metadata = {'latest_block_number': 0}
        metadata_file = self.io_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

    def _run(self) -> Pattern:
        # Create the initial KORE configuration
        initial_kore = _kore_pgm_to_kore(
            pgm=_start_kore(str(self.io_dir)),
            pattern_sort=SortApp('SortEthereumSimulation'),
            schedule='PRAGUE',
            mode='NORMAL',
            chainid=31337,
            usegas=True,
        )
        # Write input.kore for debugging
        if _DEBUG_KORE:
            with open('input.kore', 'w') as f:
                f.write(initial_kore.text)
        result = llvm_interpret(definition_dir=kdist.get('kontrol-node.simbolik'), pattern=initial_kore, check=False)
        return result

    def request(self, payload: bytes) -> bytes:
        # remove old response file if it exists
        response_file = self._response_file()
        if response_file.exists():
            response_file.unlink()

        try:
            json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            return json.dumps(
                {
                    'jsonrpc': '2.0',
                    'error': {
                        'code': -32700,
                        'message': 'Parse error',
                    },
                }
            ).encode('utf-8')

        # write request to file
        with open(self._request_file(), 'wb') as f:
            f.write(payload)
        # run the interpreter
        output = self._run()
        if _DEBUG_KORE:
            # write output.kore for debugging
            with open('output.kore', 'w') as f:
                f.write(output.text)
        # read response from file
        with open(self._response_file(), 'rb') as f:
            response = f.read()

        # response = self._postprocess(request_data, response)

        return response

    def shutdown(self) -> None:
        shutil.rmtree(self.io_dir, ignore_errors=True)

    def _request_file(self) -> Path:
        return self.io_dir / 'request.json'

    def _response_file(self) -> Path:
        return self.io_dir / 'response.json'

    def _postprocess(self, request_data: dict, response_data: bytes) -> bytes:
        if request_data.get('method') == 'anvil_dumpState':
            response_json = json.loads(response_data.decode('utf-8'))
            result = response_json.get('result', {})
            result_bytes = json.dumps(result).encode('utf-8')
            compressed_data = gzip.compress(result_bytes)
            hex_data = '0x' + compressed_data.hex()
            response_json['result'] = hex_data
            response_data = json.dumps(response_json).encode('utf-8')
        return response_data


def create_handler() -> tuple[type[BaseHTTPRequestHandler], InterpreterProcess]:

    interpreter = InterpreterProcess()

    class KontrolNodeHandler(BaseHTTPRequestHandler):

        def do_POST(self) -> None:  # noqa: N802
            if _PROFILING:
                profile = cProfile.Profile()
                profile.enable()
                os.makedirs('profiling', exist_ok=True)

            content_len = self.headers.get('Content-Length')
            assert type(content_len) is str
            content = self.rfile.read(int(content_len))

            result = interpreter.request(content)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(result)))
            self.end_headers()
            self.wfile.write(result)

            if _PROFILING:
                profile.disable()
                transaction_hash = 'TODO'
                filename = f'profiling/profiling-{transaction_hash}.prof'
                profile.dump_stats(filename)

    return (KontrolNodeHandler, interpreter)


def _start_kore(io_dir: str) -> App:
    return inj(SortApp('SortStart'), SortApp('SortEthereumSimulation'), App('Lblstart', [], [str_dv(str(io_dir))]))


def _kore_pgm_to_kore(pgm: Pattern, pattern_sort: SortApp, schedule: str, mode: str, chainid: int, usegas: bool) -> App:
    config = {
        '$PGM': inj(pattern_sort, SORT_K_ITEM, pgm),
        '$SCHEDULE': inj(SortApp('SortSchedule'), SORT_K_ITEM, _schedule_to_kore(schedule)),
        '$MODE': inj(SortApp('SortMode'), SORT_K_ITEM, _mode_to_kore(mode)),
        '$CHAINID': inj(INT, SORT_K_ITEM, int_dv(chainid)),
        '$USEGAS': inj(BOOL, SORT_K_ITEM, bool_dv(usegas)),
        '$IO': str_dv('on'),
    }
    return top_cell_initializer(config)


def _schedule_to_kore(schedule: str) -> App:
    return App(f"Lbl{munge(schedule)}'Unds'EVM")


def _mode_to_kore(mode: str) -> App:
    return App(f'Lbl{mode}')
