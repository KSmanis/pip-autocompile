from __future__ import annotations

from typing import TYPE_CHECKING

import pygit2
import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--with-functional",
        action="store_true",
        default=False,
        help="run functional tests",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "functional: mark functional tests")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--with-functional"):
        skip_functional = pytest.mark.skip(
            reason="needs --with-functional option to run"
        )
        for item in items:
            if "functional" in item.keywords:
                item.add_marker(skip_functional)


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
