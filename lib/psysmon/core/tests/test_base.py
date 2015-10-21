'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon.core.test_util as test_util
import tempfile
import os
import shutil
import logging
import psysmon
from obspy.core.utcdatetime import UTCDateTime

class BaseTestCase(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler(log_level = 'DEBUG'))


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

        self.psybase.stop_project_server()
        test_util.drop_project_database_tables(self.psybase.project)
        test_util.remove_project_filestructure(self.psybase.project)
        self.psybase.closePsysmonProject()


def suite():
    return unittest.makeSuite(BaseTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

