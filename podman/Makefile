VERSION := $(shell cd ..; python3 setup.py version|tail -n1)
DEB_NAME := ../deb_dist/python3-vula_$(VERSION)-1_all.deb
RPM_NAME := ../dist/vula-$(VERSION)-1.noarch.rpm
NET_NAME := vula-net
SO_NAME := /usr/local/lib64/python3.9/site-packages/lib/libnss_vula.so.2
dist := bullseye
#dists := buster focal hirsute bullseye impish fedora34 alpine
dists := bullseye impish fedora34
podman_args := --volume $(shell readlink -f ..):/root/vula:z --workdir /root/vula --uts=private
add_caps := --cap-add NET_ADMIN,NET_RAW
test1 := vula-$(dist)-test1
test2 := vula-$(dist)-test2
test_hosts := $(test1) $(test2)

.PHONY: help
help:
	@cat README.md
	@echo
	@echo "---------------"
	@echo "version: $(VERSION)"
	@echo "dists: $(dists)"
	@echo "test hosts: $(test_hosts)"
	@echo "selected dist: $(dist)"
	@ls -l .*stamp 2>/dev/null || true

build_args=

ifeq ($(dist),buster)
	build_args=--build-arg DISTRO=debian --build-arg VERSION=buster
endif
ifeq ($(dist),focal)
	build_args=--build-arg DISTRO=ubuntu --build-arg VERSION=20.04
endif
ifeq ($(dist),hirsute)
	build_args=--build-arg DISTRO=ubuntu --build-arg VERSION=21.04
endif
ifeq ($(dist),bullseye)
	build_args=--build-arg DISTRO=debian --build-arg VERSION=bullseye
endif
ifeq ($(dist),impish)
	build_args=--build-arg DISTRO=ubuntu --build-arg VERSION=21.10
endif

installed_image_stamp=.dpkg-install-$(dist)-stamp
systemd_path=/bin/systemd
bin_sh=bash
pkgmgr=dpkg

ifeq ($(dist),fedora34)
	installed_image_stamp=.rpm-install-$(dist)-stamp
	systemd_path=/usr/sbin/init
	pkgmgr=rpm
endif

ifeq ($(dist),alpine)
	# Alpine support is in-progress. Daemons are not running yet. We don't know
	# how to build vula_libnss. Pytest is passing, at least.
	# (run "make dist=alpine test" to run pytest in alpine)
	installed_image_stamp=.apk-install-$(dist)-stamp
	bin_sh=sh
	pkgmgr=apk
endif

.deps-buster-stamp .deps-focal-stamp .deps-hirsute-stamp .deps-bullseye-stamp .deps-impish-stamp:
	cd .. && podman build -t vula-deps-$(dist) -f podman/Dockerfile.vula-deps $(build_args) .
	touch .deps-$(dist)-stamp

.deps-fedora34-stamp:
	podman run --name vula-tmp -it fedora:34 dnf -y install systemd
	podman commit vula-tmp vula-deps-$(dist)
	podman rm vula-tmp
	podman run $(podman_args) --name vula-tmp --detach vula-deps-$(dist) $(systemd_path)
	podman exec -it vula-tmp dnf -y install iputils gcc make python3-click python3-cpuinfo python3-cryptography python3-hkdf python3-ifaddr python3-matplotlib python3-mpmath python3-networkx python3-numpy python3-packaging python3-pathtools python3-pip python3-pluggy python3-progress python3-py python3-pydbus python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner python3-qrcode python3-schema python3-setuptools python3-systemd python3-toml python3-yaml python3-zeroconf python3-babel python3-tk rpm-build wireguard-tools git
	# note: pinned pyroute may not be necessary anymore FIXME
	podman exec -it vula-tmp pip install pyroute2==0.5.14 pynacl sibc wheel
	# note: TEMP=/var/tmp/ is required because /tmp is mounted noexec on some systems
	podman exec -e TEMP=/var/tmp/ -it vula-tmp pip install vula_libnss
	podman stop vula-tmp
	podman commit vula-tmp vula-deps-$(dist)
	podman rm vula-tmp
	touch $@

