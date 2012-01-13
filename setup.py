#!/usr/bin/env python

# License
#     This file is part of Seismon.
#
#     If you use Seismon in any program or publication, please inform and
#     acknowledge its author Stefan Mertl (info@stefanmertl.com). 
# 
#     Seismon is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
The pSysmon setup script.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import sys
from distutils.core import setup
from setupExt import printStatus, printMessage, printLine, printRaw, \
    checkForNumpy, checkForMatplotlib, checkForBasemap

# Get the current pSysmon version, author and description.
for line in open('lib/psysmon/__init__.py').readlines():
    if (line.startswith('__version__') 
        or line.startswith('__author__') 
        or line.startswith('__authorEmail__') 
        or line.startswith('__description__') 
        or line.startswith('__downloadUrl__') 
        or line.startswith('__license__') 
        or line.startswith('__keywords__') 
        or line.startswith('__website__')):
        exec(line.strip())


# Define the packages to be processed.
packages = [
            'psysmon',
            'psysmon.core',
            'psysmon.packages',
            'psysmon.packages.geometry',
            'psysmon.packages.obspyImportWaveform',
            'psysmon.packages.selectWaveform',
            'psysmon.packages.tracedisplay'
           ]

# Let the user know what's going on.
printLine()
printRaw("BUILDING PSYSMON")
printStatus('pSysmon', __version__)
printStatus('python', sys.version)
printStatus('platform', sys.platform)
if sys.platform == 'win32':
    printStatus('Windows version', sys.getwindowsversion())

printRaw("")
printRaw("REQUIRED DEPENDENCIES")

# Checking for numpy
if not checkForNumpy():
    sys.exit(1)

# Checking for matplotlib
if not checkForMatplotlib('1.1.0'):
    sys.exit(1)

# Checking for basemap
if not checkForBasemap('1.0.2'):
    sys.exit(1)

printRaw("")
printRaw("")

setup(name = 'pSysmon',
      version = __version__,
      description = __description__,
      long_description = """
        pSysmon acts as a framework for developing and testing 
        of algorithms for seismological data processing. It can also be used for routine 
        data processing.
        """,
      author = __author__,
      author_email = __authorEmail__,
      url = __website__,
      download_url = __downloadUrl__,
      license = __license__,
      keywords = __keywords__,
      packages = packages,
      platforms = 'any',
      package_dir = {'': 'lib'}
      #requires = ['matplotlib (>=1.1.0)']
     )

