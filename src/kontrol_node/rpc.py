from __future__ import annotations

import ast
import gzip
import json
import pprint
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from kevm_pyk.kevm import KEVM
from kontrol.foundry import Foundry
from pyk.cterm import CTerm
from pyk.kast.inner import KApply, KSequence, KToken, Subst, flatten_label
from pyk.kast.manip import set_cell
from pyk.kdist import kdist
from pyk.ktool.krun import KRun
from pyk.prelude.bytes import bytesToken
from pyk.prelude.collections import list_empty, map_empty
from pyk.prelude.k import GENERATED_TOP_CELL
from pyk.prelude.kbool import TRUE
from pyk.prelude.utils import token
from pyk.rpc.rpc import JsonRpcServer, ServeRpcOptions
from pyk.utils import single

if TYPE_CHECKING:
    from pyk.kast.inner import KInner, KLabel

    from .cli import VMOptions

_PPRINT = pprint.PrettyPrinter(width=41, compact=True)
ACCOUNT_EMPTY: Final[KApply] = KApply('.Account_EVM-TYPES_Account')
WORDSTACK_EMPTY: Final[KApply] = KApply('.WordStack_EVM-TYPES_WordStack')
WORDSTACK_CONS: Final[str] = '_:__EVM-TYPES_WordStack_Int_WordStack'
MAP_CONS: Final[str] = '_Map_'
CHUNK_SIZE: Final[int] = 64


