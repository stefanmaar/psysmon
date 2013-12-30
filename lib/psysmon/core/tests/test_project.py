'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.core.project import Project, User
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_dbtest_project
import os
import shutil
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
        cls.db_user = cls.db_project.activeUser
        cls.db_base_dir = cls.db_project.base_dir


    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"
        shutil.rmtree(cls.db_base_dir)


    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_rid(self):
        ''' Test the resource identifier.
        '''
        project = Project(psybase = self.psybase,
                          name = 'Test Project',
                          base_dir = self.db_base_dir,
                          user = self.db_user
                         )

        self.assertEquals(project.rid, 'smi:at.uot.stest/psysmon/test_project')


    def test_database_connection(self):
        ''' Test the connection to the database.
        '''
        self.db_project.connect2Db()
        self.assertEquals(str(self.db_project.dbEngine), 'Engine(mysql://unit_test:test@localhost/psysmon_unit_test)')


    def test_create_directory_structure(self):
        ''' Test the creation of the directory structure of the project.
        '''
        project = Project(psybase = self.psybase,
                          name = 'My Test Project',
                          base_dir = self.db_base_dir,
                          user = self.db_user
                         )
        project.createDirectoryStructure()
        self.assertEquals(project.projectDir, os.path.join(self.db_base_dir, 'my_test_project'))
        self.assertTrue(os.path.isdir(project.projectDir))
        self.assertTrue(os.path.isdir(os.path.join(project.projectDir, 'data')))
        self.assertTrue(os.path.isdir(os.path.join(project.projectDir, 'tmp')))

        # Remove the directory structure.
        shutil.rmtree(project.projectDir)




def suite():
    return unittest.makeSuite(ProjectTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

