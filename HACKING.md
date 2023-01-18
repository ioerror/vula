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

For developing on your host system, you may find it helpful to set up an
environment such as the following.

Install `pipenv` and the dependencies for `pygobject`.
For other distros use the "Installing from PyPI with pip" section from
[PyGObject](https://pygobject.readthedocs.io/en/latest/getting_started.html).

On ubuntu/debian the following command can be used.

```
sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 python3-venv
```

After installing the `pygobject` dependencies you can install pipenv.
Pipenv will create a virtual python environment with all the dependencies of
vula in one place. In this setup the dependencies for vula are not shared with
the python modules directly installed on the system.

```
export PIPENV_VERBOSITY=-1
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
exec $SHELL

pipenv install --dev --skip-lock
```

To verify the installation you can run `pipenv run pytest --cov`.
In order to run commands inside the pipenv you use the `pipenv run <command>` command.
If you prefer you can start a shell inside of the pipenv using `pipenv shell`.


Full example on debian/ubuntu.

```
sudo apt update
sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0 python3-venv
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
exec $SHELL
pipenv install --dev --skip-lock
```

Now the command `pipenv run pytest --cov` should succeed.



Alternately, you can use our
[podman environment](https://codeberg.org/vula/vula/src/branch/main/podman/README.md)
scripts to easily run vula on a network of containers.

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

Generate a html report (in `htmlcov/index.html`) which shows missed lines and statements interactively:
```
pipenv run pytest --cov --cov-report=html
```

# CI/CD Setup

Vula currently uses two different CICD services, [GitLab](https://gitlab.ti.bfh.ch/vula/vula/-/pipelines) and [Codeberg CI](https://ci.codeberg.org/vula/vula).

### Pipeline configuration
The configuration for the Coderg CI pipeline can be found in the file `.woodpecker.yml`, while the configuration for the GitLab pipeline can be found in a file called `.gitlab-ci.yml`.

While GitLab is a proven solution for pipelines, the Codeberg CI project is still in a closed testing phase. It uses [Woodpecker CI](https://woodpecker-ci.org/) as CI solution, which does not have the same extensive set of functionality as Gitlab. Some notable differences:
- We do not have caching functionality in our Codeberg CI pipeline like we have on GitLab.
- We cannot use keywords like `before_script` functionality in Codeberg CI, therefore the configuratin does not look very DRY.
- We cannot upload artifacts in Codeberg CI, all jobs are currently configured to print relevant results to stdout.
- The "ping-test" job is commented out in our Codeberg CI pipeline because of "podman inside docker container" issues, check the comments in `woodpecker.yml` for more information.
- Pipeline runetime on Codberg CI is much longer (probably resource limitations and missing caching), the maximum runtime seems to be 1 hour.