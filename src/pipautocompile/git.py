from __future__ import annotations

import subprocess  # nosec
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


def working_tree(path: StrOrBytesPath | None = None) -> Path | None:
    try:
        output = subprocess.check_output(  # nosec
            ("git", "rev-parse", "--show-toplevel"),
            cwd=path,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    else:
        return Path(output.strip())
