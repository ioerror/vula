title: "Hacking vula"
date: 2025-03-28T11:35:25-07:00
draft: false
---


This document provides a few tips for working on the vula codebase.

# General

Root permissions are normally required to configure the system. However, running vula with the systemd `CAP_NET_ADMIN` capability allows configuration by non-root users.

Vula is typically run as three daemons: `organize`, `publish`, and `discover`. The latter two perform the ZeroConf/mDNS functions, while `organize` communicates with them via `d-bus` and does everything else.

It is also possible to run `organize` in monolithic mode, meaning that all three daemons' functions are performed in a single process. This is done by running `sudo vula organize run --monolithic`. 

The top-level `vula` command has a hidden `-d/--debug` option that drops you into a PDB shell when there is an exception instead of exiting.

When working on vula, it is helpful to run `systemctl stop vula-organize` and then `sudo vula -vd organize` to run the organize daemon in verbose-plus-debugging mode. The state file will retain the ownership of the `/var/lib/vula-organize` directory, so there should be no conflict keeping state between invocations as root and as the `vula-organize` user which is used when running under systemd.

# Set up a development environment

For developing on your host system, you may find it helpful to set up an environment such as the following. The following step apply to an Ubuntu/Debian system. For other distros, use the "Installing from PyPI with pip" section from [PyGObject](https://pygobject.readthedocs.io/en/latest/getting_started.html).

To install the dependencies for `pygobject`, run the following command:

```
sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 python3-venv
```

After installing the dependencies, you can install `pipenv`, which creates a virtual python environment with all the dependencies of vula in one place. In this setup, the dependencies for vula are not shared with other python modules directly installed on the system.

Install; `pipenv` with the following commands:

```
export PIPENV_VERBOSITY=-1
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
exec $SHELL

pipenv install --dev --skip-lock
```

To verify the installation, run `pipenv run pytest --cov`.

To run commands inside the `pipenv` environment, use the `pipenv run <command>` command. If you prefer, you can start a shell inside of the `pipenv` using `pipenv shell`.

The command `pipenv run pytest --cov` should now succeed.

Alternately, you can use our [podman environment](https://codeberg.org/vula/vula/src/branch/main/podman/README.md) scripts to easily run vula on a network of containers.

## Use common tools to inspect and interact with the `vula` codebase

### Code (re)formatting with black

```
pipenv run black vula
```

### Typing hints

```
pipenv run mypy
```

### Linting with flake8

```
pipenv run flake8 vula
```

### Testing with pytest

The vula test suite runs with `pytest`. The preconfiguration is saved in the file `pytest.ini`. By default, all available unit and doctests in the project directory are executed.

Run the whole test suite with pipenv:
```
pipenv run pytest
```

Use a key (e.g. method name) to target only a subset of all available tests:
```
pipenv run pytest -k "yamlfile"
```

Coverage can be computed with:
```
pipenv run pytest --cov --cov-fail-under=100
```

Generate an HTML report (in `htmlcov/index.html`) which shows missed lines and statements interactively:
```
pipenv run pytest --cov --cov-report=html
```

# CI/CD setup

Vula currently uses two different CI/CD services, [GitLab](https://gitlab.ti.bfh.ch/vula/vula/-/pipelines) and [Codeberg CI](https://ci.codeberg.org/vula/vula).

## Pipeline configuration
The configuration for the Codeberg CI pipeline can be found in the file `.woodpecker.yml`, while the configuration for the GitLab pipeline can be found in a file called `.gitlab-ci.yml`.

While GitLab is a proven solution for pipelines, the Codeberg CI project is still in a closed testing phase. It uses [Woodpecker CI](https://woodpecker-ci.org/) as CI solution, which does not have the same extensive functionality as GitLab. Some notable differences:

- We do not have caching functionality in our Codeberg CI pipeline like we have on GitLab.
- We cannot use keywords such `before_script` functionality in Codeberg CI; therefore, the configuration does not look very DRY.
- We cannot upHACKINGload artifacts in Codeberg CI; all jobs are currently configured to print relevant results to stdout.
- The "ping-test" job is commented out in our Codeberg CI pipeline because of "podman inside docker container" issues. Check the comments in `woodpecker.yml` for more information.
- Pipeline runtime on Codeberg CI is much longer (probably resource limitations and missing caching). The maximum runtime seems to be one hour.

The Codeberg CI may be run locally by checking out the woodpecker git repo and building the `woodpecker-cli` program. It may be built as a standalone binary to be installed in your path (e.g., `~/bin/`) or as a Debian package to be installed system-wide. One method to run locally works as follows:

```
git clone https://github.com/woodpecker-ci/woodpecker
cd woodpecker
make vendor
make release-cli
make bundle-cli
# Install the locally built Debian package:
sudo dpkg -i dist/woodpecker-cli_0.0.0_amd64.deb
```

Use `woodpecker-cli` to run locally:
```
woodpecker-cli exec .woodpecker.yml
```

If you would like to add a git hook, we provide the same command as a shell
script in `misc/run-woodpecker-ci-locally.sh`.

# Analyzing Python dependencies

In order to easily list and visualize vula's python dependencies, several diagrams can be generated using the Makefile goal `deps-graph`: 

```
make deps-graphs
```

The following diagrams are generated:

![Unorganized Dependencies](./contrib/deps-graphs/unorganized.svg)
All modules whether external or internal are all mixed up and linked to one another.

![Precisely Linked Dependencies](./contrib/deps-graphs/precisely_linked.svg)
This graph is clustering all the modules of the external dependencies, showing which specific module of Vula is using which external dependency.

![All Clustered Dependencies](./contrib/deps-graphs/all_clustered.svg)
To further simplify the view, everything is clustered separately which reveals how Vula is internally organized.

To view these dependencies in a text format, run the Makefile goal locally, which allows you to generate the file `vula_deps.json` in the folder `contrib/deps-graphs`. This is not directly included in the repository as it contains host-specific information such as system-specific paths.
