from __future__ import annotations

from typing import TYPE_CHECKING

import pygit2
import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


@pytest.fixture
def git_identity() -> pygit2.Signature:  # type: ignore[no-any-unimported]
    return pygit2.Signature("Peurp Ovic", "peurp@ovic.com")


@pytest.fixture
def git_repo_factory(  # type: ignore[no-any-unimported]
    git_identity: pygit2.Signature,
) -> Callable[[Path], pygit2.Repository]:
    def git_repo(path: Path) -> pygit2.Repository:  # type: ignore[no-any-unimported]
        repo = pygit2.init_repository(path)
        (path / "requirements").mkdir()
        (path / "requirements" / "spec.in").touch()
        repo.index.add_all()
        repo.index.write()
        repo.create_commit(
            "HEAD",
            git_identity,
            git_identity,
            "Initial commit",
            repo.index.write_tree(),
            [],
        )
        return repo

    return git_repo


@pytest.fixture
def git_superproject_factory(  # type: ignore[no-any-unimported]
    git_identity: pygit2.Signature,
    git_repo_factory: Callable[[Path], pygit2.Repository],
) -> Callable[[Path], pygit2.Repository]:
    def git_superproject(path: Path) -> pygit2.Repository:  # type: ignore[no-any-unimported] # noqa: E501
        superproject = git_repo_factory(path / "superproject")
        submodule = git_repo_factory(path / "submodule")

        superproject.add_submodule(submodule.workdir, "submodule")
        superproject.create_commit(
            superproject.head.name,
            git_identity,
            git_identity,
            "Add submodule",
            superproject.index.write_tree(),
            [superproject.head.target],
        )
        return superproject

    return git_superproject
