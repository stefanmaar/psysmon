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

__version__ = "0.0.2"
__author__ = "Stefan Mertl"
__authorEmail__ = "stefan@mertl-research.at"
__description__ = "A seismological data processing and prototyping software."
__longDescription__ = """pSysmon acts as a framework for developing and testing 
    of algorithms for seismological data processing. It can also be used for routine 
    data processing.
    """
__website__ = "http://psysmon.mertl-research.at"
__downloadUrl__ = "http://repo.or.cz/w/psysmon.git"
__license__ = "GNU General Public Licence version 3"
__keywords__ = "seismological prototyping prototype data processing earthquake obspy"

import logging
import wx
import os

logConfig = {}
logConfig['level'] = 'INFO'
logConfig['package_prefix'] = 'psysmon.packages'

doc_entry_point = os.path.join(os.path.dirname(__file__), 'doc')


class LoggingMainProcessFilter(logging.Filter):

    def filter(self, rec):
        return rec.processName == 'MainProcess'


class LoggingRedirectHandler(logging.Handler):
        def __init__(self, window):
            # run the regular Handler __init__
            logging.Handler.__init__(self)

            self.logArea = window

        def emit(self, record):
            msg = self.format(record)+'\n'
            wx.CallAfter(self.logArea.log, msg, record.levelname)
            #print "REDIRECT :: %s" % msg


def getLoggerHandler(mode='console', log_level = None):
    ch = logging.StreamHandler()
    if log_level is None:
        log_level = logConfig['level']
    ch.setLevel(log_level)
    formatter = logging.Formatter("#LOG# - %(asctime)s - %(process)d - %(levelname)s - %(name)s: %(message)s")
    ch.setFormatter(formatter)

    # Only log messages from the main process to the console.
    #ch.addFilter(LoggingMainProcessFilter())
    return ch


def getLoggerFileHandler(filename=None, log_level = None):
    if not filename:
        return

    if log_level is None:
        log_level = logConfig['level']

    ch = logging.FileHandler(filename)
    ch.setLevel(log_level)
    formatter = logging.Formatter("#LOG# - %(asctime)s - %(levelname)s - %(name)s: %(message)s")
    ch.setFormatter(formatter)

    return ch


def getLoggerWxRedirectHandler(window, log_level = None):
    ch = LoggingRedirectHandler(window)
    if log_level is None:
        log_level = logConfig['level']
    ch.setLevel(log_level)
    #formatter = logging.Formatter("#LOG# - %(asctime)s - %(process)d - %(levelname)s - %(name)s: %(message)s")
    formatter = logging.Formatter("%(asctime)s - %(process)d - %(name)s: %(message)s")
    ch.setFormatter(formatter)

    # Only log messages from the main process to the console.
    #ch.addFilter(LoggingMainProcessFilter())
    return ch





