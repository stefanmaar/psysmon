# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
CTypes support for the libsignal C library.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''
from __future__ import absolute_import

import ctypes
from . import clib_util
import numpy as np

# Import the signal C library.
clib_signal = clib_util.load_cdll('signal')

# Define the moving_average types.
clib_signal.moving_average.argtypes = [ctypes.c_int,
                                       ctypes.c_int,
                                       np.ctypeslib.ndpointer(dtype = np.float64,
                                                              ndim=1,
                                                              flags='C_CONTIGUOUS'),
                                       np.ctypeslib.ndpointer(dtype = np.float64,
                                                              ndim=1,
                                                              flags='C_CONTIGUOUS')]
