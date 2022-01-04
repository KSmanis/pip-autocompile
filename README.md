# pip-autocompile

[![PyPI version](https://img.shields.io/pypi/v/pip-autocompile.svg)](https://pypi.org/project/pip-autocompile/)
[![Renovate enabled](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com/)
[![pre-commit](https://github.com/KSmanis/pip-autocompile/workflows/pre-commit/badge.svg)](https://github.com/KSmanis/pip-autocompile/actions?workflow=pre-commit)
[![super-linter](https://github.com/KSmanis/pip-autocompile/workflows/super-linter/badge.svg)](https://github.com/KSmanis/pip-autocompile/actions?workflow=super-linter)
[![Maintainability](https://api.codeclimate.com/v1/badges/87818991157d33ec5421/maintainability)](https://codeclimate.com/github/KSmanis/pip-autocompile/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

Automate pip-compile for multiple environments.

## Dependencies

### Runtime

- [pip-tools](https://github.com/jazzband/pip-tools): Compile requirements
  locally
- [Docker CLI](https://github.com/docker/cli) >= 18.09: Compile requirements
  using containers
- [Git](https://git-scm.com/) >= 2.13: Skip Git submodules when
  `--no-git-recurse-submodules`
