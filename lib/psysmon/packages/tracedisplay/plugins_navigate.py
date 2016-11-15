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
import wx
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons
from obspy.core import UTCDateTime
import psysmon.core.preferences_manager as preferences_manager

class Zoom(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'navigate',
                                   category = 'view',
                                   tags = None
                                  )
        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.star_icon_16
        self.cursor = wx.CURSOR_HAND


    def getHooks(self):
        hooks = {}

        #hooks['button_press_event'] = self.onButtonPress
        #hooks['button_release_event'] = self.onButtonRelease

        return hooks


    def activate(self):
        ''' Activate the plugin.
        '''
        InteractivePlugin.activate(self)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_DOWN',),
                                                  action = self.parent.displayManager.show_next_station)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_UP',),
                                                  action = self.parent.displayManager.show_prev_station)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_RIGHT',),
                                                  action = self.parent.advanceTime)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', 'WXK_RIGHT'),
                                                  action = self.parent.advanceTimePercentage,
                                                  action_kwargs = {'step': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', 'WXK_RIGHT'),
                                                  action = self.parent.advanceTimePercentage,
                                                  action_kwargs = {'step': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', 'WXK_RIGHT'),
                                                  action = self.parent.advanceTimePercentage,
                                                  action_kwargs = {'step': 1})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_LEFT',),
                                                  action = self.parent.decreaseTime)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', 'WXK_LEFT'),
                                                  action = self.parent.decreaseTimePercentage,
                                                  action_kwargs = {'step': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', 'WXK_LEFT'),
                                                  action = self.parent.decreaseTimePercentage,
                                                  action_kwargs = {'step': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', 'WXK_LEFT'),
                                                  action = self.parent.decreaseTimePercentage,
                                                  action_kwargs = {'step': 1})


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        InteractivePlugin.deactivate(self)


