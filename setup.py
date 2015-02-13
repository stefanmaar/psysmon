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

# Define the package requirements.
requirements =[('mpl_toolkits.basemap', '1.0.7'),
               ('lxml', '2.3.2'),
               ('matplotlib', '1.4.0'),
               ('numpy', '1.9.1'),
               ('MySQLdb', '1.2.5'),
               ('obspy', '0.9.2'),
               ('pillow', '2.7.0'),
               ('cairo', '1.10.1'),
               ('Pyro4', '4.32'),
               ('scipy', '0.15.1'),
               ('sqlalchemy', '0.9.8'),
               ('wx', '3.0.0')]

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


requirements_fullfilled = True
for cur_name, cur_version in requirements:
    if not checkForPackage(cur_name, cur_version):
        requirements_fullfilled = False

if not requirements_fullfilled:
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
     )

