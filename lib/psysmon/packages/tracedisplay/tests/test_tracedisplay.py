'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon
import logging
import os
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure
from psysmon.core.test_util import clear_database_tables
import psysmon.core.gui as psygui


class TracedisplayTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        clear_database_tables(db_dialect = 'mysql',
                              db_driver = None,
                              db_host = 'localhost',
                              db_name = 'psysmon_unit_test',
                              db_user = 'unit_test',
                              db_pwd = 'test',
                              project_name = 'unit_test')
                              

        cls.psybase = create_psybase()
        create_full_project(cls.psybase)
        cls.project = cls.psybase.project
        cls.project.dbEngine.echo = True


    @classmethod
    def tearDownClass(cls):
        print "dropping database tables...\n"
        drop_project_database_tables(cls.project)
        print "removing temporary file structure....\n"
        remove_project_filestructure(cls.project)
        print "removing temporary base directory....\n"
        os.removedirs(cls.project.base_dir)
        print "....finished cleaning up.\n"


    def setUp(self):
        self.app =psygui.PSysmonApp()

        nodeTemplate = self.psybase.packageMgr.getCollectionNodeTemplate('tracedisplay')
        self.node = nodeTemplate()
        self.node.project = self.project

        # Create a logger for the node.
        loggerName = __name__+ "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)
        pass


    def tearDown(self):
        print "\n\nEs war sehr schoen - auf Wiederseh'n.\n"

    def testDlg(self):
        self.node.execute()
        self.app.MainLoop()
        pass


def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(TracedisplayTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

