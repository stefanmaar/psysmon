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

import json
import os

import mpl_toolkits.basemap as basemap
import numpy as np
import obspy.core
import obspy.core.utcdatetime as utcdatetime

import quarry_blast_validation
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm


class MssQuarryBlastReport(package_nodes.LooperCollectionChildNode):
    ''' Create a report of a quarry blast recorded on the MSS network.

    '''
    name = 'mss report'
    mode = 'looper child'
    category = 'mss'
    tags = ['macroseismic', 'mss', 'quarry', 'blast']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_input_preferences()


    def create_input_preferences(self):
        ''' Create the input preferences.
        '''
        input_page = self.pref_manager.add_page('Input')
        bi_group = input_page.add_group('blast information')

        # The quarry blast information file.
        item = psy_pm.FileBrowsePrefItem(name = 'blast_file',
                                         label = 'blast file',
                                         value = '',
                                         filemask = 'json (*.json)|*.json',
                                         tool_tip = 'The quarry blast information file created with the quarry blast validation collection node.')
        bi_group.add_item(item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Check for needed keyword arguments.
        if not self.kwargs_exists(['event'], **kwargs):
            raise RuntimeError("The needed event argument was not passed to the execute method.")

        event = kwargs['event']

        # Load the quarry_blast information.
        blast_filename = self.pref_manager.get_value('blast_file')
        if os.path.exists(blast_filename):
            with open(blast_filename, 'r') as fp:
                quarry_blast = json.load(fp = fp,
                                         cls = quarry_blast_validation.QuarryFileDecoder)
        else:
            raise RuntimeError("Couldn't open the blast file %s.", blast_filename)

        # Get the baumit quarry blast id from the event tags.
        id_tag = [x for x in event.tags if x.startswith('baumit_id:')]
        if id_tag:
            id_tag = id_tag[0]
        else:
            self.logger.error("No baumit quarry blast id tag found for event %d.", event.db_id)
            return
        spec, baumit_id = id_tag.split(':')


        # Compute the resultant of the stations.
        resultant_channels = ['Hnormal', 'Hparallel']
        res_stream = obspy.core.Stream()
        res_stations = []
        for cur_detection in event.detections:
            # TODO: Select the detection timespan only.
            cur_stream = stream.select(network = cur_detection.scnl[2],
                                       station = cur_detection.scnl[0],
                                       location = cur_detection.scnl[3])
            cur_res_stream = self.compute_resultant(cur_stream, resultant_channels)
            if not cur_res_stream:
                continue
            res_stream = res_stream + cur_res_stream
            res_stations.append(cur_detection.channel.parent_station)

        # TODO: Check if all expected stations have got a trigger. Test the
        # missing stations for available data an eventually missed events. Use
        # a threshold value of the maximum amplitude as a rule whether to
        # include the missed station into the PGV computation or not.

        # Compute the max. PGV.
        max_pgv = [(str.join(':', (x.stats.station, x.stats.network, x.stats.location)), np.max(x.data))  for x in res_stream]


        # Compute the magnitude.
        # TODO: Check the standard for the sign of the station correction.
        # Brueckl subtracts the station correction.
        proj = basemap.pyproj.Proj(init = 'epsg:' + quarry_blast[baumit_id]['epsg'])
        stat_lonlat = np.array([x.get_lon_lat() for x in res_stations])
        stat_x, stat_y = proj(stat_lonlat[:,0], stat_lonlat[:,1])
        stat_z = np.array([x.z for x in res_stations])
        quarry_x = quarry_blast[baumit_id]['x']
        quarry_y = quarry_blast[baumit_id]['y']
        quarry_z = quarry_blast[baumit_id]['z']
        hypo_dist = np.sqrt((stat_x - quarry_x)**2 + (stat_y - quarry_y)**2 + (stat_z - quarry_z)**2)
        stat_corr = np.zeros(len(max_pgv))
        magnitude = np.log10([x[1] * 1000 for x in max_pgv]) + 1.6 * np.log10(hypo_dist) - 2.074 + stat_corr


        # Update the quarry blast information dictionary.
        export_max_pgv = dict(max_pgv)
        export_magnitude = dict(zip([x.snl_string for x in res_stations], magnitude))
        quarry_blast[baumit_id]['computed_on'] = utcdatetime.UTCDateTime()
        quarry_blast[baumit_id]['event_time'] = event.start_time
        quarry_blast[baumit_id]['max_pgv'] = {}
        quarry_blast[baumit_id]['max_pgv']['data'] = export_max_pgv
        quarry_blast[baumit_id]['max_pgv']['used_channels'] = resultant_channels
        quarry_blast[baumit_id]['magnitude'] = {}
        quarry_blast[baumit_id]['magnitude']['station_mag'] = export_magnitude
        quarry_blast[baumit_id]['magnitude']['network_mag'] = np.mean(magnitude)
        quarry_blast[baumit_id]['magnitude']['network_mag_std'] = np.std(magnitude)

        # Save the quarry blast information.
        with open(blast_filename, 'w') as fp:
            json.dump(quarry_blast,
                      fp = fp,
                      cls = quarry_blast_validation.QuarryFileEncoder)

        # TODO: Write a timestamped result file for the event.


        # TODO: Clear the computation request flag in the event database.


        # TODO: Create images of the results.


        # TODO: Join the images and the data in a Latex file and create a pdf
        # file. 



    def compute_resultant(self, st, channel_names):
        ''' Compute the resultant of the peak-ground-velocity.
        '''
        x_st = st.select(channel = 'Hparallel').merge()
        y_st = st.select(channel = 'Hnormal').merge()

        res_st = obspy.core.Stream()
        for cur_x_trace, cur_y_trace in zip(x_st.traces, y_st.traces):
            cur_x = cur_x_trace.data
            cur_y = cur_y_trace.data

            if len(cur_x) != len(cur_y):
                self.logger.error("The x and y data lenght dont't match. Can't compute the res. PGV for this trace.")
                continue

            cur_res = np.sqrt(cur_x**2 + cur_y**2)

            cur_stats = {'network': cur_x_trace.stats['network'],
                         'station': cur_x_trace.stats['station'],
                         'location': cur_x_trace.stats['location'],
                         'channel': 'res',
                         'sampling_rate': cur_x_trace.stats['sampling_rate'],
                         'starttime': cur_x_trace.stats['starttime']}
            res_trace = obspy.core.Trace(data = cur_res, header = cur_stats)
            res_st.append(res_trace)

        res_st.split()

        return res_st

