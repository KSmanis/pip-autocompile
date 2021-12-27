from __future__ import annotations

from shlex import quote


def quote_args(*args: str) -> str:
    return " ".join(map(quote, args))
