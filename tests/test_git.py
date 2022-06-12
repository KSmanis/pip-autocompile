from __future__ import annotations

from typing import TYPE_CHECKING

import pygit2
import pytest

from pipautocompile.git import working_tree

if TYPE_CHECKING:
    from pathlib import Path


def test_working_tree_missing(tmp_path: Path) -> None:
    assert working_tree(tmp_path) is None


def test_working_tree_bare(tmp_path: Path) -> None:
    pygit2.init_repository(tmp_path, bare=True)
    assert working_tree(tmp_path) is None
    assert working_tree(tmp_path / ".git") is None


@pytest.mark.parametrize(
    argnames=("repo_factory_fixture", "working_trees"),
    argvalues=(
        (
            "git_repo_factory",
            {"."},
        ),
        (
            "git_superproject_factory",
            {"superproject", "submodule", "superproject/submodule"},
        ),
    ),
    ids=lambda argvalue: repr(argvalue),
)
def test_working_tree(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    repo_factory_fixture: str,
    working_trees: set[str],
) -> None:
    repo_factory = request.getfixturevalue(repo_factory_fixture)
    repo_factory(tmp_path)
    for tree in working_trees:
        repo_path = tmp_path / tree
        assert repo_path.is_dir()
        assert working_tree(repo_path) == repo_path
        dir_path = repo_path / "requirements"
        assert dir_path.is_dir()
        assert working_tree(dir_path) == repo_path
        file_path = dir_path / "spec.in"
        assert file_path.is_file()
        assert working_tree(file_path) == repo_path
        garbage_path = repo_path / "garbage"
        assert not garbage_path.exists()
        assert working_tree(garbage_path) is None
