from __future__ import annotations

from pathlib import Path
from typing import Final

TEST_DATA_DIR: Final = (Path(__file__).parent / 'test-data').resolve(strict=True)
INPUT_FILES: Final = TEST_DATA_DIR / 'input'
OUTPUT_FILES: Final = TEST_DATA_DIR / 'output'


def assert_or_update_output(actual_text: str, expected_file: Path, *, update: bool) -> None:
    if update:
        expected_file.write_text(actual_text)
    else:
        assert expected_file.is_file()
        expected_text = expected_file.read_text()
        assert actual_text == expected_text
