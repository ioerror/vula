import setuptools
from setuptools.command.build_ext import build_ext as hookBuild_ext
from subprocess import check_output
import os
from sys import platform
from os import system
from glob import glob
from platform import machine

try:
    from stdeb.command.sdist_dsc import sdist_dsc
    from stdeb.command.bdist_deb import bdist_deb
except ImportError:
    sdist_dsc = None
    bdist_deb = None
try:
    from click_man.commands.man_pages import man_pages
except ImportError:
    man_pages = None

os.environ['SOURCE_DATE_EPOCH'] = (
    check_output("git log -1 --pretty=%ct", shell=True).decode().strip()
)

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
            "configs/systemd/vula-publish.target",
            "configs/systemd/vula-organize-monolithic.target",
            "configs/systemd/vula-discover.service",
            "configs/systemd/vula-publish.service",
            "configs/systemd/vula-organize.service",
            "configs/systemd/vula-organize-monolithic.service",
        ],
    ),
    ("/etc/dbus-1/system.d/", ['configs/dbus/local.vula.services.conf'],),
    (
        # "/etc/dbus-1/system-services/",
        "/usr/share/dbus-1/system-services/",
        [
            'configs/dbus/vula-organize.service',
            'configs/dbus/vula-publish.service',
            'configs/dbus/vula-discover.service',
        ],
    ),
    (
        "/usr/share/polkit-1/actions/",
        ['configs/polkit/local.vula.organize.Debug.policy'],
    ),
    ("/usr/lib/sysusers.d/", ['configs/sysusers.d/vula.conf']),
    ("/usr/share/man/man1/", glob('man/vula*1'),),
]

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
    keywords="WireGuard, mDNS, encryption",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={"console_scripts": ["vula=vula.__main__:main",]},
    install_requires=requirements,
    data_files=our_data_files,
    include_package_data=True,
    zip_safe=False,
    tests_require=["pytest"],
    cmdclass=dict(
        bdist_deb=bdist_deb,
        sdist_dsc=sdist_dsc,
        man_pages=man_pages,
        version=print_version,
    ),
)
