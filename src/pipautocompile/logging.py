from __future__ import annotations

import click


def info(*args, **kwargs) -> None:
    kwargs["bold"] = True
    kwargs["fg"] = "yellow"
    click.secho(*args, **kwargs)
