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
import os
import csv

import psysmon.core.packageNodes as package_nodes
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.preferences_manager as pm
import psysmon.core.result as result
import psysmon.packages.sourcemap as sourcemap

import numpy as np


class ComputeSourcemap(package_nodes.LooperCollectionChildNode):
    ''' Compute the sourcemap for a given time window.

    '''
    name = 'compute sourcemap'
    mode = 'looper child'
    category = 'Localization'
    tags = ['stable', 'looper child', 'sourcemap']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        pref_page = self.pref_manager.add_page('Preferences')
        mo_group = pref_page.add_group('map options')

        item = pm.FloatSpinPrefItem(name = 'alpha',
                                    value = 1.61,
                                    limit = (0,100))
        mo_group.add_item(item)

        item = pm.FileBrowsePrefItem(name = 'corr_filename',
                                    value = '',
                                    filemask = 'comma separated version (*.csv)|*.csv|' \
                                                'all files (*)|*',
                                    tool_tip = 'Specify the CSV file holding the station correction values.')
        mo_group.add_item(item)

        item = pm.SingleChoicePrefItem(name = 'method',
                                       value = 'min',
                                       limit = ['min', 'std', 'quart'],
                                       tool_tip = 'Select the sourcemap computation method.')
        mo_group.add_item(item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
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

        station_list = []

        # TODO: Make the station selection coded by SNL.
        station_names = self.parent.pref_manager.get_value('stations')
        process_stations = [self.project.geometry_inventory.get_station(name = x) for x in station_names]
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
                continue

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
        metadata = {}
        # Create a new stat_corr dict with the keys converted to string.
        # Otherwise a dump to json textfile is not possible.
        meta_stat_corr = {}
        for cur_key in stat_corr.keys():
            meta_stat_corr[':'.join(cur_key)] = stat_corr[cur_key]
        metadata['stat_corr'] = meta_stat_corr
        metadata['alpha'] = alpha
        metadata['map_config'] = sm.map_config
        metadata['processing_time_window'] = {'start_time': process_limits[0].isoformat(),
                                              'end_time': process_limits[1].isoformat()}
        metadata['station_list'] = {x.snl_string: {'x': x.x, 'y': x.y, 'z': x.z, 'epsg': x.coord_system} for x in station_list}
        metadata['preprocessing'] = self.parent.get_settings(upper_node_limit = self)

        grid_result = result.Grid2dResult(name = 'sourcemap',
                                          start_time = process_limits[0],
                                          end_time = process_limits[1],
                                          origin_name = self.name,
                                          origin_resource = origin_resource,
                                          x_coord = sm.map_x_coord,
                                          y_coord = sm.map_y_coord,
                                          grid = sm.result_map,
                                          dx = sm.map_dx,
                                          dy = sm.map_dy,
                                          epsg = sm.map_config['epsg'],
                                          metadata = metadata)
        self.result_bag.add(grid_result)

        columns = ['name', 'network', 'location', 'x', 'y', 'z', 'coord_system', 'description']
        table_result = result.TableResult(name = 'sourcemap_used_stations',
                                          key_name = 'snl',
                                          start_time = process_limits[0],
                                          end_time = process_limits[1],
                                          origin_name = self.name,
                                          origin_resource = origin_resource,
                                          column_names = columns)
        for cur_station in station_list:
            table_result.add_row(key = cur_station.snl,
                                 name = cur_station.name,
                                 network = cur_station.network,
                                 location = cur_station.location,
                                 x = cur_station.x,
                                 y = cur_station.y,
                                 z = cur_station.z,
                                 coord_system = cur_station.coord_system,
                                 description = cur_station.description)
        self.result_bag.add(table_result)


