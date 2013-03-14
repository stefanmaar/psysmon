'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import logging
import psysmon
from psysmon.packages.geometry.inventory import InventoryXmlParser
from psysmon.packages.geometry.inventory import Inventory

class InventoryTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClas(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

    def tearDown(self):
        pass

    def test_parse_xmlfile(self):
        xml_file = 'data/simple_inventory.xml'
        xml_parser = InventoryXmlParser()
        inventory = xml_parser.parse(xml_file)

        self.assertIsInstance(inventory, Inventory)
        self.assertEqual(len(inventory.networks), 1)
        self.assertEqual(len(inventory.recorders), 1)

        cur_recorder = inventory.recorders[0]
        self.assertEqual(len(cur_recorder.sensors), 3)
        for cur_sensor in cur_recorder.sensors:
            self.assertEqual(len(cur_sensor.parameters), 1)

        cur_network = inventory.networks[0]
        self.assertEqual(len(cur_network.stations), 1)

        cur_station = cur_network.stations[0]
        self.assertEqual(len(cur_station.sensors), 3)



def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(InventoryTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

