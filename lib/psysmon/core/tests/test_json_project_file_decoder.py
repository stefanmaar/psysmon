import unittest
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

        encoder = util.ProjectFileEncoder()
        decoder = util.ProjectFileDecoder()
        json_project = encoder.encode(self.db_project)
        print 'THE JSON STRING:'
        print json_project
        print '\n'
        project_obj = decoder.decode(json_project)
        print '\nTHE DECODED OBJECT:'
        print str(project_obj)



def suite():
    return unittest.makeSuite(ProjectFileDecoderTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')




