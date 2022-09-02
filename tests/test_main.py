from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner
from python_on_whales import docker

from pipautocompile.main import cli

if TYPE_CHECKING:
    from typing import Callable

    import pygit2

pytestmark = pytest.mark.functional


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def noop_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def pip_compile_path(noop_path: Path) -> Path:
    (noop_path / "nested").mkdir()
    (noop_path / "nested" / "requirements").mkdir()
    (noop_path / "nested" / "requirements" / "foo.in").touch()
    (noop_path / "nested" / "requirements" / "bar.in").touch()
    (noop_path / "nested" / "requirements.in").touch()
    (noop_path / "requirements.in").touch()
    return noop_path


@pytest.fixture
def pip_compile_superproject_path(  # type: ignore[no-any-unimported]
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_superproject_factory: Callable[[Path], pygit2.Repository],
) -> Path:
    superproject = git_superproject_factory(tmp_path)
    superproject_path = Path(superproject.workdir)
    monkeypatch.chdir(superproject_path)
    return superproject_path


@pytest.fixture
def dockerfile_contents() -> str:
    return "FROM python:alpine AS build-deps\n"


@pytest.fixture
def docker_path(pip_compile_path: Path, dockerfile_contents: str) -> Path:
    (pip_compile_path / "nested" / "Dockerfile").write_text(dockerfile_contents)
    (pip_compile_path / "Dockerfile").write_text(dockerfile_contents)
    return pip_compile_path


@pytest.fixture
def docker_superproject_path(
    pip_compile_superproject_path: Path, dockerfile_contents: str
) -> Path:
    (pip_compile_superproject_path / "Dockerfile").write_text(dockerfile_contents)
    (pip_compile_superproject_path / "submodule" / "Dockerfile").write_text(
        dockerfile_contents
    )
    return pip_compile_superproject_path


@pytest.mark.usefixtures("noop_path")
def test_cli_noop(runner: CliRunner) -> None:
    result = runner.invoke(cli)
    assert not result.exception
    assert result.exit_code == 0
    assert not result.output


def test_cli_pip_compile(runner: CliRunner, pip_compile_path: Path) -> None:
    if shutil.which("pip-compile") is None:
        pytest.skip("Missing `pip-compile` executable")

    result = runner.invoke(cli)
    assert not result.exception
    assert result.exit_code == 0
    assert "Processing . directory...\n" in result.output
    assert (pip_compile_path / "requirements.txt").is_file()
    assert "Processing nested directory...\n" in result.output
    assert (pip_compile_path / "nested" / "requirements.txt").is_file()
    assert (pip_compile_path / "nested" / "requirements" / "foo.txt").is_file()
    assert (pip_compile_path / "nested" / "requirements" / "bar.txt").is_file()


def test_cli_pip_compile_superproject(
    runner: CliRunner, pip_compile_superproject_path: Path
) -> None:
    if shutil.which("pip-compile") is None:
        pytest.skip("Missing `pip-compile` executable")

    result = runner.invoke(cli)
    assert not result.exception
    assert result.exit_code == 0
    assert "Processing requirements directory...\n" in result.output
    assert (pip_compile_superproject_path / "requirements" / "spec.txt").is_file()
    assert "Processing submodule/requirements directory...\n" not in result.output
    assert not (
        pip_compile_superproject_path / "submodule" / "requirements" / "spec.txt"
    ).exists()


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux containers")
def test_cli_docker(runner: CliRunner, docker_path: Path) -> None:
    if docker.system.info().server_version is None:
        pytest.skip("Missing Docker daemon")

    result = runner.invoke(cli)
    assert not result.exception
    assert result.exit_code == 0
    assert "Processing . directory...\n" in result.output
    assert (docker_path / "requirements.txt").is_file()
    assert "Processing nested directory...\n" in result.output
    assert (docker_path / "nested" / "requirements.txt").is_file()
    assert (docker_path / "nested" / "requirements" / "foo.txt").is_file()
    assert (docker_path / "nested" / "requirements" / "bar.txt").is_file()


@pytest.mark.skipif(sys.platform != "linux", reason="requires Linux containers")
def test_cli_docker_superproject(
    runner: CliRunner, docker_superproject_path: Path
) -> None:
    if docker.system.info().server_version is None:
        pytest.skip("Missing Docker daemon")

    result = runner.invoke(cli)
    assert not result.exception
    assert result.exit_code == 0
    assert "Processing requirements directory...\n" in result.output
    assert (docker_superproject_path / "requirements" / "spec.txt").is_file()
    assert "Processing submodule/requirements directory...\n" not in result.output
    assert not (
        docker_superproject_path / "submodule" / "requirements" / "spec.txt"
    ).exists()
