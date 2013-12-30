'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon.core.project
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_dbtest_project
from psysmon.core.test_util import drop_project_database_tables
import os
import shutil

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
        print "Cleaning up....\n"
        drop_project_database_tables(cls.db_project)
        shutil.rmtree(cls.db_base_dir)
        print "done.\n"


    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_rid(self):
        ''' Test the resource identifier.
        '''
        project = psysmon.core.project.Project(psybase = self.psybase,
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
        project = psysmon.core.project.Project(psybase = self.psybase,
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


    def test_save_project(self):
        ''' Test the saving of the project.
        '''
        import shelve
        import psysmon.core.waveclient

        self.db_project.createDirectoryStructure()
        self.db_project.save()

        self.assertTrue(os.path.isfile(os.path.join(self.db_project.projectDir, self.db_project.projectFile)))

        db = shelve.open(os.path.join(self.db_project.projectDir, self.db_project.projectFile))

        required_keys = ['name', 'dbDriver', 'dbDialect', 'dbHost', 
                         'dbName', 'pkg_version', 'db_version', 'user', 'createTime', 
                         'waveclient', 'defaultWaveclient',
                         'scnlDataSources']
        for cur_key in required_keys:
            self.assertTrue(cur_key in db.keys())

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
        print db
        self.assertEquals(db['waveclient'], [('main client', 'psysmonDb', {}),])
        db.close()

        shutil.rmtree(self.db_project.projectDir)




def suite():
    return unittest.makeSuite(ProjectTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

