from __future__ import annotations

import logging
import sys
from collections.abc import Iterable
from typing import TYPE_CHECKING

from kontrol.utils import _LOG_FORMAT, check_k_version, config_file_path, loglevel
from pyk.cli.pyk import parse_toml_args
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler

from . import VERSION
from .cli import _create_argument_parser, generate_options, get_argument_type_setter, get_option_string_destination
from .rpc import StatefulKJsonRpcServer

if TYPE_CHECKING:
    from typing import Final, TypeVar

    from kontrol.options import VersionOptions

    from .options import VMOptions

    T = TypeVar('T')

_LOGGER: Final = logging.getLogger(__name__)


def main() -> None:
    sys.setrecursionlimit(15000000)
    parser = _create_argument_parser()
    args = parser.parse_args()
    args.config_file = config_file_path(args)
    toml_args = parse_toml_args(args, get_option_string_destination, get_argument_type_setter)
    logging.basicConfig(
        level=loglevel(args, toml_args),
        format=_LOG_FORMAT,
        handlers=[
            RichHandler(
                level=loglevel(args, toml_args),
                show_level=False,
                show_time=False,
                show_path=False,
                highlighter=NullHighlighter(),
            ),
        ],
    )

    check_k_version()

    stripped_args = toml_args | {
        key: val for (key, val) in vars(args).items() if val is not None and not (isinstance(val, Iterable) and not val)
    }
    options = generate_options(stripped_args)

    executor_name = 'exec_' + args.command.lower().replace('-', '_')
    if executor_name not in globals():
        raise AssertionError(f'Unimplemented command: {args.command}')

    execute = globals()[executor_name]
    execute(options)


# Command implementation


def exec_version(options: VersionOptions) -> None:
    print(f'Kontrol-Node version: {VERSION}')


def exec_run(options: VMOptions) -> None:
    server = StatefulKJsonRpcServer(options)
    server.serve()


if __name__ == '__main__':
    main()
