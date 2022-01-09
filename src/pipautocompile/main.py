from __future__ import annotations

import os
import subprocess  # nosec
import sys
from itertools import groupby
from pathlib import Path
from shlex import split
from typing import TYPE_CHECKING

import click
from python_on_whales import docker

from pipautocompile.git import inside_submodule
from pipautocompile.io import file_contains_pattern
from pipautocompile.io import find_spec_files
from pipautocompile.logging import info
from pipautocompile.utils import quote_args

if TYPE_CHECKING:
    from python_on_whales.components.volume.cli_wrapper import VolumeDefinition


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="pip-autocompile")  # type: ignore
@click.option(
    "--docker-build-stage",
    help="Docker build stage to search for.",
    default="build-deps",
    show_default=True,
)
@click.option(
    "--docker-ssh-agent-passthrough/--no-docker-ssh-agent-passthrough",
    help="Allow Docker passthrough of SSH agent (if present)",
    default=True,
    show_default=True,
)
@click.option(
    "--git-recurse-submodules/--no-git-recurse-submodules",
    help="Recurse Git submodules.",
    default=False,
    show_default=True,
)
@click.option(
    "--pip-compile-args",
    "pip_compile_args_str",
    help="Arguments to pass directly to the pip-compile command.",
    default="--allow-unsafe --generate-hashes --no-reuse-hashes --upgrade",
    show_default=True,
)
def cli(
    docker_build_stage: str,
    docker_ssh_agent_passthrough: bool,
    git_recurse_submodules: bool,
    pip_compile_args_str: str,
):
    """Automate pip-compile for multiple environments."""

    pip_compile_args = split(pip_compile_args_str)
    pip_compile_env = {
        "CUSTOM_COMPILE_COMMAND": quote_args("pip-autocompile", *sys.argv[1:])
    }

    for spec_dir, specs in groupby(sorted(find_spec_files()), key=lambda s: s.parent):
        if not git_recurse_submodules and inside_submodule(spec_dir):
            continue

        info(f"Processing {spec_dir} directory...")
        spec_dir = spec_dir.resolve(strict=True)
        build_dir = spec_dir.parent if spec_dir.name == "requirements" else spec_dir

        has_build_stage = file_contains_pattern(
            file=build_dir / "Dockerfile",
            pattern=fr"^FROM \S+ AS {docker_build_stage}$",
        )
        if has_build_stage:
            info("Building Docker image...")
            image = docker.build(target=docker_build_stage, context_path=build_dir)

            container_env: dict[str, str] = {}
            container_volumes: list[VolumeDefinition] = [
                ("pip-autocompile-cache-pip", "/root/.cache/pip/"),
                ("pip-autocompile-cache-pip-tools", "/root/.cache/pip-tools/"),
            ]
            if docker_ssh_agent_passthrough and "SSH_AUTH_SOCK" in os.environ:
                ssh_auth_sock = os.environ["SSH_AUTH_SOCK"]
                container_env["SSH_AUTH_SOCK"] = ssh_auth_sock
                container_volumes.append((ssh_auth_sock, ssh_auth_sock, "ro"))

            info("Running container...")
            with docker.run(
                detach=True,
                entrypoint="",
                envs=container_env,
                remove=True,
                stop_signal="SIGKILL",
                user="0:0",
                volumes=container_volumes,
                image=image,
                command=["sleep", "86400"],
            ) as container:
                info("Creating venv...")
                container.execute(
                    tty=True, command=["python", "-m", "venv", "--clear", "/app/venv/"]
                )

                info("Upgrading core dependencies...")
                container.execute(
                    tty=True,
                    command=[
                        "/app/venv/bin/pip",
                        "install",
                        "--upgrade",
                        "pip",
                        "setuptools",
                    ],
                )

                info("Installing pip-tools...")
                container.execute(
                    tty=True, command=["/app/venv/bin/pip", "install", "pip-tools"]
                )

                info("Copying specs...")
                container_spec_dir = Path("/app/specs/")
                container.copy_to(spec_dir, container_spec_dir)

                for spec in specs:
                    info(f"Compiling {spec}...")
                    container_spec = container_spec_dir / spec.name
                    container.execute(
                        envs=pip_compile_env,
                        tty=True,
                        workdir=container_spec_dir,
                        command=[
                            "/app/venv/bin/pip-compile",
                            *pip_compile_args,
                            container_spec.name,
                        ],
                    )
                    container.copy_from(
                        container_spec.with_suffix(".txt"), spec.with_suffix(".txt")
                    )
        else:
            for spec in specs:
                info(f"Compiling {spec}...")
                subprocess.check_call(  # nosec
                    ("pip-compile", *pip_compile_args, spec.name),
                    cwd=spec_dir,
                    env={**os.environ, **pip_compile_env},
                )
