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
import functools as ft

from obspy.core import UTCDateTime
import wx

import psysmon
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as preferences_manager


class Zoom(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'zoom',
                                   category = 'tools',
                                   tags = None)
        
        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.zoom_icon_16
        self.cursor = wx.CURSOR_CROSS
        #self.cursor = icons.zoom_icon_16
        #self.cursor_hotspot = (0.5, 0.5)

        self.bg = {}
        self.startTime = None
        self.endTime = None
        self.in_drag = False
        self.restore_on_release = False

        # Set the shortcut string.
        self.accelerator_string = 'SHIFT+Z'
        self.pref_accelerator_string = 'ALT+Z'

        # Accelerators for shortcuts not bound to a menu item.
        handler = ft.partial(self.on_zoom_out, ratio = 50)
        self.shortcuts['zoom_out_50'] = {'accelerator_string': '-',
                                         'handler': handler}

        handler = ft.partial(self.on_zoom_out, ratio = 25)
        self.shortcuts['zoom_out_25'] = {'accelerator_string': 'SHIFT+-',
                                         'handler': handler}

        handler = ft.partial(self.on_zoom_out, ratio = 10)
        self.shortcuts['zoom_out_10'] = {'accelerator_string': 'CTRL+-',
                                         'handler': handler}

        handler = ft.partial(self.on_zoom_out, ratio = 1)
        self.shortcuts['zoom_out_1'] = {'accelerator_string': 'ALT+-',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 50)
        self.shortcuts['zoom_in_50'] = {'accelerator_string': '+',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 25)
        self.shortcuts['zoom_in_25'] = {'accelerator_string': 'SHIFT++',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 10)
        self.shortcuts['zoom_in_10'] = {'accelerator_string': 'CTRL++',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 1)
        self.shortcuts['zoom_in_1'] = {'accelerator_string': 'ALT++',
                                       'handler': handler}
        
        

        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        resp_group = pref_page.add_group('response')

        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio',
                                                       value = 20,
                                                       limit = (1, 99))
        resp_group.add_item(item)


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.onButtonPress
        hooks['button_release_event'] = self.onButtonRelease

        return hooks


    def on_zoom_out(self, evt, ratio):
        '''
        '''
        self.parent.growTimePeriod(ratio = ratio)


    def on_zoom_in(self, evt, ratio):
        '''
        '''
        self.parent.shrinkTimePeriod(ratio = ratio)


    def activate(self):
        ''' Activate the plugin.
        '''
        InteractivePlugin.activate(self)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('"-"',),
                                                  action = self.parent.growTimePeriod)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', '"-"'),
                                                  action = self.parent.growTimePeriod,
                                                  action_kwargs = {'ratio': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', '"-"'),
                                                  action = self.parent.growTimePeriod,
                                                  action_kwargs = {'ratio': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', '"-"'),
                                                  action = self.parent.growTimePeriod,
                                                  action_kwargs = {'ratio': 1})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('"+"',),
                                                  action = self.parent.shrinkTimePeriod)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', '"+"'),
                                                  action = self.parent.shrinkTimePeriod,
                                                  action_kwargs = {'ratio': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', '"+"'),
                                                  action = self.parent.shrinkTimePeriod,
                                                  action_kwargs = {'ratio': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', '"+"'),
                                                  action = self.parent.shrinkTimePeriod,
                                                  action_kwargs = {'ratio': 1})


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        self.cleanup()
        InteractivePlugin.deactivate(self)


    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        # Clear the zoom lines.
        if hasattr(self.parent, 'viewport') and self.parent.viewport is not None:
            channel_container = self.parent.viewport.get_node(group = 'channel_container', node_type = 'container')
            for cur_container in channel_container:
                view_nodes = cur_container.get_node(node_type = 'view')
                for cur_view in view_nodes:
                    cur_view.clear_annotation_artist(parent_rid = self.rid)

            # Clear the motion notify callbacks.
            self.parent.viewport.clear_mpl_event_callbacks(event_name = 'motion_notify_event')

        self.bg = {}
        self.in_drag = False




    def onButtonPress(self, event, parent = None):
        self.logger.debug('onButtonPress - button: %s', str(event.button))
        if event.xdata is None:
            return
        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # If zoom history is available, restore the previous zoom state.
            if hasattr(self.parent, 'has_zoom_history') and self.parent.has_zoom_history():
                self.parent.undo_zoom()
                return

            # Use the right mouse button to zoom out.
            self.startTime = event.xdata
            ratio = self.pref_manager.get_value('zoom ratio')
            duration = self.parent.displayManager.endTime - self.parent.displayManager.startTime
            shrinkAmount = duration * ratio/100.0
            tmp = self.startTime
            self.startTime = tmp - shrinkAmount*2.0
            self.endTime = tmp + shrinkAmount*2.0
            self.parent.displayManager.setTimeLimits(UTCDateTime(self.startTime),
                                                   UTCDateTime(self.endTime))

            self.parent.displayManager.parent.update_display()
            return

        self.startTime = event.xdata
        self.endTime = event.xdata
        self.in_drag = True

        viewport = self.parent.viewport
        cur_view = event.canvas.GetGrandParent()
        hooks = {'motion_notify_event': self.onMouseMotion}
        viewport.register_mpl_event_callbacks(hooks)


        cur_view.plot_annotation_vline(x = event.xdata, parent_rid = self.rid, key = 'begin_line')

        cur_view.plot_panel.canvas.draw()


    def onMouseMotion(self, event, parent = None):
        self.logger.debug('mouse motion')
        if getattr(self, 'in_drag', False):
            # If mouse left button was released outside the canvas / window:
            app = wx.GetApp()
            if app is not None:
                try:
                    left_down = wx.GetMouseState().LeftIsDown()
                except Exception:
                    left_down = True
                if not left_down:
                    self.cleanup()
                    self.check_restore_tool()
                    return

        self.logger.debug('x: %f', event.x)
        if event.inaxes is not None:
            self.logger.debug('xData: %f', event.xdata)
            self.endTime = event.xdata

        viewport = getattr(self.parent, 'viewport', None)
        if viewport is None:
            return

        channel_container = viewport.get_node(group = 'channel_container', node_type = 'container')

        for cur_container in channel_container:
            view_nodes = cur_container.get_node(node_type = 'view')
            for cur_view in view_nodes:
                if event.inaxes is None:
                    inv = cur_view.axes.transData.inverted()
                    tmp = inv.transform((event.x, event.y))
                    event.xdata = tmp[0]
                if cur_view not in iter(self.bg.keys()):
                    self.bg[cur_view] = cur_view.plot_panel.canvas.copy_from_bbox(cur_view.axes.bbox)
                cur_view.plot_panel.canvas.restore_region(self.bg[cur_view])

                line_artist, label_artist = cur_view.plot_annotation_vline(x = event.xdata,
                                                                           parent_rid = self.rid,
                                                                           key = 'end_line',
                                                                           animated = True)

                cur_view.axes.draw_artist(line_artist)
                cur_view.plot_panel.canvas.blit()


    def onButtonRelease(self, event, parent = None):
        self.logger.debug('onButtonRelease')

        # Right-click release: no-op (zoom undo occurs on button press)
        if getattr(event, 'button', None) == 3:
            return

        # Only button 1 (left mouse button) during active drag performs zoom-in
        if getattr(event, 'button', None) != 1 or not getattr(self, 'in_drag', False):
            if getattr(self, 'in_drag', False):
                self.cleanup()
                self.check_restore_tool()
            return

        try:
            # Call the setTimeLimits of the displayManager.
            # The timebase of the plots is unixseconds.
            if self.startTime == self.endTime:
                # This was a single click with no drag.
                ratio = self.pref_manager.get_value('zoom ratio')
                duration = self.parent.displayManager.endTime - self.parent.displayManager.startTime
                shrinkAmount = duration * ratio/100.0
                tmp = self.startTime
                self.startTime = tmp - shrinkAmount/2.0
                self.endTime = tmp + shrinkAmount/2.0
            elif self.endTime < self.startTime:
                tmp = self.startTime
                self.startTime = self.endTime
                self.endTime = tmp

            if hasattr(self.parent, 'push_zoom_history'):
                self.parent.push_zoom_history()

            self.parent.displayManager.setTimeLimits(UTCDateTime(self.startTime),
                                                   UTCDateTime(self.endTime))

            self.parent.displayManager.parent.update_display()
        finally:
            self.cleanup()
            self.check_restore_tool()


    def check_restore_tool(self):
        ''' Check whether to restore a swapped tool.
        '''
        if getattr(self, 'restore_on_release', False):
            self.restore_on_release = False
            if hasattr(self.parent, 'restore_tool'):
                self.parent.restore_tool()
            return

        if getattr(self.parent, 'plugin_to_restore', None) is not None:
            z_down = False
            try:
                z_down = wx.GetKeyState(ord('Z')) or wx.GetKeyState(ord('z'))
            except Exception:
                pass
            if not z_down:
                if hasattr(self.parent, 'restore_tool'):
                    self.parent.restore_tool()