.deps-alpine-stamp:
	podman run --name vula-tmp --detach alpine:latest sleep 3600
	#podman exec -it vula-tmp apk add gcc py3-setuptools
	#
	podman exec -it vula-tmp apk add \
		py3-click py3-cryptography py3-ifaddr py3-matplotlib py3-networkx \
		py3-numpy py3-packaging py3-pathtools py3-pip py3-pluggy py3-progress \
		py3-py py3-pydbus py3-pygments py3-pynacl py3-pyroute2 py3-pytest py3-pytest-runner \
		py3-qrcode py3-setuptools py3-toml py3-yaml py3-zeroconf python3-babel python3-tk \
		gcc make musl-dev nss-dev musl-nscd-dev \
		apkbuild-pypi
		# libressl-dev musl-dev libffi-dev
	# note: pinned pyroute may not be necessary anymore FIXME
	podman exec -it vula-tmp pip install sibc vula_libnss hkdf schema pyroute2==0.5.14 # cpuinfo mpmath
	podman stop vula-tmp
	podman commit vula-tmp vula-deps-$(dist)
	podman rm vula-tmp
	touch $@

.PHONY: deps
deps: .deps-$(dist)-stamp

.PHONY: deps-all
deps-all:
	for dist in $(dists); do \
		make dist=$$dist deps; \
	done

.PHONY: deb
deb:
	make dist=$(dist) $(DEB_NAME)

$(DEB_NAME): .deps-$(dist)-stamp
	podman run --rm $(podman_args) --network none -it vula-deps-$(dist) make deb

.PHONY: rpm
rpm:
	make dist=fedora34 $(RPM_NAME)

$(RPM_NAME): .deps-$(dist)-stamp
	podman run --rm $(podman_args) --network none -it vula-deps-$(dist) make rpm

.dpkg-install-$(dist)-stamp: .deps-$(dist)-stamp $(DEB_NAME)
	# Now going to build a new image with vula installed via dpkg.
	# first, create new vula container:
	podman run --name vula-tmp $(podman_args) --network none --detach vula-deps-$(dist) $(systemd_path)
	# install the deb:
	podman exec -e VULA_POSTINST_DONT_START=1 vula-tmp dpkg -i deb_dist/$(DEB_NAME)
	# stop container:
	podman stop vula-tmp
	# save container as new image, over old one if it exists:
	podman commit vula-tmp vula-$(dist)
	podman rm vula-tmp
	touch $@

.rpm-install-$(dist)-stamp: .deps-$(dist)-stamp $(RPM_NAME)
	# Now going to build a new image with vula installed via rpm.
	# first, create new vula container:
	podman run --name vula-tmp $(podman_args) --network none --detach vula-deps-$(dist) $(systemd_path)
	# install the rpm:
	podman exec vula-tmp rpm -i dist/$(RPM_NAME)
	# install vula_libnss and configure it to be used
	podman exec vula-tmp cp $(SO_NAME) /usr/lib64/
	podman exec vula-tmp vula configure nsswitch
	# stop container:
	podman stop vula-tmp
	# save container as new image, over old one if it exists:
	podman commit vula-tmp vula-$(dist)
	podman rm vula-tmp
	touch $@

# for Alpine Linux's apk package format
.apk-install-$(dist)-stamp: .deps-$(dist)-stamp
	# we currently install on apk systems... using setup.py install.
	podman run --name vula-tmp $(podman_args) --network none --detach vula-deps-$(dist) sleep 86400
	podman exec -it vula-tmp python3 setup.py install
	podman stop vula-tmp
	podman commit vula-tmp vula-$(dist)
	podman rm vula-tmp
	touch $@


.dpkg-install-mitm-$(dist)-stamp: 
	# Now going to build a new image from the already built image
	# first, create new vula container from the existing image:
	podman run --name vula-mitm-deps-tmp $(podman_args) --detach vula-deps-$(dist) $(systemd_path)
	# Install new attacker dependencies
	podman exec vula-mitm-deps-tmp ./misc/install-mitm-deps.sh
	podman commit vula-mitm-deps-tmp vula-mitm-deps-$(dist)
	podman run --name vula-mitm-tmp $(podman_args) --network none --detach vula-mitm-deps-$(dist) $(systemd_path)
	# install the deb:
	podman exec -e VULA_POSTINST_DONT_START=1 vula-mitm-tmp dpkg -i deb_dist/$(DEB_NAME)
	# Disable the running vula services
	podman exec vula-mitm-tmp systemctl disable vula-organize
	podman exec vula-mitm-tmp systemctl disable vula-publish
	podman exec vula-mitm-tmp systemctl disable vula-discover
	# stop container:
	podman stop vula-mitm-tmp
	# save container as new image, over old one if it exists:
	podman commit vula-mitm-tmp vula-mallory-$(dist)
	podman rm vula-mitm-tmp
	podman rm -f vula-mitm-deps-tmp
	podman image rm vula-mitm-deps-$(dist)
	sudo -v # unlock sudo to run podman as root
	podman save vula-mallory-$(dist) | sudo podman load
	podman save vula-$(dist) | sudo podman load
	touch $@

