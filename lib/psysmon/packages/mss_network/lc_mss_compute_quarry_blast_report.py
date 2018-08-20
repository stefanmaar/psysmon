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
import pickle

import pyproj
import numpy as np
import obspy.core
import obspy.core.utcdatetime as utcdatetime
import scipy

import quarry_blast_validation
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.util as util


class MssComputeQuarryBlastReport(package_nodes.LooperCollectionChildNode):
    ''' Create a report of a quarry blast recorded on the MSS network.

    '''
    name = 'mss compute report data'
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
        rd_group = input_page.add_group('report data')

        # The quarry blast information file.
        item = psy_pm.FileBrowsePrefItem(name = 'blast_file',
                                         label = 'blast file',
                                         value = '',
                                         filemask = 'json (*.json)|*.json',
                                         tool_tip = 'The quarry blast information file created with the quarry blast validation collection node.')
        bi_group.add_item(item)

        # The report data directory.
        item = psy_pm.DirBrowsePrefItem(name = 'report_data_dir',
                                        label = 'report data directory',
                                        value = '',
                                        tool_tip = 'The directory holding the quarry blast report data.')
        rd_group.add_item(item)


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
        res_stream = obspy.core.Stream()
        res3d_stream = obspy.core.Stream()
        orig_stream = obspy.core.Stream()
        res_stations = []
        for cur_detection in event.detections:
            # TODO: Select the detection timespan only.
            cur_stream = stream.select(network = cur_detection.scnl[2],
                                       station = cur_detection.scnl[0],
                                       location = cur_detection.scnl[3])
            # Compute the 2D-resultant used for the magnitude computation.
            resultant_channels = ['Hnormal', 'Hparallel']
            cur_res_stream = self.compute_resultant(cur_stream, resultant_channels)
            if not cur_res_stream:
                continue

            #Compute the 3D-resultant used for reporting of the DUBA stations.
            resultant_3d_channels = ['Hnormal', 'Hparallel', 'Z']
            cur_res3d_stream = self.compute_resultant(cur_stream, resultant_3d_channels)

            orig_stream = orig_stream + cur_stream
            res_stream = res_stream + cur_res_stream
            res3d_stream = res3d_stream + cur_res3d_stream
            res_stations.append(cur_detection.channel.parent_station)

        # Handle the DUBAM station separately. Due to a time-error relative to
        # DUBA, the DUBAM detections are most likely not included in the event
        # detections.
        stat_dubam = [x for x in res_stations if x.name == 'DUBAM']
        self.logger.debug("##################### DUBAM HANDLING ###############")
        self.logger.debug(stat_dubam)
        if not stat_dubam:
            cur_stream = stream.select(network = 'MSSNet',
                                       station = 'DUBAM',
                                       location = '00')
            self.logger.debug(cur_stream)
            # Compute the 2D-resultant used for the magnitude computation.
            resultant_channels = ['Hnormal', 'Hparallel']
            cur_res_stream = self.compute_resultant(cur_stream, resultant_channels)
            if cur_res_stream:
                #Compute the 3D-resultant used for reporting of the DUBA stations.
                resultant_3d_channels = ['Hnormal', 'Hparallel', 'Z']
                cur_res3d_stream = self.compute_resultant(cur_stream, resultant_3d_channels)

                orig_stream = orig_stream + cur_stream
                res_stream = res_stream + cur_res_stream
                res3d_stream = res3d_stream + cur_res3d_stream
                cur_station = self.project.geometry_inventory.get_station(name = 'DUBAM')[0]
                res_stations.append(cur_station)

        self.logger.debug(res_stations)
        self.logger.debug(res_stream)
        self.logger.debug(res3d_stream)



        # Handle possible coordinate changes of station DUBAM.
        # If the field x_dubam_1 is set, the alternative DUBAM position is
        # used.
        stat_dubam = [x for x in res_stations if x.name == 'DUBAM']
        if stat_dubam:
            stat_dubam = stat_dubam[0]
            if quarry_blast[baumit_id]['x_dubam_1'] is not None:
                stat_dubam.x = quarry_blast[baumit_id]['x_dubam_1']
                stat_dubam.y = quarry_blast[baumit_id]['y_dubam_1']
                stat_dubam.z = quarry_blast[baumit_id]['z_dubam_1']
                stat_dubam.coord_system = 'epsg:31256'

        # TODO: Check if all expected stations have got a trigger. Test the
        # missing stations for available data an eventually missed events. Use
        # a threshold value of the maximum amplitude as a rule whether to
        # include the missed station into the PGV computation or not.

        # Compute the max. PGV.
        max_pgv = [(str.join(':', (x.stats.station, x.stats.network, x.stats.location)), np.max(x.data))  for x in res_stream]
        max_pgv_3d = [(str.join(':', (x.stats.station, x.stats.network, x.stats.location)), np.max(x.data))  for x in res3d_stream]

        # Compute the magnitude.
        # TODO: Check the standard for the sign of the station correction.
        # Brueckl subtracts the station correction.
        proj_baumit = pyproj.Proj(init = 'epsg:' + quarry_blast[baumit_id]['epsg'])
        proj_wgs84 = pyproj.Proj(init = 'epsg:4326')
        stat_lonlat = np.array([x.get_lon_lat() for x in res_stations])
        stat_x, stat_y = pyproj.transform(proj_wgs84, proj_baumit, stat_lonlat[:,0], stat_lonlat[:,1])
        stat_z = np.array([x.z for x in res_stations])
        quarry_x = quarry_blast[baumit_id]['x']
        quarry_y = quarry_blast[baumit_id]['y']
        quarry_z = quarry_blast[baumit_id]['z']
        hypo_dist = np.sqrt((stat_x - quarry_x)**2 + (stat_y - quarry_y)**2 + (stat_z - quarry_z)**2)
        stat_corr = np.zeros(len(max_pgv))
        magnitude = np.log10([x[1] * 1000 for x in max_pgv]) + 1.6 * np.log10(hypo_dist) - 2.074 + stat_corr


        # Compute the PSD.
        psd_data = {}
        for cur_trace in orig_stream:
            cur_psd_data = self.compute_psd(cur_trace)
            cur_scnl = util.traceid_to_scnl(cur_trace.id)
            cur_scnl_string = ':'.join(cur_scnl)
            psd_data[cur_trace.id] = cur_psd_data

        # Compute the dominant frequency.
        dom_frequ = {};
        dom_stat_frequ = {}
        for cur_station in res_stations:
            cur_psd_keys = [x for x in psd_data.keys() if x.startswith(cur_station.network + '.' + cur_station.name + '.')]
            cur_df = []
            for cur_key in cur_psd_keys:
                cur_nfft = psd_data[cur_key]['n_fft']
                left_fft = int(np.ceil(cur_nfft / 2.))
                max_ind = np.argmax(psd_data[cur_key]['psd'][1:left_fft])
                dom_frequ[cur_key] = psd_data[cur_key]['frequ'][max_ind]
                cur_df.append(dom_frequ[cur_key])

            dom_stat_frequ[cur_station.snl_string] = np.mean(cur_df)




        # Update the quarry blast information dictionary.
        export_max_pgv = dict(max_pgv)
        export_magnitude = dict(zip([x.snl_string for x in res_stations], magnitude))
        quarry_blast[baumit_id]['computed_on'] = utcdatetime.UTCDateTime()
        quarry_blast[baumit_id]['event_time'] = event.start_time
        quarry_blast[baumit_id]['max_pgv'] = {}
        quarry_blast[baumit_id]['max_pgv']['data'] = export_max_pgv
        quarry_blast[baumit_id]['max_pgv']['used_channels'] = resultant_channels
        quarry_blast[baumit_id]['max_pgv_3d'] = {}
        quarry_blast[baumit_id]['max_pgv_3d']['data'] = dict(max_pgv_3d)
        quarry_blast[baumit_id]['max_pgv_3d']['used_channels'] = resultant_3d_channels
        quarry_blast[baumit_id]['magnitude'] = {}
        quarry_blast[baumit_id]['magnitude']['station_mag'] = export_magnitude
        quarry_blast[baumit_id]['magnitude']['network_mag'] = np.mean(magnitude)
        quarry_blast[baumit_id]['magnitude']['network_mag_std'] = np.std(magnitude)
        quarry_blast[baumit_id]['dom_frequ'] = dom_frequ
        quarry_blast[baumit_id]['dom_stat_frequ'] = dom_stat_frequ
        quarry_blast[baumit_id]['hypo_dist'] = dict(zip([x.snl_string for x in res_stations], hypo_dist))

        # Save the quarry blast information.
        with open(blast_filename, 'w') as fp:
            json.dump(quarry_blast,
                      fp = fp,
                      cls = quarry_blast_validation.QuarryFileEncoder)


        # Write a result file for the event.
        output_dir = self.pref_manager.get_value('report_data_dir')
        filename = 'blast_report_data_event_%010d.pkl' % event.db_id
        report_data = {}
        report_data['baumit_id'] = baumit_id
        report_data['blast_data'] = quarry_blast[baumit_id]
        report_data['psd_data'] = psd_data
        with open(os.path.join(output_dir, filename), 'w') as fp:
            pickle.dump(report_data, fp)

        # Clear the computation request flag in the event database.
        event.tags.remove('mss_result_needed')
        event.tags.append('mss_result_computed')
        event.write_to_database(self.project)


    def compute_resultant(self, st, channel_names):
        ''' Compute the resultant of the peak-ground-velocity.
        '''
        res_st = obspy.core.Stream()
        used_streams = []
        for cur_channel in channel_names:
            cur_stream = st.select(channel = cur_channel).merge()
            if len(cur_stream) == 0:
                self.logger.error("No data found in stream %s for channel %s.", st, cur_channel)
                return res_st
            used_streams.append(cur_stream)

        # Check for correct data size.
        #if len(set([len(x.traces[0].data) for x in used_streams])) > 1:
        #    pass

        for cur_traces in zip(*[x.traces for x in used_streams]):
            cur_data = [x.data for x in cur_traces]

            if len(set([len(x) for x in cur_data])) > 1:
                self.logger.error("The lenght of the data of the individual traces dont't match. Can't compute the res. PGV for these traces: %s.", [str(x) for x in cur_traces])
                continue

            cur_data = np.array(cur_data)
            cur_res = np.sqrt(np.sum(cur_data**2, axis = 0))

            cur_stats = {'network': cur_traces[0].stats['network'],
                         'station': cur_traces[0].stats['station'],
                         'location': cur_traces[0].stats['location'],
                         'channel': 'res_{0:d}d'.format(len(cur_traces)),
                         'sampling_rate': cur_traces[0].stats['sampling_rate'],
                         'starttime': cur_traces[0].stats['starttime']}
            res_trace = obspy.core.Trace(data = cur_res, header = cur_stats)
            res_st.append(res_trace)

        res_st.split()

        return res_st


    def compute_psd(self, trace):
        ''' Compute the power spectral density of a trace.
        '''

        # Compute the power amplitude density spectrum.
        # As defined by Havskov and Alguacil (page 164), the power density spectrum can be
        # written as 
        #   P = 2* 1/T * deltaT^2 * abs(F_dft)^2
        # This is valid for the left-sided fft.
        #
        n_fft = len(trace.data)
        delta_t = 1 / trace.stats.sampling_rate
        T = (len(trace.data) - 1) * delta_t
        Y = scipy.fft(trace.data, n_fft)
        psd = 2 * delta_t**2 / T * np.abs(Y)**2
        psd = 10 * np.log10(psd)
        frequ = trace.stats.sampling_rate * np.arange(0,n_fft) / float(n_fft)
        psd_data = {}
        psd_data['n_fft'] = n_fft
        psd_data['psd'] = psd
        psd_data['frequ'] = frequ

        return psd_data

