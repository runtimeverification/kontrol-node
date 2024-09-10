from __future__ import annotations

import ast
import pprint
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

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
from pyk.rpc.rpc import JsonRpcServer
from pyk.utils import single

if TYPE_CHECKING:
    from pyk.kast.inner import KInner, KLabel
    from pyk.rpc.rpc import ServeRpcOptions

_PPRINT = pprint.PrettyPrinter(width=41, compact=True)


class StatefulKJsonRpcServer(JsonRpcServer):
    krun: KRun
    cterm: CTerm

    def __init__(self, options: ServeRpcOptions) -> None:
        super().__init__(options)

        self._register_rpc_methods()
        dir_path = Path(f'{kdist.kdist_dir}/kontrol-node/simbolik')
        self.krun = KRun(dir_path)

        start_time = datetime.now()
        self._init_cterm()
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

    def exec_get_block_by_number(self, block_number: int) -> int:
        print(f'BLOCK NUMBER: {block_number}')
        self._get_all_block_storage_dict()
        return block_number

    def exec_get_balance(self, hex_address: str, _block_number: str) -> str:
        address = _address_to_acct_id(hex_address)
        return hex(self._get_account_balance(address))

    def exec_get_transaction_count(self, hex_address: str, _block_number: str) -> str:
        address = _address_to_acct_id(hex_address)
        return hex(self._get_account_nonce(address))

    def exec_accounts(self) -> list[str]:
        return [hex(address) for address in self._get_account_addresses()]

    def exec_add_account(self, private_key: str, balance_hex: str) -> None:
        balance = int(balance_hex, 16)
        self.cterm = CTerm.from_kast(
            set_cell(self.cterm.config, 'K_CELL', KApply('acctFromPrivateKey', [token(private_key), token(balance)]))
        )
        pattern = self.krun.kast_to_kore(self.cterm.config, sort=GENERATED_TOP_CELL)
        output_kore = self.krun.run_pattern(pattern, pipe_stderr=True)
        self.cterm = CTerm.from_kast(self.krun.kore_to_kast(output_kore))
        return None

    def exec_send_transaction(self, transaction_json: dict) -> str:
        sender: int | None = _get_address_from(transaction_json, 'from')
        assert sender is not None
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

        pattern = self.krun.kast_to_kore(self.cterm.config, sort=GENERATED_TOP_CELL)
        output_kore = self.krun.run_pattern(pattern, pipe_stderr=True)
        self.cterm = CTerm.from_kast(self.krun.kore_to_kast(output_kore))

        return self._get_last_message_tx_hash()

    def exec_get_transaction_by_hash(self, tx_hash: str) -> dict | str:
        tx_receipt = self._get_tx_receipt_by_hash(tx_hash)

        if tx_receipt is None:
            return 'Transaction receipt not found'

        msg_id = str(tx_receipt['<txID>'])
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

        msg_id = str(tx_receipt_dict['<txID>'])
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
        receipt['to'] = hex(message_dict['<to>']) if '<to>' in message_dict.keys() else None
        receipt['contractAddress'] = (
            hex(tx_receipt_dict['<contractAddress>']) if '<contractAddress>' in tx_receipt_dict.keys() else None
        )
        receipt['root'] = hex(int(self._parse_ktoken_cell('TRANSACTIONSROOT_CELL')))
        return receipt

    # ------------------------------------------------------
    # VM data fetch helper functions
    # ------------------------------------------------------

    def _get_account_cell_by_address(self, address: int) -> KApply:
        accounts_cell = flatten_label('_AccountCellMap_', self.cterm.cell('ACCOUNTS_CELL'))
        for account in accounts_cell:
            assert type(account) is KApply
            acct_id = account.terms[0]
            assert type(acct_id) is KApply and acct_id.label.name == '<acctID>'
            _address = single(acct_id.terms)
            assert type(_address) is KToken
            if int(_address.token) == address:
                return account
        return account_empty()

    def _get_account_nonce(self, address: int) -> int:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == account_empty():
            return 0
        nonce_cell = account_cell.terms[6]
        assert type(nonce_cell) is KApply and nonce_cell.label.name == '<nonce>'
        nonce = single(nonce_cell.terms)
        assert type(nonce) is KToken
        return int(nonce.token)

    def _get_account_storage_slot(self, address: int, slot: int) -> int:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == account_empty():
            return 0
        storage_cell = account_cell.terms[3]
        assert type(storage_cell) is KApply and storage_cell.label.name == '<storage>'
        storage_map = single(storage_cell.terms)
        if storage_map == map_empty():
            return 0
        storage_entries = flatten_label('_Map_', storage_map)

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
        if account_cell == account_empty():
            return '0x'
        code_cell = account_cell.terms[2]
        assert type(code_cell) is KApply and code_cell.label.name == '<code>'
        code = single(code_cell.terms)
        assert type(code) is KToken
        return '0x' + ast.literal_eval(code.token).hex()

    def _get_account_balance(self, address: int) -> int:
        account_cell = self._get_account_cell_by_address(address)
        if account_cell == account_empty():
            return 0
        balance_cell = account_cell.terms[1]
        assert type(balance_cell) is KApply and balance_cell.label.name == '<balance>'
        balance = single(balance_cell.terms)
        assert type(balance) is KToken
        return int(balance.token)

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
                receipt = self._build_tx_receipt_from_cell(r)
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
            msg_id = self._parse_ktoken_cell('TXNONCE_CELL')
            messages_dict[msg_id] = {}

            messages_dict[msg_id]['<txNonce>'] = int(self._parse_ktoken_cell('TXNONCE_CELL'))
            messages_dict[msg_id]['<txGasPrice>'] = int(self._parse_ktoken_cell('TXGASPRICE_CELL'))
            messages_dict[msg_id]['<txGasLimit>'] = int(self._parse_ktoken_cell('TXGASLIMIT_CELL'))
            messages_dict[msg_id]['<value>'] = int(self._parse_ktoken_cell('VALUE_CELL'))
            messages_dict[msg_id]['<sigV>'] = int(self._parse_ktoken_cell('SIGV_CELL'))
            messages_dict[msg_id]['<sigR>'] = ast.literal_eval(self._parse_ktoken_cell('SIGR_CELL')).hex()
            messages_dict[msg_id]['<sigS>'] = ast.literal_eval(self._parse_ktoken_cell('SIGS_CELL')).hex()
            messages_dict[msg_id]['<data>'] = '0x' + ast.literal_eval(self._parse_ktoken_cell('DATA_CELL')).hex()
            messages_dict[msg_id]['<txChainID>'] = int(self._parse_ktoken_cell('TXCHAINID_CELL'))
            messages_dict[msg_id]['<txPriorityFee>'] = int(self._parse_ktoken_cell('TXPRIORITYFEE_CELL'))
            messages_dict[msg_id]['<txMaxFee>'] = int(self._parse_ktoken_cell('TXMAXFEE_CELL'))

            _c = self.cterm.cell('TO_CELL')
            if type(_c) is KToken:
                messages_dict[msg_id]['<to>'] = _acct_id_to_address(int(_c.token))

            _c = self.cterm.cell('TXTYPE_CELL')
            assert type(_c) is KApply
            messages_dict[msg_id]['<txType>'] = tx_type_to_int(_c.label)

        else:
            assert type(cell) is KApply
            queue: deque[KInner] = deque(cell.args)
            while len(queue) > 0:
                message_cell = queue.popleft()
                if isinstance(message_cell, KApply):
                    if message_cell.label.name == '<message>':
                        message_dict = {}
                        for args in message_cell.args:
                            assert type(args) is KApply
                            cell_name = str(args.label.name)
                            if isinstance(args.args[0], KToken):

                                value = None

                                if args.args[0].token.isdecimal():
                                    value = int(args.args[0].token)
                                else:
                                    value = '0x' + ast.literal_eval(args.args[0].token).hex()

                                message_dict[cell_name] = value

                        msg_id = str(message_dict['<msgID>'])
                        messages_dict[msg_id] = message_dict
                    elif 'MessageCellMap' in message_cell.label.name:
                        queue.extend(message_cell.args)

        return messages_dict

    def _get_all_block_storage_dict(self) -> dict:
        block_storage_dict = {}

        cell = self.cterm.cell('BLOCKSTORAGE_CELL')
        assert type(cell) is KApply

        queue: deque[KInner] = deque(cell.args)
        while len(queue) > 0:
            cell = queue.popleft()
            if isinstance(cell, KApply):
                # print(cell.label.name)
                if 'BlockchainItem' in cell.label.name:
                    item_dict = {}
                    for args in cell.args:
                        assert type(args) is KApply
                        cell_dict = _extract_cell_data(args)
                        assert type(cell_dict) is dict
                        item_dict[args.label.name] = cell_dict

                    # msg_id = str(message_dict['<network>'])
                    block_storage_dict[item_dict['<block>']['<number>']] = item_dict
                # elif 'Map' in cell.label.name:# or
                elif '_|->_' in cell.label.name:
                    queue.extend(cell.args)
                # else:
                #     print(cell.label.name)

        return block_storage_dict

    # ------------------------------------------------------
    # VM setup functions
    # ------------------------------------------------------

    def _add_initial_accounts(self) -> None:
        balance = 10**20

        private_keys = [
            '0xcdeac0dd5ec7c04072af48f2a4451e102a80ca5bb441a7b4d72c176cea61866e',
            '0xafdfd9c3d2095ef696594f6cedcae59e72dcd697e2a7521b1578140422a4f890',
            '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80',
        ]
        sequence_of_productions = []

        for private_key in private_keys:
            sequence_of_productions.append(KApply('acctFromPrivateKey', [token(private_key), token(balance)]))

        sequence_of_kapplies = KSequence(sequence_of_productions)
        self.cterm = CTerm.from_kast(set_cell(self.cterm.config, 'K_CELL', sequence_of_kapplies))
        pattern = self.krun.kast_to_kore(self.cterm.config, sort=GENERATED_TOP_CELL)
        output_kore = self.krun.run_pattern(pattern, pipe_stderr=True)
        self.cterm = CTerm.from_kast(self.krun.kore_to_kast(output_kore))

        return None

    def _create_initial_account_list(self) -> list[KInner]:
        init_account_list: list[KInner] = []

        # Adding a zero address
        init_account_list.append(
            KEVM.account_cell(
                token(0),
                token(0),
                bytesToken(b''),
                map_empty(),
                map_empty(),
                map_empty(),
                token(0),
            )
        )

        # Adding the Foundry cheatcode address
        init_account_list.append(Foundry.account_CHEATCODE_ADDRESS(map_empty()))

        return init_account_list

    def _init_cterm(self) -> None:
        self.krun.definition.empty_config(GENERATED_TOP_CELL)

        init_accounts_list = self._create_initial_account_list()

        init_config = self.krun.definition.init_config(GENERATED_TOP_CELL)

        init_subst = {
            '$PGM': KSequence([KEVM.sharp_execute()]),
            '$MODE': KApply('NORMAL'),
            '$SCHEDULE': KApply('SHANGHAI_EVM'),
            '$USEGAS': TRUE,
            '$CHAINID': token(31337),
            'BASEFEE_CELL': token(1000000000),
            'GASLIMIT_CELL': token(30000000),
            'TIMESTAMP_CELL': token(1725635810),
        }

        init_config = set_cell(init_config, 'ACCOUNTS_CELL', KEVM.accounts(init_accounts_list))

        init_term = Subst(init_subst)(init_config)
        self.cterm = CTerm.from_kast(init_term)
        self._add_initial_accounts()

    def _register_rpc_methods(self) -> None:
        self.register_method('eth_accounts', self.exec_accounts)
        self.register_method('eth_blockNumber', self.exec_get_block_number)
        self.register_method('eth_chainId', self.exec_get_chain_id)
        self.register_method('eth_gasPrice', self.exec_get_gas_price)
        self.register_method('eth_getBalance', self.exec_get_balance)
        self.register_method('eth_getBlockByNumber', self.exec_get_block_by_number)
        self.register_method('eth_getCode', self.exec_get_code)
        self.register_method('eth_getStorageAt', self.exec_get_storage_at)
        self.register_method('eth_getTransactionByHash', self.exec_get_transaction_by_hash)
        self.register_method('eth_getTransactionCount', self.exec_get_transaction_count)
        self.register_method('eth_getTransactionReceipt', self.exec_get_transaction_receipt)
        self.register_method('eth_memoryUsed', self.exec_get_memory_used)
        self.register_method('eth_sendTransaction', self.exec_send_transaction)
        self.register_method('kontrol_addAccount', self.exec_add_account)

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
            dict: The manually created transaction receipt.
        """
        tx_receipts: dict[str, Any] = {}
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

        tx_receipts[tx_hash] = receipt
        return tx_receipts

    def _build_tx_receipt_from_cell(self, receipt: KApply) -> dict[str, Any]:
        """Builds the transaction receipt from the given <txReceipt> cell.

        :param receipt: The KApply object representing a transaction receipt.
        :raises TypeError: Signals any receipt terms that are not handled.
        :return: The transaction receipt data.
        """
        tx_receipt: dict[str, Any] = {}
        for term in receipt.terms:
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
            (token(to) if type(to) is int else account_empty()),
            token(gas_limit),
            token(gas_price),
            token(value),
            token(nonce),
            bytesToken(bytes.fromhex(data[2:])),
        ],
    )


def account_empty() -> KApply:
    return KApply('.Account_EVM-TYPES_Account')


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