.PHONY: $(pkgmgr)-image
$(pkgmgr)-image:
	@rm -vf .$(pkgmgr)-install-$(dist)-stamp
	make dist=$(dist) .$(pkgmgr)-install-$(dist)-stamp

.PHONY: editable-image
editable-image: .editable-$(dist)-image-stamp
.editable-$(dist)-image-stamp: $(installed_image_stamp)
	# create new vula container
	podman run --name vula-tmp $(podman_args) --network none --detach vula-deps-$(dist) $(systemd_path)
	# install in editable mode
	podman exec vula-tmp python3 setup.py install
	podman exec vula-tmp python3 setup.py develop
	podman exec vula-tmp chmod 755 .. # so that systemd users can read it
	podman exec -e VULA_POSTINST_DONT_START=1 vula-tmp ./misc/python3-vula.postinst
#
	# stop container
	podman stop vula-tmp
	# save container as new image
	podman commit vula-tmp vula-$(dist)

.PHONY: .create-network
.create-network:
	-podman network create --internal $(NET_NAME)

.PHONY: shell
shell: $(installed_image_stamp)
	podman run $(podman_args) --rm -it vula-$(dist) $(bin_sh)

.PHONY: systemd-shell
systemd-shell: $(installed_image_stamp)
	-podman stop vula-$(dist)-shell
	-podman rm vula-$(dist)-shell
	-make NET_NAME=$(NET_NAME) .create-network
	podman run $(podman_args) --name vula-$(dist)-shell --network podman,$(NET_NAME) --hostname $(dist)-shell --detach $(add_caps) vula-$(dist) $(systemd_path)
	podman exec -it vula-$(dist)-shell $(bin_sh)
	podman stop vula-$(dist)-shell

.PHONY: deps-shell
deps-shell: .deps-$(dist)-stamp
	podman run $(podman_args) --rm -it vula-deps-$(dist) $(bin_sh)

.PHONY: deps-systemd-shell
deps-systemd-shell: .deps-$(dist)-stamp
	-podman stop vula-$(dist)-shell
	-podman rm vula-$(dist)-shell
	podman run $(podman_args) --name vula-$(dist)-shell --detach $(add_caps) vula-deps-$(dist) $(systemd_path)
	podman exec -it vula-$(dist)-shell $(bin_sh)
	podman stop vula-$(dist)-shell

.PHONY: testnet-start
testnet-start: .testnet-started-$(dist)-stamp
.testnet-started-$(dist)-stamp: $(installed_image_stamp)
	-make NET_NAME=$(NET_NAME) .create-network
	for c in $(test_hosts); do \
		podman create $(podman_args) --name $$c --hostname $$c --network $(NET_NAME) $(add_caps) vula-$(dist); \
		podman start $$c; \
	done
	touch $@

.PHONY: testnet-stop
testnet-stop:
	@-for c in $(test_hosts); do \
		podman stop $$c; \
	done 2>&1 | grep -v 'no container with name or ID'
	@rm -vf .testnet-started-$(dist)-stamp

.PHONY: testnet-restart
testnet-restart: testnet-stop testnet-start

.PHONY: retest
retest: testnet-restart test

.PHONY: testnet-clean
testnet-clean: testnet-stop
	@-for c in $(test_hosts); do \
		podman rm $$c; \
	done 2>&1 | grep -v 'no container with name or ID'

.PHONY: testnet-clean-all
testnet-clean-all: testnet-stop
	@-for dist in $(dists); do \
		make dist=$$dist testnet-clean; \
	done


.PHONY: testnet-shell
testnet-shell: testnet-start
	podman exec -it $(test1) $(bin_sh)

