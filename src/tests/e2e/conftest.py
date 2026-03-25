from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
import requests

from kontrol_node.options import VMOptions
from kontrol_node.rpc import KontrolNodeServer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Any, Final

SERVER_HOST: Final = 'localhost'

# Default sender from Foundry/Hardhat genesis accounts
DEFAULT_SENDER: Final = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'

FOUNDRY_TOML : Final = '''
[profile.default]
src = "src"
out = "out"
'''

# ---------------------------------------------------------------------------
# Solidity compilation
# ---------------------------------------------------------------------------


@dataclass
class CompiledContract:
    """Result of compiling a Solidity contract with forge."""

    name: str
    abi: list[dict[str, Any]]
    bytecode: str  # hex-encoded, 0x-prefixed


def _forge_compile(source: str, contract_name: str, tmp_path_factory: pytest.TempPathFactory) -> CompiledContract:
    """Compile a Solidity source string using ``forge build`` and return the artifact."""
    project_dir = tmp_path_factory.mktemp('forge')
    src_dir = project_dir / 'src'
    src_dir.mkdir()
    (src_dir / f'{contract_name}.sol').write_text(source)

    # Minimal foundry.toml
    (project_dir / 'foundry.toml').write_text(FOUNDRY_TOML)

    result = subprocess.run(
        ['forge', 'build', '--no-auto-detect'],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'forge build failed:\n{result.stderr}')

    artifact_path = project_dir / 'out' / f'{contract_name}.sol' / f'{contract_name}.json'
    if not artifact_path.exists():
        raise FileNotFoundError(f'Artifact not found: {artifact_path}')

    artifact = json.loads(artifact_path.read_text())
    bytecode = artifact['bytecode']['object']
    abi = artifact['abi']

    return CompiledContract(name=contract_name, abi=abi, bytecode=bytecode)


@pytest.fixture(scope='session')
def compile_solidity(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str, str], CompiledContract]:
    """Session-scoped fixture that returns a function to compile Solidity source code.

    Usage::

        compiled = compile_solidity('''
            // SPDX-License-Identifier: MIT
            pragma solidity ^0.8.0;
            contract Counter {
                uint256 public count;
                function increment() public { count += 1; }
            }
        ''', 'Counter')

        assert compiled.bytecode.startswith('0x')
    """

    cache: dict[tuple[str, str], CompiledContract] = {}

    def _compile(source: str, contract_name: str) -> CompiledContract:
        key = (source, contract_name)
        if key not in cache:
            cache[key] = _forge_compile(source, contract_name, tmp_path_factory)
        return cache[key]

    return _compile


# ---------------------------------------------------------------------------
# Kontrol-node server
# ---------------------------------------------------------------------------


@pytest.fixture(scope='session')
def server() -> Iterator[str]:
    """Start a kontrol-node JSON-RPC server and yield its URL.

    Session-scoped so the (expensive) server startup is paid only once.
    """
    sys.setrecursionlimit(15_000_000)

    srv = KontrolNodeServer(VMOptions({'addr': SERVER_HOST, 'port': 0}))

    server_thread = threading.Thread(target=srv.serve)
    server_thread.start()

    time.sleep(2)
    yield f'http://{SERVER_HOST}:{srv.port()}'
    srv.shutdown()
    server_thread.join()


# ---------------------------------------------------------------------------
# JSON-RPC client
# ---------------------------------------------------------------------------


def _encode_function_selector(sig: str) -> str:
    """Compute the 4-byte function selector for a Solidity function signature using cast."""
    result = subprocess.run(
        ['cast', 'sig', sig],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'cast sig {sig} failed:\n{result.stderr}')
    return result.stdout.strip()


