from __future__ import annotations

import pytest

from pipautocompile.utils import quote_args


@pytest.mark.parametrize(
    argnames=("args", "expected"),
    argvalues=(
        (tuple(), ""),
        ((None,), "None"),
        ((1, None, 1.5, True, "", " foo", "bar "), "1 None 1.5 True '' ' foo' 'bar '"),
        (("",), "''"),
        (("", ""), "'' ''"),
        (("foo",), "foo"),
        (("foo", "bar"), "foo bar"),
        (("foo", "bar", "baz"), "foo bar baz"),
        ((" ",), "' '"),
        ((" foo",), "' foo'"),
        ((" foo ",), "' foo '"),
        ((" foo", "bar"), "' foo' bar"),
        ((" foo", "bar "), "' foo' 'bar '"),
        ((" foo ", "bar "), "' foo ' 'bar '"),
        ((" foo ", " bar "), "' foo ' ' bar '"),
        ((" foo ", " bar ", " baz "), "' foo ' ' bar ' ' baz '"),
        (
            ("pip-autocompile", "--pip-compile-args", "--allow-unsafe --upgrade"),
            "pip-autocompile --pip-compile-args '--allow-unsafe --upgrade'",
        ),
    ),
    ids=lambda argvalue: repr(argvalue),
)
def test_quote_args(args: tuple[object, ...], expected: str) -> None:
    assert quote_args(*args) == expected
