from __future__ import annotations

from argparse import ArgumentParser
from functools import cached_property
from typing import TYPE_CHECKING, Any

from kevm_pyk.cli import KEVMCLIArgs
from kontrol.options import VersionOptions
from pyk.cli.utils import file_path

from .options import VMOptions

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    from .options import LoggingOptions

    T = TypeVar('T')


def generate_options(args: dict[str, Any]) -> LoggingOptions:
    command = args['command']
    options = {
        'version': VersionOptions(args),
        'run': VMOptions(args),
    }
    try:
        return options[command]
    except KeyError as err:
        raise ValueError(f'Unrecognized command: {command}') from err


def get_option_string_destination(command: str, option_string: str) -> str:
    option_string_destinations = {}
    options: dict = {
        'version': VersionOptions.from_option_string(),
        'run': VMOptions.from_option_string(),
    }
    option_string_destinations = options[command]
    return option_string_destinations.get(option_string, option_string.replace('-', '_'))


def get_argument_type_setter(command: str, option_string: str) -> Callable[[str], Any]:
    option_types = {}
    options: dict = {
        'version': VMOptions.get_argument_type(),
        'run': VMOptions.get_argument_type(),
    }
    option_types = options[command]
    return option_types.get(option_string, (lambda x: x))


class ConfigArgs:
    @cached_property
    def config_args(self) -> ArgumentParser:
        args = ArgumentParser(add_help=False)
        args.add_argument(
            '--config-file',
            dest='config_file',
            type=file_path,
            default=None,
            help='Path to Pyk config file.',
        )
        args.add_argument(
            '--config-profile',
            dest='config_profile',
            default='default',
            help='Config profile to be used.',
        )
        return args


def _create_argument_parser() -> ArgumentParser:
    def list_of(elem_type: Callable[[str], T], delim: str = ';') -> Callable[[str], list[T]]:
        def parse(s: str) -> list[T]:
            return [elem_type(elem) for elem in s.split(delim)]

        return parse

    kevm_cli_args = KEVMCLIArgs()
    config_args = ConfigArgs()
    parser = ArgumentParser(prog='kontrol-node')

    command_parser = parser.add_subparsers(dest='command', required=True)

    command_parser.add_parser('version', help='Print out version of Kontrol-Node command.')

    run = command_parser.add_parser(
        'run',
        help='Start a json rpc server',
        parents=[
            kevm_cli_args.logging_args,
            config_args.config_args,
        ],
    )
    run.add_argument(
        '--host',
        dest='addr',
        default='127.0.0.1',
        help='host address',
    )
    run.add_argument(
        '--port',
        dest='port',
        default=8081,
        help='port number',
    )
    run.add_argument(
        '--steps-tracing',
        dest='steps_tracing',
        default=False,
        action='store_true',
        help='Enable steps tracing used for debug calls returning geth-style traces',
    )
    return parser
