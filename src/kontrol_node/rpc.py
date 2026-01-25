from __future__ import annotations

import cProfile
import logging
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pyk.kdist import kdist
from pyk.konvert._utils import munge
from pyk.kore.prelude import BOOL, INT, SORT_K_ITEM, bool_dv, inj, int_dv, str_dv, top_cell_initializer
from pyk.kore.syntax import App, SortApp

if TYPE_CHECKING:
    from pyk.kore.syntax import Pattern

    from kontrol_node.options import VMOptions

_LOGGER: Final = logging.getLogger(__name__)

_PROFILING: Final[bool] = False


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
        self.http_server = HTTPServer((self.options.host, self.options.port), handler())
        self.http_server.serve_forever()
        _LOGGER.info(f'JSON-RPC server at {self.options.host}:{self.options.port} shut down.')

    def shutdown(self) -> None:
        if self.http_server:
            self.http_server.shutdown()

    def port(self) -> int:
        return self.options.port


class InterpreterProcess:
    """
    The Python server and K semantics communicate with each other via files and stdin/stdout.
    Every requests is written to a temporary file. Then the K process is notified via stdin.
    When K has processed the request, it writes the response to another temporary file, and
    notifies the Python server via stdout. The python then reads the response and forwards
    it the client.
    """

    process: subprocess.Popen[bytes]
    output_buffer: bytes = b''
    output_reader: threading.Thread
    output_ready: threading.Event
    io_dir: Path

    def __init__(self) -> None:
        self.output_reader = threading.Thread(target=self._output_reader, daemon=True)
        self.output_ready = threading.Event()
        self.output_buffer = b''
        base_dir = Path(__file__).resolve().parent
        src_dir = base_dir.parent
        test_dir = src_dir / 'tests'
        self.io_dir = test_dir / 'integration' / 'io_dir'

    def run(self) -> None:
        # TODO: use an temporary directory
        # notice, we must copy the initial state dump there

        # Create the initial KORE configuration
        initial_kore = _kore_pgm_to_kore(
            pgm=_start_kore(str(self.io_dir)),
            pattern_sort=SortApp('SortEthereumSimulation'),
            schedule='PRAGUE',
            mode='NORMAL',
            chainid=1,
            usegas=True,
        )

        # Copy the initial KORE configuration to a file
        input_file = self.io_dir / 'input.kore'
        with open(input_file, 'w') as f:
            f.write(initial_kore.text)

        output_file = self.io_dir / 'output.kore'
        steps = '-1'
        interpreter: Path = kdist.get('kontrol-node.simbolik') / 'interpreter'

        self.process = subprocess.Popen(
            [str(interpreter), str(input_file), steps, str(output_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.output_reader.start()

    def request(self, payload: bytes) -> bytes:
        assert self.process.stdin and self.process.stdout
        with open(self._request_file(), 'wb') as f:
            f.write(payload)
        self.process.stdin.write(b'RequestReady')
        self.process.stdin.flush()
        self.output_ready.wait()
        self.output_ready.clear()
        with open(self._response_file(), 'rb') as f:
            response = f.read()
        return response

    def _request_file(self) -> Path:
        return self.io_dir / 'request.json'

    def _response_file(self) -> Path:
        return self.io_dir / 'response.json'

    def _output_reader(self) -> None:
        assert self.process.stdout
        stdout = self.process.stdout
        for chunk in iter(lambda: stdout.read(4096), b''):
            self.output_buffer += chunk
        if self.output_buffer == b'RequestProcessed':
            self.output_ready.set()
            self.output_buffer = b''


def handler() -> type[BaseHTTPRequestHandler]:

    interpreter = InterpreterProcess()
    interpreter.run()

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
            self.send_header('Content-Type', 'application/json')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(result)

            if _PROFILING:
                profile.disable()
                transaction_hash = 'TODO'
                filename = f'profiling/profiling-{transaction_hash}.prof'
                profile.dump_stats(filename)

    return KontrolNodeHandler


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
