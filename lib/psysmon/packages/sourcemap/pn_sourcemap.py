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

import itertools
import logging

import psysmon.core.processingStack
import psysmon.core.preferences_manager as pm
import psysmon.core.util as p_util
import psysmon.packages.sourcemap as sourcemap

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt


class ComputeSourcemap(psysmon.core.processingStack.ProcessingNode):
    ''' Apply a median filter to a timeseries.

    '''
    nodeClass = 'SlidingWindowProcessorNode'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        psysmon.core.processingStack.ProcessingNode.__init__(self,
                                                             name = 'compute sourcemap',
                                                             mode = 'editable',
                                                             category = 'sourcemap',
                                                             tags = ['amplitude', 'localize', 'sourcemap'],
                                                             **kwargs
                                                            )
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        item = pm.FloatSpinPrefItem(name = 'alpha',
                                    value = 1.61,
                                    limit = (0,100))
        self.pref_manager.add_item(item = item)

        item = pm.SingleChoicePrefItem(name = 'corr',
                                       value = 'none',
                                       limit = ['none', '1-5', '1-10'],
                                       tool_tip = 'Select the station correction values. None for zero correction.')
        self.pref_manager.add_item(item = item)

        item = pm.SingleChoicePrefItem(name = 'method',
                                       value = 'min',
                                       limit = ['min', 'std', 'quart'],
                                       tool_tip = 'Select the sourcemap computation method.')
        self.pref_manager.add_item(item = item)



    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        alpha = self.pref_manager.get_value('alpha')

        corr_set = self.pref_manager.get_value('corr')
        cn = {}
        cn['1-5'] = {'ALBA': -0.1689, 'ARSA': 0.050, 'BISA': -1.1685, 'CONA': 0.233, 'CSNA': 0.2366, 'GILA': 0.1307,
                     'GUWA': 0.2436, 'MARA': 0.1389, 'PUBA': 0.1928, 'SITA': -0.0937, 'SOP': 0.2004}
        cn['1-10'] = {'ALBA': -0.3522, 'ARSA': 0.1491, 'BISA': -1.0543, 'CONA': 0.3833, 'CSNA': 0.3254, 'GILA': 0.1925,
                      'GUWA': 0.1688, 'MARA': 0.0035, 'PUBA': 0.1601, 'SITA': -0.2707, 'SOP': 0.2944}

        station_list = []

        # TODO: Make the station selection coded by SNL.
        station_names = self.parentStack.parent.pref_manager.get_value('stations')
        process_stations = [self.parentStack.project.geometry_inventory.get_station(name = x) for x in station_names]
        process_stations = list(itertools.chain.from_iterable(process_stations))
        for cur_station in process_stations:
            cur_stream = stream.select(station = cur_station.name)
            # TODO: Make the channel mapping user selectable.
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

            self.logger.info("Cn: %s - %f", cur_station.name, corr)
            station_list.append(sourcemap.core.Station(cur_station,
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

        # Create a 2D grid result.
        # TODO: Add the station coordinates to the description.
        res_desc = {}
        res_desc['cn'] = cn
        res_desc['alpha'] = alpha
        res_desc['map_config'] = sm.map_config
        res_desc['start_time'] = process_limits[0].isoformat()
        res_desc['end_time'] = process_limits[1].isoformat()
        res_desc['station_list'] = [x.snl for x in station_list]
        res_desc['preprocessing'] = self.parentStack.get_settings(upper_node_limit = self)
        self.add_result(name = 'sourcemap',
                        res_type = 'grid_2d',
                        grid = sm.result_map,
                        x_coord = sm.map_x_coord,
                        y_coord = sm.map_y_coord,
                        description = res_desc,
                        origin_resource = origin_resource)



        # Plot the map.
        #from mpl_toolkits.basemap import pyproj
        #proj = pyproj.Proj(init = sm.map_config['epsg'])
        #stat_lon_lat = [x.get_lon_lat() for x in sm.compute_stations]
        #stat_lon = [x[0] for x in stat_lon_lat]
        #stat_lat = [x[1] for x in stat_lon_lat]
        #stat_x, stat_y = proj(stat_lon, stat_lat)
        #plt.pcolormesh(sm.map_x_coord, sm.map_y_coord, sm.result_map, cmap = 'rainbow')
        #plt.colorbar()
        #plt.contour(sm.map_x_coord, sm.map_y_coord, sm.result_map, colors = 'k')
        #plt.scatter(stat_x, stat_y)
        #plt.show()



