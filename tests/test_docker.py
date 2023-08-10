from __future__ import annotations

from pathlib import Path

import pytest

from pipautocompile.docker import dockerfile_has_build_stage


def dockerfile_path(filename: str) -> Path:
    return Path("tests/test_docker/test_dockerfile_has_build_stage") / filename


@pytest.mark.parametrize(
    argnames=("path", "build_stage", "expectation"),
    argvalues=(
        pytest.param(
            dockerfile_path("Dockerfile.missing"),
            "build-deps",
            False,
            id="missing Dockerfile",
        ),
        pytest.param(
            dockerfile_path("Dockerfile.empty"),
            "build-deps",
            False,
            id="empty Dockerfile",
        ),
        pytest.param(
            dockerfile_path("Dockerfile.invalid"),
            "build-deps",
            False,
            id="invalid Dockerfile",
        ),
        pytest.param(
            dockerfile_path("Dockerfile"),
            "build",
            False,
            id="no match",
        ),
        pytest.param(
            dockerfile_path("Dockerfile"),
            "BUILD",
            True,
            id="match (BUILD)",
        ),
        pytest.param(
            dockerfile_path("Dockerfile"),
            "build-deps",
            True,
            id="match (build-deps)",
        ),
    ),
)
def test_dockerfile_has_build_stage(
    path: Path, build_stage: str, expectation: bool
) -> None:
    assert dockerfile_has_build_stage(path, build_stage) == expectation
