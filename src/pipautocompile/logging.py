from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from typing import Any


def info(message: Any | None = None, *, nl: bool = True) -> None:
    click.secho(message=message, nl=nl, bold=True, fg="yellow")
