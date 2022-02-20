from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygit2
import pytest

from pipautocompile.git import working_tree

if TYPE_CHECKING:
    from typing import Callable


def test_working_tree_missing(tmp_path: Path) -> None:
    assert working_tree(tmp_path) is None


def test_working_tree_bare(tmp_path: Path) -> None:
    pygit2.init_repository(tmp_path, bare=True)
    assert working_tree(tmp_path) is None
    assert working_tree(tmp_path / ".git") is None


@pytest.fixture
def git_identity() -> pygit2.Signature:  # type: ignore[no-any-unimported]
    return pygit2.Signature("Peurp Ovic", "peurp@ovic.com")


@pytest.fixture
def git_repo_factory(  # type: ignore[no-any-unimported]
    git_identity: pygit2.Signature,
) -> Callable[[Path], pygit2.Repository]:
    def git_repo(path: Path) -> pygit2.Repository:  # type: ignore[no-any-unimported]
        repo = pygit2.init_repository(path)
        (path / "dir").mkdir()
        (path / "dir" / "file").touch()
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
def git_repos(  # type: ignore[no-any-unimported]
    tmp_path: Path,
    git_identity: pygit2.Signature,
    git_repo_factory: Callable[[Path], pygit2.Repository],
) -> Path:
    superproject = git_repo_factory(tmp_path / "superproject")
    submodule = git_repo_factory(tmp_path / "submodule")

    superproject.add_submodule(submodule.workdir, "submodule")
    superproject.create_commit(
        superproject.head.name,
        git_identity,
        git_identity,
        "Add submodule",
        superproject.index.write_tree(),
        [superproject.head.target],
    )

    return tmp_path


@pytest.mark.parametrize(
    "repo", ("superproject", "superproject/submodule", "submodule")
)
def test_working_tree(git_repos: Path, repo: str) -> None:
    repo_path = git_repos / repo
    assert repo_path.is_dir()
    assert working_tree(repo_path) == repo_path
    dir_path = repo_path / "dir"
    assert dir_path.is_dir()
    assert working_tree(dir_path) == repo_path
    file_path = dir_path / "file"
    assert file_path.is_file()
    assert working_tree(file_path) == repo_path
    garbage_path = repo_path / "garbage"
    assert not garbage_path.exists()
    assert working_tree(garbage_path) is None
