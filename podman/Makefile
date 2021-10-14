VERSION := $(shell cd ..; python3 setup.py version|tail -n1)
DEB_NAME := ../deb_dist/python3-vula_${VERSION}-1_all.deb
RPM_NAME := ../dist/vula-${VERSION}-1.noarch.rpm
dist := bullseye
dists=buster focal hirsute bullseye impish fedora34
podman_args=--volume $(shell readlink -f ..):/root/vula:z --workdir /root/vula

.PHONY: help
help:
	@cat README.md

build_args=

ifeq ($(dist),buster)
	# vula hasn't ever worked easily in buster, and is currently broken in this Makefile
	build_args=--build-arg DISTRO=debian --build-arg VERSION=buster
endif
ifeq ($(dist),focal)
	# 20.04 was once our most supported target, but now is broken (maybe just
	# in podman, though?)
	build_args=--build-arg DISTRO=ubuntu --build-arg VERSION=20.04
endif
ifeq ($(dist),hirsute)
	# vula works well in Ubuntu 21.04
	build_args=--build-arg DISTRO=ubuntu --build-arg VERSION=21.04
endif
ifeq ($(dist),bullseye)
	# vula works well in Debian 11
	build_args=--build-arg DISTRO=debian --build-arg VERSION=bullseye
endif
ifeq ($(dist),impish)
	# vula appears to work well in Ubuntu 21.10
	build_args=--build-arg DISTRO=ubuntu --build-arg VERSION=21.10
endif

installed_image_stamp=dpkg-install-$(dist)-stamp
systemd_path=/bin/systemd

ifeq ($(dist),fedora34)
	# fedora support is in-progress
	installed_image_stamp=rpm-install-$(dist)-stamp
	systemd_path=/usr/sbin/init
endif

deps-buster-stamp deps-focal-stamp deps-hirsute-stamp deps-bullseye-stamp deps-impish-stamp:
	cd .. && podman build -t vula-deps-$(dist) -f podman/Dockerfile.vula-deps $(build_args) .
	touch $@

deps-fedora34-stamp:
	podman run --name vula-tmp -it fedora:34 dnf -y install systemd
	podman commit vula-tmp vula-deps-$(dist)
	podman rm vula-tmp
	podman run ${podman_args} --name vula-tmp --detach vula-deps-$(dist) ${systemd_path}
	podman exec -it vula-tmp dnf -y install make python3-click python3-cpuinfo python3-cryptography python3-hkdf python3-ifaddr python3-matplotlib python3-mpmath python3-networkx python3-numpy python3-packaging python3-pathtools python3-pip python3-pluggy python3-progress python3-py python3-pydbus python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner python3-qrcode python3-schema python3-setuptools python3-systemd python3-toml python3-yaml python3-zeroconf rpm-build wireguard-tools
	podman exec -it vula-tmp pip install pyroute2==0.5.14
	podman exec -it vula-tmp pip install pynacl
	podman exec -it vula-tmp pip install sibc
	podman stop vula-tmp
	podman commit vula-tmp vula-deps-$(dist)
	podman rm vula-tmp
	touch $@

.PHONY: deps
deps: deps-$(dist)-stamp

.PHONY: deps-all
deps-all:
	for dist in $(dists); do \
		make dist=$$dist deps; \
	done

.PHONY: deb
deb: ${DEB_NAME}

${DEB_NAME}: deps-$(dist)-stamp
	podman run --rm ${podman_args} --network none -it vula-deps-$(dist) make deb

.PHONY: rpm
rpm:
	make dist=fedora34 ${RPM_NAME}

${RPM_NAME}: deps-$(dist)-stamp
	podman run --rm ${podman_args} --network none -it vula-deps-$(dist) python3 setup.py bdist_rpm

