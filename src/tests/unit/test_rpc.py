from __future__ import annotations

from typing import Any, Final

import pytest
from pyk.kast.inner import KApply, KLabel, KSort, KToken

from kontrol_node.rpc import extract_message, extract_receipt, extract_trace_item, get_address_from_private_key

EXTRACT_TRACE_ITEM_DATA: Final[list[tuple[str, KApply, str, dict[str, Any]]]] = [
    (
        'extract_trace_item_0',
        KApply(
            label=KLabel(name='traceItem', params=()),
            args=(
                KToken(token='0', sort=KSort(name='Int')),
                KApply(
                    label=KLabel(name='PUSH', params=()),
                    args=(KToken(token='1', sort=KSort(name='Int')),),
                ),
                KApply(label=KLabel(name='.WordStack_EVM-TYPES_WordStack', params=()), args=()),
                KToken(token='b""', sort=KSort(name='Bytes')),
                KApply(label=KLabel(name='.Map', params=()), args=()),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='29999546786', sort=KSort(name='Int')),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='1', sort=KSort(name='Int')),
                KToken(token='1725635810', sort=KSort(name='Int')),
                KToken(
                    token='1364846179604156837468707468773843663978916111562',
                    sort=KSort(name='Int'),
                ),
                KToken(
                    token='119096571092301921719253721560231391405901977941',
                    sort=KSort(name='Int'),
                ),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(
                    token='119096571092301921719253721560231391405901977941',
                    sort=KSort(name='Int'),
                ),
                KApply(label=KLabel(name='.StatusCode_NETWORK_StatusCode', params=()), args=()),
            ),
        ),
        '0x',
        {
            'returnData': '0x',
            'pc': 0,
            'op': 'PUSH1',
            'stack': [],
            'memory': [],
            'storage': {},
            'depth': 1,
            'gas': 29999546786,
            'coinbase': 0,
            'gasCost': 0,
            'difficulty': 0,
            'blockNumber': 1,
            'blockTimestamp': 1725635810,
            'targetAddress': 1364846179604156837468707468773843663978916111562,
            'msgSender': 119096571092301921719253721560231391405901977941,
            'msgValue': 0,
            'txOrigin': 119096571092301921719253721560231391405901977941,
            'statusCode': 'empty',
        },
    ),
    (
        'extract_trace_item_1',
        KApply(
            label=KLabel(name='traceItem', params=()),
            args=(
                KToken(token='669', sort=KSort(name='Int')),
                KApply(label=KLabel(name='STOP_EVM_NullStackOp', params=()), args=()),
                KApply(
                    label=KLabel(name='_:__EVM-TYPES_WordStack_Int_WordStack', params=()),
                    args=(
                        KToken(token='3223021356', sort=KSort(name='Int')),
                        KApply(
                            label=KLabel(name='.WordStack_EVM-TYPES_WordStack', params=()),
                            args=(),
                        ),
                    ),
                ),
                KToken(
                    token='b"\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xa0\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00d\\x00\\x00\\x00d\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00d"',
                    sort=KSort(name='Bytes'),
                ),
                KApply(
                    label=KLabel(name='_Map_', params=()),
                    args=(
                        KApply(
                            label=KLabel(name='_Map_', params=()),
                            args=(
                                KApply(
                                    label=KLabel(name='_Map_', params=()),
                                    args=(
                                        KApply(
                                            label=KLabel(name='_Map_', params=()),
                                            args=(
                                                KApply(
                                                    label=KLabel(name='_Map_', params=()),
                                                    args=(
                                                        KApply(
                                                            label=KLabel(name='_|->_', params=()),
                                                            args=(
                                                                KToken(
                                                                    token='31',
                                                                    sort=KSort(name='Int'),
                                                                ),
                                                                KToken(
                                                                    token='116848421129523080157339061407615272923298111283713',
                                                                    sort=KSort(name='Int'),
                                                                ),
                                                            ),
                                                        ),
                                                        KApply(
                                                            label=KLabel(name='_|->_', params=()),
                                                            args=(
                                                                KToken(
                                                                    token='12',
                                                                    sort=KSort(name='Int'),
                                                                ),
                                                                KToken(
                                                                    token='1',
                                                                    sort=KSort(name='Int'),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                                KApply(
                                                    label=KLabel(name='_|->_', params=()),
                                                    args=(
                                                        KToken(
                                                            token='34',
                                                            sort=KSort(name='Int'),
                                                        ),
                                                        KToken(
                                                            token='493120498101196152138321806898883778678928149372',
                                                            sort=KSort(name='Int'),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                        KApply(
                                            label=KLabel(name='_|->_', params=()),
                                            args=(
                                                KToken(token='35', sort=KSort(name='Int')),
                                                KToken(
                                                    token='100852501475775601404650405464272661921201036538',
                                                    sort=KSort(name='Int'),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                KApply(
                                    label=KLabel(name='_|->_', params=()),
                                    args=(
                                        KToken(token='32', sort=KSort(name='Int')),
                                        KToken(
                                            token='929221947425989735260509044971516249812803787378',
                                            sort=KSort(name='Int'),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        KApply(
                            label=KLabel(name='_|->_', params=()),
                            args=(
                                KToken(token='33', sort=KSort(name='Int')),
                                KToken(
                                    token='703931746484987709520011241182268216790810902249',
                                    sort=KSort(name='Int'),
                                ),
                            ),
                        ),
                    ),
                ),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='29999738857', sort=KSort(name='Int')),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(token='3', sort=KSort(name='Int')),
                KToken(token='1725635810', sort=KSort(name='Int')),
                KToken(
                    token='1364846179604156837468707468773843663978916111562',
                    sort=KSort(name='Int'),
                ),
                KToken(
                    token='119096571092301921719253721560231391405901977941',
                    sort=KSort(name='Int'),
                ),
                KToken(token='0', sort=KSort(name='Int')),
                KToken(
                    token='119096571092301921719253721560231391405901977941',
                    sort=KSort(name='Int'),
                ),
                KApply(
                    label=KLabel(name='EVMC_SUCCESS_NETWORK_EndStatusCode', params=()),
                    args=(),
                ),
            ),
        ),
        '0x60806040',
        {
            'returnData': '0x60806040',
            'pc': 669,
            'op': 'STOP',
            'stack': ['0xc01b672c'],
            'memory': [
                '0000000000000000000000000000000000000000000000000000000000000000',
                '0000000000000000000000000000000000000000000000000000000000000000',
                '00000000000000000000000000000000000000000000000000000000000000a0',
                '0000000000000000000000000000000000000000000000000000000000000000',
                '0000000000000000000000000000000000000000000000000000000000000064',
                '0000006400000000000000000000000000000000000000000000000000000000',
                '0000006400000000000000000000000000000000000000000000000000000000',
            ],
            'storage': {
                '0x1f': '0x4ff3706b36a51e0e0a6e30aeab70cf4eb71175e201',
                '0xc': '0x1',
                '0x22': '0x566049b37b48465baaed8dc5f171e30cb31b8b7c',
                '0x23': '0x11aa61f060af699eeb4846d15673551a5f569cfa',
                '0x20': '0xa2c3c0d2a5f98a74ea0752d377f6ec7adc541a72',
                '0x21': '0x7b4d642664d837f9f843cbd0b6d3eb3e0bcc3ee9',
            },
            'depth': 1,
            'gas': 29999738857,
            'coinbase': 0,
            'gasCost': 0,
            'difficulty': 0,
            'blockNumber': 3,
            'blockTimestamp': 1725635810,
            'targetAddress': 1364846179604156837468707468773843663978916111562,
            'msgSender': 119096571092301921719253721560231391405901977941,
            'msgValue': 0,
            'txOrigin': 119096571092301921719253721560231391405901977941,
            'statusCode': 'EVMC_SUCCESS',
        },
    ),
]


@pytest.mark.parametrize(
    'test_id,input,input_2,expected', EXTRACT_TRACE_ITEM_DATA, ids=[test_id for test_id, *_ in EXTRACT_TRACE_ITEM_DATA]
)
def test_extract_test_item(test_id: str, input: KApply, input_2: str, expected: dict[str, Any]) -> None:
    # When
    actual = extract_trace_item(input, input_2)

    # Then
    assert actual == expected


EXTRACT_RECEIPT_DATA: Final[list[tuple[str, KApply, dict[str, Any]]]] = [
    (
        'extract_receipt_0',
        KApply(
            '<txReceipt>',
            (
                KApply(
                    '<txHash>',
                    (
                        KToken(
                            '"518e6dfceddd624113d2fe12891b0732f268b2fe6626de61aac123e8d884aaa1"',
                            KSort('String'),
                        ),
                    ),
                ),
                KApply('<txCumulativeGas>', (KToken('160321', KSort('Int')))),
                KApply('<logSet>', (KApply('.List', ()))),
                KApply(
                    '<bloomFilter>',
                    (
                        KToken(
                            'b"\\x00\\x00"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply('<txStatus>', (KToken('1', KSort('Int')))),
                KApply('<txID>', (KToken('0', KSort('Int')))),
                KApply(
                    '<sender>',
                    (KToken('119096571092301921719253721560231391405901977941', KSort('Int'))),
                ),
                KApply('<txBlockNumber>', (KToken('0', KSort('Int')))),
                KApply(
                    '<contractAddress>',
                    (KToken('1364846179604156837468707468773843663978916111562', KSort('Int'))),
                ),
            ),
        ),
        {
            '<txHash>': '0x518e6dfceddd624113d2fe12891b0732f268b2fe6626de61aac123e8d884aaa1',
            '<txCumulativeGas>': 160321,
            '<logSet>': [],
            '<bloomFilter>': '0x0000',
            '<txStatus>': 1,
            '<txID>': 0,
            '<sender>': 119096571092301921719253721560231391405901977941,
            '<txBlockNumber>': 0,
            '<contractAddress>': 1364846179604156837468707468773843663978916111562,
        },
    )
]


@pytest.mark.parametrize(
    'test_id,input,expected', EXTRACT_RECEIPT_DATA, ids=[test_id for test_id, *_ in EXTRACT_RECEIPT_DATA]
)
def test_extract_receipt(test_id: str, input: KApply, expected: dict[str, Any]) -> None:
    # When
    actual = extract_receipt(input)

    # Then
    assert actual == expected


EXTRACT_MESSAGE_DATA: Final[list[tuple[str, KApply, dict[str, Any]]]] = [
    (
        'extract_message_0',
        KApply(
            '<message>',
            (
                KApply(
                    '<msgID>',
                    (KToken('1', KSort('Int'))),
                ),
                KApply(
                    '<txNonce>',
                    (KToken('1', KSort('Int'))),
                ),
                KApply(
                    '<txGasPrice>',
                    (KToken('0', KSort('Int'))),
                ),
                KApply(
                    '<txGasLimit>',
                    (KToken('30000000', KSort('Int'))),
                ),
                KApply(
                    '<to>',
                    (
                        KApply(
                            '.Account_EVM-TYPES_Account',
                        ),
                    ),
                ),
                KApply(
                    '<value>',
                    (KToken('0', KSort('Int'))),
                ),
                KApply(
                    '<sigV>',
                    (KToken('62710', KSort('Int'))),
                ),
                KApply(
                    '<sigR>',
                    (
                        KToken(
                            'b"\\x97\\xa3\\r\\xfa\\x90_K\\x9b\\xe9\\x15\\xc4F\\x81 \\xb2;\\xb4\\x03_&n&X\\xf4;R\\xabLb<\\xca\\xc2"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(
                    '<sigS>',
                    (
                        KToken(
                            'b"\\x0b\\x88\\x8f\\x15\\xa4O\\x19\\xf4\\xfb_\\x8a@U\\xe0e\\xd68\\x02\\x11\\xfb\\x89}K\\xf5?\\xc0\\xa54\\x07\\xa0\\x06\\x14"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(
                    '<data>',
                    (
                        KToken(
                            'b"`\\x80`@"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(
                    '<txAccess>',
                    (
                        KApply(
                            'JSONList',
                            (
                                KApply(
                                    '.List{"JSONs"}',
                                ),
                            ),
                        ),
                    ),
                ),
                KApply(
                    '<txChainID>',
                    (KToken('31337', KSort('Int'))),
                ),
                KApply(
                    '<txPriorityFee>',
                    (KToken('0', KSort('Int'))),
                ),
                KApply(
                    '<txMaxFee>',
                    (KToken('0', KSort('Int'))),
                ),
                KApply(
                    '<txType>',
                    (
                        KApply(
                            'Legacy_EVM-TYPES_TxType',
                        ),
                    ),
                ),
            ),
        ),
        {
            '<msgID>': 1,
            '<txNonce>': 1,
            '<txGasPrice>': 0,
            '<txGasLimit>': 30000000,
            '<txType>': 0,
            '<value>': 0,
            '<sigV>': 62710,
            '<sigR>': '0x97a30dfa905f4b9be915c4468120b23bb4035f266e2658f43b52ab4c623ccac2',
            '<sigS>': '0x0b888f15a44f19f4fb5f8a4055e065d6380211fb897d4bf53fc0a53407a00614',
            '<data>': '0x60806040',
            '<txChainID>': 31337,
            '<txPriorityFee>': 0,
            '<txMaxFee>': 0,
        },
    )
]


@pytest.mark.parametrize(
    'test_id,input,expected', EXTRACT_MESSAGE_DATA, ids=[test_id for test_id, *_ in EXTRACT_MESSAGE_DATA]
)
def test_extract_message(test_id: str, input: KApply, expected: dict[str, Any]) -> None:
    # When
    actual = extract_message(input)

    # Then
    assert actual == expected


PRIVATE_KEY_TO_ADDRESS_DATA: Final[list[tuple[str, str, str]]] = [
    (
        'address-from-pk-0',
        '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80',
        '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
    )
]


@pytest.mark.parametrize(
    'test_id,input,expected', PRIVATE_KEY_TO_ADDRESS_DATA, ids=[test_id for test_id, *_ in PRIVATE_KEY_TO_ADDRESS_DATA]
)
def test_private_key_to_address(test_id: str, input: str, expected: str) -> None:
    # When
    actual = get_address_from_private_key(input)

    # Then
    assert actual == expected
