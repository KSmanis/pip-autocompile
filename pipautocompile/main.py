import os
import subprocess  # nosec
import sys
import tempfile
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple

import click

from pipautocompile.git import working_tree
from pipautocompile.io import file_contains_pattern
from pipautocompile.io import find_spec_files
from pipautocompile.logging import info
from pipautocompile.utils import quote_args

DEFAULT_BUILD_STAGE = "build-deps"
DEFAULT_PIP_COMPILE_ARGS = (
    "--allow-unsafe",
    "--generate-hashes",
    "--no-reuse-hashes",
    "--upgrade",
)


@click.command(
    context_settings={
        "help_option_names": ("-h", "--help"),
        "ignore_unknown_options": True,
    }
)
@click.version_option(package_name="pip-autocompile")  # type: ignore
@click.option(
    "--build-stage",
    help="Docker build stage to search for.",
    default=DEFAULT_BUILD_STAGE,
    show_default=True,
)
@click.option(
    "-n",
    "--dry-run",
    help="Show what would happen, but don't change anything.",
    default=False,
    is_flag=True,
)
@click.option(
    "--recurse-submodules",
    help="Recurse Git submodules.",
    default=False,
    is_flag=True,
    show_default=True,
)
@click.option(
    "--ssh-agent-docker-passthrough",
    help="Allow Docker passthrough of SSH agent (if present)",
    default=True,
    is_flag=True,
    show_default=True,
)
@click.argument(
    "pip_compile_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
def cli(
    build_stage: str,
    dry_run: bool,
    recurse_submodules: bool,
    ssh_agent_docker_passthrough: bool,
    pip_compile_args: "Tuple[str, ...]",
):
    """Automate pip-compile for multiple environments."""

    if not pip_compile_args:
        pip_compile_args = DEFAULT_PIP_COMPILE_ARGS

    initial_working_tree = working_tree()
    for spec_dir, specs in groupby(sorted(find_spec_files()), key=lambda s: s.parent):
        if not recurse_submodules and initial_working_tree != working_tree(spec_dir):
            continue

        info(f"Processing {spec_dir} directory...")
        spec_dir = spec_dir.resolve(strict=True)
        build_dir = spec_dir.parent if spec_dir.name == "requirements" else spec_dir

        env = {"CUSTOM_COMPILE_COMMAND": quote_args("pip-autocompile", *sys.argv[1:])}
        has_build_stage = file_contains_pattern(
            file=build_dir / "Dockerfile", pattern=fr"^FROM \S+ AS {build_stage}$"
        )
        if has_build_stage:
            docker_env = {**os.environ, "DOCKER_BUILDKIT": "1"}

            info("Building Docker image...")
            if not dry_run:
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
                        env=docker_env,
                    )
                    image_id = iidfile.read_text()

            container_env = env.copy()
            container_volumes = [
                f"{spec_dir}:/app/:ro",
                "pip-autocompile-cache-pip:/root/.cache/pip/",
                "pip-autocompile-cache-pip-tools:/root/.cache/pip-tools/",
            ]
            if ssh_agent_docker_passthrough and "SSH_AUTH_SOCK" in os.environ:
                ssh_auth_sock = os.environ["SSH_AUTH_SOCK"]
                container_env["SSH_AUTH_SOCK"] = ssh_auth_sock
                container_volumes.append(f"{ssh_auth_sock}:{ssh_auth_sock}:ro")

            container_id = ""
            try:
                info("Running container...")
                if not dry_run:
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
                if not dry_run:
                    subprocess.check_call(  # nosec
                        ("docker", "exec", container_id, "pip", "install", "pip-tools"),
                        env=docker_env,
                    )

                for spec in specs:
                    info(f"Compiling {spec}...")
                    if not dry_run:
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
                    if not dry_run:
                        subprocess.check_call(  # nosec
                            ("docker", "kill", container_id), env=docker_env
                        )
        else:
            for spec in specs:
                info(f"Compiling {spec}...")
                if not dry_run:
                    subprocess.check_call(  # nosec
                        ("pip-compile", *pip_compile_args, spec.name),
                        cwd=spec_dir,
                        env={**os.environ, **env},
                    )
