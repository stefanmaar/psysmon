'''
Created on May 17, 2011

@author: Stefan Mertl
'''
from __future__ import print_function

import unittest
import logging
import psysmon.core.project
import psysmon.core.test_util as test_util
import os
import shutil
from obspy.core.utcdatetime import UTCDateTime

class ProjectTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        base_path= os.path.dirname(os.path.abspath(__file__))
        packages_path = os.path.join(base_path, 'packages')
        self.psybase = test_util.create_psybase(package_directory = [packages_path,])
        self.db_project = test_util.create_dbtest_project(self.psybase)
        self.db_base_dir = self.db_project.base_dir
        self.db_user = self.db_project.activeUser

    def tearDown(self):
        self.psybase.stop_project_server()
        test_util.drop_project_database_tables(self.db_project)
        shutil.rmtree(self.db_base_dir)
        del self.db_user
        del self.db_project
        del self.psybase


    def test_rid(self):
        ''' Test the resource identifier.
        '''
        project = psysmon.core.project.Project(psybase = self.psybase,
                                       name = 'Test Project',
                                       base_dir = self.db_base_dir,
                                       user = self.db_user,
                                       db_version = {}
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
        project = psysmon.core.project.Project(psybase = self.psybase,
                          name = 'My Test Project',
                          base_dir = self.db_base_dir,
                          user = self.db_user,
                          db_version = {}
                         )
        project.createDirectoryStructure()
        self.assertEquals(project.projectDir, os.path.join(self.db_base_dir, 'my_test_project'))
        self.assertTrue(os.path.isdir(project.projectDir))
        self.assertTrue(os.path.isdir(os.path.join(project.projectDir, 'data')))
        self.assertTrue(os.path.isdir(os.path.join(project.projectDir, 'tmp')))

        # Remove the directory structure.
        shutil.rmtree(project.projectDir)


    def test_save_project(self):
        ''' Test the saving of the project.
        '''
        import shelve
        import psysmon.core.waveclient

        print(self.db_project.db_version)
        self.db_project.createDirectoryStructure()
        print(self.db_project.db_version)
        self.db_project.save()

        self.assertTrue(os.path.isfile(os.path.join(self.db_project.projectDir, self.db_project.projectFile)))

        db = shelve.open(os.path.join(self.db_project.projectDir, self.db_project.projectFile))

        required_keys = ['name', 'dbDriver', 'dbDialect', 'dbHost', 
                         'dbName', 'pkg_version', 'db_version', 'user', 'createTime', 
                         'waveclient', 'defaultWaveclient',
                         'scnlDataSources']
        for cur_key in required_keys:
            self.assertTrue(cur_key in db.iterkeys())

        pkg_version = {}
        for cur_pkg in self.psybase.packageMgr.packages.itervalues():
            pkg_version[cur_pkg.name] = cur_pkg.version

        self.assertEquals(db['name'], 'Unit Test')
        self.assertEquals(db['dbDialect'], 'mysql')
        self.assertEquals(db['dbDriver'], None)
        self.assertEquals(db['dbHost'], 'localhost')
        self.assertEquals(db['dbName'], 'psysmon_unit_test')
        self.assertEquals(db['db_version'], {})
        self.assertEquals(db['pkg_version'], pkg_version)
        self.assertEquals(db['waveclient'], [])
        self.assertEquals(db['defaultWaveclient'], 'main client')
        self.assertEquals(db['scnlDataSources'], {})

        db.close()

        self.db_project.createDatabaseStructure(self.psybase.packageMgr.packages)

        waveclient = psysmon.core.waveclient.PsysmonDbWaveClient('main client', self.db_project)
        self.db_project.addWaveClient(waveclient)
        self.db_project.save()

        db = shelve.open(os.path.join(self.db_project.projectDir, self.db_project.projectFile))
        print(db)
        self.assertEquals(db['waveclient'], [('main client', 'psysmonDb', {}),])
        db.close()

        shutil.rmtree(self.db_project.projectDir)

    def test_save_json_project(self):
        ''' Test the saving of the project.
        '''
        # Set the maxDiff attribute to None to enable long output of 
        # non-equal strings tested with assertMultiLineEqual.
        self.maxDiff = None

        # Set the createTime of the project to a known value.
        self.db_project.createTime = UTCDateTime('2013-01-01T00:00:00')

        self.db_project.createDirectoryStructure()

        # Save the project to a JSON file.
        self.db_project.save_json()

        # Read the JSON file.
        fp = open(os.path.join(self.db_project.projectDir, self.db_project.projectFile))
        json_str = fp.read()
        fp.close()

        expected_json_str = '''{
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
    "defaultWaveclient": "main client", 
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
    "waveclient": []
}'''
        self.assertMultiLineEqual(json_str, expected_json_str)


        shutil.rmtree(self.db_project.projectDir)






def suite():
    return unittest.makeSuite(ProjectTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

