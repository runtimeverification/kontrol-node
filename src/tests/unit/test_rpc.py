from __future__ import annotations

from typing import Any, Final

import pytest
from pyk.kast.inner import KApply, KLabel, KSort, KToken

from kontrol_node.rpc import extract_message, extract_receipt

EXTRACT_RECEIPT_DATA: Final[list[tuple[str, KApply, dict[str, Any]]]] = [
    (
        'extract_receipt_0',
        KApply(
            KLabel('<txReceipt>'),
            (
                KApply(
                    KLabel('<txHash>'),
                    (
                        KToken(
                            '"518e6dfceddd624113d2fe12891b0732f268b2fe6626de61aac123e8d884aaa1"',
                            KSort('String'),
                        ),
                    ),
                ),
                KApply(KLabel('<txCumulativeGas>'), (KToken('160321', KSort('Int')),)),
                KApply(KLabel('<logSet>'), (KApply(KLabel('.List'), ()),)),
                KApply(
                    KLabel('<bloomFilter>'),
                    (
                        KToken(
                            'b"\\x00\\x00"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(KLabel('<txStatus>'), (KToken('1', KSort('Int')),)),
                KApply(KLabel('<txID>'), (KToken('0', KSort('Int')),)),
                KApply(
                    KLabel('<sender>'),
                    (KToken('119096571092301921719253721560231391405901977941', KSort('Int')),),
                ),
                KApply(KLabel('<txBlockNumber>'), (KToken('0', KSort('Int')),)),
                KApply(
                    KLabel('<contractAddress>'),
                    (KToken('1364846179604156837468707468773843663978916111562', KSort('Int')),),
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
            KLabel(
                '<message>',
            ),
            (
                KApply(
                    KLabel(
                        '<msgID>',
                    ),
                    (KToken('1', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<txNonce>',
                    ),
                    (KToken('1', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<txGasPrice>',
                    ),
                    (KToken('0', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<txGasLimit>',
                    ),
                    (KToken('30000000', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<to>',
                    ),
                    (
                        KApply(
                            KLabel(
                                '.Account_EVM-TYPES_Account',
                            ),
                            (),
                        ),
                    ),
                ),
                KApply(
                    KLabel(
                        '<value>',
                    ),
                    (KToken('0', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<sigV>',
                    ),
                    (KToken('62710', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<sigR>',
                    ),
                    (
                        KToken(
                            'b"\\x97\\xa3\\r\\xfa\\x90_K\\x9b\\xe9\\x15\\xc4F\\x81 \\xb2;\\xb4\\x03_&n&X\\xf4;R\\xabLb<\\xca\\xc2"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(
                    KLabel(
                        '<sigS>',
                    ),
                    (
                        KToken(
                            'b"\\x0b\\x88\\x8f\\x15\\xa4O\\x19\\xf4\\xfb_\\x8a@U\\xe0e\\xd68\\x02\\x11\\xfb\\x89}K\\xf5?\\xc0\\xa54\\x07\\xa0\\x06\\x14"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(
                    KLabel(
                        '<data>',
                    ),
                    (
                        KToken(
                            'b"`\\x80`@"',
                            KSort('Bytes'),
                        ),
                    ),
                ),
                KApply(
                    KLabel(
                        '<txAccess>',
                    ),
                    (
                        KApply(
                            KLabel(
                                'JSONList',
                            ),
                            (
                                KApply(
                                    KLabel(
                                        '.List{"JSONs"}',
                                    ),
                                    (),
                                ),
                            ),
                        ),
                    ),
                ),
                KApply(
                    KLabel(
                        '<txChainID>',
                    ),
                    (KToken('31337', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<txPriorityFee>',
                    ),
                    (KToken('0', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<txMaxFee>',
                    ),
                    (KToken('0', KSort('Int')),),
                ),
                KApply(
                    KLabel(
                        '<txType>',
                    ),
                    (
                        KApply(
                            KLabel(
                                'Legacy_EVM-TYPES_TxType',
                            ),
                            (),
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
