from __future__ import annotations

from typing import TYPE_CHECKING

from kevm_pyk.kdist.plugin import KEVMTarget
from kevm_pyk.kompile import KompileTarget
from kontrol.kdist.utils import KSRC_DIR as KONTROL_KSRC_DIR

from .utils import KSRC_DIR

if TYPE_CHECKING:
    from typing import Final


__TARGETS__: Final = {
    'simbolik': KEVMTarget(
        {
            'target': KompileTarget.LLVM,
            'main_file': KSRC_DIR / 'node.md',
            'main_module': 'KONTROL-NODE',
            'syntax_module': 'KONTROL-NODE',
            'includes': [KONTROL_KSRC_DIR],
        },
    ),
}