class StatefulKJsonRpcServer(JsonRpcServer):
    krun: KRun
    cterm: CTerm
    traced_transactions: dict[str, Any]
    transaction_return_data: dict[str, str]
    transaction_hashes: dict[int, str]
    default_sender_address: Final[int]

    def __init__(self, options: VMOptions) -> None:
        super().__init__(ServeRpcOptions({'definition_dir': None, 'port': int(options.port), 'host': options.host}))

        self._register_rpc_methods()
        dir_path = Path(f'{kdist.kdist_dir}/kontrol-node/simbolik')
        self.krun = KRun(dir_path)
        self.traced_transactions = {}
        self.transaction_return_data = {}
        self.transaction_hashes = {}
        start_time = datetime.now()
        self._init_cterm(options.steps_tracing)
        self.default_sender_address = self._get_account_addresses()[0]
        end_time = datetime.now()

        print(f'Server initialization finished in {(end_time - start_time).total_seconds()} seconds.')

    def exec_get_chain_id(self) -> int:
        return int(self._parse_ktoken_cell('CHAINID_CELL'))

    def exec_get_memory_used(self) -> int:
        return int(self._parse_ktoken_cell('MEMORYUSED_CELL'))

    def exec_get_gas_price(self) -> int:
        return int(self._parse_ktoken_cell('GASPRICE_CELL'))

    def exec_get_block_number(self) -> int:
        return int(self._parse_ktoken_cell('NUMBER_CELL'))

    def exec_get_storage_at(self, hex_address: str, hex_slot: str, _block_number: str) -> str:
        address = _address_to_acct_id(hex_address)
        slot = int(hex_slot, base=16)
        return hex(self._get_account_storage_slot(address, slot))

    def exec_get_code(self, hex_address: str, _block_number: str) -> str:
        address = _address_to_acct_id(hex_address)
        return self._get_account_code(address)

    def exec_get_block_by_number(self, hex_number: str, transaction_detail: bool = False) -> dict:
        number = int(hex_number, base=16)
        assert number == self.block_number
        header = self._get_block_header()
        transaction_id = int(self._parse_ktoken_cell('CURRENTTXID_CELL'))
        result = {
            'hash': header['<currentBlockHash>'],
            'parentHash': header['<previousHash>'],
            'sha3Uncles': header['<ommersHash>'],
            'miner': header['<coinbase>'],
            'stateRoot': header['<stateRoot>'],
            'transactionsRoot': header['<transactionsRoot>'],
            'receiptsRoot': header['<receiptsRoot>'],
            'logsBloom': header['<logsBloom>'],
            'difficulty': header['<difficulty>'],
            'number': header['<number>'],
            'gasLimit': header['<gasLimit>'],
            'gasUsed': header['<gasUsed>'],
            'timestamp': header['<timestamp>'],
            'totalDifficulty': header['<difficulty>'],
            'extraData': header['<extraData>'],
            'mixHash': header['<mixHash>'],
            'nonce': header['<blockNonce>'],
            'baseFeePerGas': header['<baseFee>'],
            'blobGasUsed': header['<blobGasUsed>'],
            'excessBlobGas': header['<excessBlobGas>'],
            'uncles': header['<ommerBlockHeaders>'],
            'transactions': [self.transaction_hashes[transaction_id]] if number != 0 else [],
            'size': '0x3e8',
        }

        return result

    def exec_get_balance(self, hex_address: str, _block_number: str) -> str:
        address = _address_to_acct_id(hex_address)
        return hex(self._get_account_balance(address))

    def exec_get_transaction_count(self, hex_address: str, _block_number: str) -> str:
        address = _address_to_acct_id(hex_address)
        return hex(self._get_account_nonce(address))

    def exec_accounts(self) -> list[str]:
        return [hex(address) for address in self._get_account_addresses()]

    def exec_add_account(self, private_key: str, balance_hex: str) -> str:
        balance = int(balance_hex, 16)
        self.cterm = CTerm.from_kast(
            set_cell(self.cterm.config, 'K_CELL', KApply('acctFromPrivateKey', [token(private_key), token(balance)]))
        )
        self._krun_cterm()

        return self._get_rpc_response()

    def exec_dump_state(self) -> str:
        dump: dict[str, Any] = {}
        dump['accounts'] = self._dump_accounts()
        dump['best_block_number'] = hex(self.block_number)
        header = self._get_block_header()
        block = {
            'number': header['<number>'],
            'coinbase': header['<coinbase>'],
            'timestamp': header['<timestamp>'],
            'gas_limit': header['<gasLimit>'],
            'basefee': header['<baseFee>'],
            'difficulty': header['<difficulty>'],
            'prevrandao': '0x4049e9c3939dad98110354500dc0bebd598bad807233a6b7055ae794bfac22d9',
            'blob_excess_gas_and_price': {
                'excess_blob_gas': int(header['<excessBlobGas>'], base=16),
                'blob_gasprice': int(header['<blobGasUsed>'], base=16),
            },
        }
        dump['block'] = block
        dump_bytes = json.dumps(dump).encode('utf-8')
        result = '0x' + gzip.compress(dump_bytes).hex()
        return result

    def exec_set_balance(self, address: str, value: str) -> None:
        balance = int(value, 0)
        account_id = _address_to_acct_id(address)
        account = self._get_account_cell_by_address(account_id)
        new_account = KEVM.account_cell(
            id=token(account_id),
            balance=token(balance),
            code=token(b'') if account is ACCOUNT_EMPTY else account.args[2],
            storage=map_empty() if account is ACCOUNT_EMPTY else account.args[3],
            orig_storage=map_empty() if account is ACCOUNT_EMPTY else account.args[4],
            transient_storage=map_empty() if account is ACCOUNT_EMPTY else account.args[5],
            nonce=token(0) if account is ACCOUNT_EMPTY else account.args[6],
        )
        self._add_or_update_account(new_account)

    def exec_send_transaction(self, transaction_json: dict) -> str:
        sender: int | None = _get_address_from(transaction_json, 'from')
        if sender is None:
            sender = self.default_sender_address
        sender_nonce = self._get_account_nonce(sender)

        destination: int | None = _get_address_from(transaction_json, 'to')
        tx_type: str = transaction_json.get('type', 'Legacy')
        nonce: int = transaction_json.get('nonce', sender_nonce)
        gas: int = int(transaction_json.get('gas', '0x15f90'), base=16)
        gas_price: int = int(transaction_json.get('gasPrice', '0x0'), base=16)
        value: int = int(transaction_json.get('value', '0x0'), base=16)
        data: str = transaction_json.get('data', '0x0')

        self.cterm = CTerm.from_kast(
            set_cell(
                self.cterm.config,
                'K_CELL',
                eth_send_transaction(tx_type, sender, destination, gas, gas_price, value, nonce, data),
            )
        )

        self._krun_cterm()
        transaction_hash = self._get_rpc_response()
        transaction_id = int(self._parse_ktoken_cell('CURRENTTXID_CELL'))
        self.transaction_hashes[transaction_id] = transaction_hash
        if self.active_tracing:
            self._collect_trace(transaction_hash)
        return transaction_hash

    def exec_trace_transaction(self, tx_hash: str, args: dict[str, bool]) -> dict:
        result: dict[str, Any] = {}
        result['structLogs'] = self.traced_transactions[tx_hash]
        receipt = self._get_tx_receipt_by_hash(tx_hash)
        if receipt is None:
            return {}
        if '<contractAddress>' in receipt.keys():
            result['returnValue'] = self.transaction_return_data[tx_hash]
        result['failed'] = not bool(receipt['<txStatus>'])
        result['gas'] = receipt['<txCumulativeGas>']
        return result

    def exec_get_transaction_by_hash(self, tx_hash: str) -> dict | str:
        tx_receipt = self._get_tx_receipt_by_hash(tx_hash)

        if tx_receipt is None:
            return 'Transaction receipt not found'

        msg_id = tx_receipt['<txID>']
        messages_dict = self._get_all_messages_dict()

        if msg_id not in messages_dict:
            return 'Transaction not found.'

        formatted_messages_dict = _apply_format_to_message_cell_json_dict(messages_dict[msg_id])
        formatted_messages_dict['blockNumber'] = tx_receipt['<txBlockNumber>']
        formatted_messages_dict['hash'] = tx_receipt['<txHash>']
        formatted_messages_dict['from'] = _acct_id_to_address(tx_receipt['<sender>'])
        del formatted_messages_dict['priorityFee']
        del formatted_messages_dict['maxFee']
        return formatted_messages_dict

    def exec_get_transaction_receipt(self, tx_hash: str) -> dict | str:
        tx_receipt_dict = self._get_tx_receipt_by_hash(tx_hash)

        if tx_receipt_dict is None:
            return 'Transaction receipt not found'

        msg_id = tx_receipt_dict['<txID>']
        messages_dict = self._get_all_messages_dict()

        if msg_id not in messages_dict:
            return 'Transaction not found.'
        message_dict = messages_dict[msg_id]

        receipt: dict[str, Any] = {}
        receipt['type'] = hex(message_dict['<txType>'])
        receipt['status'] = hex(tx_receipt_dict['<txStatus>'])
        receipt['cumulativeGasUsed'] = hex(tx_receipt_dict['<txCumulativeGas>'])
        receipt['logs'] = tx_receipt_dict['<logSet>']
        receipt['logsBloom'] = tx_receipt_dict['<bloomFilter>']
        receipt['transactionHash'] = tx_hash
        receipt['transactionIndex'] = hex(int(msg_id))
        receipt['blockNumber'] = hex(tx_receipt_dict['<txBlockNumber>'])
        receipt['gasUsed'] = hex(tx_receipt_dict['<txCumulativeGas>'])
        receipt['effectiveGasPrice'] = hex(message_dict['<txGasPrice>'])

        receipt['to'] = message_dict['<to>'] if '<to>' in message_dict.keys() else None
        receipt['contractAddress'] = (
            hex(tx_receipt_dict['<contractAddress>']) if tx_receipt_dict['<contractAddress>'] is not None else None
        )
        receipt['root'] = hex(int(self._parse_ktoken_cell('TRANSACTIONSROOT_CELL')))
        return receipt

    # ------------------------------------------------------
    # VM data fetch helper functions
    # ------------------------------------------------------

    @property
    def active_tracing(self) -> bool:
        return self._parse_ktoken_cell('ACTIVETRACING_CELL') == 'true'

    @property
    def block_number(self) -> int:
        return int(self._parse_ktoken_cell('NUMBER_CELL'))

    def _get_rpc_response(self) -> str:
        """Parses and returns the RPC response from the 'RPCRESPONSE_CELL' in hexadecimal format.

        The function processes the cell content:
        - If the value is a decimal, it converts it to hexadecimal.
        - If the value is a quoted string (e.g., `"value"`), it strips the quotes and prepends '0x'.
        - It then updates the configuration by clearing the 'RPCRESPONSE_CELL' with an empty RPCResponse object.
        - If the RPCRESPONSE_CELL has an empty RPCResponse value, then it throws an AssertionError and the function
        returns an empty string.
        :return: The RPC response as a hexadecimal string.
        """
        try:
            response_value = self._parse_ktoken_cell('RPCRESPONSE_CELL')

            if response_value.isdecimal():
                response_value = hex(int(response_value))
            elif response_value.startswith('"'):
                response_value = '0x' + response_value[1:-1]
            self.cterm = CTerm.from_kast(set_cell(self.cterm.config, 'RPCRESPONSE_CELL', KApply('EmptyRPCResponse')))
        except AssertionError:
            response_value = '0x'
        return response_value

    def _get_account_cell_by_address(self, address: int) -> KApply:
        accounts_cell = flatten_label('_AccountCellMap_', self.cterm.cell('ACCOUNTS_CELL'))
        for account in accounts_cell:
            assert type(account) is KApply
            if extract_address(account) == address:
                return account
        return ACCOUNT_EMPTY

    def _get_account_nonce(self, address: int) -> int:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == ACCOUNT_EMPTY:
            return 0
        return extract_nonce(account_cell)

    def _get_account_storage_slot(self, address: int, slot: int) -> int:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == ACCOUNT_EMPTY:
            return 0
        storage_cell = account_cell.terms[3]
        assert type(storage_cell) is KApply and storage_cell.label.name == '<storage>'
        storage_map = single(storage_cell.terms)
        if storage_map == map_empty():
            return 0
        storage_entries = flatten_label(MAP_CONS, storage_map)

        for entry in storage_entries:
            assert type(entry) is KApply and entry.label.name == '_|->_'
            key, value = entry.terms
            assert type(key) is KToken
            if int(key.token) == slot:
                assert type(value) is KToken
                return int(value.token)
        return 0

    def _get_account_code(self, address: int) -> str:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == ACCOUNT_EMPTY:
            return '0x'
        return extract_code(account_cell)

    def _get_account_balance(self, address: int) -> int:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == ACCOUNT_EMPTY:
            return 0
        return extract_balance(account_cell)

    def _get_account_addresses(self) -> list[int]:
        accounts_cell = flatten_label('_AccountCellMap_', self.cterm.cell('ACCOUNTS_CELL'))
        account_list = []
        for account in accounts_cell:
            assert type(account) is KApply
            acct_id = account.terms[0]
            assert type(acct_id) is KApply and acct_id.label.name == '<acctID>'
            _address = single(acct_id.terms)
            assert type(_address) is KToken
            account_list.append(int(_address.token))
        account_list.sort()
        return account_list

    def _add_or_update_account(self, new_account: KApply) -> None:
        """Add a new account or update an existing one in the ACCOUNTS_CELL.

        This function updates self.cterm to reflect the modified accounts list.
        :param new_account: The account to add or update.
        """

        all_accounts = flatten_label('_AccountCellMap_', self.cterm.cell('ACCOUNTS_CELL'))
        new_account_list: list[KInner] = []
        account_found = False

        # Iterate through the accounts, modifying or retaining them as needed
        for account in all_accounts:
            assert type(account) is KApply
            if account.args[0] == new_account.args[0]:
                # Replace the existing account with the new one
                new_account_list.append(new_account)
                account_found = True
            else:
                # Retain other accounts as they are
                new_account_list.append(account)

        # If the account was not found, append the new account
        if not account_found:
            new_account_list.append(new_account)

        # Update the ACCOUNTS_CELL with the new list
        self.cterm = CTerm.from_kast(
            set_cell(
                self.cterm.config,
                'ACCOUNTS_CELL',
                KEVM.accounts(new_account_list),
            )
        )
        self._krun_cterm()

    def _dump_accounts(self) -> dict:
        accounts_cell = flatten_label('_AccountCellMap_', self.cterm.cell('ACCOUNTS_CELL'))
        account_dict = {}
        for account in accounts_cell:
            assert type(account) is KApply
            address = hex(extract_address(account))
            balance = hex(extract_balance(account))
            code = extract_code(account)
            storage = extract_storage(account)
            nonce = extract_nonce(account)
            account_dict[address] = {'nonce': nonce, 'balance': balance, 'code': code, 'storage': storage}
        return account_dict

    def _collect_trace(self, transaction_hash: str) -> None:
        parsed_trace: list[dict[str, Any]] = []
        trace_data_cell = self.cterm.cell('TRACEDATA_CELL')
        trace_data = flatten_label('_List_', trace_data_cell)
        return_data = '0x' + ast.literal_eval(self._parse_ktoken_cell('OUTPUT_CELL')).hex()
        if len(trace_data) == 1 and trace_data[0] == list_empty():
            return

        for trace_list_item in trace_data:
            assert type(trace_list_item) is KApply
            trace_item = single(trace_list_item.terms)
            assert type(trace_item) is KApply
            parsed_trace.append(extract_trace_item(trace_item, return_data))

        self.traced_transactions[transaction_hash] = parsed_trace
        self.transaction_return_data[transaction_hash] = return_data[2:]

    def _get_tx_receipt_by_msg_id(self, msg_id: int) -> dict | None:
        tx_receipts_dict = self._get_all_tx_receipts_dict()
        tx_receipt = None

        for tx_receipt_key in tx_receipts_dict:
            if tx_receipts_dict[tx_receipt_key]['<txID>'] == msg_id:
                tx_receipt = tx_receipts_dict[tx_receipt_key]

        return tx_receipt

    def _get_tx_receipt_by_hash(self, hash: str) -> dict | None:
        tx_receipts_dict = self._get_all_tx_receipts_dict()
        return tx_receipts_dict[hash]

    def _get_all_tx_receipts_dict(self) -> dict:
        cells = self.cterm.cells
        cell = cells.get('TXRECEIPTS_CELL', None)

        tx_receipts: dict[str, Any] = {}

        if cell is None:
            # For the first transaction, the cells of the message will be scattered in the model, and if there is only this transaction in the messages map, this dictionary entry must be built manually.
            return self._build_tx_receipt_from_subst()
        else:
            assert type(cell) is KApply
            kapply_receipts = flatten_label('_TxReceiptCellMap_', cell)
            for r in kapply_receipts:
                assert type(r) is KApply
                receipt = extract_receipt(r)
                tx_receipts[receipt['<txHash>']] = receipt
            return tx_receipts

    def _get_last_message_tx_hash(self) -> str:
        msg_id = int(self._parse_ktoken_cell('CURRENTTXID_CELL'))
        tx_receipt = self._get_tx_receipt_by_msg_id(msg_id)
        assert tx_receipt is not None
        return tx_receipt['<txHash>']

    def _get_all_messages_dict(self) -> dict:
        messages_dict: dict[str, dict] = {}

        cell = self.cterm.cells.get('MESSAGES_CELL', None)

        if cell is None:
            # For the first transaction, the cells of the message will be scattered in the model, and if there is only this transaction in the messages map, this dictionary entry must be built manually.
            return self._build_message_from_subst()
        else:
            assert type(cell) is KApply
            kapply_messages = flatten_label('_MessageCellMap_', cell)
            for r in kapply_messages:
                assert type(r) is KApply
                message = extract_message(r)
                messages_dict[message['<msgID>']] = message
            return messages_dict

    def _get_block_header(self) -> dict:
        return {
            '<currentBlockHash>': hex(int(self._parse_ktoken_cell('CURRENTBLOCKHASH_CELL'))),
            '<previousHash>': hex(int(self._parse_ktoken_cell('PREVIOUSHASH_CELL'))),
            '<ommersHash>': hex(int(self._parse_ktoken_cell('OMMERSHASH_CELL'))).ljust(64, '0'),
            '<coinbase>': _acct_id_to_address(int(self._parse_ktoken_cell('COINBASE_CELL'))),
            '<stateRoot>': hex(int(self._parse_ktoken_cell('STATEROOT_CELL'))).ljust(64, '0'),
            '<transactionsRoot>': hex(int(self._parse_ktoken_cell('TRANSACTIONSROOT_CELL'))).ljust(64, '0'),
            '<receiptsRoot>': hex(int(self._parse_ktoken_cell('RECEIPTSROOT_CELL'))).ljust(64, '0'),
            '<logsBloom>': '0x' + ast.literal_eval(self._parse_ktoken_cell('LOGSBLOOM_CELL')).hex(),
            '<difficulty>': hex(int(self._parse_ktoken_cell('DIFFICULTY_CELL'))),
            '<number>': hex(int(self._parse_ktoken_cell('NUMBER_CELL'))),
            '<gasLimit>': hex(int(self._parse_ktoken_cell('GASLIMIT_CELL'))),
            '<gasUsed>': hex(int(self._parse_ktoken_cell('GASUSED_CELL'))),
            '<timestamp>': hex(int(self._parse_ktoken_cell('TIMESTAMP_CELL'))),
            '<extraData>': '0x' + ast.literal_eval(self._parse_ktoken_cell('EXTRADATA_CELL')).hex(),
            '<mixHash>': hex(int(self._parse_ktoken_cell('MIXHASH_CELL'))).ljust(64, '0'),
            '<blockNonce>': hex(int(self._parse_ktoken_cell('BLOCKNONCE_CELL'))),
            '<baseFee>': hex(int(self._parse_ktoken_cell('BASEFEE_CELL'))),
            '<withdrawalsRoot>': hex(int(self._parse_ktoken_cell('WITHDRAWALSROOT_CELL'))),
            '<blobGasUsed>': hex(int(self._parse_ktoken_cell('BLOBGASUSED_CELL'))),
            '<excessBlobGas>': hex(int(self._parse_ktoken_cell('EXCESSBLOBGAS_CELL'))),
            '<beaconRoot>': hex(int(self._parse_ktoken_cell('BEACONROOT_CELL'))),
            '<ommerBlockHeaders>': [],
        }

    # ------------------------------------------------------
    # VM setup functions
    # ------------------------------------------------------

    def _add_initial_accounts(self) -> None:
        balance = 10**20

        private_keys = [
            '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80',
            '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d',
            '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a',
            '0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6',
            '0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a',
            '0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba',
            '0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e',
            '0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356',
            '0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97',
            '0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6',
        ]
        sequence_of_productions = []

        for private_key in private_keys:
            sequence_of_productions.append(KApply('acctFromPrivateKey', [token(private_key), token(balance)]))

        sequence_of_kapplies = KSequence(sequence_of_productions)
        self.cterm = CTerm.from_kast(set_cell(self.cterm.config, 'K_CELL', sequence_of_kapplies))
        self._krun_cterm()

    def _krun_cterm(self) -> None:
        pattern = self.krun.kast_to_kore(self.cterm.config, sort=GENERATED_TOP_CELL)
        output_kore = self.krun.run_pattern(pattern, pipe_stderr=True)
        self.cterm = CTerm.from_kast(self.krun.kore_to_kast(output_kore))

    def _create_initial_account_list(self) -> list[KInner]:
        init_account_list: list[KInner] = []

        # Adding the Foundry cheatcode address
        init_account_list.append(Foundry.account_CHEATCODE_ADDRESS(map_empty()))

        return init_account_list

    def _init_cterm(self, steps_tracing: bool) -> None:
        self.krun.definition.empty_config(GENERATED_TOP_CELL)
        init_accounts_list = self._create_initial_account_list()
        init_config = self.krun.definition.init_config(GENERATED_TOP_CELL)
        init_subst = {
            '$PGM': KSequence([KEVM.sharp_execute()]),
            '$MODE': KApply('NORMAL'),
            '$SCHEDULE': KApply('SHANGHAI_EVM'),
            '$USEGAS': TRUE,
            '$CHAINID': token(31337),
        }

        init_config = set_cell(init_config, 'ACCOUNTS_CELL', KEVM.accounts(init_accounts_list))
        init_config = set_cell(init_config, 'BASEFEE_CELL', token(1000000000))
        init_config = set_cell(init_config, 'GASLIMIT_CELL', token(30000000))
        init_config = set_cell(init_config, 'TIMESTAMP_CELL', token(1725635810))
        init_config = set_cell(
            init_config,
            'OMMERSHASH_CELL',
            token(13478047122767188135818125966132228187941283477090363246179690878162135454535),
        )
        init_config = set_cell(
            init_config,
            'TRANSACTIONSROOT_CELL',
            token(39309028074332508661983559455579427211983204215636056653337583610388178777121),
        )
        init_config = set_cell(init_config, 'ACTIVETRACING_CELL', token(steps_tracing))
        init_config = set_cell(init_config, 'TRACEWORDSTACK_CELL', TRUE)
        init_config = set_cell(init_config, 'TRACEMEMORY_CELL', TRUE)

        init_term = Subst(init_subst)(init_config)
        self.cterm = CTerm.from_kast(init_term)
        self._add_initial_accounts()

    def _register_rpc_methods(self) -> None:
        rpc_methods: dict[str, Callable] = {
            'anvil_dumpState': self.exec_dump_state,
            'anvil_setBalance': self.exec_set_balance,
            'debug_traceTransaction': self.exec_trace_transaction,
            'eth_accounts': self.exec_accounts,
            'eth_blockNumber': self.exec_get_block_number,
            'eth_chainId': self.exec_get_chain_id,
            'eth_gasPrice': self.exec_get_gas_price,
            'eth_getBalance': self.exec_get_balance,
            'eth_getBlockByNumber': self.exec_get_block_by_number,
            'eth_getCode': self.exec_get_code,
            'eth_getStorageAt': self.exec_get_storage_at,
            'eth_getTransactionByHash': self.exec_get_transaction_by_hash,
            'eth_getTransactionCount': self.exec_get_transaction_count,
            'eth_getTransactionReceipt': self.exec_get_transaction_receipt,
            'eth_memoryUsed': self.exec_get_memory_used,
            'eth_sendTransaction': self.exec_send_transaction,
            'kontrol_addAccount': self.exec_add_account,
        }
        for method_name, exec_function in rpc_methods.items():
            self.register_method(method_name, exec_function)

    def _parse_ktoken_cell(self, cell_name: str) -> str:
        """Retrieves the value of a `KToken` inside a cell.

        This method looks up a cell by its name, verifies that the cell is of type
        `KToken`, and returns the associated token as a string.
        :param cell_name: The name of the cell to retrieve.
        :return: The token value of the `KToken` inside the cell.
        """
        cell = self.cterm.cell(cell_name)
        assert type(cell) is KToken
        return cell.token

    def _build_tx_receipt_from_subst(self) -> dict[str, Any]:
        """Manually builds the first transaction receipt when no <txReceipts> cell map is found.

        Returns:
            str: The uid (tx_hash) of the transaction receipt.
            dict: The manually created transaction receipt.
        """
        tx_hash = '0x' + self._parse_ktoken_cell('TXHASH_CELL')[1:-1]

        receipt: dict[str, Any] = {
            '<txHash>': tx_hash,
            '<txCumulativeGas>': int(self._parse_ktoken_cell('TXCUMULATIVEGAS_CELL')),
            '<logSet>': self._parse_log_set(),
            '<txNonce>': int(self._parse_ktoken_cell('TXNONCE_CELL')),
            '<bloomFilter>': '0x' + ast.literal_eval(self._parse_ktoken_cell('BLOOMFILTER_CELL')).hex(),
            '<txStatus>': int(self._parse_ktoken_cell('TXSTATUS_CELL')),
            '<txID>': int(self._parse_ktoken_cell('TXID_CELL')),
            '<sender>': int(self._parse_ktoken_cell('SENDER_CELL')),
            '<txBlockNumber>': int(self._parse_ktoken_cell('TXBLOCKNUMBER_CELL')),
            '<contractAddress>': self._parse_contract_address(),
        }

        return {tx_hash: receipt}

    def _build_message_from_subst(self) -> dict[int, Any]:
        """Manually builds the first message when no <messages> cell map is found.

        Returns:
            dict: The manually created message.
        """
        msg_id = int(self._parse_ktoken_cell('MSGID_CELL'))

        message: dict[str, Any] = {
            '<txNonce>': int(self._parse_ktoken_cell('TXNONCE_CELL')),
            '<txGasPrice>': int(self._parse_ktoken_cell('TXGASPRICE_CELL')),
            '<txGasLimit>': int(self._parse_ktoken_cell('TXGASLIMIT_CELL')),
            '<value>': int(self._parse_ktoken_cell('VALUE_CELL')),
            '<sigV>': int(self._parse_ktoken_cell('SIGV_CELL')),
            '<sigR>': '0x' + ast.literal_eval(self._parse_ktoken_cell('SIGR_CELL')).hex(),
            '<sigS>': '0x' + ast.literal_eval(self._parse_ktoken_cell('SIGS_CELL')).hex(),
            '<data>': '0x' + ast.literal_eval(self._parse_ktoken_cell('DATA_CELL')).hex(),
            '<txChainID>': int(self._parse_ktoken_cell('TXCHAINID_CELL')),
            '<txPriorityFee>': int(self._parse_ktoken_cell('TXPRIORITYFEE_CELL')),
            '<txMaxFee>': int(self._parse_ktoken_cell('TXMAXFEE_CELL')),
            '<msgID>': msg_id,
        }
        _c = self.cterm.cell('TO_CELL')
        if type(_c) is KToken:
            message['<to>'] = _acct_id_to_address(int(_c.token))

        _c = self.cterm.cell('TXTYPE_CELL')
        assert type(_c) is KApply
        message['<txType>'] = tx_type_to_int(_c.label)

        return {msg_id: message}

    def _parse_log_set(self) -> list:
        """Parses the log set from the LOGSET_CELL."""
        cell = self.cterm.cell('LOGSET_CELL')
        assert type(cell) is KApply
        return parse_kapply_list(cell)

    def _parse_contract_address(self) -> int | None:
        """Parses the contract address from the CONTRACTADDRESS_CELL."""
        cell = self.cterm.cell('CONTRACTADDRESS_CELL')
        if type(cell) is KToken:
            return int(cell.token)
        return None


