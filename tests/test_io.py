from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pipautocompile.io import file_contains_pattern
from pipautocompile.io import find_spec_files

if TYPE_CHECKING:
    from typing import Any


@pytest.mark.parametrize(
    argnames=("contents", "pattern", "kwargs", "expected"),
    argvalues=(
        (None, r"", {}, False),
        ("", r"", {}, False),
        ("foo", r"", {}, True),
        ("", r"foo", {}, False),
        ("foo\nbar", r"foo", {}, True),
        ("foo\nbar", r"^foo", {}, True),
        ("foo\nbar", r"foo$", {}, True),
        ("foo\nbar", r"^foo$", {}, True),
        ("foo\nbar", r"bar", {}, True),
        ("foo\nbar", r"^bar", {}, True),
        ("foo\nbar", r"bar$", {}, True),
        ("foo\nbar", r"^bar$", {}, True),
        ("foo\nbar", r"foo\nbar", {}, False),
        ("foo\nbar", r"FoO", {"flags": re.IGNORECASE}, True),
        ("FROM python:alpine AS build-deps", r"^FROM \S+ AS build-deps$", {}, True),
        ("from python:alpine as build-deps", r"^FROM \S+ AS build-deps$", {}, False),
        ("FROM  python:alpine  AS  build-deps", r"^FROM \S+ AS build-deps$", {}, False),
        ("FROM python:alpine AS build", r"^FROM \S+ AS build-deps$", {}, False),
        ("FROM python:alpine AS build-deps", r"^FROM \S+ AS build$", {}, False),
    ),
    ids=lambda argvalue: repr(argvalue),
)
def test_file_contains_pattern(
    tmp_path: Path,
    contents: str | None,
    pattern: str,
    kwargs: dict[str, Any],
    expected: bool,
) -> None:
    file = tmp_path / "f"
    if contents is not None:
        file.write_text(contents)
    assert file_contains_pattern(file, pattern, **kwargs) == expected


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
