from distutils.version import StrictVersion as _ST


__title__ = "sans"
__author__ = "Zephyrkul"
__license__ = "MIT"
__copyright__ = "Copyright 2019-2019 Zephyrkul"

__version__ = "0.0.1a1"
version_info = _ST(__version__)

API_URL = ("https", "www.nationstates.net", "/cgi-bin/api.cgi")
DEFAULT_LOCAL_URL = ("http", "localhost:5557", "/")
