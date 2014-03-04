'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon.core.test_util as test_util
import shutil
import psysmon.core.util as util
import os
from obspy.core.utcdatetime import UTCDateTime

class ProjectFileEncoderTestCase(unittest.TestCase):
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


    def test_default(self):
        '''
        '''
        encoder = util.ProjectFileEncoder()
        d = encoder.default(self.db_project)
        print d


    def test_json_serialization(self):
        '''
        '''
        # Set the maxDiff attribute to None to enable long output of 
        # non-equal strings tested with assertMultiLineEqual.
        self.maxDiff = None

        # Set the createTime of the project to a known value.
        self.db_project.createTime = UTCDateTime('2013-01-01T00:00:00')

        encoder = util.ProjectFileEncoder()

        # Test empty project.
        expected_result = '''{
    "__baseclass__": [], 
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__baseclass__": [
            "object"
        ], 
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": null, 
    "name": "Unit Test", 
    "pkg_version": {
        "test_package_1": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__baseclass__": [], 
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": null, 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {}, 
            "mode": "admin", 
            "name": "unit_test"
        }
    ], 
    "waveclient": {}
}'''

        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)

        # Test project with empty collection
        self.db_project.createDirectoryStructure()
        self.db_project.addCollection('Test Collection')
        expected_result = '''{
    "__baseclass__": [], 
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__baseclass__": [
            "object"
        ], 
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": null, 
    "name": "Unit Test", 
    "pkg_version": {
        "test_package_1": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__baseclass__": [], 
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": "Test Collection", 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {
                "Test Collection": {
                    "__baseclass__": [], 
                    "__class__": "Collection", 
                    "__module__": "psysmon.core.base", 
                    "name": "Test Collection", 
                    "nodes": []
                }
            }, 
            "mode": "admin", 
            "name": "unit_test"
        }
    ], 
    "waveclient": {}
}'''
        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)


        # Test project with a collection with one collection node.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('json plain testnode')
        self.db_project.addNode2Collection(node_template)
        expected_result = '''{
    "__baseclass__": [], 
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__baseclass__": [
            "object"
        ], 
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": null, 
    "name": "Unit Test", 
    "pkg_version": {
        "test_package_1": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__baseclass__": [], 
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": "Test Collection", 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {
                "Test Collection": {
                    "__baseclass__": [], 
                    "__class__": "Collection", 
                    "__module__": "psysmon.core.base", 
                    "name": "Test Collection", 
                    "nodes": [
                        {
                            "__baseclass__": [
                                "CollectionNode"
                            ], 
                            "__class__": "JsonPlainTestNode", 
                            "__module__": "test_package.test_node", 
                            "enabled": true, 
                            "pref_manager": {
                                "__baseclass__": [], 
                                "__class__": "PreferencesManager", 
                                "__module__": "psysmon.core.preferences_manager", 
                                "pages": {
                                    "preferences": []
                                }
                            }, 
                            "provides": null, 
                            "requires": null
                        }
                    ]
                }
            }, 
            "mode": "admin", 
            "name": "unit_test"
        }
    ], 
    "waveclient": {}
}'''
        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)

        # Test project with a collection with two collection nodes 
        # and one of them containing preferences in the pref_manager.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('json preferences testnode')
        self.db_project.addNode2Collection(node_template)
        expected_result = '''{
    "__baseclass__": [], 
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__baseclass__": [
            "object"
        ], 
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": null, 
    "name": "Unit Test", 
    "pkg_version": {
        "test_package_1": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__baseclass__": [], 
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": "Test Collection", 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {
                "Test Collection": {
                    "__baseclass__": [], 
                    "__class__": "Collection", 
                    "__module__": "psysmon.core.base", 
                    "name": "Test Collection", 
                    "nodes": [
                        {
                            "__baseclass__": [
                                "CollectionNode"
                            ], 
                            "__class__": "JsonPlainTestNode", 
                            "__module__": "test_package.test_node", 
                            "enabled": true, 
                            "pref_manager": {
                                "__baseclass__": [], 
                                "__class__": "PreferencesManager", 
                                "__module__": "psysmon.core.preferences_manager", 
                                "pages": {
                                    "preferences": []
                                }
                            }, 
                            "provides": null, 
                            "requires": null
                        }, 
                        {
                            "__baseclass__": [
                                "CollectionNode"
                            ], 
                            "__class__": "JsonPreferencesTestNode", 
                            "__module__": "test_package.test_node", 
                            "enabled": true, 
                            "pref_manager": {
                                "__baseclass__": [], 
                                "__class__": "PreferencesManager", 
                                "__module__": "psysmon.core.preferences_manager", 
                                "pages": {
                                    "preferences": [
                                        {
                                            "__baseclass__": [
                                                "PreferenceItem"
                                            ], 
                                            "__class__": "TextEditPrefItem", 
                                            "__module__": "psysmon.core.preferences_manager", 
                                            "default": "test filter", 
                                            "group": null, 
                                            "gui_element": [], 
                                            "guiclass": {
                                                "ERROR": "MISSING CONVERTER", 
                                                "__baseclass__": [
                                                    "object"
                                                ], 
                                                "__class__": "type", 
                                                "__module__": "psysmon.core.guiBricks"
                                            }, 
                                            "label": "filter name", 
                                            "limit": null, 
                                            "name": "filter_name", 
                                            "value": "test filter"
                                        }, 
                                        {
                                            "__baseclass__": [
                                                "PreferenceItem"
                                            ], 
                                            "__class__": "DirBrowsePrefItem", 
                                            "__module__": "psysmon.core.preferences_manager", 
                                            "default": "", 
                                            "group": null, 
                                            "gui_element": [], 
                                            "guiclass": {
                                                "ERROR": "MISSING CONVERTER", 
                                                "__baseclass__": [
                                                    "object"
                                                ], 
                                                "__class__": "type", 
                                                "__module__": "psysmon.core.guiBricks"
                                            }, 
                                            "label": "browse", 
                                            "limit": null, 
                                            "name": "directory_browse", 
                                            "start_directory": "/home", 
                                            "value": ""
                                        }, 
                                        {
                                            "__baseclass__": [
                                                "PreferenceItem"
                                            ], 
                                            "__class__": "FloatSpinPrefItem", 
                                            "__module__": "psysmon.core.preferences_manager", 
                                            "default": "4.5", 
                                            "digits": 3, 
                                            "group": null, 
                                            "gui_element": [], 
                                            "guiclass": {
                                                "ERROR": "MISSING CONVERTER", 
                                                "__baseclass__": [
                                                    "object"
                                                ], 
                                                "__class__": "type", 
                                                "__module__": "psysmon.core.guiBricks"
                                            }, 
                                            "increment": 0.1, 
                                            "label": "filter cutoff", 
                                            "limit": null, 
                                            "name": "filter_cutoff", 
                                            "value": "4.5"
                                        }
                                    ]
                                }
                            }, 
                            "provides": null, 
                            "requires": null
                        }
                    ]
                }
            }, 
            "mode": "admin", 
            "name": "unit_test"
        }
    ], 
    "waveclient": {}
}'''
        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)


    def test_json_waveclient_serialization(self):
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

        # Test empty project.
        expected_result = '''{
    "__baseclass__": [], 
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__baseclass__": [
            "object"
        ], 
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {
        "geometry": "0.1.1", 
        "obspyImportWaveform": "0.1.1"
    }, 
    "defaultWaveclient": "db client", 
    "name": "Unit Test", 
    "pkg_version": {
        "geometry": "0.1.1", 
        "obspyImportWaveform": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__baseclass__": [], 
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": null, 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {}, 
            "mode": "admin", 
            "name": "unit_test"
        }
    ], 
    "waveclient": {
        "db client": {
            "__baseclass__": [
                "WaveClient"
            ], 
            "__class__": "PsysmonDbWaveClient", 
            "__module__": "psysmon.core.waveclient", 
            "mode": "psysmonDb", 
            "name": "db client", 
            "options": {}, 
            "stock_window": 3600
        }
    }
}'''

        self.assertMultiLineEqual(encoder.encode(project), expected_result)

        base_dir = project.base_dir
        test_util.drop_project_database_tables(project)
        shutil.rmtree(base_dir)

def suite():
    return unittest.makeSuite(ProjectFileEncoderTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')




