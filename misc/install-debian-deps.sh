#!/bin/bash
set -e

# This script is meant to be run inside of a container.
#
# See quick-install.sh for the script meant to be run on real systems.
#
# This script is tested and working with bullseye, hirsute, and impish.

# There are also special cases here which get us closer to working again in
# focal and buster, but they are incomplete:

# in the focal podman test, peers are not seeing eachother's announcements.
# more investigation is needed.

# in buster, the cryptography dependency is one blocker. If the version
# constraint is removed from it in requirements.txt, then PyYAML is another.


dist="$(cat /etc/os-release|grep VERSION_CODENAME|cut -f 2 -d=)"

echo "Installing on '$dist'"

# FIXME: some of these probably aren't needed anymore

sibc_deps="dh-python python3-click python3-progress python3-mpmath python3-numpy python3-matplotlib python3-networkx python3-setuptools-scm python3-setuptools python3-cpuinfo python3-all build-essential fakeroot"

vula_deps="wireguard-tools python3-yaml python3-click python3-nacl python3-schema python3-pip python3-pathtools make gcc python3-pydbus python3-pyroute2 python3-pytest-runner python3-pytest python3-toml python3-py python3-packaging python3-pluggy python3-hkdf python3-ifaddr python3-cryptography python3-dbus python3-pygments python3-systemd python3-qrcode python3-all python-all fakeroot build-essential dh-python debhelper python3-dev python3-zeroconf python3-stdeb python3-all-dev python3-babel python3-tk python3-sphinx python3-xlib python3-pillow gir1.2-ayatanaappindicator3-0.1 python3-pyaudio"

click_man_deps="python3-click-man click-man"

if [ "$dist" != "focal" ] && [ "$dist" != "buster" ]; then
    vula_deps="$vula_deps $click_man_deps"
fi

if [ "$dist" = "buster" ]; then
    if ! grep buster-backports /etc/apt/sources.list >/dev/null; then
        echo 'deb http://deb.debian.org/debian buster-backports main' | tee -a /etc/apt/sources.list
    fi
    vula_deps="$vula_deps python3-importlib-metadata" # needed for new pyroute2
fi

apt update
apt install -y --no-install-recommends $sibc_deps $vula_deps

if [ "$dist" = "focal" ] || [ "$dist" = "buster" ]; then
    # focal needs a newer stdeb. The one it has can't even pypi-install an
    # upgraded version of itself, as it triggers PyPI rate-limiting every time.
    tmpd=$(mktemp -d)
    pushd $tmpd
    apt install -y python3-pip
    pip3 download stdeb
#    py2dsc-deb deb_dist/stdeb-*.tar.gz
# the above py2desc works in focal, but not buster. this works in both:
        tar xf stdeb-*.tar.gz
        pushd stdeb*/
        python3 setup.py --command-packages=stdeb.command sdist_dsc bdist_deb
        dpkg -i deb_dist/python3-stdeb*deb || true
        apt install --fix-broken -y
        dpkg -i deb_dist/python3-stdeb*deb
        popd
    popd
fi

if [ "$dist" = "buster" ]; then
    # buster needs a newer zeroconf
    pypi-install zeroconf

    # buster needs a newer pyroute2, and therefore gets the latest one which is
    # now multiple packages.
    pypi-install pyroute2
    pypi-install pyroute2.core
    pypi-install pyroute2.ipdb

    # pypi-install PyYAML # fails because it collides with differently-named debian package
    # pip3 install PyYAML # fails because it cannot remove the distutils-based
                          # debian packaged version (which is required by many
                          # other debian packages)

#    pypi-install semantic_version # for setuptools_rust
#    pypi-install setuptools_rust # for cryptography
#    pypi-install cryptography # doesn't work, but removing the version constraint altogether might?

fi

pypi-install ggwave
# pip3 install ggwave

pypi-install sibc
# for latest version:
# pip3 install git+https://github.com/JJChiDguez/sibc

pypi-install vula_libnss
# for latest version:
# git clone --recursive https://codeberg.org/vula/vula_libnss
# cd vula_libnss && make deb && dpkg -i deb_dist/*.deb

# python3-pystray is only available in Debian Unstable so far
DEB_BUILD_OPTIONS=nocheck pypi-install pystray

# on older distributions it may be necessary to get newer versions of some
# packages from pypi:
# sudo pypi-install -U zeroconf
# sudo pypi-install stdeb

echo "OK: deps installed on $(hostname)"
