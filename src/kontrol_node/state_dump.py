from __future__ import annotations

import gzip
import json
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field
from pydantic.aliases import AliasChoices


def hex_to_int(value: str | int) -> int:
    if isinstance(value, str):
        return int(value, 16)
    return value


HexInt = Annotated[int, BeforeValidator(hex_to_int)]


def hex_to_bytes(value: str | bytes) -> bytes:
    if isinstance(value, str):
        return bytes.fromhex(value[2:])
    return value


HexBytes = Annotated[bytes, BeforeValidator(hex_to_bytes)]


def signed_hex_to_int(value: str | int) -> int:
    if isinstance(value, str):
        negative = False
        if len(value) > 0 and value[0] == '-':
            value = value[1:]
            negative = True
        abs_number = int(value, 16)
        return abs_number if not negative else -abs_number
    return value


SignedHexInt = Annotated[int, BeforeValidator(signed_hex_to_int)]


class BlobExcessGasAndPrice(BaseModel):
    excess_blob_gas: int
    blob_gasprice: int


class Block(BaseModel):
    number: HexInt
    beneficiary: HexInt = Field(validation_alias=AliasChoices('beneficiary', 'coinbase'))
    timestamp: HexInt
    gas_limit: HexInt
    basefee: HexInt
    difficulty: HexInt
    prevrandao: HexInt
    blob_excess_gas_and_price: BlobExcessGasAndPrice


class Account(BaseModel):
    nonce: HexInt | None
    balance: SignedHexInt | None
    code: HexBytes | None
    storage: dict[HexInt, HexInt] = {}

    @staticmethod
    def empty() -> Account:
        return Account(
            nonce=0,
            balance=0,
            code=b'',
            storage={},
        )


class StateDump(BaseModel):
    best_block_number: HexInt
    block: Block
    accounts: dict[HexInt, Account]

    @staticmethod
    def decode(data: str) -> StateDump:
        decompressed = gzip.decompress(hex_to_bytes(data))
        raw = json.loads(decompressed)
        return StateDump(**raw)

    @staticmethod
    def empty() -> StateDump:
        return StateDump(
            best_block_number=0,
            block=Block(
                number=0,
                beneficiary=0,
                timestamp=0,
                gas_limit=0,
                basefee=0,
                difficulty=0,
                prevrandao=0,
                blob_excess_gas_and_price=BlobExcessGasAndPrice(
                    excess_blob_gas=0,
                    blob_gasprice=0,
                ),
            ),
            accounts={},
        )
