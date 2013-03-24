'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import logging
import tempfile
import os
import psysmon
from psysmon.packages.geometry.inventory import InventoryXmlParser
from psysmon.packages.geometry.inventory import Inventory

class InventoryXmlParserTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')

        # Configure the logger.
        cls.logger = logging.getLogger('psysmon')
        cls.logger.setLevel('DEBUG')
        cls.logger.addHandler(psysmon.getLoggerHandler())

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_xmlfile(self):
        xml_file = os.path.join(self.data_path, 'simple_inventory.xml')
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

    def test_export_xmlfile(self):
        xml_file = os.path.join(self.data_path, 'simple_inventory.xml')
        xml_parser = InventoryXmlParser()
        inventory = xml_parser.parse(xml_file)

        outfile = tempfile.mkstemp()
        xml_parser.export_xml(inventory, outfile)
        #os.remove(outfile)



def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(InventoryXmlParserTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

