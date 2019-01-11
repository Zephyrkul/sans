from aiohttp import __version__ as _ah_version
from collections import namedtuple as _nt
from distutils.version import StrictVersion as _ST
from sys import version_info as _py_version

__title__ = "sans"
__author__ = "Zephyrkul"
__license__ = "MIT"
__copyright__ = "Copyright 2019-2019 Zephyrkul"

__version__ = "0.0.1a0"
version_info = _ST(__version__)

API_URL = ("https", "www.nationstates.net", "/cgi-bin/api.cgi")
LOCAL_URL = ("http", "localhost", "/cgi-bin/api.cgi")
AGENT_FMT = f"{{}} Python/{_py_version[0]}.{_py_version[1]} aiohttp/{_ah_version} sans/{__version__}".format
