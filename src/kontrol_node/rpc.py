from __future__ import annotations

import cProfile
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

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


def handler() -> type[BaseHTTPRequestHandler]:

    Path(f'{kdist.kdist_dir}/kontrol-node/simbolik')

    # TODO: use an temporary directory
    # notice, we must copy the initial state dump there
    base_dir = Path(__file__).resolve().parent
    src_dir = base_dir.parent
    test_dir = src_dir / 'tests'
    io_dir = test_dir / 'integration' / 'io_dir'
    requests_file = io_dir / 'requests.json'

    class KontrolNodeHandler(BaseHTTPRequestHandler):

        def do_POST(self) -> None:  # noqa: N802
            if _PROFILING:
                profile = cProfile.Profile()
                profile.enable()
                os.makedirs('profiling', exist_ok=True)

            # Copy the requests body to the requests.json file
            content_len = self.headers.get('Content-Length')
            assert type(content_len) is str
            content = self.rfile.read(int(content_len))
            with open(requests_file, 'w') as f:
                f.write(content.decode('utf-8'))

            # Create the initial KORE configuration
            initial_kore = _kore_pgm_to_kore(
                pgm=_start_kore(str(io_dir)),
                pattern_sort=SortApp('SortEthereumSimulation'),
                schedule='PRAGUE',
                mode='NORMAL',
                chainid=1,
                usegas=True,
            )

            # Run the K semantics
            _interpret(initial_kore, check=False)

            if _PROFILING:
                profile.disable()
                transaction_hash = 'TODO'
                filename = f'profiling/profiling-{transaction_hash}.prof'
                profile.dump_stats(filename)

    return KontrolNodeHandler


def _interpret(init_kore: Any, *, check: bool = True) -> Pattern:
    return llvm_interpret(kdist.get('kontrol-node.simbolik'), init_kore, check=check)


def _start_kore(io_dir: str) -> App:
    return inj(SortApp('SortStart'), SortApp('SortEthereumSimulation'), App('Lblstart', [], [str_dv(str(io_dir))]))


def _kore_pgm_to_kore(pgm: Pattern, pattern_sort: SortApp, schedule: str, mode: str, chainid: int, usegas: bool) -> App:
    config = {
        '$PGM': inj(pattern_sort, SORT_K_ITEM, pgm),
        '$SCHEDULE': inj(SortApp('SortSchedule'), SORT_K_ITEM, _schedule_to_kore(schedule)),
        '$MODE': inj(SortApp('SortMode'), SORT_K_ITEM, _mode_to_kore(mode)),
        '$CHAINID': inj(INT, SORT_K_ITEM, int_dv(chainid)),
        '$USEGAS': inj(BOOL, SORT_K_ITEM, bool_dv(usegas)),
    }
    return top_cell_initializer(config)


def _schedule_to_kore(schedule: str) -> App:
    return App(f"Lbl{munge(schedule)}'Unds'EVM")


def _mode_to_kore(mode: str) -> App:
    return App(f'Lbl{mode}')
