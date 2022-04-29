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
import psysmon.core.test_util as test_util
import psysmon.core.gui as psygui
import psysmon.gui.main.app as psy_app


@nose_attrib.attr('interactive')
class DataInventoryStatisticsDlgTestCase(unittest.TestCase):
    """

    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        cls.logger = logging.getLogger('psysmon')
        cls.logger.setLevel('DEBUG')
        cls.logger.addHandler(psysmon.getLoggerHandler())

        # Clean the unittest database.
        test_util.clean_unittest_database()

        # Create the test project.
        cls.psybase = test_util.create_psybase()
        cls.project = test_util.create_full_project(cls.psybase)


    @classmethod
    def tearDownClass(cls):
        test_util.drop_project_database_tables(cls.project)
        test_util.remove_project_filestructure(cls.project)
        os.removedirs(cls.project.base_dir)


    def setUp(self):
        self.app =psy_app.PsysmonApp()

        nodeTemplate = self.psybase.packageMgr.getCollectionNodeTemplate('data inventory statistics')
        self.node = nodeTemplate()
        self.node.project = self.project

        # Create a logger for the node.
        loggerName = __name__+ "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)


    def tearDown(self):
        pass

    def testDlg(self):
        self.node.execute()
        self.app.MainLoop()

#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(DataInventoryStatisticsDlgTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

