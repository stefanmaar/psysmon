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
#import os

import psysmon
import psysmon.packages.geometry.inventory as inventory
import psysmon.packages.sourcemap as sourcemap
import psysmon.packages.sourcemap.core



class SourceMapTestCase(unittest.TestCase):
    ''' Test suite for the sourcemap station module.
    '''

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        cls.logger = logging.getLogger('psysmon')
        cls.logger.setLevel('DEBUG')
        cls.logger.addHandler(psysmon.getLoggerHandler())

        #cls.data_path = os.path.dirname(os.path.abspath(__file__))
        #cls.data_path = os.path.join(cls.data_path, 'data')


    def test_station(self):
        ''' The the station class.
        '''
        inv = inventory.Inventory('test inventory')
        net = inventory.Network(name = 'XX')
        station = inventory.Station(name = 'station1_name',
                                    location = 'station1_location',
                                    x = 10,
                                    y = 20,
                                    z = 30)
        net.add_station(station)
        inv.add_network(net)

        sm_station = sourcemap.core.Station(station)


    def test_compute_map_configuration(self):
        ''' Test the map configuration computation.
        '''
        station_list = []
        station = inventory.Station(name = 'station1_name',
                                    location = '00',
                                    x = 15,
                                    y = 46,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station2_name',
                                    location = '00',
                                    x = 16,
                                    y = 47,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station3_name',
                                    location = '00',
                                    x = 17,
                                    y = 48,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        sm = sourcemap.core.SourceMap(stations = station_list)
        sm.compute_map_configuration()
        self.assertEqual(sm.map_config['x_lim'], (500000, 650000))
        self.assertEqual(sm.map_config['y_lim'], (5094000, 5319000))


    def test_compute_map_grid(self):
        ''' Test the computation of the map grid.
        '''
        station_list = []
        station = inventory.Station(name = 'station1_name',
                                    location = '00',
                                    x = 15,
                                    y = 46,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station2_name',
                                    location = '00',
                                    x = 16,
                                    y = 47,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station3_name',
                                    location = '00',
                                    x = 17,
                                    y = 48,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        sm = sourcemap.core.SourceMap(stations = station_list)
        sm.compute_map_configuration()
        sm.compute_map_grid()

    def test_compute_backprojection(self):
        ''' Test the computation of the backprojection matrices.
        '''
        station_list = []
        station = inventory.Station(name = 'station1_name',
                                    location = '00',
                                    x = 15,
                                    y = 46,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station2_name',
                                    location = '00',
                                    x = 16,
                                    y = 47,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station3_name',
                                    location = '00',
                                    x = 17,
                                    y = 48,
                                    z = 0,
                                    coord_system = 'epsg:4326')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        sm = sourcemap.core.SourceMap(stations = station_list)
        sm.compute_map_configuration()
        sm.compute_map_grid()
        sm.compute_backprojection()

def suite():
    return unittest.makeSuite(SourceMapTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

