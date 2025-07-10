from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import shutil

from kevm_pyk.kdist.plugin import KEVMTarget
from kevm_pyk.kompile import KompileTarget
from pyk.kdist.api import Target
from kontrol.kdist.utils import KSRC_DIR as KONTROL_KSRC_DIR

from .utils import KSRC_DIR

if TYPE_CHECKING:
    from typing import Final, Any

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
        return tuple()


__TARGETS__: Final = {
    'source': KontrolNodeSourceTarget(),
    'simbolik': KontrolNodeTarget(
        {
            'target': KompileTarget.LLVM,
            'main_file': KSRC_DIR / 'node.md',
            'main_module': 'KONTROL-NODE',
            'syntax_module': 'KONTROL-NODE',
            'includes': [KONTROL_KSRC_DIR],
        },
    ),
}
