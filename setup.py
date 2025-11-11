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

# Add the directory of setup.py to the path to find setupExt.py.
sys.path.append(os.path.join(os.path.dirname(__file__)))
from setupExt import printStatus, printMessage, printLine, printRaw, \
    checkForPackage, get_data_files


# Check the environment variables for the headless option.
# Install psysmon in development mode without GUI support using the command "psysmon_headless=1 pip install -e ./psysmon"
#headless = False
#headless_var = os.environ.get("psysmon_headless", None)
#printRaw("headless_var: ")
#printRaw(headless_var)
#if headless_var is not None and (int(headless_var) == 1):
#    printMessage("Installing in headless mode.")
#    headless = True

                              
# Check for mandatory modules.
#try:
#    import numpy  # @UnusedImport # NOQA
#except ImportError:
#    printLine()
#    printRaw("MISSING REQUIREMENT")
#    printStatus('numpy', 'Missing module')
#    printMessage('Numpy is needed to run the psysmon setup script. Please install it first.')
#    raise ImportError('Numpy is needed to run the psysmon setup script. Please install it first.')


#if not headless:
#    wx_required_version = '4.0.6'
#    try:
#        import wx
#        if parse_version(wx.__version__) < parse_version(wx_required_version):
#            printRaw("MISSING REQUIREMENT")
#            printStatus('wxPython', 'Missing module')
#            printMessage('You have to install wxPxthon >= ' + wx_required_version)
#            sys.exit(1)
#    except ImportError:
#        printRaw("MISSING REQUIREMENT")
#        printStatus('wxPython', 'Missing module')
#        printMessage('You have to install wxPxthon >= ' + wx_required_version)
#        printMessage('See https://www.wxpython.org/pages/downloads/ how to install it using a Wheel package.')
#        raise ImportError('Missing wxPython module.')


#import os
#import glob
#import inspect
#import distutil
#import setuptools
#from numpy.distutils.core import setup
#from numpy.distutils.misc_util import Configuration


# Define the scripts to be processed.
# TODO: Scan the scripts folder of all packages.
#scripts = ['scripts/psysmon',
#           'scripts/psysmomat']

# Define some package data.
#package_dir = {'': 'lib',
#               'psysmon.artwork': 'lib/psysmon/artwork'}
package_data = {'psysmon.artwork': ['splash/psysmon.png']}

# Add the documentation data files.
data_files = get_data_files(os.path.join(os.getcwd(), 'doc/user_doc/build/html/'),
                            target_dir = 'psysmon/doc',
                            exclude_dirs = ['_sources'])
data_files = []


# Define additinal files to be copied.
#dataFiles = ('artwork', ['lib/psysmon/artwork/splash/splash.png'])


# Let the user know what's going on.
#printLine()
#printRaw("BUILDING PSYSMON")
#printStatus('pSysmon', __version__)
#printStatus('python', sys.version)
#printStatus('platform', sys.platform)
#if sys.platform == 'win32':
#    printStatus('Windows version', sys.getwindowsversion())

#printRaw("")
#printRaw("REQUIRED DEPENDENCIES")
#printStatus("Headless", headless)


#requirements_fullfilled = True
#for cur_name, cur_version in requirements:
#    if not checkForPackage(cur_name, cur_version):
#        requirements_fullfilled = False
#
#if not requirements_fullfilled:
#    sys.exit(1)


#printRaw("")
#printRaw("")

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
    printRaw(files)
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
    printRaw(files)
    cur_ext = Extension(get_lib_name('detect_sta_lta'),
                        sources = files)
    ext_list.append(cur_ext)

    return ext_list


setup(package_data = package_data,
      ext_package = 'psysmon.lib',
      ext_modules = create_ext_modules()
      )
