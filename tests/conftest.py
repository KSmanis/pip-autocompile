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
def git_identity() -> pygit2.Signature:
    return pygit2.Signature("Peurp Ovic", "peurp@ovic.com")


@pytest.fixture
def git_repo_factory(
    git_identity: pygit2.Signature,
) -> Callable[[Path], pygit2.Repository]:
    def git_repo(path: Path) -> pygit2.Repository:
        repo = pygit2.init_repository(path)
        (path / "requirements").mkdir()
        (path / "requirements" / "spec.in").touch()
        repo.index.add_all()  # type: ignore[attr-defined]
        repo.index.write()  # type: ignore[attr-defined]
        repo.create_commit(
            "HEAD",
            git_identity,
            git_identity,
            "Initial commit",
            repo.index.write_tree(),  # type: ignore[attr-defined]
            [],
        )
        return repo

    return git_repo


@pytest.fixture
def git_superproject_factory(
    git_identity: pygit2.Signature,
    git_repo_factory: Callable[[Path], pygit2.Repository],
) -> Callable[[Path], pygit2.Repository]:
    def git_superproject(path: Path) -> pygit2.Repository:
        superproject = git_repo_factory(path / "superproject")
        submodule = git_repo_factory(path / "submodule")

        superproject.submodules.add(submodule.workdir, "submodule")  # type: ignore[attr-defined]
        superproject.create_commit(
            superproject.head.name,
            git_identity,
            git_identity,
            "Add submodule",
            superproject.index.write_tree(),  # type: ignore[attr-defined]
            [superproject.head.target],
        )
        return superproject

    return git_superproject
