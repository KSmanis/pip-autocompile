from __future__ import annotations

import os
import subprocess  # nosec
import sys
import tempfile
from itertools import groupby
from pathlib import Path
from shlex import split

import click

from pipautocompile.git import inside_submodule
from pipautocompile.io import file_contains_pattern
from pipautocompile.io import find_spec_files
from pipautocompile.logging import info
from pipautocompile.utils import quote_args


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

    for spec_dir, specs in groupby(sorted(find_spec_files()), key=lambda s: s.parent):
        if not git_recurse_submodules and inside_submodule(spec_dir):
            continue

        info(f"Processing {spec_dir} directory...")
        spec_dir = spec_dir.resolve(strict=True)
        build_dir = spec_dir.parent if spec_dir.name == "requirements" else spec_dir

        env = {"CUSTOM_COMPILE_COMMAND": quote_args("pip-autocompile", *sys.argv[1:])}
        has_build_stage = file_contains_pattern(
            file=build_dir / "Dockerfile",
            pattern=fr"^FROM \S+ AS {docker_build_stage}$",
        )
        if has_build_stage:
            docker_env = {**os.environ, "DOCKER_BUILDKIT": "1"}

            info("Building Docker image...")
            with tempfile.TemporaryDirectory() as temp_dir:
                iidfile = Path(temp_dir) / "iidfile"
                subprocess.check_call(  # nosec
                    (
                        "docker",
                        "build",
                        "--iidfile",
                        iidfile,
                        "--target",
                        docker_build_stage,
                        build_dir,
                    ),
                    env=docker_env,
                )
                image_id = iidfile.read_text()

            container_env = env.copy()
            container_volumes = [
                f"{spec_dir}:/app/:ro",
                "pip-autocompile-cache-pip:/root/.cache/pip/",
                "pip-autocompile-cache-pip-tools:/root/.cache/pip-tools/",
            ]
            if docker_ssh_agent_passthrough and "SSH_AUTH_SOCK" in os.environ:
                ssh_auth_sock = os.environ["SSH_AUTH_SOCK"]
                container_env["SSH_AUTH_SOCK"] = ssh_auth_sock
                container_volumes.append(f"{ssh_auth_sock}:{ssh_auth_sock}:ro")

            container_id = ""
            try:
                info("Running container...")
                with tempfile.TemporaryDirectory() as temp_dir:
                    cidfile = Path(temp_dir) / "cidfile"
                    subprocess.check_call(  # nosec
                        (
                            "docker",
                            "run",
                            "--cidfile",
                            cidfile,
                            "--detach",
                            "--entrypoint",
                            "cat",
                            *(f"--env={k}={v}" for k, v in container_env.items()),
                            "--interactive",
                            "--rm",
                            *(f"--volume={volume}" for volume in container_volumes),
                            "--workdir",
                            "/app/",
                            image_id,
                        ),
                        env=docker_env,
                    )
                    container_id = cidfile.read_text()

                info("Installing pip-tools...")
                subprocess.check_call(  # nosec
                    ("docker", "exec", container_id, "pip", "install", "pip-tools"),
                    env=docker_env,
                )

                for spec in specs:
                    info(f"Compiling {spec}...")
                    output = subprocess.check_output(  # nosec
                        (
                            "docker",
                            "exec",
                            container_id,
                            "pip-compile",
                            *pip_compile_args,
                            "-o-",
                            spec.name,
                        ),
                        env=docker_env,
                    )
                    spec.with_suffix(".txt").write_bytes(output)
            finally:
                if container_id:
                    info("Cleaning up container...")
                    subprocess.check_call(  # nosec
                        ("docker", "kill", container_id), env=docker_env
                    )
        else:
            for spec in specs:
                info(f"Compiling {spec}...")
                subprocess.check_call(  # nosec
                    ("pip-compile", *pip_compile_args, spec.name),
                    cwd=spec_dir,
                    env={**os.environ, **env},
                )
