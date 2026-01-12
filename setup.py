#!/usr/bin/env python

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
The pSysmon setup script.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''
import inspect
import os
import sys

from setuptools import setup, Extension

# Add the C source to be built.
setup_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
root_dir = os.path.join('lib', 'psysmon')

core_path = os.path.join(setup_dir, 'lib', 'psysmon', 'core')
sys.path.insert(0, core_path)
from clib_util import get_lib_name  # @UnresolvedImport
sys.path.pop(0)


def create_ext_modules():
    '''

    '''
    ext_list = []
    
    # LIBSIGNAL
    path = os.path.join(root_dir, 'core', 'src')
    files = [os.path.join(path, 'moving_average.c'), ]
    cur_ext = Extension(name = get_lib_name('signal'),
                        sources = files)
    ext_list.append(cur_ext)

    # LIBRT130
    #path = os.path.join(root_dir, 'packages', 'reftek', 'src')
    #files = [os.path.join(path, 'rt_130wrapper_py.c'),
    #         os.path.join(path, 'rt_130_py.c')]
    #printRaw(files)
    #config.add_extension('rt_130_py',
    #                     sources = files)

    # LIBDETECT
    path = os.path.join(root_dir, 'packages', 'event', 'src')
    files = [os.path.join(path, 'detect_sta_lta.c')]
    cur_ext = Extension(get_lib_name('detect_sta_lta'),
                        sources = files)
    ext_list.append(cur_ext)

    return ext_list


setup(ext_package = "psysmon.lib",
      ext_modules = create_ext_modules())
