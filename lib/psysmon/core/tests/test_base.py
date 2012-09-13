'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import clear_project_filestructure
from psysmon.core.test_util import clear_project_database
import tempfile
import os

class ProjectTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"
        cls.psybase = create_psybase()
        cls.base_dir = tempfile.mkdtemp()


    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"
        #os.removedir(cls.base_dir)


    def setUp(self):
        pass

    def tearDown(self):
        pass



    def test_create_project(self):
        ''' Test the creation of a new project.
        '''
        name = 'psy_unit_test'
        base_dir = self.base_dir
        db_host = 'localhost'
        user_name = 'unit_test'
        user_pwd = ''
        author_name = 'Stefan Test'
        author_uri = 'stest'
        agency_name = 'University of Test'
        agency_uri = 'at.uot'

        self.psybase.createPsysmonProject(name, base_dir, db_host, user_name, user_pwd, 
                                          author_name, author_uri, agency_name, agency_uri)

        clear_project_database(self.psybase.project)
        clear_project_filestructure(self.psybase.project)
        self.psybase.closePsysmonProject()


    def test_load_project(self):
        ''' Test the creation and loading of a project.
        '''
        name = 'psy_unit_test'
        base_dir = self.base_dir
        db_host = 'localhost'
        user_name = 'unit_test'
        user_pwd = ''
        author_name = 'Stefan Test'
        author_uri = 'stest'
        agency_name = 'University of Test'
        agency_uri = 'at.uot'

        self.psybase.createPsysmonProject(name, base_dir, db_host, user_name, user_pwd, 
                                          author_name, author_uri, agency_name, agency_uri)

        project_file = os.path.join(self.psybase.project.projectDir, 
                                    self.psybase.project.projectFile)
        user_name = self.psybase.project.activeUser.name
        user_pwd = self.psybase.project.activeUser.pwd

        self.psybase.closePsysmonProject()

        self.psybase.loadPsysmonProject(project_file, user_name, user_pwd)

        clear_project_database(self.psybase.project)
        clear_project_filestructure(self.psybase.project)
        self.psybase.closePsysmonProject()







def suite():
    return unittest.makeSuite(ProjectTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

