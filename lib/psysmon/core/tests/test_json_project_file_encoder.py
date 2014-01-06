'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon.core.test_util as test_util
import shutil
import psysmon.core.util as util

class ProjectFileEncoderTestCase(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.psybase = test_util.create_psybase()
        self.db_project = test_util.create_dbtest_project(self.psybase)
        self.db_base_dir = self.db_project.base_dir
        self.db_user = self.db_project.activeUser

    def tearDown(self):
        test_util.drop_project_database_tables(self.db_project)
        shutil.rmtree(self.db_base_dir)
        del self.db_user
        del self.db_project
        del self.psybase


    def test_default(self):
        '''
        '''
        encoder = util.ProjectFileEncoder()
        d = encoder.default(self.db_project)
        print d


    def test_json_serialization(self):
        '''
        '''
        encoder = util.ProjectFileEncoder()

        # Test empty project.
        print encoder.encode(self.db_project)

        # Test project with empty collection
        self.db_project.createDirectoryStructure()
        self.db_project.addCollection('Test Collection')
        print encoder.encode(self.db_project)

        # Test project with a collection with one collection node.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('example node')
        self.db_project.addNode2Collection(node_template)
        print encoder.encode(self.db_project)

        # Test project with a collection with two collection nodes 
        # and one of them containing preferences in the pref_manager.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('tracedisplay')
        self.db_project.addNode2Collection(node_template)
        print encoder.encode(self.db_project)


def suite():
    return unittest.makeSuite(ProjectFileEncoderTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