# ------------------------------------------------------
# Helpers
# ------------------------------------------------------
def _acct_id_to_address(acct_id: int) -> str:
    hex_value = hex(acct_id).lower()[2:]
    target_length = 40
    padding_length = target_length - len(hex_value)
    padded_address = '0' * padding_length + hex_value
    return '0x' + padded_address


def _get_address_from(data: dict, data_key: str) -> int | None:
    address: str | None = data.get(data_key, None)
    if address is None:
        return None
    return _address_to_acct_id(address)


def _address_to_acct_id(address: str) -> int:
    if len(address) != 42:
        raise ValueError('Invalid string length')
    return int(address, base=16)


def _apply_format_to_message_cell_json_dict(message_dict: dict) -> dict:
    formatted_message_dict = {}

    for key in message_dict:
        new_key = key.replace('<', '').replace('>', '').replace('sig', '').replace('tx', '')

        new_key = new_key[0].lower() + new_key[1:]

        if new_key == 'gasLimit':
            new_key = 'gas'
        elif new_key == 'data':
            new_key = 'input'

        if new_key == 'to':
            formatted_message_dict[new_key] = message_dict[key]
        else:
            value = message_dict[key]

            try:
                int(value, 16)
                value = '0x' + value if value[:2] != '0x' else value
            except Exception:
                if type(value) is int:
                    value = hex(value)
                elif message_dict[key].isdecimal():
                    value = hex(int(message_dict[key]))
                else:
                    value = '0x' + ast.literal_eval(message_dict[key]).hex()

            formatted_message_dict[new_key] = value

    return formatted_message_dict


