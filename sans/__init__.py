# MIT License

# Copyright (c) 2018 - 2023

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys as _sys

from ._state import set_agent as set_agent
from .auth import *
from .client import *
from .errors import *
from .limiter import *
from .lock import *
from .response import *
from .url import *
from .utils import *

if _sys.version_info < (3, 8):
    from importlib_metadata import metadata as _metadata
else:
    from importlib.metadata import metadata as _metadata

__copyright__ = "Copyright 2019-2023 Zephyrkul"

_meta = _metadata(__name__)
__title__ = _meta["Name"]
__author__ = _meta["Author"]
__license__ = _meta["License"]
__version__ = _meta["Version"]

del _sys, _metadata, _meta  # not for export
