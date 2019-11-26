from distutils.version import StrictVersion as _ST


__title__ = "sans"
__author__ = "Zephyrkul"
__license__ = "MIT"
__copyright__ = "Copyright 2019-2019 Zephyrkul"

version_info = _ST("0.0.1b6")
__version__ = str(version_info)

API_URL = ("https", "www.nationstates.net", "/cgi-bin/api.cgi")
DEFAULT_LOCAL_URL = ("http", "localhost:5557", "/")
