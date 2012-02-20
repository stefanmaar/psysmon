# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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

__version__ = "0.1.0"
__author__ = "Stefan Mertl"
__authorEmail__ = "info@stefanmertl.com"
__description__ = "A seismological data processing and prototyping software."
__longDescription__ = """pSysmon acts as a framework for developing and testing 
    of algorithms for seismological data processing. It can also be used for routine 
    data processing.
    """
__website__ = "http://www.stefanmertl.com/science/"
__downloadUrl__ = "http://repo.or.cz/w/psysmon.git"
__license__ = "GNU General Public Licence version 3"
__keywords__ = "seismological prototyping prototype data processing earthquake"


import logging

logConfig = {}
logConfig['level'] = 'DEBUG'

def getLoggerHandler(mode='console'):
    ch = logging.StreamHandler()
    ch.setLevel(logConfig['level'])
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    return ch

