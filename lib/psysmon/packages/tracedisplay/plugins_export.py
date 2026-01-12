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

import logging
import os

import wx

import psysmon
import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons
import psysmon.core.preferences_manager as preferences_manager



class ExportVisible(plugins.CommandPlugin):
    ''' Export the visible (processed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'export to file',
                                       category = 'export',
                                       tags = ['export']
                                       )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.iconsBlack16.download_icon_16


        self.exp_options = {}
        self.exp_options['wav'] = {'rescale': True,
                                   'width': 4}


        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        exp_group = pref_page.add_group('export')

        item = preferences_manager.SingleChoicePrefItem(name = 'source',
                                                        label = 'source',
                                                        value = 'visible',
                                                        limit = ['original', 'visible'],
                                                        tool_tip = 'The data to export.')
        exp_group.add_item(item)

        obspy_export_formats = ['GSE2', 'MSEED', 'PICKLE', 'Q',
                                'SAC', 'SACXY', 'SEGY', 'SH_ASC', 'SLIST',
                                'SU', 'TSPAIR', 'WAV']
        self.export_format_ext = {'GSE2': 'gse2',
                                  'MSEED': 'msd',
                                  'PICKLE': 'pkl',
                                  'Q': 'q',
                                  'SAC': 'sac',
                                  'SACYX': 'sacyx',
                                  'SEGY': 'segy',
                                  'SH_ASC': 'asc',
                                  'SLIST': 'asc',
                                  'SU': 'su',
                                  'TSPAIR': 'asc',
                                  'WAV': 'wav'}
        item = preferences_manager.SingleChoicePrefItem(name = 'export_format',
                                                        label = 'export format',
                                                        value = 'MSEED',
                                                        limit = obspy_export_formats,
                                                        tool_tip = 'The available export file formats. See the obspy documentation for further details on specific formats.')
        exp_group.add_item(item)


        item = preferences_manager.DirBrowsePrefItem(name = 'export_dir',
                                                     label = 'export directory',
                                                     value = '',
                                                     tool_tip = 'The directory where to save the exported files.')
        exp_group.add_item(item)


    def run(self):
        ''' Export the visible data to the project server.
        '''
        if self.pref_manager.get_value('source') == 'visible':
            data = self.parent.visible_data
        elif self.pref_manager.get_value('source') == 'original':
            data = self.parent.original_data

        export_dir = self.pref_manager.get_value('export_dir')

        if export_dir == '':
            # Get the export directory from the user.
            dlg = wx.DirDialog(self.parent, "Choose an export directory:",
                               style = wx.DD_DEFAULT_STYLE
                               | wx.DD_DIR_MUST_EXIST)

            if dlg.ShowModal() == wx.ID_OK:
                export_dir = dlg.GetPath()
                self.pref_manager.set_value('export_dir', export_dir)
            else:
                return

        export_format = self.pref_manager.get_value('export_format')

        for cur_trace in data:
            cur_id = cur_trace.id.replace('.', '_')
            cur_isoformat = cur_trace.stats.starttime.isoformat()
            cur_isoformat = cur_isoformat.replace(':', '')
            cur_isoformat = cur_isoformat.replace('.', '_')
            cur_filename = cur_id + '_' + cur_isoformat + '.' + self.export_format_ext[export_format]
            cur_filename = os.path.join(export_dir, cur_filename)
            if export_format.lower() in self.exp_options:
                exp_options = self.exp_options[export_format.lower()]

                if export_format.lower() == 'wav':
                    exp_options['framerate'] = cur_trace.stats.sampling_rate
            else:
                exp_options = {}
            cur_trace.write(cur_filename, format = export_format, **exp_options)
            self.logger.info('Exported trace %s to file %s.', cur_trace.id, cur_filename)

