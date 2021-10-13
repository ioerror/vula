VERSION := $(shell python3 setup.py version|tail -n1)
DEB_NAME := ./deb_dist/python3-vula_${VERSION}-1_all.deb

.PHONY: test
test:
	echo ${VERSION}

.PHONY: pypi-build
pypi-build:
	python3 -m build

.PHONY: pypi-upload
pypi-upload:
	python3 -m twine upload --repository pypi dist/*$(VERSION)*

.PHONY: deb
deb: ${DEB_NAME}

${DEB_NAME}: vula vula/*py configs configs/* configs/*/*
	python3 setup.py --command-packages=stdeb.command sdist_dsc bdist_deb

.PHONY: clean
clean:
	-rm -rf build/ dist/ vula.egg-info deb_dist
