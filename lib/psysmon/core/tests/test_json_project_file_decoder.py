import unittest
import psysmon.core.project
import psysmon.core.preferences_manager
import psysmon.core.test_util as test_util
import shutil
import psysmon.core.util as util
import os
from obspy.core.utcdatetime import UTCDateTime

class ProjectFileDecoderTestCase(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        cls.packages_path = os.path.dirname(os.path.abspath(__file__))
        cls.packages_path = os.path.join(cls.packages_path, 'packages')

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.psybase = test_util.create_psybase(package_directory = [self.packages_path, ])
        self.db_project = test_util.create_dbtest_project(self.psybase)
        self.db_base_dir = self.db_project.base_dir
        self.db_user = self.db_project.activeUser

    def tearDown(self):
        test_util.drop_project_database_tables(self.db_project)
        shutil.rmtree(self.db_base_dir)
        del self.db_user
        del self.db_project
        del self.psybase


    def test_json_deserialization(self):
        '''
        '''
        # Set the maxDiff attribute to None to enable long output of 
        # non-equal strings tested with assertMultiLineEqual.
        self.maxDiff = None

        # Set the createTime of the project to a known value.
        self.db_project.createTime = UTCDateTime('2013-01-01T00:00:00')

        # Add an empty collection.
        self.db_project.createDirectoryStructure()
        self.db_project.addCollection('Test Collection')

        # Add a collection node to the collection.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('json plain testnode')
        self.db_project.addNode2Collection(node_template)

        # Add a collection node containing preferences.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('json preferences testnode')
        self.db_project.addNode2Collection(node_template)

        encoder = util.ProjectFileEncoder()
        decoder = util.ProjectFileDecoder()
        json_project = encoder.encode(self.db_project)
        project_obj = decoder.decode(json_project)

        self.assertIsInstance(project_obj, psysmon.core.project.Project)
        self.assertEqual(project_obj.name, 'Unit Test')
        self.assertEqual(project_obj.dbHost, 'localhost')
        self.assertIsInstance(project_obj.activeUser, psysmon.core.project.User)
        self.assertEqual(len(project_obj.user), 1)
        self.assertIsInstance(project_obj.user[0], psysmon.core.project.User)
        self.assertEqual(project_obj.activeUser.name, 'unit_test')
        self.assertEqual(project_obj.rid, 'smi:at.uot.stest/psysmon/unit_test')
        self.assertEqual(len(project_obj.activeUser.collection), 1)
        self.assertIsInstance(project_obj.activeUser.collection['Test Collection'], psysmon.core.base.Collection)
        collection = project_obj.activeUser.collection['Test Collection']
        self.assertEqual(len(collection.nodes), 2)
        self.assertEqual(collection.nodes[0].__class__.__name__, 'JsonPlainTestNode')
        self.assertEqual(collection.nodes[1].__class__.__name__, 'JsonPreferencesTestNode')
        c_node = collection.nodes[0]
        self.assertIsInstance(c_node.pref_manager, psysmon.core.preferences_manager.PreferencesManager)
        self.assertEqual(len(c_node.pref_manager.pages), 1)
        self.assertEqual(len(c_node.pref_manager.pages['preferences']), 0)
        c_node = collection.nodes[1]
        self.assertIsInstance(c_node.pref_manager, psysmon.core.preferences_manager.PreferencesManager)
        self.assertEqual(len(c_node.pref_manager.pages), 1)
        self.assertEqual(len(c_node.pref_manager.pages['preferences']), 6)



    def test_json_waveclient_deserialization(self):
        '''
        '''
        import psysmon.core.waveclient

        packages_path = os.path.dirname(os.path.abspath(__file__))
        packages_path = os.path.join(packages_path, 'waveclient_packages')
        psybase = test_util.create_psybase(package_directory = [packages_path, ])
        project = test_util.create_dbtest_project(psybase)
        project.createDatabaseStructure(psybase.packageMgr.packages)

        # Set the maxDiff attribute to None to enable long output of 
        # non-equal strings tested with assertMultiLineEqual.
        self.maxDiff = None

        # Set the createTime of the project to a known value.
        project.createTime = UTCDateTime('2013-01-01T00:00:00')

        # Add a waveclient to the project.
        waveclient = psysmon.core.waveclient.PsysmonDbWaveClient('db client', project)
        project.addWaveClient(waveclient)
        project.defaultWaveclient = 'db client'


        encoder = util.ProjectFileEncoder()
        decoder = util.ProjectFileDecoder()
        json_project = encoder.encode(project)
        project_obj = decoder.decode(json_project)

        # TODO: Test the project_obj for validity.
        print project_obj.waveclient['db client'].mode

        base_dir = project.base_dir
        test_util.drop_project_database_tables(project)
        shutil.rmtree(base_dir)

def suite():
    return unittest.makeSuite(ProjectFileDecoderTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')




