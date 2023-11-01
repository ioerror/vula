VERSION := $(shell python3 setup.py version|tail -n1)
DEB_NAME := ./deb_dist/python3-vula_${VERSION}-1_all.deb
RPM_NAME := ./dist/vula-$(VERSION)-1.noarch.rpm
FOLDER = vula test podman

.PHONY: test
test:
	echo ${VERSION}

gettext-build:
	python3 setup.py compile_catalog --directory vula/locale --locale de_DE --domain ui
	python3 setup.py compile_catalog --directory vula/locale --locale de_DE --domain ui.view
	python3 setup.py compile_catalog --directory vula/locale --locale en_US --domain ui
	python3 setup.py compile_catalog --directory vula/locale --locale en_US --domain ui.view


# This requires `apt install python3-build python3-venv`
.PHONY: pypi-build
pypi-build:
	python3 -m build

# This requires `apt install python3-build python3-venv`
.PHONY: pypi-upload
pypi-upload:
	python3 -m twine check dist/*$(VERSION)*
	python3 -m twine upload --repository pypi dist/*$(VERSION)*

.PHONY: deb
deb: ${DEB_NAME}

${DEB_NAME}: vula vula/*py vula/frontend/*py vula/frontend/view/*py configs configs/* configs/*/* setup.py gettext-build
	python3 setup.py --command-packages=stdeb.command sdist_dsc --compat=10 bdist_deb

.PHONY: rpm
rpm: ${RPM_NAME}

${RPM_NAME}: vula vula/*py vula/frontend/*py vula/frontend/view/*py configs configs/* configs/*/* setup.py
	python3 setup.py --command-packages=stdeb.command bdist_rpm
.PHONY: pytest-coverage
pytest-coverage:
	pipenv run pytest --cov --cov-report xml --cov-report html --cov-report term

.PHONY: clean
clean:
	-rm -rf build/ dist/ vula.egg-info deb_dist
	find vula/locale -type f -name \*.mo -delete

.PHONY: format
format: black

.PHONY: check-format
check-format: check-black

.PHONY: check
check: check-format flake8

.PHONY: isort
isort:
	pipenv run isort --atomic $(FOLDER)

.PHONY: check-isort
check-isort:
	pipenv run isort -c -v $(FOLDER)

.PHONY: black
black:
	pipenv run black $(FOLDER)

.PHONY: check-black
check-black:
	pipenv run black --check $(FOLDER)

.PHONY: flake8
flake8:
	pipenv run flake8 $(FOLDER)

.PHONY: mypy
mypy:
	pipenv run mypy

.PHONY: pytest
pytest:
	pipenv run pytest

.PHONY: sast-analysis
sast-analysis:
	pipenv run bandit -r -ll -s B104 -f txt -o ./report-bandit.txt ./vula
	pipenv run semgrep --json -o ./report-semgrep.txt --config="p/security-audit" ./vula/

.PHONY: deps-graphs
deps-graphs:
	# this requires pipenv, pydeps, graphviz, ...
	pipenv run pydeps --pylib-all --cluster --max-cluster-size 10 -o contrib/deps-graphs/precisely_linked.svg vula
	pipenv run pydeps --pylib-all --cluster --keep-target-cluster --max-cluster-size 10 -o contrib/deps-graphs/all_clustered.svg vula
	pipenv run pydeps --pylib-all --show-deps vula -o contrib/deps-graphs/unorganized.svg > contrib/deps-graphs/vula_deps.json

.PHONY: dev-deps-apt
dev-deps-apt:
	export PATH=$$PATH:~/.local/bin
	apt update
	apt install -y --no-install-recommends pkg-config libglib2.0-dev libcairo2-dev libgirepository1.0-dev python3-dev git
	python -m pip install --user pipx
	python -m pip install --user pylint
	python -m pipx ensurepath
	pipx install pipenv
	pipenv install --dev --skip-lock

.PHONY: dev-deps-pacman
dev-deps-pacman:
	PATH=$$PATH:~/.local/bin
	sudo pacman -S python-pipenv cairo pkgconf gobject-introspection gtk3
	pipenv install --dev --skip-lock

.PHONY: fuzz
fuzz:
	python contrib/fuzzing/vulaFuzzer.py
