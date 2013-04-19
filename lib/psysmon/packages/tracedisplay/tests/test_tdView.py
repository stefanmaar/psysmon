# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
        print "hello"
        # Get the pSysmon base directory.
        psyBaseDir = '/home/stefan/Development/pSysmon/trunk/pSysmon/src/psysmon/'
        psyBaseDir = os.path.dirname(psyBaseDir)
    
        # Initialize the pSysmon base object.
        psyBase = Base(psyBaseDir)
        psyBase.scan4Package()
        
        # Load the pSysmon test project.
        path = "/home/stefan/Projects/05_science/pSysmonProjects/test/test.ppr"
        psyBase.loadPsysmonProject(path)
            
        # Quest for the user and the database password.
        psyBase.project.setActiveUser('psysmon', 'psysmon')
           
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

