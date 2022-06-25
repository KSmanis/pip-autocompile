from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from pipautocompile.logging import info

if TYPE_CHECKING:
    from typing import Any


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.mark.parametrize(
    argnames=("args", "kwargs", "expected"),
    argvalues=(
        (tuple(), {}, {"nt": b"\r\n", "posix": b"\n"}),
        (tuple(), {"nl": True}, {"nt": b"\r\n", "posix": b"\n"}),
        (tuple(), {"nl": False}, {"nt": b"", "posix": b""}),
        ((None,), {}, {"nt": b"\r\n", "posix": b"\n"}),
        ((None,), {"nl": True}, {"nt": b"\r\n", "posix": b"\n"}),
        ((None,), {"nl": False}, {"nt": b"", "posix": b""}),
        ((1,), {}, {"nt": b"1\r\n", "posix": b"\x1b[33m\x1b[1m1\x1b[0m\n"}),
        ((1,), {"nl": True}, {"nt": b"1\r\n", "posix": b"\x1b[33m\x1b[1m1\x1b[0m\n"}),
        ((1,), {"nl": False}, {"nt": b"1", "posix": b"\x1b[33m\x1b[1m1\x1b[0m"}),
        (("",), {}, {"nt": b"\r\n", "posix": b"\x1b[33m\x1b[1m\x1b[0m\n"}),
        (("",), {"nl": True}, {"nt": b"\r\n", "posix": b"\x1b[33m\x1b[1m\x1b[0m\n"}),
        (("",), {"nl": False}, {"nt": b"", "posix": b"\x1b[33m\x1b[1m\x1b[0m"}),
        (("foo",), {}, {"nt": b"foo\r\n", "posix": b"\x1b[33m\x1b[1mfoo\x1b[0m\n"}),
        (
            ("foo",),
            {"nl": True},
            {"nt": b"foo\r\n", "posix": b"\x1b[33m\x1b[1mfoo\x1b[0m\n"},
        ),
        (
            ("foo",),
            {"nl": False},
            {"nt": b"foo", "posix": b"\x1b[33m\x1b[1mfoo\x1b[0m"},
        ),
        (
            tuple(),
            {"message": "foo"},
            {"nt": b"foo\r\n", "posix": b"\x1b[33m\x1b[1mfoo\x1b[0m\n"},
        ),
        (
            tuple(),
            {"message": "foo", "nl": True},
            {"nt": b"foo\r\n", "posix": b"\x1b[33m\x1b[1mfoo\x1b[0m\n"},
        ),
        (
            tuple(),
            {"message": "foo", "nl": False},
            {"nt": b"foo", "posix": b"\x1b[33m\x1b[1mfoo\x1b[0m"},
        ),
    ),
    ids=lambda argvalue: repr(argvalue),
)
def test_info(
    runner: CliRunner,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    expected: dict[str, bytes],
) -> None:
    with runner.isolation(color=True) as (out, err):
        info(*args, **kwargs)
        assert out.getvalue() == expected[os.name]
        assert err is None
