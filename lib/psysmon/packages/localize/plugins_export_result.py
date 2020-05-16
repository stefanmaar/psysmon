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
'''
The plugin for the localization using the circle method.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import logging
import os
import csv
import operator as op
import time

import geojson
import numpy as np
import psysmon
import psysmon.core.preferences_manager as preferences_manager
import pyproj


class ExportLocalizationResut(psysmon.core.plugins.CommandPlugin):
    ''' Run a localization using the circle method.

    '''
    nodeClass = 'GraphicLocalizationNode'


    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.CommandPlugin.__init__(self,
                                                    name = 'export result',
                                                    category = 'localize',
                                                    tags = ['export', 'localization result']
                                                    )

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = psysmon.artwork.icons.iconsBlack16.export_icon_16

        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        out_group = pref_page.add_group('output')
        item = preferences_manager.DirBrowsePrefItem(name = 'output_dir',
                                                     label = 'output directory',
                                                     value = '',
                                                     tool_tip = 'Specify a directory where the PSD data files are located.'
                                                    )
        out_group.add_item(item)


    def run(self):
        ''' Export the localization result.
        '''
        self.logger.info("Exporting the localization result.")
        output_dir = self.pref_manager.get_value('output_dir')

        # Check for an existing 2D map view.
        map_view_name = self.rid[:self.rid.rfind('/') + 1] + 'map_view'
        map_view = self.parent.viewport.get_node(name = map_view_name)
        if len(map_view) > 1:
            raise RuntimeError("More than one map_view instances were returned. This shouldn't happen. Don't know how to continue.")
        map_view = map_view[0]

        if map_view:
            prefix = 'loc_result_'
            postfix = ''
            time_str = time.strftime('%Y%m%d_%H%M%S')

            # TODO: Create a new folder for the view

            # Get the currently selected event id and create a dedicated output
            # directory for the event.
            # TODO: Check if it is possible, that the currently selected event
            # id and the event ids of the computed results (circle, tdoa) don't
            # match.
            selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/select_event',
                                                              name = 'selected_event')
            if selected_event_info:
                if len(selected_event_info) > 1:
                    raise RuntimeError("More than one event info was returned. This shouldn't happen.")
                selected_event_info = selected_event_info[0]
                map_event_id = selected_event_info.value['id']
            else:
                self.logger.error("No selected event available. Can't continue the localization.")
                return

            # Create an output directory for the event.
            map_event_dir_name = 'event_%d_%s' % (int(map_event_id), time_str)
            map_output_dir = os.path.join(output_dir, map_event_dir_name)
            if not os.path.exists(map_output_dir):
                os.makedirs(map_output_dir)


            # Export the shared data of the circle method.
            used_data_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/circle_method',
                                                                               name = 'used_data')
            if used_data_info:
                if len(used_data_info) > 1:
                    raise RuntimeError("More than one used_data info was returned. This shouldn't happen.")
                used_data_info = used_data_info[0]
                used_picks = used_data_info.value['picks']
                event_id = used_data_info.value['event_id']

                postfix = '_event_%d_%s' % (int(event_id), time_str)
                exp_type = 'circle-picks'
                ext = 'csv'
                used_picks = sorted(used_picks, key = op.attrgetter('label'))
                pick_rows = [(x.event_id, x.channel.scnl_string, x.label, x.time.isoformat()) for x in used_picks]

                # Create an output directory for the event.
                cur_event_dir_name = 'event_%d_%s' % (int(event_id), time_str)
                cur_output_dir = os.path.join(output_dir, cur_event_dir_name)
                if not os.path.exists(cur_output_dir):
                    os.makedirs(cur_output_dir)

                # Write the pick data to a csv file.
                filename = os.path.join(cur_output_dir, prefix + exp_type + postfix + '.' + ext)
                with open(filename, 'wb') as export_file:
                    csv_writer = csv.writer(export_file, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
                    csv_writer.writerow(['event_id', 'scnl', 'label', 'time'])
                    csv_writer.writerows(pick_rows)
            else:
                self.logger.info("No circle method results found. ")

            # Export the shared data of the TDOA method.
            # TODO: Add the parameters of the tdoa method (velocity, used
            # picks) as feature properties to the geojson output.
            used_data_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/tdoa_method',
                                                                               name = 'used_data')
            if used_data_info:
                if len(used_data_info) > 1:
                    raise RuntimeError("More than one used_data info was returned. This shouldn't happen.")
                used_data_info = used_data_info[0]
                used_picks = used_data_info.value['picks']
                event_id = used_data_info.value['event_id']

                postfix = '_event_%d_%s' % (int(event_id), time_str)
                exp_type = 'tdoa-picks'
                ext = 'csv'
                used_picks = sorted(used_picks, key = op.attrgetter('label'))
                pick_rows = [(x.event_id, x.channel.scnl_string, x.label, x.time.isoformat()) for x in used_picks]

                # Create an output directory for the event.
                cur_event_dir_name = 'event_%d_%s' % (int(event_id), time_str)
                cur_output_dir = os.path.join(output_dir, cur_event_dir_name)
                if not os.path.exists(cur_output_dir):
                    os.makedirs(cur_output_dir)

                # Write the pick data to a csv file.
                filename = os.path.join(cur_output_dir, prefix + exp_type + postfix + '.' + ext)
                with open(filename, 'w') as export_file:
                    csv_writer = csv.writer(export_file, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
                    csv_writer.writerow(['event_id', 'scnl', 'label', 'time'])
                    csv_writer.writerows(pick_rows)
            else:
                self.logger.info("No tdoa method results found. ")

            computed_data_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/tdoa_method',
                                                                               name = 'computed_data')
            if computed_data_info:
                if len(computed_data_info) > 1:
                    raise RuntimeError("More than one used_data info was returned. This shouldn't happen.")
                computed_data_info = computed_data_info[0]

                postfix = '_event_%d_%s' % (int(event_id), time_str)
                exp_type = 'tdoa-hyperbola-'
                ext = 'json'
                cur_featurelist = []
                for cur_key, cur_hyp in computed_data_info.value['hyperbola'].items():
                    # Convert the projected xy to lonlat.
                    lonlat = self.xy_to_lonlat(xy = cur_hyp,
                                               src_sys = map_view.map_config['epsg'])

                    # Create the geojson feature.
                    cur_linestring = geojson.LineString(lonlat.tolist())
                    cur_props = {'key': cur_key}
                    cur_feature = geojson.Feature(geometry = cur_linestring,
                                                  properties = cur_props)
                    cur_featurelist.append(cur_feature)

                cur_fc = geojson.FeatureCollection(cur_featurelist)

                # Create an output directory for the event.
                cur_event_dir_name = 'event_%d_%s' % (int(event_id), time_str)
                cur_output_dir = os.path.join(output_dir, cur_event_dir_name)
                if not os.path.exists(cur_output_dir):
                    os.makedirs(cur_output_dir)

                # Write the feature collection to a geojson file.
                json_filename = os.path.join(cur_output_dir, prefix + exp_type + postfix + '.' + ext)
                with open(json_filename, 'w') as json_file:
                    geojson.dump(cur_fc, json_file)
            else:
                self.logger.info("No tdoa method results found. ")

            # Export the map image.
            exp_type = 'map-image'
            ext = 'png'
            filename = os.path.join(map_output_dir, prefix + exp_type + postfix + '.' + ext)
            map_view.plot_panel.figure.savefig(filename, dpi = 300)


    def xy_to_lonlat(self, xy, src_sys):
        ''' Convert xy coordinates to WGS84 longitude and latitude (epsg:4326).
        '''
        dest_sys = "epsg:4326"

        src_proj = pyproj.Proj(init = src_sys)
        dst_proj = pyproj.Proj(init = dest_sys)

        lon, lat = pyproj.transform(src_proj, dst_proj, xy[:, 0], xy[:, 1])
        lonlat = np.array(list(zip(lon, lat)))
        return lonlat