def _abi_encode(sig: str, args: list[str]) -> str:
    """ABI-encode a function call using cast."""
    result = subprocess.run(
        ['cast', 'calldata', sig, *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'cast calldata {sig} {args} failed:\n{result.stderr}')
    return result.stdout.strip()


@dataclass
class RPCClient:
    """JSON-RPC client that talks directly to kontrol-node via HTTP.

    kontrol-node expects ``eth_sendTransaction`` (it signs internally) and does
    not support ``eth_call``. State reads go through ``eth_getStorageAt``.
    """

    rpc_url: str
    sender: str = DEFAULT_SENDER
    _next_id: int = field(default=1, repr=False)

    def _rpc(self, method: str, params: list[Any] | None = None) -> Any:
        payload = {
            'jsonrpc': '2.0',
            'id': self._next_id,
            'method': method,
            'params': params or [],
        }
        self._next_id += 1
        response = requests.post(self.rpc_url, json=payload)
        if not response.content:
            raise RuntimeError(f'RPC returned empty response for {method}')
        data = response.json()
        if 'error' in data:
            raise RuntimeError(f'RPC error: {data["error"]}')
        return data.get('result')

    def _rpc_raw(self, payload: str | bytes) -> requests.Response:
        """Send a raw request (not necessarily valid JSON-RPC) and return the raw response."""
        headers = {'Content-Type': 'application/json'}
        return requests.post(self.rpc_url, data=payload, headers=headers)

    # -- RPC convenience methods ---------------------------------------------

    def chain_id(self) -> int:
        return self._rpc('eth_chainId')

    def balance(self, address: str) -> int:
        result = self._rpc('eth_getBalance', [address, 'latest'])
        return int(result, 16) if isinstance(result, str) else int(result)

    def nonce(self, address: str) -> int:
        result = self._rpc('eth_getTransactionCount', [address, 'latest'])
        return int(result, 16) if isinstance(result, str) else int(result)

    def block_number(self) -> int:
        result = self._rpc('eth_getBlockByNumber', ['latest', False])
        return int(result['number'], 16) if isinstance(result['number'], str) else int(result['number'])

    def code(self, address: str) -> str:
        return self._rpc('eth_getCode', [address, 'latest'])

    def storage(self, address: str, slot: int | str) -> str:
        slot_hex = hex(slot) if isinstance(slot, int) else slot
        return self._rpc('eth_getStorageAt', [address, slot_hex, 'latest'])

    def storage_as_int(self, address: str, slot: int | str) -> int:
        result = self.storage(address, slot)
        return int(result, 16) if isinstance(result, str) else int(result)

    def receipt(self, tx_hash: str) -> dict[str, Any]:
        return self._rpc('eth_getTransactionReceipt', [tx_hash])

    def send_transaction(
        self,
        to: str | None = None,
        data: str | None = None,
        value: int = 0,
        gas: int = 90000,
        sender: str | None = None,
    ) -> str:
        """Send a transaction via eth_sendTransaction. Returns the tx hash.

        The kontrol-node handles signing internally based on the ``from`` address.
        """
        tx: dict[str, Any] = {
            'from': sender or self.sender,
            'gas': hex(gas),
            'value': hex(value),
        }
        if to is not None:
            tx['to'] = to
        if data is not None:
            tx['data'] = data
        return self._rpc('eth_sendTransaction', [tx])

    def deploy(
        self,
        compiled: CompiledContract,
        constructor_args: list[str] | None = None,
        gas: int = 5_000_000,
        sender: str | None = None,
    ) -> DeployedContract:
        """Deploy a compiled contract and return a DeployedContract handle."""
        deploy_data = compiled.bytecode
        if constructor_args:
            # We'd need to ABI-encode constructor args and append to bytecode.
            # For now, support only contracts with no constructor args, or
            # pre-encoded constructor args.
            raise NotImplementedError('Constructor args not yet supported — encode manually into bytecode')

        tx_hash = self.send_transaction(data=deploy_data, gas=gas, sender=sender)
        rx = self.receipt(tx_hash)
        contract_address = rx.get('contractAddress')
        if not contract_address:
            raise RuntimeError(f'Deployment failed, no contract address in receipt: {rx}')

        return DeployedContract(
            address=contract_address,
            abi=compiled.abi,
            client=self,
        )


@dataclass
class DeployedContract:
    """Handle to a deployed contract with convenience methods for send and storage reads.

    Since kontrol-node does not support ``eth_call``, use ``storage()`` to read
    contract state by slot index.
    """

    address: str
    abi: list[dict[str, Any]]
    client: RPCClient

    def send(
        self, sig: str, args: list[str] | None = None, value: int = 0, gas: int = 90000, sender: str | None = None
    ) -> str:
        """Send a state-changing transaction. Returns the tx hash."""
        calldata = _abi_encode(sig, args or [])
        return self.client.send_transaction(to=self.address, data=calldata, value=value, gas=gas, sender=sender)

    def storage(self, slot: int | str) -> str:
        """Read a raw storage slot (returns 32-byte hex)."""
        return self.client.storage(self.address, slot)

    def storage_as_int(self, slot: int | str) -> int:
        """Read a storage slot as an integer."""
        return self.client.storage_as_int(self.address, slot)


@pytest.fixture(scope='session')
def rpc(server: str) -> RPCClient:
    """Session-scoped RPC client connected to the kontrol-node."""
    return RPCClient(rpc_url=server)
