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

from obspy.core.utcdatetime import UTCDateTime
import logging
import os

import psysmon
from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import Channel
from psysmon.packages.geometry.inventory import RecorderStream
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorParameter

class InventoryTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        pass

    def tearDown(self):
        print "Es war sehr schoen - auf Wiederseh'n.\n"

    def test_station_creation(self):
        ''' Test the creation of a station.
        '''
        station = Station(name = 'TEST',
                          location = 'test site',
                          x = 10,
                          y = 20,
                          z = 30)

        self.assertEqual(station.name, 'TEST')
        self.assertEqual(station.location, 'test site')
        self.assertEqual(station.x, 10)
        self.assertEqual(station.y, 20)
        self.assertEqual(station.z, 30)
        self.assertIsNone(station.id)
        self.assertEqual(station.channels, [])
        self.assertEqual(station.parent_inventory, None)
        self.assertFalse(station.has_changed)


    def test_add_channel_to_station(self):
        station = Station(name = 'station_name',
                          location = 'station_location',
                          x = 10,
                          y = 20,
                          z = 30)

        channel_2_add = Channel(name = 'channel_name')

        cur_starttime = UTCDateTime('1976-06-20')
        cur_endtime = UTCDateTime('2014-06-20')
        station.add_channel(channel_2_add,
                            start_time = cur_starttime,
                            end_time = cur_endtime)

        self.assertEqual(len(station.channels), 1)
        self.assertEqual(station.channels[0], (channel_2_add, cur_starttime, cur_endtime))



    def test_add_stream_to_recorder(self):
        recorder = Recorder(serial = 'AAAA', type = 'test recorder')

        stream_2_add = RecorderStream(name = 'stream_name',
                                      label = 'stream_label')

        recorder.add_stream(stream_2_add)

        self.assertEqual(len(recorder.streams), 1)
        self.assertEqual(recorder.streams[0], stream_2_add)


    def test_get_stream_from_recorder(self):
        recorder = Recorder(serial = 'AAAA', type = 'test recorder')

        stream_2_add = RecorderStream(name = 'stream1_name',
                                      label = 'stream1_label')
        recorder.add_stream(stream_2_add)

        stream_2_add = RecorderStream(name = 'stream2_name',
                                      label = 'stream2_label')

        recorder.add_stream(stream_2_add)

        self.assertEqual(len(recorder.streams), 2)

        cur_stream = recorder.get_stream(name = 'stream1_name')
        self.assertEqual(len(cur_stream), 1)
        self.assertEqual(cur_stream[0].name, 'stream1_name')
        self.assertEqual(cur_stream[0].label, 'stream1_label')


    def test_add_sensor_to_stream(self):
        stream= RecorderStream(name = 'stream1_name',
                               label = 'stream1_label')

        sensor_2_add = Sensor(serial = 'sensor1_name',
                              type = 'sensor1_type',
                              rec_channel_name = '001',
                              channel_name = 'HHZ',
                              label = 'sensor1_label')

        cur_starttime = UTCDateTime('1976-06-20')
        cur_endtime = UTCDateTime('2014-06-20')
        stream.add_sensor(sensor_2_add,
                          start_time = cur_starttime,
                          end_time = cur_endtime)

        self.assertEqual(len(stream.sensors), 1)
        self.assertEqual(stream.sensors[0], (sensor_2_add, cur_starttime, cur_endtime))



#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(InventoryTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

