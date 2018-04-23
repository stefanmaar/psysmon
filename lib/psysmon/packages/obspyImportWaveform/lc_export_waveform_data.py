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

import os

import obspy.core.util.base


import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog as gui_preference_dialog


class ExportWaveformData(package_nodes.LooperCollectionChildNode):
    ''' Export waveform data to a file.

    '''
    name = 'export waveform data'
    mode = 'looper child'
    category = 'export'
    tags = ['waveform', 'data', 'export']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_format_preferences()
        self.create_timespan_preferences()
        self.create_output_preferences()


    @property
    def pre_stream_length(self):
        ''' The time-span needed for correct processing prior to the start time
        of the stream passed to the execute method [s].
        '''
        return self.pref_manager.get_value('pre_event_length')


    @property
    def post_stream_length(self):
        ''' The time-span needed for correct processing after the start time
        of the stream passed to the execute method [s].
        '''
        return self.pref_manager.get_value('pre_event_length')


    def create_format_preferences(self):
        ''' Create the format preferences.
        '''
        format_page = self.pref_manager.add_page('Format')
        format_group = format_page.add_group('format')

        obspy_formats = obspy.core.util.base.ENTRY_POINTS['waveform'].keys()
        obspy_formats = sorted(obspy_formats)
        item = psy_pm.SingleChoicePrefItem(name = 'file_format',
                                           label = 'file format',
                                           limit = obspy_formats,
                                           value = 'MSEED',
                                           tool_tip = 'The export file format supported by obspy.')
        format_group.add_item(item)

        # TODO: Add format preferences for selected output formats.


    def create_timespan_preferences(self):
        ''' Create the timespan preferences.
        '''
        timespan_page = self.pref_manager.add_page('Time-span')
        window_group = timespan_page.add_group('time window')

        # The pre-event time for the export.
        item = psy_pm.FloatSpinPrefItem(name = 'pre_event_length',
                                        label = 'pre event length',
                                        value = 10,
                                        digits = 3,
                                        limit = (0, 1000000),
                                        tool_tip = 'The seconds prepended to the exported event.')
        window_group.add_item(item)

        # The post-event time for the export.
        item = psy_pm.FloatSpinPrefItem(name = 'post_event_length',
                                        label = 'post event length',
                                        value = 10,
                                        digits = 3,
                                        limit = (0, 1000000),
                                        tool_tip = 'The seconds appended to the exported event.')
        window_group.add_item(item)


    def create_output_preferences(self):
        ''' Create the output preferences.
        '''
        output_page = self.pref_manager.add_page('Output')
        dest_group = output_page.add_group('destination')
        folder_group = output_page.add_group('folder')
        ds_group = output_page.add_group('data source')

        # The destination option.
        item = psy_pm.SingleChoicePrefItem(name = 'destination',
                                           label = 'destination',
                                           limit = ('folder', 'data source'),
                                           value = 'folder',
                                           hooks = {'on_value_change': self.on_destination_changed},
                                           tool_tip = 'The location where the exported data files will be saved.')
        dest_group.add_item(item)

        # The destination folder.
        item = psy_pm.DirBrowsePrefItem(name = 'folder',
                                        value = '',
                                        tool_tip = 'The folder where the data files will be saved.')
        folder_group.add_item(item)

        # The waveclient to work with.
        item = psy_pm.SingleChoicePrefItem(name = 'waveclient',
                                           label = 'waveclient',
                                           limit = (),
                                           value = '',
                                           tool_tip = 'The available database waveclients.',
                                           hooks = {'on_value_change': self.on_waveclient_selected})
        ds_group.add_item(item)

        # The waveform directories of the waveclient.
        column_labels = ['db_id', 'waveclient', 'waveform dir', 'alias', 'description',
                         'data file extension', 'first import', 'last scan']
        item = psy_pm.ListCtrlEditPrefItem(name = 'wf_dir',
                                           label = 'waveform directory',
                                           value = [],
                                           column_labels = column_labels,
                                           limit = [],
                                           tool_tip = 'The available waveform directories.',
                                           hooks = {'on_value_change': self.on_wf_dir_selected})

        ds_group.add_item(item)




    def on_destination_changed(self):
        ''' Handle the change of the destination preference value.
        '''
        if self.pref_manager.get_value('destination') == 'folder':
            enable = ['folder',]
            disable = ['waveclient', 'wf_dir']
        elif self.pref_manager.get_value('destination') == 'data source':
            enable = ['waveclient', 'wf_dir']
            disable = ['folder',]

        for cur_item_name in enable:
            item = self.pref_manager.get_item(cur_item_name)[0]
            item.enable_gui_element()

        for cur_item_name in disable:
            item = self.pref_manager.get_item(cur_item_name)[0]
            item.disable_gui_element()


    def on_wf_dir_selected(self):
        ''' Handle selections of the waveform directory.
        '''
        selected_wf_dir = self.pref_manager.get_value('wf_dir')
        if selected_wf_dir:
            selected_wf_dir = selected_wf_dir[0]
        else:
            return

        item = self.pref_manager.get_item('search_path')[0]
        control_element = item.gui_element[0].controlElement
        item.start_directory = selected_wf_dir.alias
        control_element.startDirectory = selected_wf_dir.alias


    def on_waveclient_selected(self):
        ''' Handle selections of the waveclient.
        '''
        selected_waveclient = self.pref_manager.get_value('waveclient')
        if not selected_waveclient:
            return

        client = self.project.waveclient[selected_waveclient]
        client.loadWaveformDirList()
        waveform_dir_list = client.waveformDirList
        self.pref_manager.set_limit('wf_dir', waveform_dir_list)

        # Select existing values based on the waveform dir id.
        values = self.pref_manager.get_value('wf_dir')
        value_ids = [x[0] for x in values]
        values = [x for x in waveform_dir_list if x[0] in value_ids]
        values = list(set(values))
        self.pref_manager.set_value('wf_dir', values)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        self.on_destination_changed()

        dlg.ShowModal()
        dlg.Destroy()



    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the looper child node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Check for needed keyword arguments.
        if not self.kwargs_exists(['event'], **kwargs):
            event = None
        else:
            event = kwargs['event']

        destination = self.pref_manager.get_value('destination')
        if destination == 'folder':
            self.export_to_folder(stream = stream,
                                  channels = channels,
                                  event = event)
        elif destination == 'data source':
            self.export_to_data_source(stream = stream)



    def export_to_folder(self, stream, channels, event = None):
        ''' Write the data stream to a folder.
        '''
        export_format = self.pref_manager.get_value('file_format')
        dest_dir = self.pref_manager.get_value('folder')

        for cur_channel in channels:
            if len(cur_channel.streams) > 1:
                self.logger.error("Can't handle multiple assigned streams. Skipping channel %s.", cur_channel.scnl)
                continue
            cur_rec_stream = cur_channel.streams[0].item
            orig_serial = cur_rec_stream.serial
            tmp = cur_rec_stream.name.split(':')
            orig_loc = tmp[0]
            orig_channel = tmp[1]
            orig_net = cur_channel.parent_station.network

            cur_stream = stream.select(network = cur_channel.parent_station.network,
                                       station = cur_channel.parent_station.name,
                                       location = cur_channel.parent_station.location,
                                       channel = cur_channel.name)
            cur_stream = cur_stream.split()
            for cur_trace in cur_stream:
                cur_trace.stats.network = orig_net
                cur_trace.stats.station = orig_serial
                cur_trace.stats.location = orig_loc
                cur_trace.stats.channel = orig_channel
                cur_start = cur_trace.stats.starttime
                filename = '%d_%03d_%02d%02d%02d_%s_%s_%s_%s.msd' % (cur_start.year,
                                                           cur_start.julday,
                                                           cur_start.hour,
                                                           cur_start.minute,
                                                           cur_start.second,
                                                           orig_net,
                                                           orig_serial,
                                                           orig_loc,
                                                           orig_channel)

                if event:
                    dest_path = os.path.join(dest_dir, 'event_%010d' % event.db_id)
                else:
                    dest_path = dest_dir

                dest_path = os.path.join(dest_path, str(cur_start.year), str(cur_start.julday), orig_serial)


                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)

                file_path = os.path.join(dest_path, filename)
                try:
                    cur_trace.write(file_path, format = export_format)
                except Exception as e:
                    self.logger.exception(e)
