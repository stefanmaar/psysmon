'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon
import logging
from psysmon.core.base import Base
from psysmon.core.waveclient import PsysmonDbWaveClient,EarthwormWaveClient
import psysmon.core.gui as psygui
import os
import copy


class TracedisplayTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        pass

        #self.dlg = EditGeometryDlg(node, psyBase.project)
        #self.dlg.Show()


    def tearDown(self):
        print "\n\nEs war sehr schoen - auf Wiederseh'n.\n"

    def testDlg(self):
        self.node.execute()
        self.app.MainLoop()


#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(TracedisplayTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

