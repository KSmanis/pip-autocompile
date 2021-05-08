import os
import re
import shlex
import subprocess  # nosec
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Tuple, Union

import click

DEFAULT_BUILD_STAGE = "build-deps"
DEFAULT_PIP_COMPILE_ARGS = (
    "--allow-unsafe",
    "--generate-hashes",
    "--no-reuse-hashes",
    "--upgrade",
)


def _find_spec_files(
    path: Union[str, os.PathLike] = ".",
    patterns: Iterable[str] = (
        "**/requirements.in",
        "**/requirements/**/*.in",
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
        click.secho(f"Compiling {spec}...", fg="yellow", bold=True)
        spec_dir = spec.resolve(strict=True).parent
        build_dir = spec_dir if spec.name == "requirements.in" else spec_dir.parent

        env = {
            "CUSTOM_COMPILE_COMMAND": _shell_quote(("pip-autocompile", *sys.argv[1:]))
        }
        has_build_stage = _file_contains_regex(
            file=build_dir / "Dockerfile",
            regex=fr"^FROM \S+ AS {build_stage}$",
        )
        if has_build_stage:
            with tempfile.TemporaryDirectory() as temp_dir:
                iidfile = Path(temp_dir) / "iidfile"
                subprocess.check_call(  # nosec
                    (
                        "docker",
                        "build",
                        "--iidfile",
                        iidfile,
                        "--target",
                        build_stage,
                        build_dir,
                    ),
                    env={**os.environ, "DOCKER_BUILDKIT": "1"},
                )
                image_id = iidfile.read_text()

            output = subprocess.check_output(  # nosec
                (
                    "docker",
                    "run",
                    *(f"--env={k}={v}" for k, v in env.items()),
                    "--rm",
                    "--volume",
                    f"{spec_dir}:/app/:ro",
                    "--volume",
                    "pip-autocompile-cache-pip:/root/.cache/pip/",
                    "--volume",
                    "pip-autocompile-cache-pip-tools:/root/.cache/pip-tools/",
                    "--workdir",
                    "/app/",
                    image_id,
                    "sh",
                    "-c",
                    """
                        set -eux;
                        pip install pip-tools >&2;
                        pip-compile {args} -o- {spec_name};
                    """.format(
                        args=_shell_quote(pip_compile_args),
                        spec_name=_shell_quote(spec.name),
                    ),
                ),
                env={**os.environ, "DOCKER_BUILDKIT": "1"},
            )
            spec.with_suffix(".txt").write_bytes(output)
        else:
            subprocess.check_call(  # nosec
                ["pip-compile", *pip_compile_args, spec.name],
                cwd=spec_dir,
                env={**os.environ, **env},
            )
