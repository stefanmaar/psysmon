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
                                       name = 'export',
                                       category = 'export',
                                       tags = ['export']
                                       )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.export_icon_16


        # Add the plugin preferences.
        item = preferences_manager.SingleChoicePrefItem(name = 'source',
                                                        label = 'source',
                                                        value = 'visible',
                                                        limit = ['original', 'visible'],
                                                        tool_tip = 'The data to export.')
        self.pref_manager.add_item(item = item)

        obspy_export_formats = ['GSE2', 'MSEED', 'PICKLE', 'Q',
                                'SAC', 'SACXY', 'SEGY', 'SH_ASC', 'SLIST',
                                'SU', 'TSPAIR']
        self.export_format_ext = {'GSE2' : 'gse2',
                                  'MSEED' : 'msd',
                                  'PICKLE' : 'pkl',
                                  'Q' : 'q',
                                  'SAC' : 'sac',
                                  'SACYX' : 'sacyx',
                                  'SEGY' : 'segy',
                                  'SH_ASC' : 'asc',
                                  'SLIST' : 'asc',
                                  'SU' : 'su',
                                  'TSPAIR' : 'asc'}
        item = preferences_manager.SingleChoicePrefItem(name = 'export_format',
                                                        label = 'export format',
                                                        value = 'TSPAIR',
                                                        limit = obspy_export_formats,
                                                        tool_tip = 'The available export file formats. See the obspy documentation for further details on specific formats.')
        self.pref_manager.add_item(item = item)


        item = preferences_manager.DirBrowsePrefItem(name = 'export_dir',
                                                     label = 'export directory',
                                                     value = '',
                                                     tool_tip = 'The directory where to save the exported files.')
        self.pref_manager.add_item(item = item)


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
            cur_id = cur_trace.id.replace('.','_')
            cur_isoformat = cur_trace.stats.starttime.isoformat()
            cur_isoformat = cur_isoformat.replace(':', '')
            cur_isoformat = cur_isoformat.replace('.', '_')
            cur_filename = cur_id + '_' + cur_isoformat + '.' + self.export_format_ext[export_format]
            cur_filename = os.path.join(export_dir, cur_filename)
            cur_trace.write(cur_filename, format = export_format)
            self.logger.info('Exported trace %s to file %s.', cur_trace.id, cur_filename)

