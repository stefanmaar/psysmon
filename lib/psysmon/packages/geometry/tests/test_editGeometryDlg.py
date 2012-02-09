'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.packages.geometry.editGeometry import EditGeometryDlg
from psysmon.core.base import Base
import psysmon.core.gui as psygui
import os


class EditGeometryDlgTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        # Get the pSysmon base directory.
        psyBaseDir = '/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/01_src/psysmon/lib/psysmon/'
        psyBaseDir = os.path.dirname(psyBaseDir)

        # Initialize the pSysmon base object.
        psyBase = Base(psyBaseDir)
        #psyBase.scan4Package()

        # Load the pSysmon test project.
        path = "/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/03_pSysmonProjects/test/test.ppr"
        psyBase.loadPsysmonProject(path)

        # Quest for the user and the database password.
        psyBase.project.setActiveUser('stefan','')

        # Load the database structure of the project packages.
        psyBase.project.loadDatabaseStructure(psyBase.packageMgr.packages)

        self.app =psygui.PSysmonApp()
        self.dlg = EditGeometryDlg(None, psyBase.project)
        #self.dlg.Show()


    def tearDown(self):
        print "Good by."

    def testDlg(self):
        print "hello"
        self.dlg.Show()
        self.app.MainLoop()


#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    tests = ['test']
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(EditGeometryDlgTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

