from __future__ import annotations

import cProfile
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Final

from eth_keys import keys
from pydantic import BaseModel
from pyk.kdist import kdist
from pyk.konvert._utils import munge
from pyk.kore.prelude import BOOL, INT, SORT_K_ITEM, bool_dv, inj, int_dv, str_dv, top_cell_initializer
from pyk.kore.syntax import App, SortApp
from pyk.ktool.krun import KRun, llvm_interpret

from kontrol_node.rpc_server import JsonRpcServer, ServeRpcOptions
from kontrol_node.state_dump import Account

if TYPE_CHECKING:
    from collections.abc import Iterator

    from eth_keys.datatypes import PublicKey
    from pyk.kore.syntax import Pattern

    from kontrol_node.state_dump import StateDump

    from .cli import VMOptions

CHUNK_SIZE: Final[int] = 64
PROFILING: Final[bool] = False

# 32 bytes, and two characters for '0x'
HASH_LENGTH: Final[int] = 32 * 2 + 2


# For performance reasons, `kontrol-node` entirely avoids converting between
# KAST and KORE. The commmunication between the Python code and the K code
# is done by reading and writing JSON files.

# For requests that don't modify state (eth_getCode, eth_getStorageAt, etc.),
# the K semantics is never run. The state is ready from disk, where it was
# dumped by the K code on the last state-modifying request.

# For requests that modify the state (eth_sendTransaction), the Python server
# writes the JSON-RPC request to a file. Next, it calls KRun passing the file
# path as an argument. The K Code executes the request, and writes the result
# to disk. The result is 1) the transaction result 2) the transaction receipt
# 3) the debug trace and 4) the new state dump (includes accounts).

# Simbolik needs at minimum the following RPC methods
# eth_sendTransaction
# eth_waitForTransactionReceipt <--- should be removed from Simbolik
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


class Database:

    def get_initial_state(self) -> StateDump:
        raise NotImplementedError()

    def get_block_state(self, block_number: int) -> StateDump:
        raise NotImplementedError()

    def get_transaction_receipt(self, tx_hash: str) -> Any:
        raise NotImplementedError()

    def get_transaction(self, tx_hash: str) -> Any:
        raise NotImplementedError()

    def get_transaction_trace(self, tx_hash: str) -> Iterator[bytes]:
        """
        Debug traces are never parsed into structured data, only read as raw bytes
        This is because they can be very large, and parsing them would be very slow
        Instead they are passed as raw bytes to the RPC response
        """
        raise NotImplementedError()


