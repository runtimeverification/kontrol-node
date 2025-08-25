from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from kevm_pyk.kdist.plugin import KEVMTarget
from kevm_pyk.kompile import KompileTarget
from kontrol.kdist.utils import KSRC_DIR as KONTROL_KSRC_DIR
from pyk.kdist.api import Target

from .utils import KSRC_DIR

if TYPE_CHECKING:
    from typing import Any, Final


class KontrolNodeSourceTarget(Target):
    SRC_DIR: Final = Path(__file__).parent

    def build(self, output_dir: Path, deps: dict[str, Path], args: dict[str, Any], verbose: bool) -> None:
        shutil.copy(self.SRC_DIR / 'node.md', output_dir / 'node.md')

    def source(self) -> tuple[Path, ...]:
        return (self.SRC_DIR,)


class KontrolNodeTarget(KEVMTarget):
    def deps(self) -> tuple[str, ...]:
        return super().deps() + ('kontrol-node.source',)

    def source(self) -> tuple[Path, ...]:
        # return empty source, as otherwise manifest generation fails due to missing files in kontrol_node python module
        # that only exist in kevm_pyk
        return ()


__TARGETS__: Final = {
    'source': KontrolNodeSourceTarget(),
    'simbolik': KontrolNodeTarget(
        {
            'target': KompileTarget.LLVM,
            'main_file': KSRC_DIR / 'node.md',
            'main_module': 'KONTROL-NODE',
            'syntax_module': 'KONTROL-NODE',
            'includes': [KONTROL_KSRC_DIR],
            'optimization': 2,
        },
    ),
}
