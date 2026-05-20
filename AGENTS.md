# VDSM - Agent Instructions

## Build & Dev Commands

```bash
# Regenerate Makefile after pulling changes
./autogen.sh --system --enable-timestamp

# Build
make

# Full check (lint + tests, in order)
make check

# Lint only (gitignore → reuse → execcmd → black → flake8 → pylint)
make lint

# Tests via tox (uses system site-packages, PYTHONPATH=lib)
tox -e lib              # library code
tox -e network          # network tests
tox -e virt             # virt tests
tox -e storage-user     # storage (user perms)
tox -e storage-root     # storage (root perms, needs --privileged)
tox -e hooks            # hooks (PYTHONPATH includes vdsm_hooks)
tox -e tests            # misc tests

# Single test file
tox -e lib -- --no-cov tests/lib/some_test.py

# Storage tests need userstorage setup first
make storage            # create test storage
tox -e storage-user
```

## Environment

- **Container venv**: `/venv` (pre-configured, already in PATH via `.bashrc`)
- **Local venv**: `make venv` → `~/.venv/vdsm/bin/activate`
- **PYTHONPATH**: `lib` (set automatically in tox.ini)
- **Test base temp**: `/var/tmp/vdsm` (not /tmp)
- **Containers**: `quay.io/ovirt/vdsm-test:{centos-9,centos-10,alma-9,alma-10}`

## Code Style

- **Formatter**: Black with `-l 79 -S` (line-length 79, skip string normalization)
- **Linter**: pylint ≥3.2 `<4.0`, flake8 ≥6.0 (ignore E731, E722, W504, W503)
- **SPDX headers**: All files need `SPDX-FileCopyrightText` + `SPDX-License-Identifier: GPL-2.0-or-later`
- **Add headers**: `contrib/add-spdx-header.sh new_file.py`

## Test Quirks

- **Timeout**: 30s default (override with `@pytest.mark.timeout(60)`)
- **Markers**: `integration`, `root`, `slow`, `stress`, `unit`, `legacy_switch`, `ovs_switch`
- **Skip slow/stress**: markers in tox.ini exclude them by default
- **Root tests**: storage-root, some network tests need `--privileged` container
- **flake8 per-file ignores**: test XML strings (E501), statsd false positive (F824)
- **xfail strict**: Tests marked xfail must fail, override with `strict=False`

## Architecture

- `lib/vdsm/` - core library (network, storage, virt, gluster, rpc, api)
- `lib/yajsonrpc/` - JSON-RPC library
- `lib/vdsmclient/` - VDSM client library
- `vdsm_hooks/` - hook scripts (one subdir per hook)
- `tests/` - tests mirror lib/ structure
- `static/` - config files, systemd units, vdsm-tool
- `doc/` - Sphinx documentation

## CI

- **Lint**: runs `./ci/lint.sh` (autogen + make + make lint)
- **Tests**: runs `./ci/tests.sh` (needs `--privileged` for network/storage)
- **Storage**: separate jobs for user and root, run on self-hosted docker runners
- **RPM build**: `./ci/rpm.sh` in `quay.io/ovirt/buildcontainer:{el9stream,el10stream}`
