# Requirements

Vula currently supports the GNU/Linux operating system. We plan to port the software to other operating systems in the future.

The software has been developed and tested on Debian 11 (bullseye), Mobian, and Ubuntu (21.04 and 21.10). It is likely to work on other modern systemd-based distributions. Vula can also be run without systemd, and/or in a single monolithic process, but this scenario is not yet documented.

Although we do not provide pre-built Debian packages for download, but you can install a debianized version of our Python package using the `pypi-install` tool. To install the dependencies required for building vula packages, or for installing a Debian package using `pypi-install`, run the following commands:

* `sudo apt install -y --no-install-recommends build-essential debhelper dh-python fakeroot gcc make python3-all python3-all-dev python3-click python3-cpuinfo python3-cryptography python3-dbus python3-dev python3-hkdf python3-ifaddr python3-matplotlib python3-mpmath python3-nacl python3-networkx python3-numpy python3-packaging python3-pathtools python3-pip python3-pluggy python3-progress python3-py python3-pydbus python3-pygments python3-pyroute2 python3-pytest python3-pytest-runner python3-qrcode python3-schema python3-setuptools python3-setuptools-scm python3-systemd python3-toml python3-yaml python3-zeroconf python3-babel python3-tk python-all wireguard-tools python3-sphinx python3-xlib python3-pillow gir1.2-ayatanaappindicator3-0.1 python3-opencv`
* `sudo pip install highctidh`

Note that you need `python3-click` module version 8.+. but `apt` may install the latest rather than version 8.+. You may need to remove the installed version and reinstall the `click` module using `pypi`, using the following commands:

* `sudo apt-get remove python3-click`
* `sudo pypi-install click`

# Install

`make deb` produces a Debian package. <!-- what is the context for this? -->

Choose one of the following installation methods.

## Option 0: Quick install

Run the command:

```
./misc/quick-install.sh
```


## Option 1: Build and install Debian packages from a new git checkout

For working system-tray support in the Gnome desktop environment , you may need to install the Ubuntu AppIndicators extension:

* `sudo apt-get install gnome-shell-extension-appindicator`
* `gnome-extensions enable ubuntu-appindicators@ubuntu.com`

In addition to the dependencies in the `apt` command above, you will also need the [`highctidh`](https://codeberg.org/vula/highctidh) module. It can be installed using `pypi-install` as shown above, or other ways as described in its [`README.python.md`](https://codeberg.org/vula/highctidh/src/branch/main/README.python.md).

Run the following commands to clone the repository, build the packages, and install:

```
git clone https://codeberg.org/vula/highctidh/
cd highctidh/
make deb && sudo dpkg -i dist/python3-highctidh_*.deb
cd ..
git clone --recurse-submodules https://codeberg.org/vula/vula_libnss
cd vula_libnss/
make deb && sudo dpkg -i dist/python3-vula-libnss_*.deb
cd ../
git clone https://codeberg.org/vula/vula
cd vula
make deb && sudo dpkg -i dist/python3-vula_*_all.deb
```

## Option 2: Build a wheel and install with pip

This option is not currently recommended, as a `pip install` of vula will place systemd and other configuration files in the wrong place. However, if you are interested in helping to get vula working on other distributions, `pip install highctidh vula_libnss vula` is a place to start.

This option is available for advanced technical users, requiring manual setup of `[vula_libnss](https://codeberg.org/vula/vula_libnss)` after installing `vula_libnss`. This essentially means ensuring that the libnss shared-object file is installed in `/lib/libnss_vula.so.2`. This file may be installed by building a Debian package or by installing `vula_libnss` with pip and manually copying the `libnss_vula.so.2` file from inside the installed location to the correct location on the system.

Run the following commands to clone the repository and install with pip:

```
git clone https://codeberg.org/vula/vula
cd vula
sudo pip install .
```

After installing with pip, configure the system as follows:

```
sudo vula configure nsswitch
sudo systemctl daemon-reload
sudo systemctl restart systemd-sysusers
sudo systemctl reload dbus
sudo systemctl enable --now vula-organize
```

These steps are performed automatically by the Debian package's [postinstall script](https://codeberg.org/vula/vula/src/branch/main/misc/python3-vula.postinst).

## Option 3: Build an RPM

We have done minimal testing of vula on RPM-based systems, but it is possible to type `make rpm` in the vula repo and generate an RPM (using the setuptools `bdist_rpm` command). The post-installation steps mentioned in option 2 apply to RPM-based systems as well, because the RPM does not include a postinstall script. See the `Makefile` in this directory for hints on how to install the dependencies on Fedora.

It is also possible to build an RPM in Fedora inside of a `podman` container by running `make dist=fedora34 rpm` in the `podman` directory.

On Fedora you can install the rpm-build package with `sudo dnf install rpm-build` and then build the package by executing `make rpm` in the vula repo.

Compatibility issues with RPM-based systems are collected in TODO.md.

## Option 4: Install from AUR (for Arch-based systems only)

As with RPM, only rudimentary testing has been done on Arch/Manjaro.

The current installation process requires packages from [AUR](https://aur.archlinux.org/), but one of the vula dependencies, `python-highctidh`, is unavailable from AUR. Installing packages from AUR is inherently dangerous, so always check the PKGBUILD files.

The simplest approach to installation is using an [AUR helper](https://wiki.archlinux.org/title/AUR_helpers) such as `yay`, as with the following command:

```
yay -S python-vula-git
```

The `python-highctidh` module will need to be installed outside of AUR until it is packaged.

In order to run `vula` commands as user, you must be in a group called `sudo`. This is not a default group on Arch systems, so you must add it manually.

# Running vula

To see the current status:
* `vula`

To start vula (via dbus activation) if it is not started, or to print the status
if it is started:
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

To see the preference settings:
* `vula prefs`

To see commands for editing preferences:
* `vula prefs --help`

To start graphical the user interface:
* `vula gui`

Watch 
[STATUS.md](https://codeberg.org/vula/vula/src/branch/main/STATUS.md) for more information about what currently works and doesn't.

## vula GUI

The graphical user interface uses Tkinter as a Python binding to the Tk GUI toolkit.

### Screenshots

#### Peers
![peers](misc/frontend/peer.png)

#### Preferences
![preferences](misc/frontend/dashboard.png)

#### My verification key
![my verification key](misc/frontend/verification_key.png)

#### My descriptor
![my descriptor](misc/frontend/descriptor.png)