def _is_label_a_map(name: str) -> bool:
    map_names = ['<accounts>', '<messages>', '<blocks>']

    if name in map_names:
        return True

    return False


def _extract_cell_data(cell: KApply) -> list | dict | int | str:
    if _is_label_a_map(cell.label.name):
        return _from_cell_map_to_list(cell)

    return _convert_cell_to_dict(cell)


def _from_cell_map_to_list(cell: KApply) -> list:
    index_list = []
    cell_list = list(cell.args)

    index = 0
    while index < len(cell_list):
        _c = cell_list[index]
        if type(_c) is KApply and 'CellMap' in _c.label.name:
            index_list.append(index)
            for arg in list(_c.args):
                cell_list.append(arg)
        index += 1

    index_list.reverse()

    for index in index_list:
        cell_list.pop(index)

    return_list = [_extract_cell_data(_c) for _c in cell_list if type(_c) is KApply]

    _PPRINT.pprint(return_list)
    return return_list


def _convert_cell_to_dict(cell: KApply) -> dict | int | str:
    cell_dict = {}

    for args in cell.args:

        if type(args) is not KToken:
            assert type(args) is KApply

            cell_dict[args.label.name] = _extract_cell_data(args)
        else:
            assert type(args) is KToken
            if args.token.isdecimal():
                value = int(args.token)
            else:
                value = '0x' + ast.literal_eval(args.token).hex()

            return value

    return cell_dict


