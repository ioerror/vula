VERSION := $(shell python3 setup.py version|tail -n1)

.PHONY: test
test:
	echo ${VERSION}

.PHONY: deb
deb:
	echo $(VERSION)
	python setup.py compile
	python setup.py --command-packages=stdeb.command sdist_dsc
	cp -v misc/python3-vula.postinst deb_dist/vula-$(VERSION)/debian/
	cd deb_dist/vula-$(VERSION) &&	dpkg-buildpackage -rfakeroot -us -uc
