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

import functools as ft
import logging

import wx

import psysmon
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons


class Navigate(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'navigate',
                                   category = 'tools',
                                   tags = None)
        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.star_icon_16
        self.cursor = wx.CURSOR_HAND

        # Set the shortcut string.
        self.accelerator_string = 'N'

        # Accelerators for shortcuts not bound to a menu item.
        handler = ft.partial(self.on_time_advance, step = 100)
        self.shortcuts['advance_100'] = {'accelerator_string': 'Right',
                                         'handler': handler}

        handler = ft.partial(self.on_time_advance, step = 25)
        self.shortcuts['advance_25'] = {'accelerator_string': 'SHIFT+Right',
                                        'handler': handler}

        handler = ft.partial(self.on_time_advance, step = 10)
        self.shortcuts['advance_10'] = {'accelerator_string': 'CTRL+Right',
                                        'handler': handler}

        handler = ft.partial(self.on_time_advance, step = 1)
        self.shortcuts['advance_1'] = {'accelerator_string': 'ALT+Right',
                                       'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 100)
        self.shortcuts['regress_100'] = {'accelerator_string': 'Left',
                                         'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 25)
        self.shortcuts['regress_25'] = {'accelerator_string': 'SHIFT+Left',
                                        'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 10)
        self.shortcuts['regress_10'] = {'accelerator_string': 'CTRL+Left',
                                        'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 1)
        self.shortcuts['regress_1'] = {'accelerator_string': 'ALT+Left',
                                       'handler': handler}


    def getHooks(self):
        hooks = {}

        #hooks['button_press_event'] = self.onButtonPress
        #hooks['button_release_event'] = self.onButtonRelease

        return hooks


    def on_time_advance(self, evt, step):
        '''
        '''
        self.parent.advanceTimePercentage(step = step)


    def on_time_regress(self, evt, step):
        '''
        '''
        self.parent.decreaseTimePercentage(step = step)


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


