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

import psysmon
import psysmon.core.preferences_manager as preferences_manager


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
        item = preferences_manager.DirBrowsePrefItem(name = 'output_dir',
                                                     label = 'output directory',
                                                     value = '',
                                                     tool_tip = 'Specify a directory where the PSD data files are located.'
                                                    )
        self.pref_manager.add_item(item = item)



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
            # Create a new folder for the view


            # Export all available picks. Mark those used for the
            # localization.
            # Check for the shared selected event.
            used_data_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/circle_method',
                                                                               name = 'used_data')
            if used_data_info:
                if len(used_data_info) > 1:
                    raise RuntimeError("More than one used_data info was returned. This shouldn't happen.")
                used_data_info = used_data_info[0]
                used_picks = used_data_info.value['picks']
                event_id = used_data_info.value['event_id']
            else:
                self.logger.error("The is no localization result from the circle method available. Can't export anything.")
                return

            time_str = time.strftime('%Y%m%d_%H%M%S')
            prefix = 'loc_result_'
            exp_type = 'picks'
            postfix = '_event_%d_%s' % (int(event_id), time_str)
            ext = 'csv'
            used_picks = sorted(used_picks, key = op.attrgetter('label'))
            pick_rows = [(x.event_id, x.channel.scnl_string, x.label, x.time.isoformat()) for x in used_picks]
            # Write the pick data to a csv file.
            filename = os.path.join(output_dir, prefix + exp_type + postfix + '.' + ext)
            with open(filename, 'wb') as export_file:
                csv_writer = csv.writer(export_file, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
                csv_writer.writerow(['event_id', 'scnl', 'label', 'time'])
                csv_writer.writerows(pick_rows)

            # Export the map image.
            exp_type = 'circles'
            ext = 'png'
            filename = os.path.join(output_dir, prefix + exp_type + postfix + '.' + ext)
            map_view.plot_panel.figure.savefig(filename, dpi = 300)








