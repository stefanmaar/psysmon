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

import psysmon
from psysmon.core.plugins import CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons


class ResetView(CommandPlugin):
    ''' Reset all views to the original view.
    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.
        '''
        CommandPlugin.__init__(self,
                               name = 'reset view',
                               category = 'control',
                               tags = ['view', 'reset'],
                               position_pref = 2,
                               )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.reload_icon_16

        # Set the shortcut string.
        self.accelerator_string = 'Space'

    def run(self):
        ''' Reset the display to the original view.
        '''
        if hasattr(self.parent, 'reset_view'):
            self.parent.reset_view()
