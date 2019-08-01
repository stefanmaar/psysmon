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
Utilities to handle external C libraries.

This module uses code from the obspy package.

:copyright:
    Stefan Mertl
    The ObsPy Development Team (devs@obspy.org)

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

from builtins import str
import os
import re
import platform
import ctypes
import distutils.sysconfig as sysconfig
import warnings


def cleanse_pymodule_filename(filename):
    """
    Replace all characters not allowed in Python module names in filename with
    "_".

    See bug report:
     - http://stackoverflow.com/questions/21853678/install-obspy-in-cygwin
     - See #755

    See also:
     - http://stackoverflow.com/questions/7552311/
     - http://docs.python.org/2/reference/lexical_analysis.html#identifiers

    >>> print(cleanse_pymodule_filename("0blup-bli.554_3!32"))
    _blup_bli_554_3_32
    """
    filename = re.sub(r'^[^a-zA-Z_]', "_", filename)
    filename = re.sub(r'[^a-zA-Z0-9_]', "_", filename)
    return filename


def get_lib_name(name, add_extension_suffix = False):
    """
    Helper function to get an architecture and Python version specific library
    filename.
    """
    # our custom defined part of the extension file name
    libname = "lib%s_%s_%s_py%s" % (
        name, platform.system(), platform.architecture()[0],
        ''.join([str(i) for i in platform.python_version_tuple()[:2]]))

    libname = cleanse_pymodule_filename(libname)

    if add_extension_suffix:
        # append any extension suffix defined by Python for current platform
        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        # in principle "EXT_SUFFIX" is what we want.
        # "SO" seems to be deprecated on newer python
        # but: older python seems to have empty "EXT_SUFFIX", so we fall back
        if not ext_suffix:
            try:
                ext_suffix = sysconfig.get_config_var("SO")
            except Exception as e:
                msg = ("Empty 'EXT_SUFFIX' encountered while building CDLL "
                       "filename and fallback to 'SO' variable failed "
                       "(%s)." % str(e))
                warnings.warn(msg)
                pass
        if ext_suffix:
            libname = libname + ext_suffix

    return libname


def load_cdll(name):
    """
    Helper function to load a shared library built during pSysmon installation
    with ctypes.

    :type name: str
    :param name: Name of the library to load (e.g. 'mseed').
    :rtype: :class:`ctypes.CDLL`
    """
    # our custom defined part of the extension file name
    libname = get_lib_name(name, add_extension_suffix = True)
    libdir = os.path.join(os.path.dirname(__file__), os.pardir, 'lib')
    libpath = os.path.join(libdir, libname)
    try:
        cdll = ctypes.CDLL(libpath)
    except Exception as e:
        msg = 'Could not load shared library "%s".\n\n %s' % (libname, str(e))
        raise ImportError(msg)
    return cdll



