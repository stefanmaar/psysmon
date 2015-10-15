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

import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons



class ExportVisible(plugins.CommandPlugin):
    ''' Export the visible (processed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'export visible',
                                       category = 'export',
                                       tags = ['export', 'visible']
                                       )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.export_icon_16


    def run(self):
        ''' Export the visible data to the project server.
        '''
        self.parent.project.export_data(uri = self.parent.collection_node.rid + '/proc_stream',
                                        data = self.parent.visible_data)


class ExportOriginal(plugins.CommandPlugin):
    ''' Export the original (unprocessed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'export original',
                                       category = 'export',
                                       tags = ['export', 'orignial']
                                       )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.export_icon_16


    def run(self):
        ''' Export the unprocessed data to the project server.
        '''
        self.parent.project.export_data(uri = self.parent.collection_node.rid + '/orig_stream',
                                        data = self.parent.original_data)





class ExportVisibleToAscii(plugins.CommandPlugin):
    ''' Export the visible (processed) data to ASCII formatted files.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'export visible to ASCII',
                                       category = 'export',
                                       tags = ['export', 'visible', 'ascii']
                                       )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.export_icon_16


    def run(self):
        ''' Export the visible data to the project server.
        '''
        # Get the export directory from the user.
        dlg = wx.DirDialog(self.parent, "Choose an export directory:",
                           style = wx.DD_DEFAULT_STYLE
                           | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() == wx.ID_OK:
            export_dir = dlg.GetPath()

            for cur_trace in self.parent.visible_data:
                cur_id = cur_trace.id.replace('.','_')
                cur_isoformat = cur_trace.stats.starttime.isoformat()
                cur_isoformat = cur_isoformat.replace(':', '')
                cur_isoformat = cur_isoformat.replace('.', '_')
                cur_filename = cur_id + '_' + cur_isoformat + '.ascii'
                cur_filename = os.path.join(export_dir, cur_filename)
                cur_trace.write(cur_filename, format = 'TSPAIR')
                self.logger.info('Exported trace %s to file %s.', cur_trace.id, cur_filename)

