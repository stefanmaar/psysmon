import unittest
import psysmon
import logging
from psysmon.core.tests.util import createPsyBase
from psysmon.core.tests.util import createBareProject

class DatabaseTableCreation(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        # Configure the logger.
        self.logger = logging.getLogger('psysmon')
        self.logger.setLevel(psysmon.logConfig['level'])
        self.logger.addHandler(psysmon.getLoggerHandler())

        # Initialize the pSysmon base object.
        self.psybase = createPsyBase()

        # Create a bare project.
        self.project = createBareProject(self.psybase)



    def tearDown(self):
        print "\n\nEs war sehr schoen - auf Wiederseh'n.\n"


    def testDlg(self):
        self.project.connect2Db('')
        self.project.loadDatabaseStructure(self.psybase.packageMgr.packages)
        self.project.dbMetaData.drop_all()
        self.project.dbMetaData.clear()

        self.project.createDatabaseStructure(self.psybase.packageMgr.packages)


#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(DatabaseTableCreation, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

