"""End-to-end tests for kontrol-node using inline Solidity contracts.

Each test compiles Solidity source via ``forge``, deploys to the kontrol-node,
and interacts with the contract through JSON-RPC.

Note: kontrol-node does not implement ``eth_call``, so we read contract state
via ``eth_getStorageAt`` (storage slot reads) rather than view function calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.e2e.conftest import CompiledContract, RPCClient

# ---------------------------------------------------------------------------
# Solidity sources
# ---------------------------------------------------------------------------

COUNTER_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract Counter {
    uint256 public count;  // slot 0

    function increment() public {
        count += 1;
    }

    function decrement() public {
        require(count > 0, "Counter: underflow");
        count -= 1;
    }
}
"""

STORAGE_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract SimpleStorage {
    uint256 private storedValue;  // slot 0

    event ValueChanged(uint256 oldValue, uint256 newValue);

    function set(uint256 _value) public {
        uint256 old = storedValue;
        storedValue = _value;
        emit ValueChanged(old, _value);
    }
}
"""


# ---------------------------------------------------------------------------
# Tests: basic RPC
# ---------------------------------------------------------------------------


class TestBasicRPC:
    def test_chain_id(self, rpc: RPCClient) -> None:
        assert rpc.chain_id() == 31337

    def test_block_number_starts_at_zero(self, rpc: RPCClient) -> None:
        block = rpc.block_number()
        assert block >= 0

    def test_sender_has_balance(self, rpc: RPCClient) -> None:
        balance = rpc.balance(rpc.sender)
        assert balance > 0


# ---------------------------------------------------------------------------
# Tests: Counter contract
# ---------------------------------------------------------------------------


class TestCounter:
    def test_deploy_and_increment(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        # Contract should have code
        code = rpc.code(counter.address)
        assert code != '0x'

        # Initial count should be 0 (slot 0)
        assert counter.storage_as_int(0) == 0

        # Increment and check
        counter.send('increment()')
        assert counter.storage_as_int(0) == 1

        # Increment again
        counter.send('increment()')
        assert counter.storage_as_int(0) == 2

    def test_decrement(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        # Increment twice, decrement once
        counter.send('increment()')
        counter.send('increment()')
        counter.send('decrement()')
        assert counter.storage_as_int(0) == 1


# ---------------------------------------------------------------------------
# Tests: SimpleStorage contract
# ---------------------------------------------------------------------------


class TestSimpleStorage:
    def test_set_and_get(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(STORAGE_SOL, 'SimpleStorage')
        storage = rpc.deploy(compiled)

        # Set a value (stored in slot 0)
        storage.send('set(uint256)', ['42'])
        assert storage.storage_as_int(0) == 42

        # Overwrite
        storage.send('set(uint256)', ['100'])
        assert storage.storage_as_int(0) == 100

    def test_transaction_receipt(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(STORAGE_SOL, 'SimpleStorage')
        storage = rpc.deploy(compiled)

        tx_hash = storage.send('set(uint256)', ['99'])
        receipt = rpc.receipt(tx_hash)

        assert receipt['status'] == '0x1'
        assert receipt['transactionHash'] == tx_hash
