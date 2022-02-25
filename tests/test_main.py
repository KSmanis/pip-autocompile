from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from pipautocompile.main import cli

if TYPE_CHECKING:
    from pathlib import Path


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
