VERSION := $(shell cd ..; python3 setup.py version|tail -n1)
DEB_NAME := ../deb_dist/python3-vula_${VERSION}-1_all.deb

podman_args=--volume $(shell readlink -f ..):/root/vula --workdir /root/vula

.PHONY: help
help:
	@cat README.md

.PHONY: deb
deb: ${DEB_NAME}

debian-deps-stamp:
	# build base image with systemd.
	# uncomment this to avoid using the podman cache:
	# podman build -t vula-debian-deps -f Dockerfile.debian-systemd --no-cache .
	podman build -t vula-debian-deps -f Dockerfile.debian-systemd .
	touch $@

${DEB_NAME}: debian-deps-stamp
	podman run --rm ${podman_args} --network none -it vula-debian-deps make deb

dpkg-image-stamp: ${DEB_NAME}
    # Now going to build a new image with vula installed via dpkg.
	# first, create new vula container:
	podman run --name vula-tmp ${podman_args} --network none --detach vula-debian-deps /bin/systemd
	# install debs:
	podman exec -e VULA_POSTINST_DONT_START=1 vula-tmp dpkg -i deb_dist/${DEB_NAME}
	# stop container:
	podman stop vula-tmp
	# save container as new image, over old one if it exists:
	podman commit vula-tmp vula-debian
	#
	# Although we can build the image as root, we can't grant it CAP_NET_ADMIN
	# as we don't have that ourselves. So, we need to transfer the image into
	# root's local registry to run it as root:
	sudo -v # unlock sudo to run podman as root
	podman save vula-debian | sudo podman load
	podman rm vula-tmp
	touch image-stamp
	touch $@

image-stamp:
	make dpkg-image-stamp
	# OK: created vula-debian image with dpkg install of vula. You can also run
	# "make editable-image" to replace it with an editable installation.
	touch $@

.PHONY: dpkg-image
dpkg-image:
	rm -f dpkg-image-stamp editable-image-stamp
	make dpkg-image-stamp

.PHONY: editable-image
editable-image: editable-image-stamp
editable-image-stamp: dpkg-image-stamp
	# create new vula container
	podman run --name vula-tmp ${podman_args} --network none --detach vula-debian /bin/systemd
	# install debs
	podman exec vula-tmp python setup.py install
	podman exec vula-tmp python setup.py develop
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
	podman commit vula-tmp vula-debian
	#
	# Although we can build the image as root, we can't grant it CAP_NET_ADMIN
	# as we don't have that ourselves. So, we need to transfer the image into
	# root's local registry to run it as root:
	sudo -v # unlock sudo to run podman as root
	podman save vula-debian | sudo podman load
	podman rm vula-tmp
	touch image-stamp
	touch $@

image-stamp: dpkg-image-stamp

.PHONY: shell
shell: dpkg-image-stamp
	sudo podman run ${podman_args} --rm -it vula-debian bash

.PHONY: testnet-start
testnet-start: testnet-started-stamp
testnet-started-stamp: dpkg-image-stamp
	sudo podman network create --internal vula-net || true
	for c in vula-test1 vula-test2; do \
		sudo podman create ${podman_args} --name $$c --hostname $$c --network vula-net --cap-add NET_ADMIN,NET_RAW vula-debian; \
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
testnet-shell: testnet-started-stamp
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

lan-container-stamp: dpkg-image-stamp
	sudo podman create ${podman_args} --name vula --hostname $(shell hostname) --cap-add NET_ADMIN,NET_RAW --network host vula-debian
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
	podman stop vula-debian-deps-tmp || true
	podman stop vula-tmp || true
	podman rm vula-debian-deps-tmp || true
	podman rm vula-tmp || true

.PHONY: clean-images
clean-images:
	podman rmi vula-debian || true
	sudo podman rmi vula-debian || true
	rm -vf dpkg-image-stamp editable-image-stamp image-stamp

.PHONY: clean
clean: clean-containers clean-images testnet-clean
	rm -f ${DEB_NAME}
	# OK (errors are normal for this target)
	# note that the "make clean" target doesn't clean all podman artifacts:
	# - use "make lan-clean" to delete the "vula" container made by "make lan-start"
	# - use "make clean-all" to also delete the "vula-debian-deps" image

.PHONY: clean-all
clean-all: clean lan-clean
	podman rmi vula-debian-deps || true
	rm -vf *-stamp

