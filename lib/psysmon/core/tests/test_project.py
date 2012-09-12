'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.core.project import Project, User
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_dbtest_project
import os
import tempfile

class ProjectTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"
        cls.psybase = create_psybase()
        cls.db_project = create_dbtest_project(cls.psybase)
        cls.base_dir = tempfile.mkdtemp()


    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"
        os.removedirs(cls.base_dir)


    def setUp(self):
        print "Preparing the user and the project.\n"
        self.user = User(user_name = 'test_user',
                         user_pwd = '',
                         user_mode = 'admin',
                         author_name = 'Stefan Test',
                         author_uri = 'stest',
                         agency_name = 'University of Test',
                         agency_uri = 'at.uot'
                        )


    def tearDown(self):
        pass


    def test_rid(self):
        ''' Test the resource identifier.
        '''
        project = Project(psybase = self.psybase,
                          name = 'Test Project',
                          base_dir = self.base_dir,
                          user = self.user
                         )

        self.assertEquals(project.rid, 'smi:at.uot.stest/psysmon/test_project')


    def test_database_connection(self):
        ''' Test the connection to the database.
        '''
        self.db_project.connect2Db()
        self.assertEquals(str(self.db_project.dbEngine), 'Engine(mysql://unit_test@localhost/psysmon_unit_test)')



def suite():
    return unittest.makeSuite(ProjectTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

