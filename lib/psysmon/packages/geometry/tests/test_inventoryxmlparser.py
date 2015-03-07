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
from psysmon.packages.geometry.inventory import TimeBox
from obspy.core.utcdatetime import UTCDateTime

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

        # Test the sensor.
        self.assertEqual(len(inventory.sensors), 1)
        cur_sensor = inventory.sensors[0]
        self.assertEqual(cur_sensor.serial, '1417')
        self.assertEqual(cur_sensor.model, 'Seismonitor 1Hz')
        self.assertEqual(cur_sensor.producer, 'Geospace')
        self.assertEqual(cur_sensor.description, 'Sensor description.')

        # Test the sensor components.
        self.assertEqual(len(cur_sensor.components), 3)
        cur_component = cur_sensor.get_component(name = 'Z')
        self.assertEqual(len(cur_component), 1)
        cur_component = cur_component[0]
        self.assertEqual(cur_component.name, 'Z')
        self.assertEqual(cur_component.description, 'Sensor component Z description.')
        self.assertEqual(len(cur_component.parameters), 1)
        cur_parameter = cur_component.parameters[0]
        self.assertEqual(cur_parameter.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.end_time, UTCDateTime('2009-02-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.sensitivity, 340.55)
        self.assertEqual(cur_parameter.tf_normalization_factor, 0.4)
        self.assertEqual(cur_parameter.tf_normalization_frequency, 1.0)
        self.assertEqual(len(cur_parameter.tf_poles), 3)
        self.assertTrue(complex('-4.44+4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-4.44-4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-1.083+0j') in cur_parameter.tf_poles)
        self.assertEqual(len(cur_parameter.tf_zeros), 3)
        self.assertEqual(cur_parameter.tf_zeros, [complex(0), complex(0), complex(0)])


        cur_component = cur_sensor.get_component(name = 'N')
        self.assertEqual(len(cur_component), 1)
        cur_component = cur_component[0]
        self.assertEqual(cur_component.name, 'N')
        self.assertEqual(cur_component.description, 'Sensor component N description.')
        self.assertEqual(len(cur_component.parameters), 1)
        cur_parameter = cur_component.parameters[0]
        self.assertEqual(cur_parameter.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.end_time, UTCDateTime('2009-03-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.sensitivity, 340.55)
        self.assertEqual(cur_parameter.tf_normalization_factor, 0.4)
        self.assertEqual(cur_parameter.tf_normalization_frequency, 2.0)
        self.assertEqual(len(cur_parameter.tf_poles), 3)
        self.assertTrue(complex('-4.44+4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-4.44-4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-1.083+0j') in cur_parameter.tf_poles)
        self.assertEqual(len(cur_parameter.tf_zeros), 3)
        self.assertEqual(cur_parameter.tf_zeros, [complex(0), complex(0), complex(0)])

        cur_component = cur_sensor.get_component(name = 'E')
        self.assertEqual(len(cur_component), 1)
        cur_component = cur_component[0]
        self.assertEqual(cur_component.name, 'E')
        self.assertEqual(cur_component.description, 'Sensor component E description.')
        self.assertEqual(len(cur_component.parameters), 1)
        cur_parameter = cur_component.parameters[0]
        self.assertEqual(cur_parameter.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_parameter.end_time)
        self.assertEqual(cur_parameter.sensitivity, 340.55)
        self.assertEqual(cur_parameter.tf_normalization_factor, 0.4)
        self.assertEqual(cur_parameter.tf_normalization_frequency, 3.0)
        self.assertEqual(len(cur_parameter.tf_poles), 3)
        self.assertTrue(complex('-4.44+4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-4.44-4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-1.083+0j') in cur_parameter.tf_poles)
        self.assertEqual(len(cur_parameter.tf_zeros), 3)
        self.assertEqual(cur_parameter.tf_zeros, [complex(0), complex(0), complex(0)])



        # Test the recorders.
        self.assertEqual(len(inventory.recorders), 1)
        cur_recorder = inventory.recorders[0]
        self.assertEqual(cur_recorder.serial, '9D6C')
        self.assertEqual(cur_recorder.type, 'Reftek 130-01')
        self.assertEqual(cur_recorder.description, 'Recorder description.')
        self.assertEqual(len(cur_recorder.streams), 3)

        # Test the first stream.
        cur_stream = cur_recorder.streams[0]
        self.assertEqual(cur_stream.name, '101')
        self.assertEqual(cur_stream.label, 'Stream-101')
        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.components), 1)

        cur_param = cur_stream.parameters[0]
        self.assertEqual(cur_param.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_param.end_time, UTCDateTime('2009-02-01T00:00:00.000000Z'))
        self.assertEqual(cur_param.gain, 32.)
        self.assertEqual(cur_param.bitweight, 1.5895e-6)

        cur_timebox = cur_stream.components[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_timebox.end_time, UTCDateTime('2009-02-01T00:00:00.000000Z'))
        cur_component = cur_timebox.item
        self.assertEqual(cur_component.serial, '1417')
        self.assertEqual(cur_component.name, 'Z')

        # Test the second stream.
        cur_stream = cur_recorder.streams[1]
        self.assertEqual(cur_stream.name, '102')
        self.assertEqual(cur_stream.label, 'Stream-102')
        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.components), 1)

        cur_param = cur_stream.parameters[0]
        self.assertEqual(cur_param.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_param.end_time)
        self.assertEqual(cur_param.gain, 32.)
        self.assertEqual(cur_param.bitweight, 1.5895e-6)

        cur_timebox = cur_stream.components[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_component = cur_timebox.item
        self.assertEqual(cur_component.serial, '1417')
        self.assertEqual(cur_component.name, 'N')

        # Test the third stream.
        cur_stream = cur_recorder.streams[2]
        self.assertEqual(cur_stream.name, '103')
        self.assertEqual(cur_stream.label, 'Stream-103')
        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.components), 1)

        cur_param = cur_stream.parameters[0]
        self.assertEqual(cur_param.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_param.end_time)
        self.assertEqual(cur_param.gain, 32.)
        self.assertEqual(cur_param.bitweight, 1.5895e-6)

        cur_timebox = cur_stream.components[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_component = cur_timebox.item
        self.assertEqual(cur_component.serial, '1417')
        self.assertEqual(cur_component.name, 'E')


        # Test the network.
        self.assertEqual(len(inventory.networks), 1)
        cur_network = inventory.networks[0]
        self.assertEqual(cur_network.name, 'XX')
        self.assertEqual(cur_network.type, 'network type')
        self.assertEqual(cur_network.description, 'Network description.')
        self.assertEqual(len(cur_network.stations), 1)

        # Test the station.
        cur_station = cur_network.stations[0]
        self.assertEqual(cur_station.name, 'GILA')
        self.assertEqual(cur_station.location, '00')
        self.assertEqual(cur_station.x, 15.887788)
        self.assertEqual(cur_station.y, 47.69577)
        self.assertEqual(cur_station.z, 643.0)
        self.assertEqual(cur_station.coord_system, 'epsg:4326')
        self.assertEqual(cur_station.description, 'Grillenberg')
        self.assertEqual(len(cur_station.channels), 3)

        # Test the first channel.
        cur_channel = cur_station.channels[0]
        self.assertEqual(cur_channel.name, 'HHZ')
        self.assertEqual(cur_channel.description, 'Description for channel HHZ.')
        self.assertEqual(len(cur_channel.streams), 1)
        cur_timebox = cur_channel.streams[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2010-02-04T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_stream = cur_timebox.item
        self.assertEqual(cur_stream.serial, '9D6C')
        self.assertEqual(cur_stream.name, '101')
        self.assertEqual(cur_stream.label, 'Stream-101')

        # Test the second channel.
        cur_channel = cur_station.channels[1]
        self.assertEqual(cur_channel.name, 'HHN')
        self.assertEqual(cur_channel.description, 'Description for channel HHN.')
        self.assertEqual(len(cur_channel.streams), 1)
        cur_timebox = cur_channel.streams[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2010-02-04T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_stream = cur_timebox.item
        self.assertEqual(cur_stream.serial, '9D6C')
        self.assertEqual(cur_stream.name, '102')
        self.assertEqual(cur_stream.label, 'Stream-102')


        # Test the third channel.
        cur_channel = cur_station.channels[2]
        self.assertEqual(cur_channel.name, 'HHE')
        self.assertEqual(cur_channel.description, 'Description for channel HHE.')
        self.assertEqual(len(cur_channel.streams), 1)
        cur_timebox = cur_channel.streams[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2010-02-04T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_stream = cur_timebox.item
        self.assertEqual(cur_stream.serial, '9D6C')
        self.assertEqual(cur_stream.name, '103')
        self.assertEqual(cur_stream.label, 'Stream-103')


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

