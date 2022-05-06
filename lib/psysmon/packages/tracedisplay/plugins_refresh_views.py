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

from psysmon.core.plugins import CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons


class Refresh(CommandPlugin):
    ''' Refresh all views.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        CommandPlugin.__init__(self,
                               name = 'refresh views',
                               category = 'control',
                               tags = ['view', 'refresh'],
                               position_pref = 1,
                               )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.refresh_icon_16

        # Set the shortcut string.
        self.accelerator_string = 'CTRL+R'


    def run(self):
        ''' Export the visible data to the project server.
        '''
        self.parent.update_display()
