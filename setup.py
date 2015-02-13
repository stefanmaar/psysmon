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

import sys
from distutils.core import setup
from setupExt import printStatus, printMessage, printLine, printRaw, \
    checkForPackage

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
            'psysmon.packages.example',
            'psysmon.packages.example2',
            'psysmon.packages.geometry',
            'psysmon.packages.obspyImportWaveform',
            'psysmon.packages.tracedisplay',
            'psysmon.artwork',
            'psysmon.artwork.icons'
           ]

# Define the scripts to be processed.
scripts = ['scripts/psysmon']

# Define some package data.
packageDir = {'': 'lib',
              'psysmon.artwork': 'lib/psysmon/artwork'}
packageData = {'psysmon.artwork': ['splash/psysmon.png']}

# Define additinal files to be copied.
#dataFiles = ('artwork', ['lib/psysmon/artwork/splash/splash.png'])

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

# Checking for basemap
if not checkForPackage('mpl_toolkits.basemap', '1.0.7'):
    sys.exit(1)

# Checking for lxml
if not checkForPackage('lxml', '2.3.2'):
    sys.exit(1)

# Checking for matplotlib
if not checkForPackage('matplotlib', '1.4.0'):
    sys.exit(1)

# Checking for numpy
if not checkForPackage('numpy', '1.9.1'):
    sys.exit(1)

# Checking for mysql-python
if not checkForPackage('MySQLdb', '1.2.5'):
    sys.exit(1)

# Checking for obspy.core
if not checkForPackage('obspy', '0.9.2'):
    sys.exit(1)

# Checking for PIL
if not checkForPackage('pillow', '2.7.0'):
    sys.exit(1)

# Checking for py2cairo
if not checkForPackage('cairo', '1.10.1'):
    sys.exit(1)

# Checking for Pyro4
if not checkForPackage('Pyro4', '4.32'):
    sys.exit(1)

# Checking for scipy
if not checkForPackage('scipy', '0.15.1'):
    sys.exit(1)

# Checking for sqlAlchemy
if not checkForPackage('sqlalchemy', '0.9.8'):
    sys.exit(1)

# Checking for wx
if not checkForPackage('wx', '3.0.0'):
    sys.exit(1)



printRaw("")
printRaw("")

setup(name = 'psysmon',
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
      scripts = scripts,
      package_dir = packageDir,
      package_data = packageData
      #data_files = dataFiles
      #requires = ['matplotlib (>=1.1.0)']
     )

