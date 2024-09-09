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

        self.register_method('eth_chainId', self.exec_get_chain_id)
        self.register_method('eth_memoryUsed', self.exec_get_memory_used)
        self.register_method('eth_gasPrice', self.exec_get_gas_price)
        self.register_method('eth_blockNumber', self.exec_get_block_number)
        self.register_method('eth_getBlockByNumber', self.exec_get_block_by_number)
        self.register_method('eth_accounts', self.exec_accounts)
        self.register_method('eth_getBalance', self.exec_get_balance)
        self.register_method('eth_sendTransaction', self.exec_send_transaction)
        self.register_method('eth_getTransactionByHash', self.exec_get_transaction_by_hash)
        self.register_method('eth_getTransactionReceipt', self.exec_get_transaction_receipt)
        self.register_method('kontrol_requestValue', self.exec_request_value)
        self.register_method('kontrol_addAccount', self.exec_add_account)

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

    def exec_get_block_by_number(self, block_number: int) -> int:
        print(f'BLOCK NUMBER: {block_number}')
        self._get_all_block_storage_dict()
        return block_number

    def exec_get_balance(self, address: str) -> str:
        acct_id = _address_to_acct_id(address)
        accounts_dict = self._get_all_accounts_dict()
        return hex(int(accounts_dict[str(acct_id)]['<balance>'])).lower()

    def exec_accounts(self) -> list[str]:
        accounts_list = []

        for key in self._get_all_accounts_dict():
            accounts_list.append(_acct_id_to_address(int(key)))

        return accounts_list

    def exec_add_account(self, private_key: str, balance_hex: str) -> None:
        balance = int(balance_hex, 16)
        self.cterm = CTerm.from_kast(
            set_cell(self.cterm.config, 'K_CELL', KApply('acctFromPrivateKey', [token(private_key), token(balance)]))
        )
        pattern = self.krun.kast_to_kore(self.cterm.config, sort=GENERATED_TOP_CELL)
        output_kore = self.krun.run_pattern(pattern, pipe_stderr=True)
        self.cterm = CTerm.from_kast(self.krun.kore_to_kast(output_kore))
        return None

    def exec_request_value(self) -> int:
        self.cterm = CTerm.from_kast(set_cell(self.cterm.config, 'K_CELL', KApply('kontrol_requestValue', [])))
        pattern = self.krun.kast_to_kore(self.cterm.config, sort=GENERATED_TOP_CELL)
        output_kore = self.krun.run_pattern(pattern, pipe_stderr=True)
        self.cterm = CTerm.from_kast(self.krun.kore_to_kast(output_kore))
        rpc_response_cell = self.cterm.cell('RPCRESPONSE_CELL')
        _PPRINT.pprint(rpc_response_cell)
        return 0

    def exec_send_transaction(self, transaction_json: dict) -> str:
        sender: int | None = _get_address_from(transaction_json, 'from')
        # TODO: if `sender` account is missing, use the first accounts[0] from the initial state
        assert sender is not None
        sender_data = self._get_account_cell_by_address(sender)
        destination: int | None = _get_address_from(transaction_json, 'to')

        tx_type: str = transaction_json.get('type', 'Legacy')
        nonce: int = transaction_json.get('nonce', int(sender_data['<nonce>']))
        gas: int = int(transaction_json.get('gas', '0x15f90'), base=16)
        gas_price: int = int(transaction_json.get('gasPrice', '0x0'), 16)
        value: int = int(transaction_json.get('value', '0x0'), 16)
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
        receipt['cumulativeGasUsed'] = hex(tx_receipt_dict['<txCumulativeGasUsed>'])
        receipt['logs'] = tx_receipt_dict['<logSet>']
        receipt['logsBloom'] = tx_receipt_dict['<bloomFilter>']
        receipt['transactionHash'] = tx_hash
        receipt['transactionIndex'] = hex(int(msg_id))
        receipt['blockNumber'] = hex(tx_receipt_dict['<txBlockNumber>'])
        receipt['gasUsed'] = hex(tx_receipt_dict['<txCumulativeGasUsed>'])
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

    def _get_account_cell_by_address(self, address: int) -> dict:
        accounts_dict = self._get_all_accounts_dict()
        account_data = accounts_dict[str(address)] if str(address) in accounts_dict else None
        return account_data

    def _get_all_accounts_dict(self) -> dict:
        cells = self.cterm.cells
        cell = cells.get('ACCOUNTS_CELL', None)
        assert type(cell) is KApply

        accounts_dict = {}

        queue: deque[KInner] = deque(cell.args)
        while len(queue) > 0:
            account_cell = queue.popleft()
            if isinstance(account_cell, KApply):
                if account_cell.label.name == '<account>':
                    account_dict = {}
                    for args in account_cell.args:
                        assert type(args) is KApply
                        cell_name = args.label.name
                        if isinstance(args.args[0], KToken):
                            account_dict[cell_name] = args.args[0].token

                    accounts_dict[account_dict['<acctID>']] = account_dict
                elif 'AccountCellMap' in account_cell.label.name:
                    queue.extend(account_cell.args)

        return accounts_dict

    def _get_tx_receipt_by_msg_id(self, msg_id: int) -> dict | None:
        tx_receipts_dict = self._get_all_tx_receipts_dict()
        tx_receipt = None

        for tx_receipt_key in tx_receipts_dict:
            if tx_receipts_dict[tx_receipt_key]['<txID>'] == msg_id:
                tx_receipt = tx_receipts_dict[tx_receipt_key]

        return tx_receipt

    def _get_tx_receipt_by_hash(self, hash: str) -> dict | None:
        tx_receipts_dict = self._get_all_tx_receipts_dict()
        return tx_receipts_dict[hash[2:]]

    def _get_all_tx_receipts_dict(self) -> dict:
        cells = self.cterm.cells
        cell = cells.get('TXRECEIPTS_CELL', None)

        tx_receipts_dict: dict[str, Any] = {}

        if cell is None:
            # For the first transaction, the cells of the message will be scattered in the model, and if there is only this transaction in the messages map, this dictionary entry must be built manually.
            tx_hash = self._parse_ktoken_cell('TXHASH_CELL')[1:-1]

            tx_receipts_dict[tx_hash] = {'<txHash>': '0x' + tx_hash}

            tx_receipts_dict[tx_hash]['<txCumulativeGasUsed>'] = int(self._parse_ktoken_cell('TXCUMULATIVEGAS_CELL'))
            tx_receipts_dict[tx_hash]['<txNonce>'] = int(self._parse_ktoken_cell('TXNONCE_CELL'))
            tx_receipts_dict[tx_hash]['<bloomFilter>'] = (
                '0x' + ast.literal_eval(self._parse_ktoken_cell('BLOOMFILTER_CELL')).hex()
            )
            tx_receipts_dict[tx_hash]['<txStatus>'] = int(self._parse_ktoken_cell('TXSTATUS_CELL'))
            tx_receipts_dict[tx_hash]['<txID>'] = int(self._parse_ktoken_cell('TXID_CELL'))
            tx_receipts_dict[tx_hash]['<sender>'] = int(self._parse_ktoken_cell('SENDER_CELL'))
            tx_receipts_dict[tx_hash]['<txBlockNumber>'] = int(self._parse_ktoken_cell('TXBLOCKNUMBER_CELL'))
            cell = self.cterm.cell('LOGSET_CELL')
            assert type(cell) is KApply
            tx_receipts_dict[tx_hash]['<logSet>'] = parse_kapply_list(cell)
            cell = self.cterm.cell('CONTRACTADDRESS_CELL')
            if type(cell) is KToken:
                tx_receipts_dict[tx_hash]['<contractAddress>'] = int(cell.token)

        else:
            assert type(cell) is KApply
            queue: deque[KInner] = deque(cell.args)
            while len(queue) > 0:
                tx_receipt_cell = queue.popleft()
                if isinstance(tx_receipt_cell, KApply):
                    if tx_receipt_cell.label.name == '<txReceipt>':
                        tx_receipt_dict: dict[str, Any] = {}
                        for args in tx_receipt_cell.args:
                            assert type(args) is KApply
                            cell_name = args.label.name
                            if isinstance(args.args[0], KToken):
                                value = None

                                if args.args[0].token.isdecimal():
                                    value = int(args.args[0].token)
                                else:
                                    value = '0x' + ast.literal_eval(args.args[0].token).hex()

                                tx_receipt_dict[cell_name] = value

                        tx_receipts_dict[tx_receipt_dict['<txHash>']] = tx_receipt_dict
                    elif 'txReceiptCellMap' in tx_receipt_cell.label.name:
                        queue.extend(tx_receipt_cell.args)

        return tx_receipts_dict

    def _get_last_message_tx_hash(self) -> str:
        last_tx_id = int(self._parse_ktoken_cell('CURRENTTXID_CELL'))
        tx_receipt = self._get_tx_receipt_by_msg_id(last_tx_id)
        assert tx_receipt is not None
        last_tx_hash = tx_receipt['<txHash>']
        return last_tx_hash

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

    def _parse_ktoken_cell(self, cell_name: str) -> str:
        cell = self.cterm.cell(cell_name)
        assert type(cell) is KToken
        return cell.token


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
            (token(to) if type(to) is int else dot_account()),
            token(gas_limit),
            token(gas_price),
            token(value),
            token(nonce),
            bytesToken(bytes.fromhex(data[2:])),
        ],
    )


def dot_account() -> KApply:
    return KApply('.Account_EVM-TYPES_Account')


def tx_type_to_int(txtype: KLabel) -> int:
    if txtype.name == 'Legacy_EVM-TYPES_TxType':
        return 0
    else:
        raise ValueError(f'Unknown transaction type: {txtype.name}.')


def parse_kapply_list(kapply_list: KApply) -> list:
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
