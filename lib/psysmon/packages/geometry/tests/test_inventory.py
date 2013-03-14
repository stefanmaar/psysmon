'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import wx
from psysmon.packages.geometry.inventory import Inventory,Recorder,Station,Sensor
import psysmon.core.gui as psygui

class InventoryTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        self.inventory = Inventory('test')

    def tearDown(self):
        print "Good by."

    def testXmlImport(self):
        xmlFile = 'data/psysmonGeometry.xml'
        self.inventory.importFromXml(xmlFile)



#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(InventoryTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

