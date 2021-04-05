# Setup development environment

Install the suggested Python development tools:
```
export PIPENV_VERBOSITY=-1
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install pipenv
pipenv install black flake8 isort mypy pytest pytest-cov --dev --skip-lock
```

## Use common tools to inspect and interact with the `vula` codebase

### Typing hints

```
pipenv run mypy
```

### Linting with flake8

```
pipenv run flake8 vula
```

### Code (re)formatting with black

```
pipenv run black vula
```

### pytest

```
pipenv run pytest
pipenv run pytest --cov --cov-fail-under=100
```
