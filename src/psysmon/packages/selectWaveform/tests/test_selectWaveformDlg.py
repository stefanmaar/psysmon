'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.packages.selectWaveform.selectWaveform import SelectWaveformEditDlg
from psysmon.core.base import Base
import psysmon.core.gui as psygui
import os


class SelectWaveformEditDlgTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        # Get the pSysmon base directory.
        psyBaseDir = '/home/stefan/01_kram/04_projekte/02_adhocrates/01_fuerDieEwigkeit/2011_pSysmon/01_src/trunk/pSysmon/src/psysmon/'
        psyBaseDir = os.path.dirname(psyBaseDir)
    
        # Initialize the pSysmon base object.
        psyBase = Base(psyBaseDir)
        psyBase.scan4Package()
        
        # Load the pSysmon test project.
        path = "/home/stefan/01_kram/04_projekte/02_adhocrates/01_fuerDieEwigkeit/2011_pSysmon/03_pSysmonProjects/test/test.ppr"
        psyBase.loadPsysmonProject(path)
            
        # Quest for the user and the database password.
        psyBase.project.setActiveUser('psysmon', 'psysmon')
            
        self.app =psygui.PSysmonApp()
        self.dlg = SelectWaveformEditDlg(None, psyBase.project)
        

    def tearDown(self):
        print "Good by."
    
    def testDlg(self):
        self.dlg.Show()
        self.app.MainLoop()
        
        
#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    tests = ['testDlg']
    return unittest.TestSuite(map(SelectWaveformEditDlgTestCase, tests))


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

