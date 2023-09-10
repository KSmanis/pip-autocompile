from __future__ import annotations

from shlex import quote


def quote_args(*args: object) -> str:
    return " ".join(quote(str(arg)) for arg in args)