dpkg-install-$(dist)-stamp: deps-$(dist)-stamp
	# Now going to build a new image with vula installed via dpkg.
	# first, create new vula container:
	podman run --name vula-tmp ${podman_args} --network none --detach vula-deps-$(dist) ${systemd_path}
	# build the deb:
	podman exec vula-tmp make deb
	# install the deb:
	podman exec -e VULA_POSTINST_DONT_START=1 vula-tmp dpkg -i deb_dist/${DEB_NAME}
	# stop container:
	podman stop vula-tmp
	# save container as new image, over old one if it exists:
	podman commit vula-tmp vula-$(dist)
	#
	# Although we can build the image as root, we can't grant it CAP_NET_ADMIN
	# as we don't have that ourselves. So, we need to transfer the image into
	# root's local registry to run it as root:
	sudo -v # unlock sudo to run podman as root
	podman save vula-$(dist) | sudo podman load
	podman rm vula-tmp
	touch $@

rpm-install-$(dist)-stamp: deps-$(dist)-stamp
	# Now going to build a new image with vula installed via dpkg.
	# first, create new vula container:
	podman run --name vula-tmp ${podman_args} --network none --detach vula-deps-$(dist) ${systemd_path}
	# build the rpm:
	podman exec vula-tmp python3 setup.py bdist_rpm
	# install the rpm:
	podman exec vula-tmp rpm -i dist/${RPM_NAME}
	# stop container:
	podman stop vula-tmp
	# save container as new image, over old one if it exists:
	podman commit vula-tmp vula-$(dist)
	#
	# Although we can build the image as root, we can't grant it CAP_NET_ADMIN
	# as we don't have that ourselves. So, we need to transfer the image into
	# root's local registry to run it as root:
	sudo -v # unlock sudo to run podman as root
	podman save vula-$(dist) | sudo podman load
	podman rm vula-tmp
	touch $@

.PHONY: dpkg-image
dpkg-image:
	rm -vf dpkg-install-$(dist)-stamp
	make dist=$(dist) dpkg-install-$(dist)-stamp

.PHONY: rpm-image
rpm-image:
	rm -vf rpm-install-$(dist)-stamp
	make dist=$(dist) rpm-install-$(dist)-stamp

.PHONY: editable-image
editable-image: editable-$(dist)-image-stamp
editable-$(dist)-image-stamp: ${installed_image_stamp}
	# create new vula container
	podman run --name vula-tmp ${podman_args} --network none --detach vula-$(dist) ${systemd_path}
	# install debs
	podman exec vula-tmp python3 setup.py install
	podman exec vula-tmp python3 setup.py develop
#
# 	if we built the editable image from vula-debian-deps instead of vula-debian, we
#   would now run this:
#	podman exec -e VULA_POSTINST_DONT_START=1 vula-tmp ./misc/python3-vula.postinst
#   ... but that isn't actually working, we we build editable on top of the
#   dpkg image for now. FIXME.
#
	# stop container
	podman stop vula-tmp
	# save container as new image
	podman commit vula-tmp vula-$(dist)
	#
	# Although we can build the image as root, we can't grant it CAP_NET_ADMIN
	# as we don't have that ourselves. So, we need to transfer the image into
	# root's local registry to run it as root:
	sudo -v # unlock sudo to run podman as root
	podman save vula-$(dist) | sudo podman load
	podman rm vula-tmp
	touch $@

.PHONY: shell
shell: ${installed_image_stamp}
	sudo podman run ${podman_args} --rm -it vula-$(dist) bash

.PHONY: deps-shell
deps-shell: deps-$(dist)-stamp
	podman run ${podman_args} --rm -it vula-deps-$(dist) bash

.PHONY: deps-systemd-shell
deps-systemd-shell: deps-$(dist)-stamp
	podman run ${podman_args} --name vula-tmp --detach vula-deps-$(dist) ${systemd_path}
	podman exec -it vula-tmp bash
	podman stop vula-tmp
	podman rm vula-tmp

.PHONY: testnet-start
testnet-start: testnet-started-stamp
testnet-started-stamp: ${installed_image_stamp}
	sudo podman network create --internal vula-net || true
	for c in vula-test1 vula-test2; do \
		sudo podman create ${podman_args} --name $$c --hostname $$c --network vula-net --cap-add NET_ADMIN,NET_RAW vula-$(dist); \
		sudo podman start $$c; \
	done
	touch $@