def eth_send_transaction(
    tx_type: str, sender: int, to: int | None, gas_limit: int, gas_price: int, value: int, nonce: int, data: str
) -> KApply:
    return KApply(
        'eth_sendTransaction',
        [
            KApply(tx_type + '_EVM-TYPES_TxType'),
            token(sender),
            (token(to) if type(to) is int else ACCOUNT_EMPTY),
            token(gas_limit),
            token(gas_price),
            token(value),
            token(nonce),
            bytesToken(bytes.fromhex(data[2:])),
        ],
    )


def tx_type_to_int(txtype: KLabel) -> int:
    if txtype.name == 'Legacy_EVM-TYPES_TxType':
        return 0
    else:
        raise ValueError(f'Unknown transaction type: {txtype.name}.')


def parse_kapply_list(kapply_list: KApply) -> list:
    """Parses a KApply list of KTokens into a Python list by extracting the KToken values.

    :param kapply_list:  The KApply structure representing the list.
    :return:  A Python list containing the token values extracted from the KApply list.
    """
    if kapply_list == list_empty():
        return []
    list_items = flatten_label('_List_', kapply_list)
    values = []
    for list_item in list_items:
        assert type(list_item) is KApply('ListItem')
        t = single(list_item.terms)
        assert type(t) is KToken
        values.append(t.token)
    return values


