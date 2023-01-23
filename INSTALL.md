# Requirements

Currently, GNU/Linux is the only supported operating system. We plan to port
the software to other operating systems in the future.

The software has been developed and tested on Debian 11 (bullseye), Mobian, and
Ubuntu (21.04 and 21.10). It previously was working on Ubuntu 20.04 but the
installation instructions have not been successfully tested there recently. It
is likely to work on other modern systemd-based distributions.

Vula can also be run without systemd, and/or in a single monolithic process,
but how to do so is not yet documented.

We do not yet offer Debian packages for download directly, but you can install
a debianized version of our Python package using the `pypi-install` tool.

To install the dependencies required for building vula packages yourself, or
for installing a debian package via `pypi-install`, run this command:

* `sudo apt install -y --no-install-recommends build-essential debhelper dh-python fakeroot gcc make python3-all python3-all-dev python3-click python3-cpuinfo python3-cryptography python3-dbus python3-dev python3-hkdf python3-ifaddr python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy python3-packaging python3-pathtools python3-pip python3-pluggy python3-progress python3-py python3-pydbus python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner python3-qrcode python3-schema python3-setuptools python3-setuptools-scm python3-stdeb python3-systemd python3-toml python3-yaml python3-zeroconf python3-babel python3-tk python-all wireguard-tools python3-sphinx python3-xlib python3-pillow gir1.2-ayatanaappindicator3-0.1`
* `sudo pip install sibc`

You need `python3-click` module version 8.+, `apt` might install the latest version,
but will fail to install version 8.+. You need to remove the installed version and
reinstall the `click` module using `pypi`:

* `sudo apt-get remove python3-click`
* `sudo pypi-install click`

# Install

## option 0: dpkg installation via PyPI

The
[`pypi-install`](https://pypi.org/project/stdeb/#pypi-install-command-line-command)
command, provided by the `python3-stdeb` package, can create and install `.deb`
packages from many packages available on the Python Package Index. This is
currently our recommended way for users of Debian and Ubuntu to install vula
and any Python dependencies which are not included with your distribution. On
Debian 11 or Ubuntu 21.x, after running the above `apt` command, simply run
these four commands:

```
sudo pypi-install sibc
# DEB_BUILD_OPTIONS=nocheck skips running tests as pystray on PyPI doesn't
# have them included and causes the build to fail.
sudo DEB_BUILD_OPTIONS=nocheck pypi-install pystray
sudo pypi-install vula_libnss
sudo pypi-install ggwave
sudo pypi-install vula
```

Installing the deb will automatically configure `nsswitch`, restart
`systemd-sysusers`, reload `dbus`, etc, and will tell `systemd` to enable and
start the `vula-organize` service.

On older distributions it may be necessary to `pypi-install` some other
packages such as `zeroconf` and `pyroute2`. Accurate installation instructions
for Ubuntu 20.04 should be restored here soon.

For working system tray support on the Gnome desktop environment it may be
necessary to install the Ubuntu AppIndicators extension:

* `sudo apt-get install gnome-shell-extension-appindicator`
* `gnome-extensions enable ubuntu-appindicators@ubuntu.com`

## option 1: build and install Debian Packages from a git checkout

In addition to the dependencies in the `apt` command above, you will also need
the [`sibc`](https://github.com/JJChiDguez/sibc) module. It can be installed
using `pypi-install` as shown above, or other ways as described in its
[`README`](https://github.com/JJChiDguez/sibc#for-development).

```
git clone --recurse-submodules https://codeberg.org/vula/vula_libnss
cd vula_libnss
make deb && sudo dpkg -i deb_dist/python3-vula-libnss_*.deb
cd ../
git clone https://codeberg.org/vula/vula
cd vula
make deb && sudo dpkg -i deb_dist/python3-vula_*_all.deb
```

## option 2: build a wheel and install with pip

This option is not currently recommended, as a `pip install` of vula will place
systemd and other configuration files in the wrong place. However, if you are
interested in helping to get vula working on other distributions, `pip install
sibc vula_libnss vula` is a place to start.

This option is available for advanced technical users - it requires manual
setup of `[vula_libnss](https://codeberg.org/vula/vula_libnss)` after
installing `vula_libnss`. This essentially means ensuring that the libnss
shared object file is installed in `/lib/libnss_vula.so.2`. This may be
installed by building a Debian package or by installing `vula_libnss` with pip
and manually copying the `libnss_vula.so.2` file from inside the installed
location to the correct location on the system.

```
git clone https://codeberg.org/vula/vula
cd vula
sudo pip install .
```

After installing with pip, users will need to configure the system:

```
sudo vula configure nsswitch
sudo systemctl daemon-reload
sudo systemctl restart systemd-sysusers
sudo systemctl reload dbus
sudo systemctl enable --now vula-organize
```

These are steps which are automatically performed by the Debian package's
[postinstall
script](https://codeberg.org/vula/vula/src/branch/main/misc/python3-vula.postinst).

## option 3: build an RPM

We have only done minimal testing of vula on RPM-based systems, but, it is
possible to type `make rpm` in the vula repo and generate an RPM (using
setuptools' `bdist_rpm` command). The post-installation steps mentioned in
option 2 above currently apply to RPM-based systems as well, because the RPM
does not include a postinstall script. See the `Makefile` in this directory for
hints on how to install the dependencies on Fedora.

It is also possible to build an RPM in Fedora inside of a `podman` container by
running `make dist=fedora34 rpm` in the `podman` directory.

On Fedora you can install the rpm-build package with `sudo dnf install rpm-build`
and then build the package executing `make rpm` in the vula repo.

Note that compatibility issues with RPM-based systems are collected in TODO.md.

## option 4: install from AUR (only for arch based systems)

Same as above only rudimentary testing of the functionality has been done on arch / manjaro.

The current installation process requires packages from [AUR](https://aur.archlinux.org/).
Currently one of the vula dependencies `python-sibc-git` is also available from AUR.
Installing packages from AUR is inherently dangerous, always check the PKGBUILD files.

The simplest installation is using an [AUR helper](https://wiki.archlinux.org/title/AUR_helpers) like `yay`.

```
yay -S python-sibc-git python-vula-git
```

In order to run `vula` commands as user you must be in a group called `sudo`. 
On arch systems this is not a default group, you must add it manually.

# Running vula

To see the current status:
* `vula`

To start vula (via dbus activation) if it is not started, or print the status
if it is:
* `vula start`

To see a list of subcommands:
* `vula --help`

To see a list of peers:
* `vula peer`

To see a list of commands for working with peers:
* `vula peer --help`

To see a list of peers, including disabled peers:
* `vula peer show --all`

To see descriptors and qrcodes for all enabled peers:
* `vula peer show -Dq`

To see the preferences:
* `vula prefs`

To see commands for editing preferences:
* `vula prefs --help`

To start graphical user interface:
* `vula gui`

More documentation is coming soon. See
[STATUS.md](https://codeberg.org/vula/vula/src/branch/main/STATUS.md) for more
information about what currently works and doesn't.

## vula GUI

The graphical user interface uses Tkinter as a Python binding to the Tk GUI toolkit.

### Screenshots

#### Peers
![peers](misc/tk_frontend/peers.png)

#### Preferences
![preferences](misc/tk_frontend/preferences.png)

#### My verification key
![my verification key](misc/tk_frontend/my_verification_key.png)

#### My descriptor
![my descriptor](misc/tk_frontend/my_descriptor.png)
