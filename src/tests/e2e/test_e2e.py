"""End-to-end tests for kontrol-node using inline Solidity contracts.

Each test compiles Solidity source via ``forge``, deploys to the kontrol-node,
and interacts with the contract through JSON-RPC.

Note: kontrol-node does not implement ``eth_call``, so we read contract state
via ``eth_getStorageAt`` (storage slot reads) rather than view function calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

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

PAYABLE_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract Payable {
    receive() external payable {}
}
"""


# ---------------------------------------------------------------------------
# Tests: eth_chainId
# ---------------------------------------------------------------------------


class TestEthChainId:
    def test_returns_31337(self, rpc: RPCClient) -> None:
        assert rpc.chain_id() == 31337


# ---------------------------------------------------------------------------
# Tests: eth_sendTransaction
# ---------------------------------------------------------------------------


class TestEthSendTransaction:
    def test_deploy_contract(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        code = rpc.code(counter.address)
        assert code != '0x'
        assert len(code) > 2

    def test_call_function(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        counter.send('increment()')
        assert counter.storage_as_int(0) == 1

    def test_send_value(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(PAYABLE_SOL, 'Payable')
        payable = rpc.deploy(compiled)

        one_ether = 10**18
        rpc.send_transaction(to=payable.address, value=one_ether)

        contract_balance = rpc.balance(payable.address)
        assert contract_balance == one_ether

    @pytest.mark.xfail(reason='kontrol-node returns empty response body on sign error', strict=True)
    def test_unknown_sender_fails(self, rpc: RPCClient) -> None:
        unknown = '0x0000000000000000000000000000000000000001'
        with pytest.raises(RuntimeError, match='Could not sign transaction'):
            rpc.send_transaction(to=rpc.sender, sender=unknown)

    def test_returns_tx_hash(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        tx_hash = counter.send('increment()')
        assert tx_hash.startswith('0x')
        assert len(tx_hash) == 66  # 0x + 64 hex chars


# ---------------------------------------------------------------------------
# Tests: eth_getTransactionReceipt
# ---------------------------------------------------------------------------


class TestEthGetTransactionReceipt:
    def test_successful_tx(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        tx_hash = counter.send('increment()')
        receipt = rpc.receipt(tx_hash)

        assert receipt['status'] == '0x1'
        assert receipt['transactionHash'] == tx_hash
        assert receipt['from'] is not None
        assert receipt['gasUsed'] is not None
        assert int(receipt['gasUsed'], 16) > 0

    def test_deploy_receipt_has_contract_address(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        # Deploy manually to get the tx_hash
        tx_hash = rpc.send_transaction(data=compiled.bytecode, gas=5_000_000)
        receipt = rpc.receipt(tx_hash)

        assert receipt['status'] == '0x1'
        assert receipt['contractAddress'] is not None
        assert receipt['contractAddress'].startswith('0x')

    def test_call_receipt_has_null_contract_address(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        tx_hash = counter.send('increment()')
        receipt = rpc.receipt(tx_hash)

        assert receipt['contractAddress'] is None

    def test_nonexistent_tx_returns_null(self, rpc: RPCClient) -> None:
        fake_hash = '0x' + '00' * 32
        result = rpc._rpc('eth_getTransactionReceipt', [fake_hash])
        assert result is None


# ---------------------------------------------------------------------------
# Tests: eth_getTransactionByHash
# ---------------------------------------------------------------------------


class TestEthGetTransactionByHash:
    def test_returns_tx_data(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        tx_hash = counter.send('increment()')
        tx = rpc._rpc('eth_getTransactionByHash', [tx_hash])

        assert tx is not None
        assert tx['type'] == '0x0'
        assert 'nonce' in tx
        assert tx['to'] is not None
        assert 'gas' in tx
        assert 'value' in tx
        assert 'input' in tx
        assert 'gasPrice' in tx
        assert int(tx['chainId'], 16) == 31337

    def test_nonexistent_tx_returns_null(self, rpc: RPCClient) -> None:
        fake_hash = '0x' + '00' * 32
        result = rpc._rpc('eth_getTransactionByHash', [fake_hash])
        assert result is None


# ---------------------------------------------------------------------------
# Tests: eth_getCode
# ---------------------------------------------------------------------------


class TestEthGetCode:
    def test_contract_has_code(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        code = rpc.code(counter.address)
        assert code.startswith('0x')
        assert len(code) > 2

    def test_eoa_returns_0x(self, rpc: RPCClient) -> None:
        code = rpc.code(rpc.sender)
        assert code == '0x'

    def test_nonexistent_account_returns_0x(self, rpc: RPCClient) -> None:
        nonexistent = '0x0000000000000000000000000000000000000099'
        code = rpc.code(nonexistent)
        assert code == '0x'


# ---------------------------------------------------------------------------
# Tests: eth_getBalance
# ---------------------------------------------------------------------------


class TestEthGetBalance:
    def test_genesis_account_has_balance(self, rpc: RPCClient) -> None:
        balance = rpc.balance(rpc.sender)
        # Genesis accounts start with 10000 ETH
        assert balance > 0

    def test_nonexistent_account_returns_zero(self, rpc: RPCClient) -> None:
        nonexistent = '0x0000000000000000000000000000000000000099'
        balance = rpc.balance(nonexistent)
        assert balance == 0

    def test_balance_decreases_after_sending_value(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        # Use a different sender to avoid interference from other tests
        second_sender = '0x70997970C51812dc3A010C7d01b50e0d17dc79C8'
        balance_before = rpc.balance(second_sender)

        compiled = compile_solidity(PAYABLE_SOL, 'Payable')
        payable = rpc.deploy(compiled)

        one_ether = 10**18
        rpc.send_transaction(to=payable.address, value=one_ether, sender=second_sender)

        balance_after = rpc.balance(second_sender)
        # Balance should decrease by at least the sent value (plus gas)
        assert balance_after < balance_before
        assert balance_before - balance_after >= one_ether


# ---------------------------------------------------------------------------
# Tests: eth_getBlockByNumber
# ---------------------------------------------------------------------------


class TestEthGetBlockByNumber:
    def test_genesis_block(self, rpc: RPCClient) -> None:
        block = rpc._rpc('eth_getBlockByNumber', ['0x0', False])

        assert block is not None
        assert block['number'] == '0x0'
        assert 'hash' in block
        assert 'parentHash' in block
        assert 'miner' in block
        assert 'gasLimit' in block
        assert 'timestamp' in block

    def test_latest_block(self, rpc: RPCClient) -> None:
        block = rpc._rpc('eth_getBlockByNumber', ['latest', False])

        assert block is not None
        assert 'number' in block
        assert 'hash' in block

    def test_block_number_increases_after_tx(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        block_before = rpc.block_number()

        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        rpc.deploy(compiled)

        block_after = rpc.block_number()
        assert block_after > block_before

    def test_nonexistent_block_returns_null(self, rpc: RPCClient) -> None:
        result = rpc._rpc('eth_getBlockByNumber', ['0xffffff', False])
        assert result is None

    def test_earliest_returns_genesis(self, rpc: RPCClient) -> None:
        block = rpc._rpc('eth_getBlockByNumber', ['earliest', False])
        assert block is not None
        assert block['number'] == '0x0'


# ---------------------------------------------------------------------------
# Tests: eth_getBlockByHash
# ---------------------------------------------------------------------------


class TestEthGetBlockByHash:
    def test_lookup_by_hash(self, rpc: RPCClient) -> None:
        # Get genesis block to learn its hash
        genesis = rpc._rpc('eth_getBlockByNumber', ['0x0', False])
        assert genesis is not None
        block_hash = genesis['hash']

        # Look it up by hash
        block = rpc._rpc('eth_getBlockByHash', [block_hash, False])
        assert block is not None
        assert block['number'] == '0x0'
        assert block['hash'] == block_hash

    def test_nonexistent_hash_returns_null(self, rpc: RPCClient) -> None:
        fake_hash = '0x' + '00' * 32
        result = rpc._rpc('eth_getBlockByHash', [fake_hash, False])
        assert result is None


# ---------------------------------------------------------------------------
# Tests: eth_getTransactionCount
# ---------------------------------------------------------------------------


class TestEthGetTransactionCount:
    def test_genesis_account_starts_at_zero(self, rpc: RPCClient) -> None:
        # Use a fresh account that hasn't sent any txs in other tests
        fresh_account = '0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc'
        nonce = rpc.nonce(fresh_account)
        assert nonce == 0

    def test_nonce_increments_after_tx(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        # Use a specific account for this test
        account = '0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65'
        nonce_before = rpc.nonce(account)

        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled, sender=account)

        nonce_after = rpc.nonce(account)
        assert nonce_after == nonce_before + 1

        counter.send('increment()', sender=account)
        nonce_after_2 = rpc.nonce(account)
        assert nonce_after_2 == nonce_before + 2

    def test_nonexistent_account_returns_zero(self, rpc: RPCClient) -> None:
        nonexistent = '0x0000000000000000000000000000000000000099'
        nonce = rpc.nonce(nonexistent)
        assert nonce == 0


# ---------------------------------------------------------------------------
# Tests: eth_getStorageAt
# ---------------------------------------------------------------------------


class TestEthGetStorageAt:
    def test_read_storage_slot(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(STORAGE_SOL, 'SimpleStorage')
        storage = rpc.deploy(compiled)

        storage.send('set(uint256)', ['42'])
        value = storage.storage_as_int(0)
        assert value == 42

    def test_empty_slot_returns_zero(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        value = counter.storage_as_int(0)
        assert value == 0

    def test_nonexistent_account_returns_zero(self, rpc: RPCClient) -> None:
        nonexistent = '0x0000000000000000000000000000000000000099'
        value = rpc.storage_as_int(nonexistent, 0)
        assert value == 0


# ---------------------------------------------------------------------------
# Tests: anvil_setBalance
# ---------------------------------------------------------------------------


class TestAnvilSetBalance:
    def test_set_existing_account_balance(self, rpc: RPCClient) -> None:
        account = '0x976EA74026E726554dB657fA54763abd0C3a0aa9'
        new_balance = 12345

        result = rpc._rpc('anvil_setBalance', [account, hex(new_balance)])
        assert result is None  # returns null on success

        balance = rpc.balance(account)
        assert balance == new_balance

    def test_set_new_account_balance(self, rpc: RPCClient) -> None:
        new_account = '0x0000000000000000000000000000000000001234'
        new_balance = 999

        rpc._rpc('anvil_setBalance', [new_account, hex(new_balance)])

        balance = rpc.balance(new_account)
        assert balance == new_balance


# ---------------------------------------------------------------------------
# Tests: anvil_dumpState
# ---------------------------------------------------------------------------


class TestAnvilDumpState:
    def test_returns_state(self, rpc: RPCClient) -> None:
        result = rpc._rpc('anvil_dumpState', [None])

        assert result is not None
        assert isinstance(result, dict)
        assert 'accounts' in result

    def test_deployed_contract_in_state(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        result = rpc._rpc('anvil_dumpState', [None])
        assert result is not None

        # The contract address should appear in accounts
        accounts = result.get('accounts', {})
        addr_lower = counter.address.lower()
        # Addresses in the dump may or may not be checksummed
        account_keys_lower = {k.lower() for k in accounts.keys()}
        assert addr_lower in account_keys_lower


# ---------------------------------------------------------------------------
# Tests: debug_traceTransaction
# ---------------------------------------------------------------------------


class TestDebugTraceTransaction:
    def test_trace_simple_tx(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        tx_hash = counter.send('increment()')
        trace = rpc._rpc('debug_traceTransaction', [tx_hash, {}])

        assert trace is not None
        assert 'failed' in trace
        assert trace['failed'] is False
        assert 'gas' in trace
        assert trace['gas'] > 0
        assert 'structLogs' in trace

    def test_trace_nonexistent_returns_null(self, rpc: RPCClient) -> None:
        fake_hash = '0x' + '00' * 32
        result = rpc._rpc('debug_traceTransaction', [fake_hash, {}])
        assert result is None


# ---------------------------------------------------------------------------
# Tests: error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_unknown_method(self, rpc: RPCClient) -> None:
        with pytest.raises(RuntimeError, match='Method not found'):
            rpc._rpc('eth_nonexistentMethod', [])

    def test_invalid_json_returns_parse_error(self, rpc: RPCClient) -> None:
        response = rpc._rpc_raw('not json')
        data = response.json()
        assert 'error' in data
        assert data['error']['code'] == -32700  # Parse error


# ---------------------------------------------------------------------------
# Tests: contract interactions (Counter)
# ---------------------------------------------------------------------------


class TestCounter:
    def test_increment_multiple_times(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        assert counter.storage_as_int(0) == 0

        counter.send('increment()')
        assert counter.storage_as_int(0) == 1

        counter.send('increment()')
        assert counter.storage_as_int(0) == 2

    def test_decrement(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(COUNTER_SOL, 'Counter')
        counter = rpc.deploy(compiled)

        counter.send('increment()')
        counter.send('increment()')
        counter.send('decrement()')
        assert counter.storage_as_int(0) == 1


# ---------------------------------------------------------------------------
# Tests: contract interactions (SimpleStorage)
# ---------------------------------------------------------------------------


class TestSimpleStorage:
    def test_set_and_get(
        self,
        compile_solidity: Callable[[str, str], CompiledContract],
        rpc: RPCClient,
    ) -> None:
        compiled = compile_solidity(STORAGE_SOL, 'SimpleStorage')
        storage = rpc.deploy(compiled)

        storage.send('set(uint256)', ['42'])
        assert storage.storage_as_int(0) == 42

        storage.send('set(uint256)', ['100'])
        assert storage.storage_as_int(0) == 100