.PHONY: test
test: testnet-start
	podman ps
	-make test-pytest
	@-for c in $(test_hosts); do \
		podman exec -it $$c vula start; \
	done
	make test-ping
	podman exec $(test1) vula peer
	@echo -n "test environment: "
	@podman exec -it $(test1) cat /etc/os-release|grep VERSION_CODENAME|cut -f 2 -d=
	#
	# note: run "make testnet-stop" to stop these containers,
	# 		 or "make testnet-clean" to delete them.
	#


.PHONY: testnet-mitm-start
testnet-mitm-start: .testnet-mitm-started-$(dist)-stamp
.testnet-mitm-started-$(dist)-stamp: $(installed_image_stamp) .dpkg-install-mitm-$(dist)-stamp
	-sudo podman network create --internal $(NET_NAME)
	sudo podman create --volume $(shell readlink -f ..):/root/vula:rw --name mallory --hostname mallory $(add_caps) --network $(NET_NAME) $(add_caps) vula-mallory-$(dist)
	sudo podman start mallory
	for c in $(test_hosts); do \
		sudo podman create $(podman_args) --name $$c --hostname $$c --network $(NET_NAME) $(add_caps) vula-$(dist); \
		sudo podman start $$c; \
	done
	touch $@
	# wait until mitm network setup completed
	sleep 30

.PHONY: testnet-mitm-stop
testnet-mitm-stop:
	sudo -v
	@-for c in $(test_hosts); do \
		sudo podman stop $$c; \
	done 2>&1 | grep -v 'no container with name or ID'
	@-sudo podman stop mallory
	@rm -vf .testnet-mitm-started-$(dist)-stamp

.PHONY: testnet-mitm-restart
testnet-mitm-restart: testnet-mitm-stop testnet-mitm-start

.PHONY: testnet-mitm-clean
testnet-mitm-clean: testnet-mitm-stop
	sudo -v
	@-for c in $(test_hosts); do \
                sudo podman rm $$c; \
	done 2>&1 | grep -v 'no container with name or ID'
	@-sudo podman rm mallory
	@-sudo podman network rm $(NET_NAME)


.PHONY: testnet-mitm-clean-all
testnet-mitm-clean-all: testnet-mitm-stop
	@-for dist in $(dists); do \
                make dist=$$dist testnet-mitm-clean; \
	done


