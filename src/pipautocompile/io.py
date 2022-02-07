from __future__ import annotations

from pathlib import Path
from re import search
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from typing import Iterator

    from _typeshed import StrOrBytesPath
    from _typeshed import StrPath


def file_contains_pattern(
    file: StrOrBytesPath | int, pattern: str, **search_kwargs: Any
) -> bool:
    try:
        f = open(file)
    except OSError:
        pass
    else:
        with f:
            for line in f:
                if search(pattern, line, **search_kwargs):
                    return True
    return False


def find_spec_files(pattern: str, path: StrPath = ".") -> Iterator[Path]:
    for spec in Path(path).glob(pattern):
        if spec.is_file():
            yield spec
