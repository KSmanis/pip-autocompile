from __future__ import annotations

from pathlib import Path

import pytest

from pipautocompile.io import find_spec_files


@pytest.fixture
def spec_tree(tmp_path: Path) -> Path:
    (tmp_path / "fake").mkdir()
    (tmp_path / "fake" / "requirements").mkdir()
    (tmp_path / "fake" / "requirements" / "foo.in").mkdir()
    (tmp_path / "fake" / "requirements.in").mkdir()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "requirements").mkdir()
    (tmp_path / "nested" / "requirements" / "foo.in").touch()
    (tmp_path / "nested" / "requirements" / "bar.in").touch()
    (tmp_path / "nested" / "requirements.in").touch()
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "50_base.in").touch()
    (tmp_path / "requirements" / "50_base.spec").touch()
    (tmp_path / "requirements" / "60_dev.in").touch()
    (tmp_path / "requirements" / "60_dev.spec").touch()
    (tmp_path / "requirements" / "61_prod.in").touch()
    (tmp_path / "requirements" / "61_prod.spec").touch()
    (tmp_path / "requirements.in").touch()
    return tmp_path


@pytest.mark.parametrize("chdir", (True, False), ids=("relative", "absolute"))
@pytest.mark.parametrize(
    argnames=("pattern", "expected_specs"),
    argvalues=(
        (
            "*.spec",
            set(),
        ),
        (
            "requirements.in",
            {
                "requirements.in",
            },
        ),
        (
            "requirements/*.in",
            {
                "requirements/50_base.in",
                "requirements/60_dev.in",
                "requirements/61_prod.in",
            },
        ),
        (
            "*/requirements.in",
            {
                "nested/requirements.in",
            },
        ),
        (
            "**/requirements.in",
            {
                "requirements.in",
                "nested/requirements.in",
            },
        ),
        (
            "**/requirements/*.in",
            {
                "nested/requirements/foo.in",
                "nested/requirements/bar.in",
                "requirements/50_base.in",
                "requirements/60_dev.in",
                "requirements/61_prod.in",
            },
        ),
        (
            "**/requirements/*.spec",
            {
                "requirements/50_base.spec",
                "requirements/60_dev.spec",
                "requirements/61_prod.spec",
            },
        ),
    ),
)
def test_find_spec_files(
    request: pytest.FixtureRequest,
    spec_tree: Path,
    chdir: bool,
    pattern: str,
    expected_specs: set[str],
) -> None:
    if chdir:
        request.getfixturevalue("monkeypatch").chdir(spec_tree)
        spec_tree = Path()
    rooted_specs = {spec_tree / spec for spec in expected_specs}
    assert set(find_spec_files(pattern, path=spec_tree)) == rooted_specs
