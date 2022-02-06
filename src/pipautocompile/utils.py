from __future__ import annotations

from shlex import quote
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def quote_args(*args: Any) -> str:
    return " ".join(quote(str(arg)) for arg in args)
