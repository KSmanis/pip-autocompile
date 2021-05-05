import logging
import os
import re
import shlex
import subprocess  # nosec
import sys
from pathlib import Path
from typing import Iterable, List, Tuple, Union

import click
from python_on_whales import docker

DEFAULT_BUILD_STAGE = "build-deps"
DEFAULT_PIP_COMPILE_ARGS = (
    "--allow-unsafe",
    "--generate-hashes",
    "--no-reuse-hashes",
    "--upgrade",
)

logging.basicConfig(level=logging.INFO)


def _find_spec_files(
    path: Union[str, os.PathLike] = ".",
    patterns: Iterable[str] = (
        "**/requirements.in",
        "**/requirements/*.in",
    ),
) -> List[Path]:
    return sorted(s for p in patterns for s in Path(path).glob(p) if s.is_file())


def _file_contains_regex(
    file: Union[str, bytes, os.PathLike],
    regex: str,
    flags: Union[int, re.RegexFlag] = 0,
) -> bool:
    try:
        f = open(file)
    except OSError:
        pass
    else:
        with f:
            for line in f:
                if re.search(regex, line, flags) is not None:
                    return True
    return False


def _shell_quote(s: Union[str, Iterable[str]]) -> str:
    return shlex.quote(s) if isinstance(s, str) else " ".join(map(shlex.quote, s))


@click.command(
    context_settings={
        "help_option_names": ("-h", "--help"),
        "ignore_unknown_options": True,
    }
)
@click.version_option()
@click.option(
    "--build-stage",
    help="Docker build stage to search for.",
    default=DEFAULT_BUILD_STAGE,
    show_default=True,
)
@click.argument(
    "pip_compile_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
def cli(build_stage: str, pip_compile_args: Tuple[str, ...]):
    """Automate pip-compile for multiple environments."""

    if not pip_compile_args:
        pip_compile_args = DEFAULT_PIP_COMPILE_ARGS

    for spec in _find_spec_files():
        logging.info(f"Processing '{spec}'...")
        basename_in = spec.name
        basename_out = spec.with_suffix(".txt").name
        spec_dir = spec.resolve(strict=True).parent
        build_dir = spec_dir if basename_in == "requirements.in" else spec_dir.parent

        args = _shell_quote(sys.argv[1:])
        env = {"CUSTOM_COMPILE_COMMAND": f"pip-autocompile {args}"}
        has_build_stage = _file_contains_regex(
            file=build_dir / "Dockerfile",
            regex=fr"^FROM \S+ AS {build_stage}$",
        )
        if has_build_stage:
            image_id = docker.build(context_path=build_dir, target=build_stage).id
            docker.run(
                image=image_id,
                command=[
                    "sh",
                    "-c",
                    """
                        set -eux;
                        python -m venv /opt/venv/;
                        /opt/venv/bin/pip install pip-tools;
                        /opt/venv/bin/pip-compile {pip_compile_args} {basename_in};
                        chown "$(stat -c '%u:%g' {basename_in})" {basename_out};
                        chmod "$(stat -c '%a' {basename_in})" {basename_out};
                    """.format(
                        basename_in=_shell_quote(basename_in),
                        basename_out=_shell_quote(basename_out),
                        pip_compile_args=_shell_quote(pip_compile_args),
                    ),
                ],
                envs=env,
                remove=True,
                volumes=[
                    (spec_dir, "/app/"),
                    ("pip-autocompile-cache-pip", "/root/.cache/pip/"),
                    ("pip-autocompile-cache-pip-tools", "/root/.cache/pip-tools/"),
                ],
                workdir="/app/",
            )
        else:
            subprocess.check_call(  # nosec
                ["pip-compile", *pip_compile_args, basename_in],
                cwd=spec_dir,
                env={**os.environ, **env},
            )
