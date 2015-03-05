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
import logging
import tempfile
import os
import psysmon
from psysmon.packages.geometry.inventory_parser import InventoryXmlParser
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
        self.assertEqual(inventory.name, 'ALPAACT')
        self.assertEqual(len(inventory.sensors), 1)
        cur_sensor = inventory.sensors[0]
        self.assertEqual(cur_sensor.serial, '1417')
        self.assertEqual(cur_sensor.model, 'Seismonitor 1Hz')
        self.assertEqual(cur_sensor.producer, 'Geospace')
        self.assertEqual(cur_sensor.description, 'Sensor description.')


        #self.assertEqual(len(inventory.networks), 1)
        #self.assertEqual(len(inventory.recorders), 1)

        #cur_recorder = inventory.recorders[0]
        #self.assertEqual(len(cur_recorder.sensors), 3)
        #for cur_sensor in cur_recorder.sensors:
        #    self.assertEqual(len(cur_sensor.parameters), 1)

        #cur_network = inventory.networks[0]
        #self.assertEqual(len(cur_network.stations), 1)

        #cur_station = cur_network.stations[0]
        #self.assertEqual(len(cur_station.sensors), 3)

    def test_export_xmlfile(self):
        xml_file = os.path.join(self.data_path, 'simple_inventory.xml')
        xml_parser = InventoryXmlParser()
        inventory = xml_parser.parse(xml_file)

        outfile = tempfile.mkstemp()
        xml_parser.export_xml(inventory, outfile[1])

        # Read the created outputfile.
        ei = xml_parser.parse(outfile[1])

        # Compare the two inventories.
        self.assertEqual(inventory, ei)

        # Remove the output file.
        os.remove(outfile[1])



def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(InventoryXmlParserTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

