from __future__ import annotations

from typing import TYPE_CHECKING

from dockerfile import GoIOError
from dockerfile import GoParseError
from dockerfile import parse_file

if TYPE_CHECKING:
    from pathlib import Path


def dockerfile_has_build_stage(path: Path, build_stage: str) -> bool:
    try:
        commands = parse_file(str(path))
    except (GoIOError, GoParseError):
        return False
    else:
        return any(
            c.cmd.casefold() == "from"
            and len(c.value) >= 3
            and c.value[-2].casefold() == "as"
            and c.value[-1] == build_stage
            for c in commands
        )
