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

import logging


import psysmon.core.plugins as plugins
import psysmon.core.preferences_manager as preferences_manager
import psysmon.artwork.icons as icons
import psysmon.packages.sourcemap as sourcemap
import psysmon.packages.sourcemap.core


import numpy as np
import matplotlib.pyplot as plt



class PublishVisible(plugins.CommandPlugin):
    ''' Publish the visible (processed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'compute sourcemap',
                                       category = 'localize',
                                       tags = ['localize', 'amplitude']
                                       )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.export_icon_16

        item = preferences_manager.FloatSpinPrefItem(name = 'alpha',
                                                     value = 1.61,
                                                     limit = (0,100))
        self.pref_manager.add_item(item = item)

        item = preferences_manager.SingleChoicePrefItem(name = 'corr',
                                                        value = 'none',
                                                        limit = ['none', '1-5', '1-10'],
                                                        tool_tip = 'Select the station correction values. None for zero correction.')
        self.pref_manager.add_item(item = item)

        item = preferences_manager.SingleChoicePrefItem(name = 'method',
                                                        value = 'min',
                                                        limit = ['min', 'std', 'quart'],
                                                        tool_tip = 'Select the sourcemap computation method.')
        self.pref_manager.add_item(item = item)



    def run(self):
        ''' Publish the visible data to the project server.
        '''
        self.logger.info("Running the sourcemap plugin.")
        #self.parent.project.export_data(uri = self.parent.collection_node.rid + '/proc_stream',
        #                                data = self.parent.visible_data)


        alpha = self.pref_manager.get_value('alpha')

        corr_set = self.pref_manager.get_value('corr')
        cn = {}
        cn['1-5'] = {'ALBA': -0.1689, 'ARSA': 0.050, 'BISA': -1.1685, 'CONA': 0.233, 'CSNA': 0.2366, 'GILA': 0.1307,
                     'GUWA': 0.2436, 'MARA': 0.1389, 'PUBA': 0.1928, 'SITA': -0.0937, 'SOP': 0.2004}
        cn['1-10'] = {'ALBA': -0.3522, 'ARSA': 0.1491, 'BISA': -1.0543, 'CONA': 0.3833, 'CSNA': 0.3254, 'GILA': 0.1925,
                      'GUWA': 0.1688, 'MARA': 0.0035, 'PUBA': 0.1601, 'SITA': -0.2707, 'SOP': 0.2944}

        proc_stream = self.parent.dataManager.procStream

        # Convert the stations to sourcemap stations.
        station_list = []
        for cur_station in self.parent.displayManager.showStations:
            cur_stream = proc_stream.select(station = cur_station.name)
            trace_v = cur_stream.select(channel = 'HHZ')
            trace_h1 = cur_stream.select(channel = 'HHN')
            trace_h2 = cur_stream.select(channel = 'HHE')
            if trace_v:
                data_v = trace_v.traces[0].data
            else:
                self.logger.error("No vertical data found.")
                return

            if trace_h1:
                data_h1 = trace_h1.traces[0].data
            else:
                data_h1 = np.zeros(len(data_v))

            if trace_h2:
                data_h2 = trace_h2.traces[0].data
            else:
                data_h2 = np.zeros(len(data_v))

            if corr_set == 'none':
                corr = 0
            elif cur_station.name in cn[corr_set].keys():
                corr = cn[corr_set][cur_station.name]
            else:
                corr = 0

            print "Cn: %s - %f" % (cur_station.name, corr)
            station_list.append(sourcemap.core.Station(cur_station.station,
                                                       data_v = data_v,
                                                       data_h1 = data_h1,
                                                       data_h2 = data_h2,
                                                       corr = corr))

        sm = sourcemap.core.SourceMap(stations = station_list, alpha = alpha,
                                      method = self.pref_manager.get_value('method'))
        sm.compute_map_configuration()
        sm.compute_map_grid()
        sm.compute_backprojection()
        sm.compute_pseudomag()
        sm.compute_sourcemap()

        # Plot the map.
        from mpl_toolkits.basemap import pyproj
        proj = pyproj.Proj(init = sm.map_config['epsg'])
        stat_lon_lat = [x.get_lon_lat() for x in sm.compute_stations]
        stat_lon = [x[0] for x in stat_lon_lat]
        stat_lat = [x[1] for x in stat_lon_lat]
        stat_x, stat_y = proj(stat_lon, stat_lat)
        plt.pcolormesh(sm.map_x_coord, sm.map_y_coord, sm.result_map, cmap = 'rainbow')
        plt.colorbar()
        plt.contour(sm.map_x_coord, sm.map_y_coord, sm.result_map, colors = 'k')
        plt.scatter(stat_x, stat_y)

        epi_lon = 16.3960
        epi_lat = 47.9012
        epi_x, epi_y = proj(epi_lon, epi_lat)
        plt.plot(epi_x, epi_y, '*')

        plt.show()

