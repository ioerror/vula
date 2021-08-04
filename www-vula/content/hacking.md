---
title: "Hacking"
date: 2021-08-04T17:15:53+02:00
draft: false
---

This document has a few tips for working on the vula codebase.

Vula is typically run as three daemons: `organize`, `publish`, and `discover`.
The latter two perform the ZeroConf/mDNS functions, and `organize` communicates
with them via `d-bus` and does everything else.

It is also possible to run `organize` in monolithic mode, meaning that all
three daemons' functions are performed in a single process, by running `sudo
vula organize run --monolithic`. root is required to be able to configure the
system; when running under systemd the `CAP_NET_ADMIN` capability allows us to
do this without being root.

The top-level `vula` command has a hidden `-d/--debug` option which will drop
you in to a pdb shell when there is an exception instead of exiting. When
working on vula, it is helpful to `systemctl stop vula-organize` and then run
`sudo vula -vd organize` to run the organize daemon in verbose and debugging
mode. The state file will retain the ownership of the `/var/lib/vula-organize`
directory, so there should be no conflict keeping state between invocations as
root and as the `vula-organize` user which is used when running under systemd.

# Setup development environment

For developing on your host system, you may find it helpful to set up an environment such as this:

```
export PIPENV_VERBOSITY=-1
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
pipenv install black flake8 isort mypy pytest pytest-cov --dev --skip-lock
```

Alternately, you can use our
[multipass-tests](https://codeberg.org/vula/vula/src/branch/main/multipass-tests/README.md)
scripts to easily run vula on a network of virtual machines.

## Use common tools to inspect and interact with the `vula` codebase

### Code (re)formatting with black

```
pipenv run black vula
```

### Typing hints

Note: haven't actually used mypy in a long time, but might return to it in the future.

```
pipenv run mypy
```

### Linting with flake8

Note: we are long overdue for running this.

```
pipenv run flake8 vula
```

### pytest

Our test suite runs with `pytest`. Coverage can be computed with `pytest --cov
--cov-fail-under=100` but we haven't done that recently.

