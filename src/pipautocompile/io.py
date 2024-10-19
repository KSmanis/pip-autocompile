from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from _typeshed import StrPath


def find_spec_files(pattern: str, path: StrPath = ".") -> Iterator[Path]:
    for spec in Path(path).glob(pattern):
        if spec.is_file():
            yield spec
