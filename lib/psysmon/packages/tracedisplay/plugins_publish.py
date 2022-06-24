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



class PublishVisible(plugins.CommandPlugin):
    ''' Publish the visible (processed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'publish visible',
                                       category = 'export',
                                       tags = ['publish', 'visible']
                                       )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.iconsBlack16.export_icon_16



    def run(self):
        ''' Publish the visible data to the project server.
        '''
        self.parent.project.export_data(uri = self.parent.collection_node.rid + '/proc_stream',
                                        data = self.parent.visible_data)


class PublishOriginal(plugins.CommandPlugin):
    ''' Publish the original (unprocessed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'publish original',
                                       category = 'export',
                                       tags = ['publish', 'orignial']
                                       )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.iconsBlack16.export_icon_16


    def run(self):
        ''' Export the unprocessed data to the project server.
        '''
        self.parent.project.export_data(uri = self.parent.collection_node.rid + '/orig_stream',
                                        data = self.parent.original_data)

