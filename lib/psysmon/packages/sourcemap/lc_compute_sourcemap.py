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

import matplotlib.pyplot as plt
import matplotlib.patches
from mpl_toolkits.basemap import pyproj
import numpy as np
import scipy as sp

import psysmon.core.packageNodes as package_nodes
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.preferences_manager as pm
import psysmon.core.result as result
import psysmon.packages.sourcemap as sourcemap
import sourcemap.core


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

        # The sourcemap instance.
        self.sm = None

        # Flag to indicate if the amplitude weight has to be computed.
        self.compute_weight = True

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
                                       limit = ['min', 'std', 'quart', 'minmax'],
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


    def initialize(self):
        ''' Initialize the node.
        '''
        super(ComputeSourcemap, self).initialize()

        # Reset the weight computation flag.
        self.compute_weight = True

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

        # Create the sourcemap stations.
        station_names = self.parent.pref_manager.get_value('stations')
        process_stations = [self.project.geometry_inventory.get_station(name = x.split(':')[0], network = x.split(':')[1], location = x.split(':')[2]) for x in station_names]
        process_stations = list(itertools.chain.from_iterable(process_stations))

        station_list = []
        for cur_station in process_stations:
            if cur_station.snl in iter(stat_corr.keys()):
                cur_corr = stat_corr[cur_station.snl]
            else:
                cur_corr = 0
            station_list.append(sourcemap.core.Station(cur_station,
                                                       corr = cur_corr))

        # TODO: Create preference items for the following variables.
        map_dx = 500
        map_dy = 500
        hypo_depth = 0
        use_station_corr = True

        self.sm = sourcemap.core.SourceMap(stations = station_list,
                                           alpha = self.pref_manager.get_value('alpha'),
                                           method = self.pref_manager.get_value('method'),
                                           map_dx = map_dx,
                                           map_dy = map_dy,
                                           hypo_depth = hypo_depth)

        self.sm.compute_map_configuration()
        self.sm.compute_map_grid()
        self.sm.compute_distance_grid()
        self.sm.compute_traveltime_grid()
        self.sm.compute_backprojection(use_station_corr = use_station_corr)



    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        self.sm.clear()

        self.add_data(stream = stream,
                      start_time = process_limits[0],
                      end_time = process_limits[1])

        # Compute the amplitude weight once the first data has been added.
        # TODO: Make the computation undependent of the adding of the data.
        # This somehow requires to pass the sps of the data of the station to
        # the sourcemap before the first data is loaded. Is this possible?
        #if self.compute_weight:
        #    self.sm.compute_amplitude_weight()
        #    self.compute_weight = False

        self.sm.compute_amplitude_weight()

        # TODO: Create preference items for the following variables.
        pseudo_amp_method = 'windowed_max'

        self.sm.compute_pseudo_amp(method = pseudo_amp_method)
        self.sm.compute_pseudomag()
        self.sm.compute_sourcemap()


        # Export the sourcemap to an image file.
        self.export_as_image(start_time = process_limits[0],
                             end_time = process_limits[1])


        # Create a 2D grid result.
        metadata = {}
        # Create a new stat_corr dict with the keys converted to string.
        # Otherwise a dump to json textfile is not possible.
        meta_stat_corr = {}
        for cur_station in self.sm.compute_stations:
            meta_stat_corr[cur_station.snl_string] = cur_station.corr
        metadata['stat_corr'] = meta_stat_corr
        metadata['map_config'] = self.sm.map_config
        metadata['processing_time_window'] = {'start_time': process_limits[0].isoformat(),
                                              'end_time': process_limits[1].isoformat()}
        metadata['station_list'] = {x.snl_string: {'x': x.x, 'y': x.y, 'z': x.z, 'epsg': x.coord_system} for x in self.sm.compute_stations}
        metadata['sourcemap_config'] = {}
        metadata['sourcemap_config']['alpha'] = self.sm.alpha
        metadata['sourcemap_config']['hypo_depth'] = self.sm.hypo_depth
        metadata['sourcemap_config']['v_surf_min'] = self.sm.v_surf_min
        metadata['sourcemap_config']['method'] = self.sm.method
        metadata['sourcemap_config']['pseudo_amp_method'] = pseudo_amp_method
        metadata['preprocessing'] = self.parent.get_settings(upper_node_limit = self)

        if len(self.sm.result_map) > 0:
            grid_result = result.Grid2dResult(name = 'sourcemap',
                                              start_time = process_limits[0],
                                              end_time = process_limits[1],
                                              origin_name = self.name,
                                              origin_resource = origin_resource,
                                              x_coord = self.sm.map_x_coord,
                                              y_coord = self.sm.map_y_coord,
                                              grid = self.sm.result_map,
                                              dx = self.sm.map_dx,
                                              dy = self.sm.map_dy,
                                              epsg = self.sm.map_config['epsg'],
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
        for cur_station in self.sm.compute_stations:
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



    def add_data(self, stream, start_time, end_time):
        ''' Add the data for the given timespan to the sourcemap.
        '''
        # TODO: Make the channel mapping a user preference. Check the
        # polarization analysis for a reference.
        #channels = ['HHZ', 'HHN', 'HHE']
        channels = ['Z', 'HNormal', 'HParallel']

        # TODO: Add a check, that the required channels are available.

        for cur_station in self.sm.compute_stations:
            for cur_channel in channels:
                cur_stream = stream.select(station = cur_station.name,
                                           location = cur_station.location,
                                           channel = cur_channel).copy()

                if cur_stream:
                    cur_trace = cur_stream.traces[0]

                    if np.abs((cur_trace.stats.starttime - start_time)) > (1.5 * cur_trace.stats.delta):
                        self.logger.error("The trace start time doesn't match the start time of the processing window.")
                        continue

                    # Trim the data to equal length.
                    # It is assumed, that the sampling rate of all traces in
                    # the stream is the same.
                    win_length = int(np.floor(cur_station.data_length * cur_trace.stats.sampling_rate))
                    cur_data = cur_trace.data[:win_length]

                    try:
                        cur_station.add_data(cur_data, sps = cur_trace.stats.sampling_rate)
                    except:
                        self.logger.exception("Couldn't add the data to the station.")



    def export_as_image(self, start_time, end_time):
        ''' Export the sourcemap to an image file. '''
        proj = pyproj.Proj(init = 'epsg:32633')
        # Compute the projected station coordinates.
        stat_lon = [cur_stat.get_lon_lat()[0] for cur_stat in self.sm.compute_stations]
        stat_lat = [cur_stat.get_lon_lat()[1] for cur_stat in self.sm.compute_stations]
        stat_x, stat_y = proj(stat_lon, stat_lat)


        # Compute the masking convex hull.
        point_list = np.array([stat_x, stat_y]).transpose()
        cv = sp.spatial.ConvexHull(point_list)


        fig = plt.figure(figsize = (8, 8))
        ax = fig.add_subplot(111)

        if len(self.sm.result_map) > 0:
            if self.sm.method == 'min':
                clim = (-2., 5)
                #artist = ax.pcolormesh(sm.map_x_coord, sm.map_y_coord, sm.result_map, cmap = 'viridis')
                artist = ax.pcolormesh(self.sm.map_x_coord, self.sm.map_y_coord, self.sm.result_map, cmap = 'viridis',
                                        vmin = clim[0], vmax = clim[1])
                cb = fig.colorbar(artist, ax = ax, ticks = np.arange(clim[0], clim[1] + 1), extend = 'max')
                cb.set_label('pseudo-magnitude')
            elif self.sm.method == 'std':
                clim = (0., 2.)
                artist = ax.pcolormesh(self.sm.map_x_coord, self.sm.map_y_coord, self.sm.result_map, cmap = 'viridis',
                                        vmin = clim[0], vmax = clim[1])
                cb = fig.colorbar(artist, ax = ax, ticks = np.arange(clim[0], clim[1]), extend = 'max')
                cb.set_label('std. deviation of pseudo-mag.')
            else:
                artist = ax.pcolormesh(self.sm.map_x_coord, self.sm.map_y_coord, self.sm.result_map, cmap = 'viridis')
                cb = fig.colorbar(artist, ax = ax)
            cv_poly = matplotlib.patches.Polygon(point_list[cv.vertices, :], closed = True,
                                                 transform = plt.gca().transData)
            artist.set_clip_path(cv_poly)

        # Add the stations.
        ax.scatter(stat_x, stat_y, s=100, marker='^', color='r', picker=5, zorder = 3)

        if len(self.sm.result_map) > 0:
            if self.sm.method == 'min':
                levels = np.arange(0, 6, 0.25)
                artist = ax.contour(self.sm.map_x_coord,
                                    self.sm.map_y_coord,
                                    self.sm.result_map,
                                    levels = levels,
                                    colors = 'w',
                                    linewidths = 0.25)
                plt.clabel(artist,
                           artist.levels[0::4],
                           inline = 1,
                           fmt = '%.2f',
                           fontsize = 4)
            else:
                artist = ax.contour(self.sm.map_x_coord,
                                    self.sm.map_y_coord,
                                    self.sm.result_map,
                                    colors = 'w',
                                    linewidths = 0.25)


        ax.axis('equal')

        ax.set_xlim([np.min(point_list[cv.vertices, 0]), np.max(point_list[cv.vertices, 0])])
        ax.set_ylim([np.min(point_list[cv.vertices, 1]), np.max(point_list[cv.vertices, 1])])

        ax.set_title(start_time.isoformat() + ' - ' + end_time.isoformat() + ' - ' + self.sm.method)

        # TODO: Add an matplotlib figure result. Also take care of deleting the
        # figure when clearing the resultbag! Add a clear() method to the
        # Result class for this task.
        output_dir = self.parent.pref_manager.get_value('output_dir')
        filename = 'sourcemap_' + self.sm.method +'_' + start_time.isoformat().replace(':', '') + '_' + end_time.isoformat().replace(':', '') + '.png'
        fig.savefig(os.path.join(output_dir, filename), dpi = 300)

        # Delete the figure.
        fig.clear()
        plt.close(fig)
        del fig


