from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyk.cli.args import LoggingOptions

if TYPE_CHECKING:
    from collections.abc import Callable


class VMOptions(LoggingOptions):
    addr: str
    port: int
    steps_tracing: bool
    chain_id: int
    gas_price: int

    @staticmethod
    def default() -> dict[str, Any]:
        return {
            'addr': '127.0.0.1',
            'port': 8081,
            'steps_tracing': False,
            'chain_id': 31337,
            'gas_price': 0,
        }

    @staticmethod
    def from_option_string() -> dict[str, str]:
        return LoggingOptions.from_option_string()

    @staticmethod
    def get_argument_type() -> dict[str, Callable]:
        return LoggingOptions.get_argument_type()