.PHONY: testnet-stop
testnet-stop:
	for c in vula-test1 vula-test2; do \
		sudo podman stop $$c; \
	done || true
	rm -f testnet-started-stamp

.PHONY: testnet-restart
testnet-restart: testnet-stop testnet-start

.PHONY: retest
retest: testnet-restart test

.PHONY: testnet-clean
testnet-clean: testnet-stop
	for c in vula-test1 vula-test2; do \
		sudo podman rm $$c; \
	done || true

.PHONY: testnet-shell
testnet-shell: testnet-start
	sudo podman exec -it vula-test1 bash

.PHONY: test
test: testnet-start
	sudo podman ps
	#
	# note: run "make testnet-stop" to stop these containers,
	# 		 or "make testnet-clean" to delete them.
	#
	sudo podman exec -it vula-test1 pytest-3
	sudo podman exec -it vula-test1 vula start
	sudo podman exec -it vula-test2 vula start
	sudo podman exec -it vula-test2 ping -c 1 vula-test1.local.
	sudo podman exec -it vula-test1 vula peer
	@echo -n "test environment: "
	@sudo podman exec -it vula-test1 cat /etc/os-release|grep VERSION_CODENAME|cut -f 2 -d=

.PHONY: test-all
test-all:
	# only these three work presently
	make dist=hirsute testnet-clean test
	make dist=bullseye testnet-clean test
	make dist=impish testnet-clean test

.PHONY: test-all-clean
test-all-clean:
	make dist=hirsute clean test
	make dist=bullseye clean test
	make dist=impish clean test

lan-container-stamp: ${installed_image_stamp}
	sudo podman create ${podman_args} --name vula --hostname $(shell hostname) --cap-add NET_ADMIN,NET_RAW --network host vula-$(dist)
	touch $@

lan-container-started-stamp: lan-container-stamp
	sudo podman start vula
	sleep 1
	touch $@

.PHONY: lan-start
lan-start: lan-container-started-stamp
	sudo podman exec vula vula status --only-systemd
	# podman should now have a "vula" container in the host network namespace.
	# to get a shell in it, run "make lan-shell"

.PHONY: lan-stop
lan-stop:
	sudo podman stop vula || true
	rm -f lan-container-started-stamp

.PHONY: lan-clean
lan-clean: lan-stop
	@if [ -e lan-container-stamp ]; then \
		echo -n "Really delete 'vula' container created by lan-start? [yN]"; \
		read a; \
		if [ "$$a" = "y" ]; then \
			sudo podman rm vula || true; \
			rm -f lan-container-stamp; \
		else \
			echo "OK, not deleting 'vula' container."; \
		fi; \
	fi

.PHONY: lan-shell
lan-shell: lan-container-started-stamp
	sudo podman exec -it vula bash

.PHONY: clean-containers
clean-containers: testnet-clean
	sudo podman network rm vula-net || true
	podman stop vula-tmp || true
	podman rm vula-tmp || true

.PHONY: clean-images
clean-images:
	for dist in $(dists); do \
		podman rmi vula-$$dist || true; \
		sudo podman rmi vula-$$dist || true; \
		rm -vf dpkg-install-$$dist-stamp; \
		rm -vf rpm-install-$$dist-stamp; \
		rm -vf editable-$$dist-image-stamp; \
	done

.PHONY: clean
clean: clean-containers clean-images
	rm -f ${DEB_NAME} ${RPM_NAME}
	# OK (errors are normal for this target)
	# note that the "make clean" target doesn't clean all podman artifacts:
	# - use "make lan-clean" to delete the "vula" container made by "make lan-start"
	# - use "make clean-all" to also delete the "vula-debian-deps" image

.PHONY: clean-all
clean-all: clean lan-clean
	for dist in $(dists); do \
		podman rmi vula-deps-$$dist || true; \
		rm -vf deps-$$dist-stamp; \
	done
