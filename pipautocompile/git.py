import subprocess  # nosec
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union

    from _typeshed import StrOrBytesPath


def working_tree(path: "Union[StrOrBytesPath, None]" = None) -> "Union[Path, None]":
    try:
        output = subprocess.check_output(  # nosec
            ("git", "rev-parse", "--show-toplevel"),
            cwd=path,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    else:
        return Path(output.strip())
