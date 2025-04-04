# Requirements

Vula currently supports the GNU/Linux operating system. We plan to port the software to other operating systems in the future.

The software has been developed and tested on Debian 11 (bullseye), Mobian, and Ubuntu (21.04 and 21.10). It is likely to work on other modern systemd-based distributions. Vula can also be run without systemd, and/or in a single monolithic process, but this scenario is not yet documented.

Although we do not provide pre-built Debian packages for download, you can build packages locally as described in Option 0 and Option 1 below.

# Installing vula

Choose one of the following installation options.

## Option 0: Quick install

**Important: This installation option requires an Ubuntu 24.10 system.**

The quick-build.sh script runs apt to install necessary system prerequisites, pulls down the latest code from the required git repositories, and builds the vula deb packages.

Complete the following steps to install vula.

1. From the root of your local vula repository, run the quick-build.sh script: 

```
./misc/quick-build.sh
```

If apt reports a missing dependency, the script fails with errors. You can usually recover by running `sudo apt install -f` and running the script again.

2. After a successful run, the script lists the deb packages that have been built. Install them manually as follows:

```
sudo dpkg -i dist/python3-vula_0.2.2025031100-2_all.deb vula_libnss/dist/python3-vula-libnss_0.0.2024120900-1_amd64.deb highctidh/dist/python3-highctidh_1.0.2024092800-1_amd64.deb ggwave/dist/libggwave-dev_0.4.2_amd64.deb ggwave/dist/python3-ggwave_0.4.2-0_amd64.deb pymonocypher/dist/python3-pymonocypher_4.0.2.5-0_amd64.deb reunion/dist/python3-rendez_1.2.1-1_all.deb
```

3. Vula starts as soon as the packages are installed. To check if it is running properly, use the following command:

```
vula status
```

If the installation was successful, you should see output similar to the following:

[ active ] vula-publish.service                (0:03:18)
[ active ] vula-discover.service               (0:03:18)
[ active ] vula-organize.service               (0:03:18)
[ active ] local.vula.organize dbus service (running repair --dry-run)
[ active ] 2 enabled peers correctly configured; 0 disabled


## Option 1: Building and installing on other Debian-based systems

Even when it does not work out-of-the-box, the quick-build.sh script is a good starting point for testing compatibility with other Debian-based systems. Manually running the script commands will help identify dependency problems, most of which can be easily remedied. We appreciate your assistence in validating install procedures on other distributions and versions. If you install this software on your system, please create an issue on the vula site and tell us about your experiences.


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


# Running vula

To see the current status:
* `vula status`

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










