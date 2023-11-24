from warnings import filterwarnings

filterwarnings("ignore")

import os
import time
from glob import glob
from shutil import copy2
from subprocess import check_output
from sys import platform

import setuptools
from setuptools.command.build_ext import build_ext as hookBuild_ext

try:
    from babel.messages import frontend as babel
    compile_catalog = babel.compile_catalog
except ImportError:
    compile_catalog=None
try:
    from stdeb.command.bdist_deb import bdist_deb
    from stdeb.command.sdist_dsc import sdist_dsc

    class sdist_dsc_with_postinst(sdist_dsc):
        def run(self):
            res = super(sdist_dsc_with_postinst, self).run()
            print("Installing vula postinst")
            copy2(
                'misc/python3-vula.postinst',
                self.dist_dir + '/vula-{}/debian/'.format(version),
            )
            return res

except ImportError:
    sdist_dsc = None
    sdist_dsc_with_postinst = None
    bdist_deb = None
try:
    from click_man.commands.man_pages import man_pages
except ImportError:
    man_pages = None

try:
    os.environ['SOURCE_DATE_EPOCH'] = (
        check_output("git log -1 --pretty=%ct", shell=True).decode().strip()
    )
except:
    os.environ['SOURCE_DATE_EPOCH'] = str(int(time.time()))

if os.path.exists('vula/__version__.py'):
    with open("vula/__version__.py", "r") as obj:
        version = str(obj.readline().strip())
        version = version.split('"')[1]

if os.path.exists('requirements.txt'):
    with open("requirements.txt", "r") as obj:
        requirements = obj.read().splitlines()
else:
    # this makes stdeb work
    requirements = []

with open("README.md", "r") as obj:
    long_description = obj.read()

linux_data_files = [
    (
        "/etc/systemd/system/",
        [
            "configs/systemd/vula.slice",
            "configs/systemd/vula.target",
            "configs/systemd/vula-discover.target",
            "configs/systemd/vula-discover-alt.target",
            "configs/systemd/vula-publish.target",
            "configs/systemd/vula-publish-alt.target",
            "configs/systemd/vula-organize-monolithic.target",
            "configs/systemd/vula-discover.service",
            "configs/systemd/vula-discover-alt.service",
            "configs/systemd/vula-publish.service",
            "configs/systemd/vula-publish-alt.service",
            "configs/systemd/vula-organize.service",
            "configs/systemd/vula-organize-monolithic.service",
        ],
    ),
    (
        "/etc/dbus-1/system.d/",
        ['configs/dbus/local.vula.services.conf'],
    ),
    (
        "/usr/share/applications",
        [
            "misc/linux-desktop/vula.desktop",
            "misc/linux-desktop/vula-tray.desktop",
        ]
    ),
    (
        "/usr/share/icons",
        [
            "misc/linux-desktop/vula_gui_icon.png"
        ]
    ),
        (
        "/usr/share/icons/vula",
        [
            "misc/images/add_ip_to_peer_entry.png",
            "misc/images/clipboard.png",
            "misc/images/delete.png",
            "misc/images/edit_name_entry.png",
            "misc/images/pin_and_verify.png",
            "misc/images/save.png",
            "misc/images/show_qr.png",
            "misc/images/next.png",
            "misc/images/previous.png",
            "misc/images/edit.png",
            "misc/images/save_blue.png",
            "misc/images/cancel.png",
            "misc/images/help.png",
            "misc/images/repair.png",
            "misc/images/rediscover.png",
            "misc/images/release_gateway.png",
        ]
    ),
    (
        "/usr/share/dbus-1/system-services/",
        [
            'configs/dbus/local.vula.organize.service',
            'configs/dbus/local.vula.publish.service',
            'configs/dbus/local.vula.discover.service',
            'configs/dbus/local.vula.publishalt.service',
            'configs/dbus/local.vula.discoveralt.service',
        ],
    ),
    (
        "/usr/share/polkit-1/actions/",
        ['configs/polkit/local.vula.organize.Debug.policy'],
    ),
    ("/usr/lib/sysusers.d/", ['configs/sysusers.d/vula.conf']),
    (
        "/usr/share/man/man1/",
        glob('man/vula*1'),
    ),
    (
        "",
        ["misc/python3-vula.postinst"],
    ),
]

# The locations for files on macOS. This differs from Linux in
# that the files are stored in usr/local instead of usr/share.
macos_data_files = [
    (
        "/usr/local/share/dbus-1/",
        ['configs/dbus/local.vula.services.conf'],
    ),
    (
        "/usr/local/dbus-1/system-services/",
        [
            'configs/dbus/local.vula.organize.service',
            'configs/dbus/local.vula.publish.service',
            'configs/dbus/local.vula.discover.service',
            'configs/dbus/local.vula.publish-alt.service',
            'configs/dbus/local.vula.discover-alt.service',

        ],
    ),
    ("/usr/local/lib/sysusers.d/", ['configs/sysusers.d/vula.conf']),
    (
        "/usr/local/man/man1/",
        glob('man/vula*1'),
    ),
    (
        "",
        ["misc/python3-vula.postinst"],
    ),
]

# Uses the macOS specific paths for Darwin (macOS) systems
if platform == "darwin":
    our_data_files = macos_data_files
else:
    our_data_files = linux_data_files

if platform.startswith("openbsd"):
    our_data_files = []


class print_version(hookBuild_ext):
    def run(self):
        print(version)


setuptools.setup(
    name="vula",
    version=version,
    author="Vula Authors",
    author_email="git@vula.link",
    description=("Automatic local network encryption"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3",
    url="https://codeberg.org/vula/vula",
    packages=setuptools.find_packages(),
    keywords="WireGuard, mDNS, encryption, post-quantum, local-area network, CTIDH, CSIDH, Curve25519",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "vula=vula.__main__:main",
        ]
    },
    install_requires=requirements,
    data_files=our_data_files,
    package_data={'vula': ['vula/locale/*/LC_MESSAGES/*.mo']},
    include_package_data=True,
    zip_safe=False,
    tests_require=["pytest"],
    cmdclass=dict(
        compile_catalog=compile_catalog,
        bdist_deb=bdist_deb,
        sdist_dsc=sdist_dsc_with_postinst,
        man_pages=man_pages,
        version=print_version,
    ),
)