.PHONY: test-passive-adversary
test-passive-adversary: testnet-mitm-start
	sudo podman exec -it mallory python3 vula/mitm/test_passive_adversary.py banner Eve
	sudo podman exec -itd mallory python3 vula/mitm/test_passive_adversary.py run $(shell sudo podman inspect vula-bullseye-test1 | grep 'IPAddress' | awk '{print $$2}' | sed '1d' | awk -F\" '{print $$2}') $(shell sudo podman inspect vula-bullseye-test2 | grep 'IPAddress' | awk '{print $$2}' | sed '1d' | awk -F\" '{print $$2}') 10 True
	sudo podman exec -it $(test2) ping -c 7 $(test1).local.
	sleep 10
	sudo podman exec -it mallory python3 vula/mitm/test_passive_adversary.py result

.PHONY: test-active-adversary
test-active-adversary: testnet-mitm-start
	sudo podman exec -it mallory python3 vula/mitm/test_passive_adversary.py banner Mallory
	sudo podman exec -it vula-bullseye-test1 vula peer
	@-sudo podman exec -it $(test2) ping -c 1 $(test1).local.
	sudo podman exec -itd mallory python3 -m vula.mitm.mdns_poison --ip $(shell sudo podman inspect mallory | grep 'IPAddress' | awk '{print $$2}' | sed '1d' | awk -F\" '{print $$2}') --interesting-hosts vula-bullseye-test1,vula-bullseye-test2
	sleep 90
	python3 ../vula/mitm/test_passive_adversary.py activeresult
	sudo podman exec -it vula-bullseye-test1 vula peer

.PHONY: test-pytest
test-pytest: testnet-start
	podman exec -it $(test1) pytest-3

.PHONY: test-ping
test-ping: testnet-start
	podman exec -it $(test2) perl -e 'until ("active\n" eq `systemctl is-active vula-organize.service`) {sleep 1}'
	sleep 1
	podman exec -it $(test1) vula status
	podman exec -it $(test2) vula status
	podman exec -it $(test2) ping -c 1 $(test1).local.

.PHONY: test-all
test-all:
	for dist in $(dists); do \
		make dist=$$dist test; \
	done

.PHONY: test-all-separate
test-all-separate:
	for dist in $(dists); do \
		make dist=$$dist test testnet-clean; \
	done

.PHONY: clean-containers
clean-containers: testnet-clean-all
	@-podman network rm $(NET_NAME) 		2>&1 | grep -v 'network not found'
	@-podman stop vula-tmp					2>&1 | grep -v 'no container with name or ID'
	@-podman rm vula-tmp					2>&1 | grep -v 'no container with name or ID'
	@-for dist in $(dists); do \
		podman stop vula-$$dist-shell; \
		podman rm vula-$$dist-shell; \
	done 2>&1 | grep -v 'no container with name or ID'

.PHONY: clean-images
clean-images:
	@-for dist in $(dists); do \
		podman rmi vula-$$dist; \
		podman rmi vula-mallory-$$dist; \
		rm -vf .dpkg-install-$$dist-stamp; \
		rm -vf .rpm-install-$$dist-stamp; \
		rm -vf .apk-install-$$dist-stamp; \
		rm -vf .editable-$$dist-image-stamp; \
		make dist=$(dist) testnet-clean; \
	done 2>&1 | grep -v 'no such image'

.PHONY: clean-packages
clean-packages:
	@rm -vf $(DEB_NAME) $(RPM_NAME)

.PHONY: clean
clean: clean-packages clean-containers clean-images
	# OK (errors are normal for this target)
	# note that the "make clean" target doesn't clean all podman artifacts:
	# - use "make clean-all" to also delete the "vula-debian-deps" image

.PHONY: clean-all
clean-all: clean
	@-for dist in $(dists); do \
		podman rmi vula-deps-$$dist; \
		rm -vf .deps-$$dist-stamp; \
	done 2>&1 | grep -v 'no such image' || true

.PHONY: clean-sudo
clean-sudo: 
	sudo -v # unlock sudo to run podman as root
	make clean-all
	@-make testnet-mitm-clean
	@-podman stop vula-mitm-deps-tmp        2>&1 | grep -v 'no container with name or ID'
	@-podman stop vula-mitm-tmp             2>&1 | grep -v 'no container with name or ID'
	@-podman rm vula-mitm-deps-tmp          2>&1 | grep -v 'no container with name or ID'
	@-podman rm vula-mitm-tmp               2>&1 | grep -v 'no container with name or ID'
	@-sudo podman stop mallory              2>&1 | grep -v 'no container with name or ID'
	@-sudo podman rm mallory                2>&1 | grep -v 'no container with name or ID'
	@-podman stop mallory                   2>&1 | grep -v 'no container with name or ID'
	@-podman rm mallory                     2>&1 | grep -v 'no container with name or ID'
	@-podman stop mallory                   2>&1 | grep -v 'no container with name or ID'
	@-podman rm mallory                     2>&1 | grep -v 'no container with name or ID'
	@-sudo podman stop vula-bullseye-test1	2>&1 | grep -v 'no container with name or ID'
	@-sudo podman stop vula-bullseye-test2	2>&1 | grep -v 'no container with name or ID'
	@-sudo podman rm vula-bullseye-test1	2>&1 | grep -v 'no container with name or ID'
	@-sudo podman rm vula-bullseye-test2	2>&1 | grep -v 'no container with name or ID'
	@-sudo podman rmi vula-mallory-bullseye	2>&1 | grep -v 'no container with name or ID'
	@-sudo podman rmi vula-bullseye			2>&1 | grep -v 'no container with name or ID'
	@-sudo podman network rm -f vula-net
	@rm -vf .deps-bullseye-mitm
	@rm -vf ./podman/.test-passed-stamp
	@rm -vf ./podman/.mallory-started-stamp
	@-for dist in $(dists); do \
		sudo podman rm vula-$$dist-test1 \
		sudo podman rm vula-$$dist-test2 \
		sudo podman rmi vula-$$dist \
		sudo podman rmi vula-mallory-$$dist; \
		rm -vf .dpkg-install-mitm-$$dist-stamp; \
	done 2>&1 | grep -v 'no such image'