def extract_trace_item(trace_item: KApply, return_data: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    result['returnData'] = return_data
    # program counter
    program_counter_token = trace_item.terms[0]
    assert type(program_counter_token) is KToken
    result['pc'] = int(program_counter_token.token)
    # opcode
    opcode_kapply = trace_item.terms[1]
    assert type(opcode_kapply) is KApply
    opcode_size = ''
    if len(opcode_kapply.terms) > 0:
        opcode_token = single(opcode_kapply.terms)
        assert type(opcode_token) is KToken
        opcode_size = opcode_token.token
    result['op'] = opcode_kapply.label.name.split('_')[0] + opcode_size
    # wordstack
    wordstack_kapply = trace_item.terms[2]
    assert type(wordstack_kapply) is KApply
    if wordstack_kapply == WORDSTACK_EMPTY:
        wordstack = []
    else:
        wordstack = [hex(int(e.token)) for e in flatten_label(WORDSTACK_CONS, wordstack_kapply) if type(e) is KToken]
        wordstack.reverse()
    result['stack'] = wordstack
    # local memory
    local_mem_token = trace_item.terms[3]
    assert type(local_mem_token) is KToken
    local_mem = ast.literal_eval(local_mem_token.token).hex()
    memory_chunks = [
        (local_mem[i : i + CHUNK_SIZE]).ljust(CHUNK_SIZE, '0') for i in range(0, len(local_mem), CHUNK_SIZE)
    ]
    result['memory'] = memory_chunks
    # call depth
    call_depth_token = trace_item.terms[5]
    assert type(call_depth_token) is KToken
    result['depth'] = int(call_depth_token.token) + 1
    # gas available
    gas_token = trace_item.terms[6]
    assert type(gas_token) is KToken
    result['gas'] = int(gas_token.token)
    result['gasCost'] = 0
    return result


def extract_address(account_cell: KApply) -> int:
    assert type(account_cell) is KApply
    acct_id = account_cell.terms[0]
    assert type(acct_id) is KApply and acct_id.label.name == '<acctID>'
    _address = single(acct_id.terms)
    assert type(_address) is KToken
    return int(_address.token)


def extract_nonce(account_cell: KApply) -> int:
    nonce_cell = account_cell.terms[6]
    assert type(nonce_cell) is KApply and nonce_cell.label.name == '<nonce>'
    nonce = single(nonce_cell.terms)
    assert type(nonce) is KToken
    return int(nonce.token)


def extract_code(account_cell: KApply) -> str:
    code_cell = account_cell.terms[2]
    assert type(code_cell) is KApply and code_cell.label.name == '<code>'
    code = single(code_cell.terms)
    assert type(code) is KToken
    return '0x' + ast.literal_eval(code.token).hex()


def extract_balance(account_cell: KApply) -> int:
    balance_cell = account_cell.terms[1]
    assert type(balance_cell) is KApply and balance_cell.label.name == '<balance>'
    balance = single(balance_cell.terms)
    assert type(balance) is KToken
    return int(balance.token)


def extract_storage(account_cell: KApply) -> dict[str, str]:
    storage_cell = account_cell.terms[3]
    storage_dict: dict[str, str] = {}

    assert type(storage_cell) is KApply and storage_cell.label.name == '<storage>'
    storage_map = single(storage_cell.terms)
    if storage_map == map_empty():
        return {}

    storage_entries = flatten_label(MAP_CONS, storage_map)
    for entry in storage_entries:
        assert type(entry) is KApply and entry.label.name == '_|->_'
        key, value = entry.terms
        assert type(key) is KToken
        assert type(value) is KToken
        storage_dict[hex(int(key.token))] = hex(int(value.token))
    return storage_dict


def extract_receipt(receipt_cell: KApply) -> dict[str, Any]:
    """Builds the transaction receipt from the given <txReceipt> cell.

    :param receipt: The KApply object representing a transaction receipt.
    :raises TypeError: Signals any receipt terms that are not handled.
    :return: The transaction receipt data.
    """
    tx_receipt: dict[str, Any] = {}
    for term in receipt_cell.terms:
        assert type(term) is KApply
        key = term.label.name
        value = single(term.args)
        if key == '<logSet>':
            assert type(value) is KApply
            tx_receipt[key] = parse_kapply_list(value)
            continue

        if key == '<contractAddress>':
            tx_receipt[key] = int(value.token) if type(value) is KToken else None
            continue

        assert type(value) is KToken
        if key == '<txHash>':
            tx_receipt[key] = '0x' + value.token[1:-1]
        elif key == '<bloomFilter>':
            tx_receipt[key] = '0x' + ast.literal_eval(value.token).hex()
        elif key in ['<txCumulativeGas>', '<txNonce>', '<txStatus>', '<txID>', '<sender>', '<txBlockNumber>']:
            tx_receipt[key] = int(value.token)
        else:
            raise TypeError(f'Unexpected key {key}.')
    return tx_receipt


def extract_message(message_cell: KApply) -> dict[str, Any]:
    """Builds the message from the given <message> cell.

    :param receipt: The KApply object representing a message.
    :raises TypeError: Signals any receipt terms that are not handled.
    :return: The message data.
    """
    msg_dict: dict[str, Any] = {}
    for term in message_cell.terms:
        assert type(term) is KApply
        key = term.label.name
        value = single(term.args)
        if key == '<txAccess>':
            continue
        if key == '<to>':
            if type(value) is KToken:
                msg_dict[key] = _acct_id_to_address(int(value.token))
            continue
        if key == '<txType>':
            assert type(value) is KApply
            msg_dict[key] = tx_type_to_int(value.label)
            continue
        assert type(value) is KToken
        if key in ['<sigR>', '<sigS>', '<data>']:
            msg_dict[key] = '0x' + ast.literal_eval(value.token).hex()
        elif key in [
            '<msgID>',
            '<txNonce>',
            '<txGasPrice>',
            '<txGasLimit>',
            '<value>',
            '<sigV>',
            '<txChainID>',
            '<txPriorityFee>',
            '<txMaxFee>',
        ]:
            msg_dict[key] = int(value.token)
        else:
            raise TypeError(f'Unexpected key {key}.')
    return msg_dict
