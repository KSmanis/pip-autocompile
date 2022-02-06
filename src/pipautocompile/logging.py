from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from typing import Any


def info(*args: Any, **kwargs: Any) -> None:
    kwargs["bold"] = True
    kwargs["fg"] = "yellow"
    click.secho(*args, **kwargs)