class StatefulKJsonRpcServer(JsonRpcServer):
    krun: KRun
    db: Database

    def __init__(self, options: VMOptions) -> None:
        super().__init__(ServeRpcOptions({'definition_dir': None, 'port': int(options.port), 'host': options.host}))
        self._register_rpc_methods()
        dir_path = Path(f'{kdist.kdist_dir}/kontrol-node/simbolik')
        self.krun = KRun(dir_path)
        self.db = Database()
        print('Server initialization finished.')

    def _register_rpc_methods(self) -> None:
        rpc_methods: dict[str, Callable] = {
            'anvil_dumpState': self.exec_dump_state,
            'debug_traceTransaction': self.exec_trace_transaction,
            'eth_getBlockByHash': self.exec_get_block_by_hash,
            'eth_getBlockByNumber': self.exec_get_block_by_number,
            'eth_getCode': self.exec_get_code,
            'eth_getStorageAt': self.exec_get_storage_at,
            'eth_getTransactionByHash': self.exec_get_transaction_by_hash,
            'eth_getTransactionCount': self.exec_get_transaction_count,
            'eth_getTransactionReceipt': self.exec_get_transaction_receipt,
            'eth_sendTransaction': self.exec_send_transaction,
        }
        for method_name, exec_function in rpc_methods.items():
            self.register_method(method_name, exec_function)

    def exec_get_storage_at(self, hex_address: str, hex_slot: str, _block_number: str) -> str:
        block_number = int(_block_number, base=0)
        address = int(hex_address, base=0)
        slot = int(hex_slot, base=0)
        storage = (
            self.db.get_block_state(block_number)
            .accounts.get(address, Account.empty())
            .storage.get(
                slot,
                0,
            )
            .to_bytes(32, byteorder='big')
            .hex()
        )
        return '0x' + storage

    def exec_get_code(self, hex_address: str, _block_number: str) -> str:
        block_number = int(_block_number, base=0)
        address = int(hex_address, base=0)
        code = self.db.get_block_state(block_number).accounts.get(address, Account.empty()).code or b''
        return '0x' + code.hex()

    def exec_get_block_by_hash(self, hash: str, transaction_detail: bool = False) -> dict | None:
        raise NotImplementedError()

    def exec_get_block_by_number(self, number: str, transaction_detail: bool = False) -> dict | None:
        raise NotImplementedError()

    def exec_get_transaction_count(self, hex_address: str, _block_number: str) -> str:
        raise NotImplementedError()

    def exec_dump_state(self) -> str:
        raise NotImplementedError()

    def exec_send_transaction(self, transaction_json: dict) -> str:
        if PROFILING:
            profile = cProfile.Profile()
            profile.enable()
            os.makedirs('profiling', exist_ok=True)

        base_dir = Path(__file__).resolve().parent
        src_dir = base_dir.parent
        test_dir = src_dir / 'tests'
        io_dir = test_dir / 'integration' / 'io_dir'

        # Write the transaction JSON to the requests.json file
        requests_path = io_dir / 'requests.json'
        with open(requests_path, 'w') as f:
            json.dump([{'jsonrpc': '2.0', 'method': 'eth_sendTransaction', 'params': [transaction_json], 'id': 0}], f)

        start = self.start_kore(str(io_dir))
        mode = 'NORMAL'
        schedule = 'PRAGUE'
        initial_kore = kore_pgm_to_kore(
            start,
            SortApp('SortEthereumSimulation'),
            schedule,
            mode,
            chainid=1,
            usegas=True,
        )
        # echo 'inj{SortStart{}, SortEthereumSimulation{}}(Lblstart{}(\dv{SortString{}}("/home/raoul/rv/kontrol-node/src/tests/integration/io_dir")))' | $(uv run kdist which)/kontrol-node/simbolik/interpreter /dev/stdin 0 /dev/stdout
        interpret(initial_kore, check=False)

        if PROFILING:
            profile.disable()
            transaction_hash = 'TODO'
            filename = f'profiling/profiling-{transaction_hash}.prof'
            profile.dump_stats(filename)

        return ''

    def start_kore(self, io_dir: str) -> App:
        return inj(SortApp('SortStart'), SortApp('SortEthereumSimulation'), App('Lblstart', [], [str_dv(str(io_dir))]))

    def exec_trace_transaction(self, tx_hash: str, args: dict[str, bool]) -> dict | None:
        raise NotImplementedError()

    def exec_get_transaction_by_hash(self, tx_hash: str) -> dict | str:
        raise NotImplementedError()

    def exec_get_transaction_receipt(self, tx_hash: str) -> dict | str:
        raise NotImplementedError()


def interpret(init_kore: Any, *, check: bool = True) -> Pattern:
    return llvm_interpret(kdist.get('kontrol-node.simbolik'), init_kore, check=check, depth=0)


def kore_pgm_to_kore(pgm: Pattern, pattern_sort: SortApp, schedule: str, mode: str, chainid: int, usegas: bool) -> App:
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


class DebugTraceTransactionResponse(BaseModel):
    gas: int
    returnValue: str | None  # noqa: N815
    structLogs: tuple[TraceItem, ...]  # noqa: N815
    failed: bool


class TraceItem(BaseModel):
    pc: int
    op: str
    stack: list[str]
    memoryChange: list[str] | None  # noqa: N815
    storageChanges: dict[str, dict[str, str]]  # noqa: N815
    nonceChanges: dict[str, str]  # noqa: N815
    balanceChanges: dict[str, str]  # noqa: N815
    callDataChange: str | None  # noqa: N815
    returnDataChange: str | None  # noqa: N815
    programChange: str | None  # noqa: N815
    deployedCodeChanges: dict[str, str] | None  # noqa: N815
    initCodeChanges: dict[str, str] | None  # noqa: N815
    depth: int
    gas: int
    coinbase: int  # address
    gasCost: int  # noqa: N815
    difficulty: int
    blockNumber: int  # noqa: N815
    blockTimestamp: int  # noqa: N815
    targetAddress: int  # noqa: N815
    codeAddress: int  # noqa: N815
    msgSender: int  # noqa: N815
    msgValue: int  # noqa: N815
    txOrigin: int  # noqa: N815
    isInitCode: bool  # noqa: N815
    statusCode: str  # noqa: N815


def get_address_from_private_key(private_key: str) -> str:
    private_key_bytes = bytes.fromhex(private_key[2:])
    private_key_obj = keys.PrivateKey(private_key_bytes)
    public_key: PublicKey = private_key_obj.public_key
    address = public_key.to_checksum_address()
    return address
