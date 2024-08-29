from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pyk import __version__ as pyk_version
from pyk.kbuild.utils import KVersion, k_version

if TYPE_CHECKING:
    from argparse import Namespace
    from typing import Final

_LOGGER: Final = logging.getLogger(__name__)
_LOG_FORMAT: Final = '%(levelname)s %(asctime)s %(name)s - %(message)s'


# Helpers
def _loglevel(args: Namespace, toml_args: dict) -> int:
    def is_attr_used(attr_name: str) -> bool | None:
        return getattr(args, attr_name, None) or toml_args.get(attr_name)

    if is_attr_used('debug'):
        return logging.DEBUG

    if is_attr_used('verbose'):
        return logging.INFO

    return logging.WARNING


def _config_file_path(args: Namespace) -> Path:
    return (
        Path.joinpath(
            Path('.'),
            'kontrol.toml',
        )
        if not getattr(args, 'config_file', None)
        else args.config_file
    )


def _check_k_version() -> None:
    expected_k_version = KVersion.parse(f'v{pyk_version}')
    actual_k_version = k_version()

    if not _compare_versions(expected_k_version, actual_k_version):
        _LOGGER.warning(
            f'K version {expected_k_version.text} was expected but K version {actual_k_version.text} is being used.'
        )


def _compare_versions(ver1: KVersion, ver2: KVersion) -> bool:
    if ver1.major != ver2.major or ver1.minor != ver2.minor or ver1.patch != ver2.patch:
        return False

    if ver1.git == ver2.git:
        return True

    if ver1.git and ver2.git:
        return False

    git = ver1.git or ver2.git
    assert git  # git is not None for exactly one of ver1 and ver2
    return not git.ahead and not git.dirty
