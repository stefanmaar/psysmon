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

import unittest
import wx
from unittest.mock import patch, MagicMock

import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from obspy.core.utcdatetime import UTCDateTime
from psysmon.packages.tracedisplay.plugins_navigate import Navigate
from psysmon.packages.tracedisplay.plugins_zoom import Zoom
from psysmon.packages.tracedisplay.tracedisplay import TraceDisplayDlg, TraceDisplayKeyFilter


class DummyDisplayManager(object):
    def __init__(self, startTime=1000.0, endTime=2000.0):
        self.startTime = startTime
        self.endTime = endTime
        self.shrink_ratio = None
        self.grow_ratio = None
        self.advance_step = None
        self.decrease_step = None
        self.parent = None
        self.show_next_station_called = False
        self.show_prev_station_called = False

    @property
    def duration(self):
        if self.startTime is not None and self.endTime is not None:
            return self.endTime - self.startTime
        return None

    def setTimeLimits(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    def setDuration(self, duration):
        self.endTime = self.startTime + duration

    def setStartTime(self, startTime):
        duration = self.endTime - self.startTime
        self.startTime = startTime
        self.endTime = startTime + duration

    def show_next_station(self):
        self.show_next_station_called = True

    def show_prev_station(self):
        self.show_prev_station_called = True

    def advanceTimePercentage(self, step=100):
        self.advance_step = step

    def decreaseTimePercentage(self, step=100):
        self.decrease_step = step


class DummyParent(object):
    def __init__(self):
        self.displayManager = DummyDisplayManager()
        self.displayManager.parent = self
        from psysmon.gui.shortcut import ShortcutManager
        self.shortcut_manager = ShortcutManager()
        self.update_called = False
        self.plugins = []
        self.plugin_to_restore = None
        self.collection_node = type('DummyNode', (), {'rid': 'test/node'})()
        self.zoom_history = []
        self.max_zoom_history = 3
        self.orig_startTime = self.displayManager.startTime
        self.orig_duration = self.displayManager.duration
        self.logger = psysmon.get_logger(self)
        self.statusbar = type('DummyStatusbar', (), {'set_shortcut_tips_msg': lambda s, msg: None})()

    def update_display(self):
        self.update_called = True

    def advanceTime(self):
        self.displayManager.advanceTimePercentage(100)
        self.update_display()

    def decreaseTime(self):
        self.displayManager.decreaseTimePercentage(100)
        self.update_display()

    def advanceTimePercentage(self, step=100):
        self.displayManager.advanceTimePercentage(step)
        self.update_display()

    def decreaseTimePercentage(self, step=100):
        self.displayManager.decreaseTimePercentage(step)
        self.update_display()

    def check_menu_checkitem(self, plugin):
        pass

    def uncheck_menu_checkitem(self, plugin):
        pass

    def deactivate_interactive_plugin(self, plugin):
        plugin.active = False

    def activate_interactive_plugin(self, plugin):
        plugin.active = True

    def is_text_control_focused(self):
        return False

    def get_plugin(self, name):
        return TraceDisplayDlg.get_plugin(self, name)

    def get_active_interactive_plugin(self):
        return TraceDisplayDlg.get_active_interactive_plugin(self)

    def activate_interactive_tool(self, plugin):
        TraceDisplayDlg.activate_interactive_tool(self, plugin)

    def swap_tool(self, name='zoom'):
        TraceDisplayDlg.swap_tool(self, name)

    def restore_tool(self):
        TraceDisplayDlg.restore_tool(self)

    def push_zoom_history(self, start_time=None, end_time=None):
        return TraceDisplayDlg.push_zoom_history(self, start_time, end_time)

    def undo_zoom(self):
        return TraceDisplayDlg.undo_zoom(self)

    def has_zoom_history(self):
        return TraceDisplayDlg.has_zoom_history(self)

    def clear_zoom_history(self):
        return TraceDisplayDlg.clear_zoom_history(self)

    def reset_view(self):
        return TraceDisplayDlg.reset_view(self)

    def on_key_up(self, event):
        return TraceDisplayDlg.on_key_up(self, event)

    def on_char_hook(self, event):
        return TraceDisplayDlg.on_char_hook(self, event)

    def on_activate(self, event):
        return TraceDisplayDlg.on_activate(self, event)


class MockKeyEvent(object):
    def __init__(self, key_code, event_type=wx.wxEVT_KEY_UP, shift=False, ctrl=False, alt=False, cmd=False):
        self.key_code = key_code
        self.event_type = event_type
        self.shift = shift
        self.ctrl = ctrl
        self.alt = alt
        self.cmd = cmd
        self.skipped = False

    def GetKeyCode(self):
        return self.key_code

    def GetEventType(self):
        return self.event_type

    def ShiftDown(self):
        return self.shift

    def ControlDown(self):
        return self.ctrl

    def CmdDown(self):
        return self.cmd

    def AltDown(self):
        return self.alt

    def Skip(self):
        self.skipped = True


class ZoomFeaturesTestCase(unittest.TestCase):

    def test_zoom_cursor_and_accelerator(self):
        zoom = Zoom()
        self.assertEqual(zoom.cursor, wx.CURSOR_CROSS)
        self.assertEqual(zoom.accelerator_string, 'SHIFT+Z')
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.restore_on_release)

    def test_navigate_preferences_and_zoom_history_config(self):
        nav = Navigate()
        history_item = nav.pref_manager.get_item(name='zoom_history_steps')[0]
        self.assertIsNotNone(history_item)
        self.assertEqual(nav.pref_manager.get_value('zoom_history_steps'), 3)
        self.assertEqual(history_item.limit, (1, 10))

    def test_momentary_hold_to_zoom_and_clean_restore(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]

        # Navigate is active
        nav.active = True
        self.assertEqual(parent.get_active_interactive_plugin(), nav)

        # 1. User presses 'z' -> hold-to-zoom swaps to Zoom tool
        evt_down = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_DOWN)
        parent.on_char_hook(evt_down)
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)
        self.assertEqual(parent.plugin_to_restore, nav)

        # 2. User releases 'z' -> restores Navigate cleanly
        evt_up = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_UP)
        parent.on_key_up(evt_up)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_hold_to_zoom_when_no_tool_initially_active(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]

        # No tool active
        nav.active = False
        zoom.active = False

        # Pressing 'z' activates Navigate and swaps to Zoom
        evt_down = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_DOWN)
        parent.on_char_hook(evt_down)
        self.assertTrue(zoom.active)
        self.assertEqual(parent.plugin_to_restore, nav)

        # Releasing 'z' restores Navigate
        evt_up = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_UP)
        parent.on_key_up(evt_up)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_shift_z_permanently_selects_zoom(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # Shift + Z from anywhere permanently selects Zoom
        evt = MockKeyEvent(ord('Z'), shift=True)
        parent.on_char_hook(evt)
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

        # Releasing 'z' does NOT restore Navigate because it was permanent
        evt_up = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_UP)
        parent.on_key_up(evt_up)
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)

    def test_zoom_history_lifo_and_depth(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        parent.plugins = [nav]

        # Push 3 zoom levels
        parent.displayManager.startTime = 100.0
        parent.displayManager.endTime = 200.0
        parent.push_zoom_history()

        parent.displayManager.startTime = 120.0
        parent.displayManager.endTime = 180.0
        parent.push_zoom_history()

        parent.displayManager.startTime = 140.0
        parent.displayManager.endTime = 160.0
        parent.push_zoom_history()

        self.assertEqual(len(parent.zoom_history), 3)

        # Push a 4th level: depth is 3, so oldest (100, 200) should be dropped
        parent.displayManager.startTime = 145.0
        parent.displayManager.endTime = 155.0
        parent.push_zoom_history()

        self.assertEqual(len(parent.zoom_history), 3)
        self.assertEqual(parent.zoom_history[0], (UTCDateTime(120.0), UTCDateTime(180.0)))
        self.assertEqual(parent.zoom_history[-1], (UTCDateTime(145.0), UTCDateTime(155.0)))

        # Undo 1 step (LIFO)
        self.assertTrue(parent.undo_zoom())
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(145.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(155.0))
        self.assertEqual(len(parent.zoom_history), 2)

        # Undo 2nd step
        self.assertTrue(parent.undo_zoom())
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(140.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(160.0))

        # Undo 3rd step
        self.assertTrue(parent.undo_zoom())
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(120.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(180.0))

        # No more steps left
        self.assertFalse(parent.undo_zoom())

    def test_ctrl_z_and_cmd_z_undo_zoom_from_char_hook(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        parent.plugins = [nav]

        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()

        parent.displayManager.startTime = 1200.0
        parent.displayManager.endTime = 1800.0

        # Ctrl + Z
        evt_ctrl_z = MockKeyEvent(ord('z'), ctrl=True)
        parent.on_char_hook(evt_ctrl_z)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))

        # Cmd + Z
        parent.displayManager.startTime = 1300.0
        parent.displayManager.endTime = 1700.0
        parent.push_zoom_history()
        parent.displayManager.startTime = 1400.0
        parent.displayManager.endTime = 1600.0

        evt_cmd_z = MockKeyEvent(ord('z'), cmd=True)
        parent.on_char_hook(evt_cmd_z)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1300.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(1700.0))

    def test_right_click_mouse_driven_zoom_reset_while_holding_z(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # User performs a zoom-in to establish history
        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()
        parent.displayManager.startTime = 1200.0
        parent.displayManager.endTime = 1800.0

        # User holds 'z': swaps to zoom tool
        parent.on_char_hook(MockKeyEvent(ord('z')))
        self.assertTrue(zoom.active)

        # User right-clicks (button 3): undoes 1 step of zoom history
        class MockMouseEvent(object):
            def __init__(self, button, xdata=1500.0):
                self.button = button
                self.xdata = xdata

        evt_press = MockMouseEvent(button=3)
        zoom.onButtonPress(evt_press)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))
        self.assertFalse(parent.has_zoom_history())

        # Release right click: ignored, never triggers zoom-in
        evt_release = MockMouseEvent(button=3)
        zoom.onButtonRelease(evt_release)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))
        self.assertTrue(zoom.active)

        # Release 'z': cleanly restores Navigate
        parent.on_key_up(MockKeyEvent(ord('z')))
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)

    def test_space_clears_zoom_history(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        parent.plugins = [nav]

        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()
        self.assertTrue(parent.has_zoom_history())

        # Space key resets view and clears zoom history
        evt_space = MockKeyEvent(wx.WXK_SPACE)
        parent.on_char_hook(evt_space)
        self.assertFalse(parent.has_zoom_history())
        self.assertEqual(len(parent.zoom_history), 0)

    def test_drag_release_z_first_restores_on_mouse_release(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # Swap to zoom
        parent.on_char_hook(MockKeyEvent(ord('z')))
        self.assertTrue(zoom.active)

        # Start drag
        zoom.in_drag = True
        zoom.startTime = 1100.0
        zoom.endTime = 1600.0

        # User releases 'z' while drag is still active
        parent.on_key_up(MockKeyEvent(ord('z')))
        self.assertTrue(zoom.restore_on_release)
        self.assertTrue(zoom.active)  # Still active until mouse release

        # Mouse release occurs
        class MockButton1Event(object):
            def __init__(self):
                self.button = 1

        zoom.onButtonRelease(MockButton1Event())
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.restore_on_release)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_escape_cancels_active_drag_and_restores_tool(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        parent.on_char_hook(MockKeyEvent(ord('z')))
        self.assertTrue(zoom.active)
        zoom.in_drag = True

        # User presses Escape
        parent.on_char_hook(MockKeyEvent(wx.WXK_ESCAPE))
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_window_focus_loss_restores_tool(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        parent.on_char_hook(MockKeyEvent(ord('z')))
        self.assertTrue(zoom.active)

        class MockActivateEvent(object):
            def __init__(self, active=False):
                self.active = active
                self.skipped = False

            def GetActive(self):
                return self.active

            def Skip(self):
                self.skipped = True

        parent.on_activate(MockActivateEvent(active=False))
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_global_event_filter(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        parent.swap_tool('zoom')
        self.assertTrue(zoom.active)

        key_filter = TraceDisplayKeyFilter(parent)

        # Unrelated key: skipped, tool stays zoom
        evt_a = MockKeyEvent(ord('A'), event_type=wx.wxEVT_KEY_UP)
        result = key_filter.FilterEvent(evt_a)
        self.assertEqual(result, wx.EventFilter.Event_Skip)
        self.assertTrue(zoom.active)

        # 'z' key-up: filtered and tool restored
        evt_z = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_UP)
        result = key_filter.FilterEvent(evt_z)
        self.assertEqual(result, wx.EventFilter.Event_Skip)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_station_navigation_shortcuts_preserved(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        nav.activate()

        # Check that station switching shortcuts (WXK_DOWN, WXK_UP) are intact
        shortcuts = parent.shortcut_manager.get_shortcut(origin_rid=nav.rid)
        down_shortcuts = [s for s in shortcuts if s.key_combination == ('WXK_DOWN',)]
        up_shortcuts = [s for s in shortcuts if s.key_combination == ('WXK_UP',)]
        self.assertEqual(len(down_shortcuts), 1)
        self.assertEqual(len(up_shortcuts), 1)

        down_shortcuts[0].action()
        self.assertTrue(parent.displayManager.show_next_station_called)

        up_shortcuts[0].action()
        self.assertTrue(parent.displayManager.show_prev_station_called)


if __name__ == '__main__':
    unittest.main()
