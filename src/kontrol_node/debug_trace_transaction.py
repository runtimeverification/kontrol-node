from __future__ import annotations

import binascii
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel


def hex_to_int(value: str | int) -> int:
    if isinstance(value, str):
        if value == '' or value == '0x':
            return 0
        return int(value, 16)
    return value


def signed_hex_to_int(value: str | int) -> int:
    if isinstance(value, str):
        negative = False
        if len(value) > 0 and value[0] == '-':
            value = value[1:]
            negative = True
        if value == '' or value == '0x':
            return 0
        abs_number = int(value, 16)
        return abs_number if not negative else -abs_number
    return value


HexInt = Annotated[int, BeforeValidator(hex_to_int)]

SignedHexInt = Annotated[int, BeforeValidator(signed_hex_to_int)]


def hex_to_bytes(value: str | bytes) -> bytes:
    if isinstance(value, str):
        return binascii.a2b_hex(value.removeprefix('0x'))
    return value


HexBytes = Annotated[bytes, BeforeValidator(hex_to_bytes)]


class DebugBase(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )


class StatusCode(str, Enum):
    EVMC_FAILURE = 'EVMC_FAILURE'
    EVMC_INVALID_INSTRUCTION = 'EVMC_INVALID_INSTRUCTION'
    EVMC_UNDEFINED_INSTRUCTION = 'EVMC_UNDEFINED_INSTRUCTION'
    EVMC_OUT_OF_GAS = 'EVMC_OUT_OF_GAS'
    EVMC_BAD_JUMP_DESTINATION = 'EVMC_BAD_JUMP_DESTINATION'
    EVMC_STACK_OVERFLOW = 'EVMC_STACK_OVERFLOW'
    EVMC_STACK_UNDERFLOW = 'EVMC_STACK_UNDERFLOW'
    EVMC_CALL_DEPTH_EXCEEDED = 'EVMC_CALL_DEPTH_EXCEEDED'
    EVMC_INVALID_MEMORY_ACCESS = 'EVMC_INVALID_MEMORY_ACCESS'
    EVMC_STATIC_MODE_VIOLATION = 'EVMC_STATIC_MODE_VIOLATION'
    EVMC_PRECOMPILE_FAILURE = 'EVMC_PRECOMPILE_FAILURE'
    EVMC_NONCE_EXCEEDED = 'EVMC_NONCE_EXCEEDED'
    EVMC_INVALID_BLOCK = 'EVMC_INVALID_BLOCK'
    EVMC_SUCCESS = 'EVMC_SUCCESS'
    EVMC_REVERT = 'EVMC_REVERT'
    EVMC_REJECTED = 'EVMC_REJECTED'
    EVMC_INTERNAL_ERROR = 'EVMC_INTERNAL_ERROR'
    EMPTY = 'empty'  # no status code yet determined by rpc-node


class StructLog(DebugBase):
    return_data: HexBytes | None = None  # used for anvil, deprecated for kontrol-node trace
    pc: int
    op: str
    stack: tuple[HexInt, ...]
    memory: tuple[HexBytes, ...] | None = None  # used for anvil, deprecated for kontrol-node trace
    memory_change: tuple[HexBytes, ...] | None = None
    storage: dict[HexInt, HexInt] | None = None  # deprecated, legacy kontrol-node trace
    storage_changes: dict[HexInt, dict[HexInt, HexInt]] | None = None
    balance_changes: dict[HexInt, SignedHexInt] | None = None
    nonce_changes: dict[HexInt, HexInt] | None = None
    call_data_change: HexBytes | None = None
    return_data_change: HexBytes | None = None
    program_change: HexBytes | None = None
    deployed_code_changes: dict[HexInt, HexBytes] | None = None
    init_code_changes: dict[HexInt, HexBytes] | None = None
    depth: int
    gas: int
    coinbase: int | None = None
    gas_cost: int
    difficulty: int | None = None
    block_number: int | None = None
    block_timestamp: int | None = None
    target_address: int | None = None
    code_address: int | None = None
    msg_sender: int | None = None
    msg_value: int | None = None
    tx_origin: int | None = None
    is_init_code: bool | None = None
    status_code: StatusCode | None = None


class DebugTrace(DebugBase):
    failed: bool
    gas: int
    return_value: HexInt
    struct_logs: tuple[StructLog, ...]
