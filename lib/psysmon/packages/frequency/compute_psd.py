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

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from obspy.core.utcdatetime import UTCDateTime


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


    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        pagename = '3 output'
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

	# Split the timespan into processing chunks.
        overlap_length = window_length * (1 - window_overlap/100.)

        windows_between = int((end_time - start_time)/overlap_length)
        window_list = [start_time + x * overlap_length for x in range(windows_between)]
	window_list[0] = start_time


        # Process each SCNL
        for cur_scnl in self.pref_manager.get_value('scnl_list'):
            # Get the channel instance from the inventory.

            window_psd = []

            # Compute the psd for each window.
            for k, cur_window in enumerate(window_list):
                print "Computing window %s." % str(cur_window)

                # If the current window starts on a new day, save the old
                # window_psd to a daily file.

                # Get the waveform data.

                # Detrend the data.

                # Get the sensor parameters.

                # If sensor parameters are available: convert to velocity.

                # Compute the PSD using matplotlib.mlab.psd

                # Append the psd data to the window_psd list.




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

