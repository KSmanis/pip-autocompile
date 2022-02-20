from __future__ import annotations

from pathlib import Path

import pygit2


def working_tree(path: Path = Path()) -> Path | None:
    try:
        return Path(pygit2.Repository(path).workdir)
    except (pygit2.GitError, TypeError):
        # `GitError`: `path` does not contain a Git repository
        # `TypeError`: `path` contains a bare Git repository
        return None
