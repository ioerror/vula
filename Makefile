VERSION := $(shell python3 setup.py version|tail -n1)

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
deb:
	echo $(VERSION)
	python3 setup.py --command-packages=stdeb.command sdist_dsc
	cp -v misc/python3-vula.postinst deb_dist/vula-$(VERSION)/debian/
	cd deb_dist/vula-$(VERSION) &&	dpkg-buildpackage -rfakeroot -us -uc

.PHONY: clean
clean:
	-rm -rf build/ dist/ vula.egg-info deb_dist
