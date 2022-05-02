from __future__ import print_function
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

import unittest
import nose.plugins.attrib as nose_attrib
import psysmon
import logging
import os
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_empty_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure
import psysmon.core.gui as psygui
import psysmon.gui.main.app as psy_app

@nose_attrib.attr('interactive')
class EventLooperNodeEditDlgTestCase(unittest.TestCase):
    """
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        cls.psybase = create_psybase()
        cls.project = create_empty_project(cls.psybase)
        print("In setUpClass...\n")


    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print("dropping database tables...\n")
        drop_project_database_tables(cls.project)
        print("removing temporary file structure....\n")
        remove_project_filestructure(cls.project)
        print("removing temporary base directory....\n")
        os.removedirs(cls.project.base_dir)
        print("....finished cleaning up.\n")


    def setUp(self):
        self.app = psy_app.PsysmonApp()

        nodeTemplate = self.psybase.packageMgr.getCollectionNodeTemplate('event looper')
        self.node = nodeTemplate()
        self.node.project = self.project

        # Create a logger for the node.
        loggerName = __name__+ "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)


    def tearDown(self):
        print("\n\nEs war sehr schoen - auf Wiederseh'n.\n")

    def testDlg(self):
        self.node.edit()
        self.app.MainLoop()


def suite():
    return unittest.makeSuite(EventLooperNodeEditDlgTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

