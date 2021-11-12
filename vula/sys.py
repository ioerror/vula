"""
Later this file will have some logic to import the right implementation of Sys
for the current operating system. Currently, only pyroute2 on Linux is
supported.
"""

from .sys_pyroute2 import Sys  # noqa: F401
