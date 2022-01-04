from __future__ import annotations

import subprocess  # nosec
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


def inside_submodule(path: StrOrBytesPath | None = None) -> bool:
    try:
        output = subprocess.check_output(  # nosec
            ("git", "rev-parse", "--show-superproject-working-tree"),
            cwd=path,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    else:
        return output != b""
