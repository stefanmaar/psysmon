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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The importWaveform module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
import os
import shelve
import copy

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack

import obspy.core
from obspy.core.utcdatetime import UTCDateTime
import matplotlib.mlab as mlab


class ComputePsdNode(psysmon.core.packageNodes.CollectionNode):
    '''
    '''
    name = 'compute PSD'
    mode = 'editable'
    category = 'Frequency analysis'
    tags = ['development', 'power spectral density']

    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        self.create_time_and_component_prefs()
        self.create_parameters_prefs()
        self.create_processing_prefs()
        self.create_output_prefs()


    def create_time_and_component_prefs(self):
        ''' Create the preference items of the collection node.
        '''
        pagename = '1 time and components'
        self.pref_manager.add_page(pagename)

        # The start time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                                      label = 'start time',
                                                      value = UTCDateTime('2012-07-09T00:00:00'),
                                                      group = 'time range',
                                                      tool_tip = 'The start time of the interval to process.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        # The end time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                                      label = 'end time',
                                                      value = UTCDateTime('2012-07-09T00:00:00'),
                                                      group = 'time range',
                                                      tool_tip = 'The end time of the interval to process.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        # The SCNL list
        pref_item = psy_pm.ListCtrlEditPrefItem(name = 'scnl_list',
                                           label = 'SCNL',
                                           value = [],
                                           column_labels = ['station', 'channel', 'network', 'location'],
                                           group = 'component selection',
                                           tool_tip = 'Select the components to process.'
                                          )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


    def create_parameters_prefs(self):
        ''' Create the preference items of the parameters section.
        '''
        pagename = '2 parameters'
        self.pref_manager.add_page(pagename)

        pref_item = psy_pm.FloatSpinPrefItem(name = 'window_length',
                                             label = 'window length [s]',
                                             group = 'FFT',
                                             value = 300,
                                             limit = [0, 1e10],
                                             increment = 1,
                                             digits = 3,
                                             tool_tip = 'The length of the computation window [s].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        pref_item = psy_pm.IntegerSpinPrefItem(name = 'window_overlap',
                                             label = 'window overlap [%]',
                                             group = 'FFT',
                                             value = 50,
                                             limit = [0, 99],
                                             tool_tip = 'The overlap of the computation windows [%].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        pref_item = psy_pm.IntegerSpinPrefItem(name = 'psd_nfft',
                                             label = 'nfft',
                                             group = 'FFT',
                                             value = 8192,
                                             limit = [0, 1000000],
                                             tool_tip = 'The length of the fft window [samples].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        pref_item = psy_pm.IntegerSpinPrefItem(name = 'psd_overlap',
                                             label = 'fft overlap [%]',
                                             group = 'FFT',
                                             value = 50,
                                             limit = [0, 99],
                                             tool_tip = 'The overlap of the fft windows [%].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


    def create_processing_prefs(self):
        ''' Create the processing preference items.
        '''
        pagename = '3 processing'
        self.pref_manager.add_page(pagename)

        item = psy_pm.CustomPrefItem(name = 'processing_stack',
                                     label = 'processing stack',
                                     group = 'signal processing',
                                     value = None,
                                     gui_class = PStackEditField,
                                     tool_tip = 'Edit the processing stack nodes.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = item)


    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        pagename = '4 output'
        self.pref_manager.add_page(pagename)

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        group = 'output',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the PSD files.'
                                       )
        self.pref_manager.add_item(pagename = pagename,
                                   item = item)




    def edit(self):
        # Initialize the components
        if self.project.geometry_inventory:
            channels = sorted([x.scnl for x in self.project.geometry_inventory.get_channel()])
            self.pref_manager.set_limit('scnl_list', channels)

        # Initialize the processing stack.
        processing_nodes = self.project.getProcessingNodes(('common', ))
        if self.pref_manager.get_value('processing_stack') is None:
                detrend_node_template = [x for x in processing_nodes if x.name == 'detrend'][0]
                detrend_node = copy.deepcopy(detrend_node_template)
                self.pref_manager.set_value('processing_stack', [detrend_node, ])

        self.pref_manager.set_limit('processing_stack', processing_nodes)

        dlg = ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        '''
        '''
        window_length = self.pref_manager.get_value('window_length')
        window_overlap = self.pref_manager.get_value('window_overlap')
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        psd_nfft = self.pref_manager.get_value('psd_nfft')
        psd_overlap = self.pref_manager.get_value('psd_overlap')

        # Create a processing stack instance.
        processing_stack = ProcessingStack(name = 'pstack',
                                           project = self.project,
                                           nodes = self.pref_manager.get_value('processing_stack'))

	# Split the timespan into processing chunks.
        overlap_length = window_length * (1 - window_overlap/100.)

        windows_between = int((end_time - start_time)/overlap_length)
        window_list = [start_time + x * overlap_length for x in range(windows_between)]
	window_list[0] = start_time

        # Process each SCNL
        for cur_scnl in self.pref_manager.get_value('scnl_list'):
            save_day = UTCDateTime(year = start_time.year,
                                   month = start_time.month,
                                   day = start_time.day)

            # Get the channel instance from the inventory.
            cur_channel = self.project.geometry_inventory.get_channel(station = cur_scnl[0],
                                                                      network = cur_scnl[2],
                                                                      location = cur_scnl[3],
                                                                      name = cur_scnl[1])
            if len(cur_channel) == 0:
                self.logger.error("No channel found for scnl: %s", cur_scnl)
                continue
            elif len(cur_channel) > 1:
                self.logger.error("Multiple channels found for scnl: %s; channels: %s", cur_scnl, cur_channel)
            else:
                cur_channel = cur_channel[0]

            psd_data = {}

            # Compute the psd for each window.
            for k, cur_window_start in enumerate(window_list):
                self.logger.info("Computing window %s.", str(cur_window_start))


                # If the current window starts on a new day, save the old
                # window_psd to a daily file.
                if cur_window_start - save_day > 86400:
                    self.save_psd_data(psd_data, cur_scnl)
                    save_day = UTCDateTime(year = cur_window_start.year,
                                           month = cur_window_start.month,
                                           day = cur_window_start.day)
                    psd_data = {}

                # Get the active stream(s) from the channel.
                geom_stream = cur_channel.get_stream(start_time = cur_window_start,
                                                     end_time = cur_window_start + window_length)

                # Get the waveform data.
                cur_stream = self.request_stream(start_time = cur_window_start,
                                                 end_time = cur_window_start + window_length,
                                                 scnl = [cur_scnl,])
                cur_stream = cur_stream.copy()

                if cur_stream:
                    self.logger.info("Processing stream %s.", cur_stream)
                    # Detrend the data.
                    try:
                        cur_stream = cur_stream.split()
                        processing_stack.execute(cur_stream)
                    except Exception as e:
                        self.logger.error('Error when processing the stream %s:\n%s', str(cur_stream), e)
                        continue

                    # Merge the stream again.
                    cur_stream = cur_stream.merge()

                    # Compute the PSD using matplotlib.mlab.psd
                    n_overlap = psd_nfft / 100 * psd_overlap
                    (P, frequ) = mlab.psd(cur_stream.traces[0].data,
                                          Fs = cur_stream.traces[0].stats.sampling_rate,
                                          NFFT = psd_nfft,
                                          noverlap = n_overlap)

                    if P.ndim == 2:
                        P = P.squeeze()

                    # Get the units of the trace data.
                    unit = []
                    for cur_trace in cur_stream:
                        cur_unit = cur_trace.stats.unit
                        if cur_unit not in unit:
                            unit.append(cur_unit)

                    if len(unit) != 1:
                        self.logger.error('Found more than one unit definition for the stream %s: %s.', cur_stream, unit)
                        unit = 'undefined'
                    else:
                        unit = unit[0]

                    # Append the psd data to the window_psd list.
                    #psd_data.append((cur_window_start, frequ, P, window_length, window_overlap,
                    #                   psd_nfft, psd_overlap, cur_scnl))
                    cur_psd = {}
                    cur_psd['frequ'] = frequ
                    cur_psd['P'] = P
                    cur_psd['window_length'] = window_length
                    cur_psd['window_overlap'] = window_overlap
                    cur_psd['psd_nfft'] = psd_nfft
                    cur_psd['psd_overlap'] = psd_overlap
                    cur_psd['scnl'] = cur_scnl
                    cur_psd['unit'] = unit
                    psd_data[cur_window_start.isoformat()] = cur_psd
                else:
                    #psd_data.append((cur_window_start, None, None, window_length, window_overlap,
                    #                   psd_nfft, psd_overlap, cur_scnl))
                    cur_psd = {}
                    cur_psd['frequ'] = None
                    cur_psd['P'] = None
                    cur_psd['window_length'] = window_length
                    cur_psd['window_overlap'] = window_overlap
                    cur_psd['psd_nfft'] = psd_nfft
                    cur_psd['psd_overlap'] = psd_overlap
                    cur_psd['scnl'] = cur_scnl
                    cur_psd['unit'] = 'undefined'
                    psd_data[cur_window_start.isoformat()] = cur_psd

            # Save the remaining psd data.
            if psd_data:
                self.save_psd_data(psd_data, cur_scnl)



    def save_psd_data(self, psd_data, scnl):
        ''' Save the psd data to a file.
        '''
        if not psd_data:
            return

        output_dir = self.pref_manager.get_value('output_dir')
        dir_name = os.path.join(output_dir, scnl[0])
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        first_time = UTCDateTime(sorted(psd_data.keys())[0])

        filename = '%s_%s.psd' % (first_time.strftime('%Y%m%d'), '_'.join(scnl))
        filename = os.path.join(dir_name, filename)
        db = shelve.open(filename)
        db['psd_data'] = psd_data
        db.close()
        self.logger.info("Saved PSD data in file %s.", filename)




    def request_stream(self, start_time, end_time, scnl):
        ''' Request a data stream from the waveclient.

        '''
        data_sources = {}
        for cur_scnl in scnl:
            if cur_scnl in self.project.scnlDataSources.keys():
                if self.project.scnlDataSources[cur_scnl] not in data_sources.keys():
                    data_sources[self.project.scnlDataSources[cur_scnl]] = [cur_scnl, ]
                else:
                    data_sources[self.project.scnlDataSources[cur_scnl]].append(cur_scnl)
            else:
                if self.project.defaultWaveclient not in data_sources.keys():
                    data_sources[self.project.defaultWaveclient] = [cur_scnl, ]
                else:
                    data_sources[self.project.defaultWaveclient].append(cur_scnl)

        stream = obspy.core.Stream()

        for cur_name in data_sources.iterkeys():
            curWaveclient = self.project.waveclient[cur_name]
            curStream =  curWaveclient.getWaveform(startTime = start_time,
                                                   endTime = end_time,
                                                   scnl = scnl)
            stream += curStream

        return stream

