'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon.core.test_util as test_util
import tempfile
import os
import shutil
from obspy.core.utcdatetime import UTCDateTime

class BaseTestCase(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"


    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"


    def setUp(self):
        base_path= os.path.dirname(os.path.abspath(__file__))
        packages_path = os.path.join(base_path, 'packages')
        self.psybase = test_util.create_psybase(package_directory = [packages_path,])
        self.base_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.base_dir)



    def test_create_project(self):
        ''' Test the creation of a new project.
        '''
        name = 'psy_unit_test'
        base_dir = self.base_dir
        db_host = 'localhost'
        user_name = 'unit_test'
        user_pwd = 'test'
        author_name = 'Stefan Test'
        author_uri = 'stest'
        agency_name = 'University of Test'
        agency_uri = 'at.uot'

        self.psybase.createPsysmonProject(name, base_dir, db_host, user_name, user_pwd, 
                                          author_name, author_uri, agency_name, agency_uri)

        test_util.drop_project_database_tables(self.psybase.project)
        test_util.remove_project_filestructure(self.psybase.project)
        self.psybase.closePsysmonProject()


    def test_load_project(self):
        ''' Test the creation and loading of a project.
        '''
        name = 'psy_unit_test'
        base_dir = self.base_dir
        db_host = 'localhost'
        user_name = 'unit_test'
        user_pwd = 'test'
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

        test_util.drop_project_database_tables(self.psybase.project)
        test_util.remove_project_filestructure(self.psybase.project)
        self.psybase.closePsysmonProject()

    def test_load_json_project(self):
        name = 'psy_unit_test'
        base_dir = self.base_dir
        db_host = 'localhost'
        user_name = 'unit_test'
        user_pwd = 'test'
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

        # Set the createTime of the project to a known value.
        self.psybase.project.createTime = UTCDateTime('2013-01-01T00:00:00')

        self.psybase.closePsysmonProject()

        self.psybase.load_json_project(project_file, user_name, user_pwd)

        #test_util.drop_project_database_tables(self.psybase.project)
        #test_util.remove_project_filestructure(self.psybase.project)
        self.psybase.closePsysmonProject()


def suite():
    return unittest.makeSuite(BaseTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

