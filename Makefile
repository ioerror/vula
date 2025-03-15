export PIPENV_VERBOSITY=-1
export PYTHONWARNINGS=ignore
VERSION := $(shell cat vula/__version__.py |cut -f 2 -d'"')
ARCH := $(shell uname -m)
TGZ_NAME := vula-${VERSION}.tar.gz
DEB_NAME := python3-vula_${VERSION}-1_all.deb
RPM_NAME := vula-$(VERSION)-1.noarch.rpm
FOLDER = vula test podman
PYBUILD_NAME := vula
PYBUILD_SYSTEM := flit
DEB_BUILD_OPTIONS=nocheck

.PHONY: black check check-black check-format check-isort clean deb \
	deb-and-wheel-in-podman deps-graphs dev-deps-apt dev-deps-pacman \
	flake8 format fuzz isort mypy pypi-upload pytest pytest-coverage rpm \
	sast-analysis test wheel

version:
	echo "vula ${VERSION} on ${ARCH}"

./vula/locale/en_US/LC_MESSAGES/ui.mo: ./vula/locale/en_US/LC_MESSAGES/ui.po
	python3 setup.py compile_catalog --directory vula/locale --locale de_DE --domain ui
	python3 setup.py compile_catalog --directory vula/locale --locale de_DE --domain ui.view
	python3 setup.py compile_catalog --directory vula/locale --locale en_US --domain ui
	python3 setup.py compile_catalog --directory vula/locale --locale en_US --domain ui.view


# This requires `apt install python3-build python3-venv`
wheel:
	python3 -m build

# This requires `apt install python3-build python3-venv`
pypi-upload:
	python3 -m twine check dist/*$(VERSION)*
	python3 -m twine upload --repository pypi dist/*$(VERSION)*

./dist/${TGZ_NAME}: vula vula/*py vula/frontend/*py vula/frontend/view/*py configs configs/* configs/*/* setup.py ./vula/locale/en_US/LC_MESSAGES/ui.mo
	python3 -m build

deb: ./dist/${DEB_NAME}

./dist/${DEB_NAME}: ./dist/${TGZ_NAME}
	cd dist && rm -rvf "vula-${VERSION}" && tar xf ${TGZ_NAME} \
        && cd vula-${VERSION} && cp -rvp ../../debian ./debian && \
        DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -rfakeroot -uc -us --sanitize-env && \
		cd .. && rm -rf vula-${VERSION}

pytest-coverage:
	pipenv run pytest --cov --cov-report xml --cov-report html --cov-report term

clean:
	-rm -rf build/ dist/
	find vula/locale -type f -name \*.mo -delete

format: black

check-format: check-black

check: check-format flake8

isort:
	pipenv run isort --atomic $(FOLDER)

check-isort:
	pipenv run isort -c -v $(FOLDER)

black:
	pipenv run black $(FOLDER)

check-black:
	pipenv run black --check $(FOLDER)

flake8:
	pipenv run flake8 $(FOLDER)

mypy:
	pipenv run mypy

pytest:
	pipenv run pytest

sast-analysis:
	pipenv run bandit -r -ll -s B104 -f txt -o ./report-bandit.txt ./vula
	pipenv run semgrep --json -o ./report-semgrep.txt --config="p/security-audit" ./vula/

deps-graphs:
	# this requires pipenv, pydeps, graphviz, ...
	pipenv run pydeps --pylib-all --cluster --max-cluster-size 10 -o contrib/deps-graphs/precisely_linked.svg vula
	pipenv run pydeps --pylib-all --cluster --keep-target-cluster --max-cluster-size 10 -o contrib/deps-graphs/all_clustered.svg vula
	pipenv run pydeps --pylib-all --show-deps vula -o contrib/deps-graphs/unorganized.svg > contrib/deps-graphs/vula_deps.json

dev-deps-apt:
	export PATH=$$PATH:~/.local/bin
	apt update
	apt install -y --no-install-recommends pkg-config libglib2.0-dev libcairo2-dev libgirepository1.0-dev python3-dev git
	python -m pip install --user pipx
	python -m pip install --user pylint
	python -m pipx ensurepath
	pipx install pipenv
	pipenv install --dev --skip-lock

dev-deps-pacman:
	PATH=$$PATH:~/.local/bin
	sudo pacman -S python-pipenv cairo pkgconf gobject-introspection gtk3
	pipenv install --dev --skip-lock

fuzz:
	python contrib/fuzzing/vulaFuzzer.py

deb-and-wheel-in-podman:
	echo "Building ${VERSION}"
	podman run -v `pwd`:/vula --workdir /vula --rm -it debian:bookworm bash -c '/vula/misc/install-debian-deps.sh && make wheel && make deb && make version'
	echo "Built ${VERSION} for ${ARCH}"

