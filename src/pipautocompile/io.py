from __future__ import annotations

from pathlib import Path
from re import compile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from re import RegexFlag
    from typing import Iterable
    from typing import Iterator

    from _typeshed import StrOrBytesPath
    from _typeshed import StrPath


def file_contains_pattern(
    file: StrOrBytesPath | int,
    pattern: str,
    *,
    flags: int | RegexFlag = 0,
) -> bool:
    try:
        f = open(file)
    except OSError:
        pass
    else:
        compiled_pattern = compile(pattern, flags)
        with f:
            for line in f:
                if compiled_pattern.search(line) is not None:
                    return True
    return False


def find_spec_files(
    path: StrPath = ".",
    patterns: Iterable[str] = ("**/requirements.in", "**/requirements/*.in"),
) -> Iterator[Path]:
    for s in Path(path).rglob("*.in"):
        if s.is_file() and any(s.resolve(strict=True).match(p) for p in patterns):
            yield s
