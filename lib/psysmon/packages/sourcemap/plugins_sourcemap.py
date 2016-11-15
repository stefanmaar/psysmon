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
import os
import csv


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
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.globe_2_icon_16

        item = preferences_manager.FloatSpinPrefItem(name = 'alpha',
                                                     value = 1.61,
                                                     limit = (0,100))
        self.pref_manager.add_item(item = item)


        item = preferences_manager.FileBrowsePrefItem(name = 'corr_filename',
                                                      value = '',
                                                      filemask = 'comma separated version (*.csv)|*.csv|' \
                                                                'all files (*)|*',
                                                      tool_tip = 'Specify the CSV file holding the station correction values.')
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

        # Try to load the station correction file.
        corr_filename = self.pref_manager.get_value('corr_filename')
        stat_corr = {}
        if os.path.exists(corr_filename):
            with open(corr_filename) as fp:
                reader = csv.DictReader(fp)
                for cur_row in reader:
                    cur_net = cur_row['network']
                    cur_station = cur_row['station']
                    cur_loc = cur_row['location']
                    cur_corr = float(cur_row['corr'])
                    stat_corr[(cur_station, cur_net, cur_loc)] = cur_corr

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

            if cur_station.snl in stat_corr.keys():
                corr = stat_corr[cur_station.snl]
            else:
                corr = 0

            self.logger.info("station correction: %s - %f", cur_station.name, corr)
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

        #epi_lon = 16.3960
        #epi_lat = 47.9012
        #epi_x, epi_y = proj(epi_lon, epi_lat)
        #plt.plot(epi_x, epi_y, '*')

        plt.show()

