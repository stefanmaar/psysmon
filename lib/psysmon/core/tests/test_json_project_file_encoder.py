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
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": "main client", 
    "name": "Unit Test", 
    "pkg_version": {
        "events": "0.0.1", 
        "example": "0.1.1", 
        "example 2": "0.1.1", 
        "geometry": "0.1.1", 
        "obspyImportWaveform": "0.1.1", 
        "test_package_1": "0.1.1", 
        "tracedisplay": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
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
    "waveclient": []
}'''

        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)

        # Test project with empty collection
        self.db_project.createDirectoryStructure()
        self.db_project.addCollection('Test Collection')
        expected_result = '''{
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": "main client", 
    "name": "Unit Test", 
    "pkg_version": {
        "events": "0.0.1", 
        "example": "0.1.1", 
        "example 2": "0.1.1", 
        "geometry": "0.1.1", 
        "obspyImportWaveform": "0.1.1", 
        "test_package_1": "0.1.1", 
        "tracedisplay": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": "Test Collection", 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {
                "Test Collection": {
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
    "waveclient": []
}'''
        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)


        # Test project with a collection with one collection node.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('json plain testnode')
        self.db_project.addNode2Collection(node_template)
        expected_result = '''{
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": "main client", 
    "name": "Unit Test", 
    "pkg_version": {
        "events": "0.0.1", 
        "example": "0.1.1", 
        "example 2": "0.1.1", 
        "geometry": "0.1.1", 
        "obspyImportWaveform": "0.1.1", 
        "test_package_1": "0.1.1", 
        "tracedisplay": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": "Test Collection", 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {
                "Test Collection": {
                    "__class__": "Collection", 
                    "__module__": "psysmon.core.base", 
                    "name": "Test Collection", 
                    "nodes": [
                        {
                            "__class__": "JsonPlainTestNode", 
                            "__module__": "test_package.test_node", 
                            "class": "JsonPlainTestNode", 
                            "enabled": true, 
                            "module": "test_package.test_node", 
                            "name": "json plain testnode", 
                            "parentPackage": null, 
                            "pref_manager": {
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
    "waveclient": []
}'''
        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)

        # Test project with a collection with two collection nodes 
        # and one of them containing preferences in the pref_manager.
        node_template = self.psybase.packageMgr.getCollectionNodeTemplate('json preferences testnode')
        self.db_project.addNode2Collection(node_template)
        expected_result = '''{
    "__class__": "Project", 
    "__module__": "psysmon.core.project", 
    "createTime": {
        "__class__": "UTCDateTime", 
        "__module__": "obspy.core.utcdatetime", 
        "utcdatetime": "2013-01-01T00:00:00"
    }, 
    "dbDialect": "mysql", 
    "dbDriver": null, 
    "dbHost": "localhost", 
    "dbName": "psysmon_unit_test", 
    "db_version": {}, 
    "defaultWaveclient": "main client", 
    "name": "Unit Test", 
    "pkg_version": {
        "events": "0.0.1", 
        "example": "0.1.1", 
        "example 2": "0.1.1", 
        "geometry": "0.1.1", 
        "obspyImportWaveform": "0.1.1", 
        "test_package_1": "0.1.1", 
        "tracedisplay": "0.1.1"
    }, 
    "scnlDataSources": {}, 
    "user": [
        {
            "__class__": "User", 
            "__module__": "psysmon.core.project", 
            "activeCollection": "Test Collection", 
            "agency_name": "University of Test", 
            "agency_uri": "at.uot", 
            "author_name": "Stefan Test", 
            "author_uri": "stest", 
            "collection": {
                "Test Collection": {
                    "__class__": "Collection", 
                    "__module__": "psysmon.core.base", 
                    "name": "Test Collection", 
                    "nodes": [
                        {
                            "__class__": "JsonPlainTestNode", 
                            "__module__": "test_package.test_node", 
                            "class": "JsonPlainTestNode", 
                            "enabled": true, 
                            "module": "test_package.test_node", 
                            "name": "json plain testnode", 
                            "parentPackage": null, 
                            "pref_manager": {
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
                            "__class__": "JsonPreferencesTestNode", 
                            "__module__": "test_package.test_node", 
                            "class": "JsonPreferencesTestNode", 
                            "enabled": true, 
                            "module": "test_package.test_node", 
                            "name": "json preferences testnode", 
                            "parentPackage": null, 
                            "pref_manager": {
                                "__class__": "PreferencesManager", 
                                "__module__": "psysmon.core.preferences_manager", 
                                "pages": {
                                    "preferences": [
                                        {
                                            "__class__": "TextEditPrefItem", 
                                            "__module__": "psysmon.core.preferences_manager", 
                                            "class": "TextEditPrefItem", 
                                            "default": "test filter", 
                                            "group": null, 
                                            "gui_element": [], 
                                            "guiclass": {
                                                "ERROR": "MISSING CONVERTER", 
                                                "__class__": "type", 
                                                "__module__": "psysmon.core.guiBricks"
                                            }, 
                                            "label": "filter name", 
                                            "limit": null, 
                                            "mode": "textedit", 
                                            "module": "psysmon.core.preferences_manager", 
                                            "name": "filter_name", 
                                            "value": "test filter"
                                        }, 
                                        {
                                            "__class__": "DirBrowsePrefItem", 
                                            "__module__": "psysmon.core.preferences_manager", 
                                            "class": "DirBrowsePrefItem", 
                                            "default": "", 
                                            "group": null, 
                                            "gui_element": [], 
                                            "guiclass": {
                                                "ERROR": "MISSING CONVERTER", 
                                                "__class__": "type", 
                                                "__module__": "psysmon.core.guiBricks"
                                            }, 
                                            "label": "browse", 
                                            "limit": null, 
                                            "mode": "dirbrowse", 
                                            "module": "psysmon.core.preferences_manager", 
                                            "name": "directory_browse", 
                                            "start_directory": "/home", 
                                            "value": ""
                                        }, 
                                        {
                                            "__class__": "FloatSpinPrefItem", 
                                            "__module__": "psysmon.core.preferences_manager", 
                                            "class": "FloatSpinPrefItem", 
                                            "default": "4.5", 
                                            "digits": 3, 
                                            "group": null, 
                                            "gui_element": [], 
                                            "guiclass": {
                                                "ERROR": "MISSING CONVERTER", 
                                                "__class__": "type", 
                                                "__module__": "psysmon.core.guiBricks"
                                            }, 
                                            "increment": 0.1, 
                                            "label": "filter cutoff", 
                                            "limit": null, 
                                            "mode": "float_spin", 
                                            "module": "psysmon.core.preferences_manager", 
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
    "waveclient": []
}'''
        self.assertMultiLineEqual(encoder.encode(self.db_project), expected_result)


def suite():
    return unittest.makeSuite(ProjectFileEncoderTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')




