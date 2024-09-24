from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyk.cli.args import LoggingOptions

if TYPE_CHECKING:
    from collections.abc import Callable


class VMOptions(LoggingOptions):
    host: str
    port: int
    steps_tracing: bool

    @staticmethod
    def default() -> dict[str, Any]:
        return {
            'host': '127.0.0.1',
            'port': 8081,
            'steps_tracing': False,
        }

    @staticmethod
    def from_option_string() -> dict[str, str]:
        return LoggingOptions.from_option_string()

    @staticmethod
    def get_argument_type() -> dict[str, Callable]:
        return LoggingOptions.get_argument_type()
