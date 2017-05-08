# -*- coding: utf-8 -*-
"""
Platform independent terminal interface module.

It imports the appropriate operating system specific implementation.
"""
#
# (C) Pywikibot team, 2003-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id: 9a5fbf18b0dbd661c43e226cfe0d67e0cf1e8e3f $'

import sys

if sys.platform == 'win32':
    from .terminal_interface_win32 import Win32UI as UI
else:
    from .terminal_interface_unix import UnixUI as UI

__all__ = ('UI',)
