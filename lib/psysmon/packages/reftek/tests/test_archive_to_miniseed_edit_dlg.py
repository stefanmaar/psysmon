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


import matplotlib as mpl
mpl.rcParams['backend'] = 'WXAgg'

import unittest
import nose.plugins.attrib as nose_attrib
import psysmon
import logging
import os

import psysmon.core.gui as psygui
from psysmon.core.test_util import create_psybase
from obspy.core.utcdatetime import UTCDateTime


@nose_attrib.attr('interactive')
class ConvertArchiveToMiniseedEditDlgTestCase(unittest.TestCase):
    """
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        cls.psybase = create_psybase()


    @classmethod
    def tearDownClass(cls):
        print "stopping the project server..."
        cls.psybase.stop_project_server()
        print "...done.\n"


    def setUp(self):
        self.app = psygui.PSysmonApp()

        nodeTemplate = self.psybase.packageMgr.getCollectionNodeTemplate('reftek archive to miniseed')
        self.node = nodeTemplate()

        #self.node.pref_manager.set_value('start_time', UTCDateTime('2010-08-31T00:00:00'))
        #self.node.pref_manager.set_value('end_time', UTCDateTime('2010-09-01T00:00:00'))

        # Create a logger for the node.
        loggerName = __name__+ "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)


    def tearDown(self):
        pass


    def test_dialog(self):
        self.node.edit()
        self.app.MainLoop()


def suite():
    return unittest.makeSuite(ConvertArchiveToMiniseedEditDlgTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

