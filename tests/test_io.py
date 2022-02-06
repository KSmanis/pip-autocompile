from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pipautocompile.io import find_spec_files

if TYPE_CHECKING:
    from typing import Any


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


@pytest.fixture(params=(True, False), ids=("relative", "absolute"))
def spec_root(request: pytest.FixtureRequest, spec_tree: Path) -> Path:
    if request.param:  # type: ignore[attr-defined]
        request.getfixturevalue("monkeypatch").chdir(spec_tree)
        return Path()
    else:
        return spec_tree


@pytest.mark.parametrize(
    argnames=("kwargs", "expected_specs"),
    argvalues=(
        pytest.param(
            {},
            {
                "nested/requirements/foo.in",
                "nested/requirements/bar.in",
                "nested/requirements.in",
                "requirements/50_base.in",
                "requirements/60_dev.in",
                "requirements/61_prod.in",
                "requirements.in",
            },
            id="default patterns",
        ),
        pytest.param(
            {"patterns": {"requirements.in"}},
            {
                "requirements.in",
            },
            id="requirements.in",
        ),
        pytest.param(
            {"patterns": {"requirements/*.in"}},
            {
                "requirements/50_base.in",
                "requirements/60_dev.in",
                "requirements/61_prod.in",
            },
            id="requirements/*.in",
        ),
        pytest.param(
            {"patterns": {"*/requirements.in"}},
            {
                "nested/requirements.in",
            },
            id="*/requirements.in",
        ),
        pytest.param(
            {"patterns": {"**/requirements.in"}},
            {
                "requirements.in",
                "nested/requirements.in",
            },
            id="**/requirements.in",
        ),
        pytest.param(
            {"patterns": {"**/requirements/*.in"}},
            {
                "nested/requirements/foo.in",
                "nested/requirements/bar.in",
                "requirements/50_base.in",
                "requirements/60_dev.in",
                "requirements/61_prod.in",
            },
            id="**/requirements/*.in",
        ),
        pytest.param(
            {"patterns": {"**/requirements/*.spec"}},
            {
                "requirements/50_base.spec",
                "requirements/60_dev.spec",
                "requirements/61_prod.spec",
            },
            id="**/requirements/*.spec",
        ),
        pytest.param(
            {"patterns": {"**/requirements/*.in", "**/requirements/*.spec"}},
            {
                "nested/requirements/foo.in",
                "nested/requirements/bar.in",
                "requirements/50_base.in",
                "requirements/60_dev.in",
                "requirements/61_prod.in",
                "requirements/50_base.spec",
                "requirements/60_dev.spec",
                "requirements/61_prod.spec",
            },
            id="**/requirements/*.(in|spec)",
        ),
    ),
)
def test_find_spec_files(
    spec_root: Path, kwargs: dict[str, Any], expected_specs: set[str]
) -> None:
    rooted_specs = {spec_root / spec for spec in expected_specs}
    assert set(find_spec_files(spec_root, **kwargs)) == rooted_specs
