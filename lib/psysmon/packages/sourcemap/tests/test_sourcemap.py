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
import os

import numpy as np

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

        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')


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


        data_v = np.zeros(100)
        data_h1 = np.zeros(100)
        data_h2 = np.zeros(100)

        data_v[20] = 10
        data_v[30] = -5
        data_h1[10] = 2
        data_h1[3] = -8
        data_h2[30] = 5
        data_h2[31] = -6

        sm_station = sourcemap.core.Station(station,
                                            data_v = data_v,
                                            data_h1 = data_h1,
                                            data_h2 = data_h2)

        alt_res = sm_station.alt_resultant
        self.assertEqual(alt_res, np.sqrt(446))



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

    def test_compute_traveltime_grid(self):
        ''' Test the traveltime grid computation.
        '''
        station_list = []
        station = inventory.Station(name = 'station1_name',
                                    location = '00',
                                    x = 560000,
                                    y = 5300000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station2_name',
                                    location = '00',
                                    x = 570000,
                                    y = 5300000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station3_name',
                                    location = '00',
                                    x = 560000,
                                    y = 5310000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station4_name',
                                    location = '00',
                                    x = 570000,
                                    y = 5310000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        sm = sourcemap.core.SourceMap(stations = station_list)
        sm.compute_map_configuration()
        sm.compute_map_grid()
        sm.compute_distance_grid()
        sm.compute_traveltime_grid()


    def test_compute_weight_limits(self):
        ''' Test the map configuration computation.
        '''
        station_list = []
        station = inventory.Station(name = 'station1_name',
                                    location = '00',
                                    x = 560000,
                                    y = 5300000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station2_name',
                                    location = '00',
                                    x = 570000,
                                    y = 5300000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station3_name',
                                    location = '00',
                                    x = 560000,
                                    y = 5310000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        station = inventory.Station(name = 'station4_name',
                                    location = '00',
                                    x = 570000,
                                    y = 5310000,
                                    z = 0,
                                    coord_system = 'epsg:32633')
        sm_station = sourcemap.core.Station(station)
        station_list.append(sm_station)

        sm = sourcemap.core.SourceMap(stations = station_list)
        sm.compute_map_configuration()
        sm.compute_map_grid()
        sm.compute_distance_grid()
        sm.compute_traveltime_grid()

        # Create dummy data and add it to the stations.
        sps = 100
        data_len = np.ceil(sm.window_length * sps)
        data = np.random.rand(data_len)
        for cur_station in sm.compute_stations:
            cur_station.data_v = data
            cur_station.data_h1 = data
            cur_station.data_h2 = data
            cur_station.time = np.arange(data_len) * 1/float(sps)
            cur_station.compute_weight_limits()


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


    def test_synthetic_data(self):
        ''' Test the computation using the synthetic data set.
        '''
        import pickle
        import psysmon.packages.geometry.inventory_parser as inventory_parser

        # Read the station geometry.
        self.logger.setLevel('INFO')
        xml_file = os.path.join(self.data_path, 'alpaact_inventory.xml')
        xml_parser = inventory_parser.InventoryXmlParser()
        inventory = xml_parser.parse(xml_file)
        self.logger.setLevel('DEBUG')


        # Load the synthetic data.
        data_file = os.path.join(self.data_path, 'sourcemap_synthetic_data.pkl')
        fid = open(data_file, 'rb')
        db = pickle.load(fid)
        fid.close()


        # Convert the stations to sourcemap stations.
        station_list = []
        compute_stations = ['ALBA', 'GE03', 'GILA', 'GUWA', 'MARA', 'PITA', 'PUBA', 'SITA', 'VEIA']
        for cur_station in inventory.networks[0].stations:
            if cur_station.name not in compute_stations:
                continue
            data_v = db['seismograms'][cur_station.snl]
            data_h1 = np.zeros(len(data_v))
            data_h2 = np.zeros(len(data_v))
            station_list.append(sourcemap.core.Station(cur_station,
                                                       data_v = data_v,
                                                       data_h1 = data_h1,
                                                       data_h2 = data_h2))

        sm = sourcemap.core.SourceMap(stations = station_list, alpha = db['alpha'], method = 'min')
        sm.compute_map_configuration()
        sm.compute_map_grid()
        sm.compute_backprojection()
        sm.compute_pseudomag()
        sm.compute_sourcemap()

        # Plot the map.
        import pyproj
        import matplotlib.pyplot as plt
        proj = pyproj.Proj(init = sm.map_config['epsg'])
        hypo_x, hypo_y = proj(db['hypo_lon_lat'][0], db['hypo_lon_lat'][1])
        plt.pcolormesh(sm.map_x_coord, sm.map_y_coord, sm.result_map)
        plt.plot(hypo_x, hypo_y, '^', markersize = 10)
        plt.colorbar()
        plt.show()



def suite():
    return unittest.makeSuite(SourceMapTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

