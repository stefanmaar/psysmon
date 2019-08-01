from __future__ import absolute_import
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
import logging
import itertools
from operator import itemgetter, attrgetter
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub
import time
import wx
from wx import CallAfter
import wx.aui
import wx.lib.colourdb
from obspy.core import Stream
import psysmon.core.gui as psygui
import psysmon.core.packageNodes
from psysmon.core.packageNodes import CollectionNode
from psysmon.core.processingStack import ProcessingStack
from psysmon.packages.geometry.inventory import Inventory
from psysmon.packages.geometry.db_inventory import DbInventory
from obspy.core.utcdatetime import UTCDateTime
from . import container
import psysmon.core.preferences_manager as pref_manager
import psysmon.core.gui_preference_dialog as psy_guiprefdlg
import psysmon.core.plugins
import psysmon.core.util
import psysmon.packages.event.core as ev_core
import psysmon.core.gui
import psysmon.core.gui_view

try:
    from agw import foldpanelbar as fpb
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.foldpanelbar as fpb

try:
    from agw import ribbon as ribbon
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.ribbon as ribbon

try:
    from agw import pycollapsiblepane as pcp
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.pycollapsiblepane as pcp

keyMap = {
    wx.WXK_BACK : "WXK_BACK",
    wx.WXK_TAB : "WXK_TAB",
    wx.WXK_RETURN : "WXK_RETURN",
    wx.WXK_ESCAPE : "WXK_ESCAPE",
    wx.WXK_SPACE : "WXK_SPACE",
    wx.WXK_DELETE : "WXK_DELETE",
    wx.WXK_START : "WXK_START",
    wx.WXK_LBUTTON : "WXK_LBUTTON",
    wx.WXK_RBUTTON : "WXK_RBUTTON",
    wx.WXK_CANCEL : "WXK_CANCEL",
    wx.WXK_MBUTTON : "WXK_MBUTTON",
    wx.WXK_CLEAR : "WXK_CLEAR",
    wx.WXK_SHIFT : "WXK_SHIFT",
    wx.WXK_ALT : "WXK_ALT",
    wx.WXK_CONTROL : "WXK_CONTROL",
    wx.WXK_MENU : "WXK_MENU",
    wx.WXK_PAUSE : "WXK_PAUSE",
    wx.WXK_CAPITAL : "WXK_CAPITAL",
    #wx.WXK_PRIOR : "WXK_PRIOR",
    #wx.WXK_NEXT : "WXK_NEXT",
    wx.WXK_END : "WXK_END",
    wx.WXK_HOME : "WXK_HOME",
    wx.WXK_LEFT : "WXK_LEFT",
    wx.WXK_UP : "WXK_UP",
    wx.WXK_RIGHT : "WXK_RIGHT",
    wx.WXK_DOWN : "WXK_DOWN",
    wx.WXK_SELECT : "WXK_SELECT",
    wx.WXK_PRINT : "WXK_PRINT",
    wx.WXK_EXECUTE : "WXK_EXECUTE",
    wx.WXK_SNAPSHOT : "WXK_SNAPSHOT",
    wx.WXK_INSERT : "WXK_INSERT",
    wx.WXK_HELP : "WXK_HELP",
    wx.WXK_NUMPAD0 : "WXK_NUMPAD0",
    wx.WXK_NUMPAD1 : "WXK_NUMPAD1",
    wx.WXK_NUMPAD2 : "WXK_NUMPAD2",
    wx.WXK_NUMPAD3 : "WXK_NUMPAD3",
    wx.WXK_NUMPAD4 : "WXK_NUMPAD4",
    wx.WXK_NUMPAD5 : "WXK_NUMPAD5",
    wx.WXK_NUMPAD6 : "WXK_NUMPAD6",
    wx.WXK_NUMPAD7 : "WXK_NUMPAD7",
    wx.WXK_NUMPAD8 : "WXK_NUMPAD8",
    wx.WXK_NUMPAD9 : "WXK_NUMPAD9",
    wx.WXK_MULTIPLY : "WXK_MULTIPLY",
    wx.WXK_ADD : "WXK_ADD",
    wx.WXK_SEPARATOR : "WXK_SEPARATOR",
    wx.WXK_SUBTRACT : "WXK_SUBTRACT",
    wx.WXK_DECIMAL : "WXK_DECIMAL",
    wx.WXK_DIVIDE : "WXK_DIVIDE",
    wx.WXK_F1 : "WXK_F1",
    wx.WXK_F2 : "WXK_F2",
    wx.WXK_F3 : "WXK_F3",
    wx.WXK_F4 : "WXK_F4",
    wx.WXK_F5 : "WXK_F5",
    wx.WXK_F6 : "WXK_F6",
    wx.WXK_F7 : "WXK_F7",
    wx.WXK_F8 : "WXK_F8",
    wx.WXK_F9 : "WXK_F9",
    wx.WXK_F10 : "WXK_F10",
    wx.WXK_F11 : "WXK_F11",
    wx.WXK_F12 : "WXK_F12",
    wx.WXK_F13 : "WXK_F13",
    wx.WXK_F14 : "WXK_F14",
    wx.WXK_F15 : "WXK_F15",
    wx.WXK_F16 : "WXK_F16",
    wx.WXK_F17 : "WXK_F17",
    wx.WXK_F18 : "WXK_F18",
    wx.WXK_F19 : "WXK_F19",
    wx.WXK_F20 : "WXK_F20",
    wx.WXK_F21 : "WXK_F21",
    wx.WXK_F22 : "WXK_F22",
    wx.WXK_F23 : "WXK_F23",
    wx.WXK_F24 : "WXK_F24",
    wx.WXK_NUMLOCK : "WXK_NUMLOCK",
    wx.WXK_SCROLL : "WXK_SCROLL",
    wx.WXK_PAGEUP : "WXK_PAGEUP",
    wx.WXK_PAGEDOWN : "WXK_PAGEDOWN",
    wx.WXK_NUMPAD_SPACE : "WXK_NUMPAD_SPACE",
    wx.WXK_NUMPAD_TAB : "WXK_NUMPAD_TAB",
    wx.WXK_NUMPAD_ENTER : "WXK_NUMPAD_ENTER",
    wx.WXK_NUMPAD_F1 : "WXK_NUMPAD_F1",
    wx.WXK_NUMPAD_F2 : "WXK_NUMPAD_F2",
    wx.WXK_NUMPAD_F3 : "WXK_NUMPAD_F3",
    wx.WXK_NUMPAD_F4 : "WXK_NUMPAD_F4",
    wx.WXK_NUMPAD_HOME : "WXK_NUMPAD_HOME",
    wx.WXK_NUMPAD_LEFT : "WXK_NUMPAD_LEFT",
    wx.WXK_NUMPAD_UP : "WXK_NUMPAD_UP",
    wx.WXK_NUMPAD_RIGHT : "WXK_NUMPAD_RIGHT",
    wx.WXK_NUMPAD_DOWN : "WXK_NUMPAD_DOWN",
    #wx.WXK_NUMPAD_PRIOR : "WXK_NUMPAD_PRIOR",
    wx.WXK_NUMPAD_PAGEUP : "WXK_NUMPAD_PAGEUP",
    #wx.WXK_NUMPAD_NEXT : "WXK_NUMPAD_NEXT",
    wx.WXK_NUMPAD_PAGEDOWN : "WXK_NUMPAD_PAGEDOWN",
    wx.WXK_NUMPAD_END : "WXK_NUMPAD_END",
    wx.WXK_NUMPAD_BEGIN : "WXK_NUMPAD_BEGIN",
    wx.WXK_NUMPAD_INSERT : "WXK_NUMPAD_INSERT",
    wx.WXK_NUMPAD_DELETE : "WXK_NUMPAD_DELETE",
    wx.WXK_NUMPAD_EQUAL : "WXK_NUMPAD_EQUAL",
    wx.WXK_NUMPAD_MULTIPLY : "WXK_NUMPAD_MULTIPLY",
    wx.WXK_NUMPAD_ADD : "WXK_NUMPAD_ADD",
    wx.WXK_NUMPAD_SEPARATOR : "WXK_NUMPAD_SEPARATOR",
    wx.WXK_NUMPAD_SUBTRACT : "WXK_NUMPAD_SUBTRACT",
    wx.WXK_NUMPAD_DECIMAL : "WXK_NUMPAD_DECIMAL",
    wx.WXK_NUMPAD_DIVIDE : "WXK_NUMPAD_DIVIDE",

    wx.WXK_WINDOWS_LEFT : "WXK_WINDOWS_LEFT",
    wx.WXK_WINDOWS_RIGHT : "WXK_WINDOWS_RIGHT",
    wx.WXK_WINDOWS_MENU : "WXK_WINDOWS_MENU",

    wx.WXK_COMMAND : "WXK_COMMAND",

    wx.WXK_SPECIAL1 : "WXK_SPECIAL1",
    wx.WXK_SPECIAL2 : "WXK_SPECIAL2",
    wx.WXK_SPECIAL3 : "WXK_SPECIAL3",
    wx.WXK_SPECIAL4 : "WXK_SPECIAL4",
    wx.WXK_SPECIAL5 : "WXK_SPECIAL5",
    wx.WXK_SPECIAL6 : "WXK_SPECIAL6",
    wx.WXK_SPECIAL7 : "WXK_SPECIAL7",
    wx.WXK_SPECIAL8 : "WXK_SPECIAL8",
    wx.WXK_SPECIAL9 : "WXK_SPECIAL9",
    wx.WXK_SPECIAL10 : "WXK_SPECIAL10",
    wx.WXK_SPECIAL11 : "WXK_SPECIAL11",
    wx.WXK_SPECIAL12 : "WXK_SPECIAL12",
    wx.WXK_SPECIAL13 : "WXK_SPECIAL13",
    wx.WXK_SPECIAL14 : "WXK_SPECIAL14",
    wx.WXK_SPECIAL15 : "WXK_SPECIAL15",
    wx.WXK_SPECIAL16 : "WXK_SPECIAL16",
    wx.WXK_SPECIAL17 : "WXK_SPECIAL17",
    wx.WXK_SPECIAL18 : "WXK_SPECIAL18",
    wx.WXK_SPECIAL19 : "WXK_SPECIAL19",
    wx.WXK_SPECIAL2 : "WXK_SPECIAL2",
}


class TraceDisplay(psysmon.core.packageNodes.CollectionNode):
    '''

    '''
    name = 'tracedisplay'
    mode = 'editable'
    category = 'Display'
    tags = ['development']


    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)


        pref_page = self.pref_manager.add_page('Preferences')
        time_group = pref_page.add_group('time range')
        comp_group = pref_page.add_group('component selection')

        pref_item = pref_manager.DateTimeEditPrefItem(name = 'start_time',
                                    label = 'start time',
                                    value = UTCDateTime('2012-07-09T00:00:00'))
        time_group.add_item(pref_item)

        pref_item = pref_manager.FloatSpinPrefItem(name = 'duration',
                                    label = 'duration',
                                    value = 300.,
                                    limit = (0, 86400))
        time_group.add_item(pref_item)

        pref_item = pref_manager.SingleChoicePrefItem(name = 'display_mode',
                                                      label = 'display mode',
                                                      limit = ('network', 'array'),
                                                      value = 'network',
                                                      hooks = {'on_value_change': self.on_display_mode_changed})
        comp_group.add_item(pref_item)


        pref_item = pref_manager.MultiChoicePrefItem(name = 'show_stations',
                                                     label = 'stations',
                                                     limit = ('ALBA', 'BISA', 'SITA'),
                                                     value = ['ALBA'])
        comp_group.add_item(pref_item)


        pref_item = pref_manager.MultiChoicePrefItem(name = 'show_arrays',
                                                     label = 'arrays',
                                                     limit = ('array_name', ),
                                                     value = ['array_name'])
        comp_group.add_item(pref_item)


        pref_item = pref_manager.MultiChoicePrefItem(name = 'show_channels',
                                                     label = 'channels',
                                                     limit = ('HHZ', 'HHN', 'HHE'),
                                                     value = ['HHZ',])
        comp_group.add_item(pref_item)


        pref_item = pref_manager.SingleChoicePrefItem(name = 'sort_stations',
                                                      label = 'sort stations',
                                                      limit = ('by name',),
                                                      value = 'by name')
        comp_group.add_item(pref_item)


    def on_display_mode_changed(self):
        '''
        '''
        if self.pref_manager.get_value('display_mode') == 'network':
            item = self.pref_manager.get_item('show_stations')[0]
            item.enable_gui_element()
            item = self.pref_manager.get_item('show_arrays')[0]
            item.disable_gui_element()
        elif self.pref_manager.get_value('display_mode') == 'array':
            item = self.pref_manager.get_item('show_stations')[0]
            item.disable_gui_element()
            item = self.pref_manager.get_item('show_arrays')[0]
            item.enable_gui_element()

    def edit(self):
        stations = sorted([x.name + ':' + x.network + ':' + x.location for x in self.project.geometry_inventory.get_station()])
        self.pref_manager.set_limit('show_stations', stations)

        arrays = sorted([x.name for x in self.project.geometry_inventory.arrays])
        self.pref_manager.set_limit('show_arrays', arrays)

        channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
        self.pref_manager.set_limit('show_channels', channels)


        dlg = psy_guiprefdlg.ListbookPrefDialog(preferences = self.pref_manager)
        self.on_display_mode_changed()
        dlg.ShowModal()
        dlg.Destroy()

    def execute(self, prevNodeOutput={}):

        self.logger.debug('Executing TraceDisplay')


        app = psygui.PSysmonApp()

        # Get the plugins for this class.
        plugins = self.project.getPlugins(('common', self.__class__.__name__))

        tdDlg = TraceDisplayDlg(self,
                                project = self.project,
                                parent = None,
                                id = wx.ID_ANY,
                                title = "TraceDisplay Development",
                                plugins = plugins)
        tdDlg.Show()
        app.MainLoop()



class TraceDisplayEditDlg(wx.Frame):
    ''' The TraceDisplay edit dialog window.

    '''
    def __init__(self, collectionNode, psyProject,  parent, id=-1, title='tracedisplay preferences', 
                 size=(640,480)):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY, 
                           title=title, 
                           size=size,
                           style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)

        # Create the logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.collectionNode = collectionNode
        self.psyProject = psyProject
        self.check_file_format = True

        self.initUI()
        self.SetMinSize(self.GetBestSize())
        self.initUserSelections()




class TraceDisplayDlg(psysmon.core.gui.PsysmonDockingFrame):
    ''' The TraceDisplay main window.


    Attributes
    ----------
    logger : :class:`logging.logger`
        The logger used for debug, status and similiar messages.


    '''

    def __init__(self, collection_node, project, parent = None, id = wx.ID_ANY, title = "tracedisplay",
                 plugins = None, size=(1000, 600)):
        ''' The constructor.

        '''
        psysmon.core.gui.PsysmonDockingFrame.__init__(self,
                                                      parent = parent,
                                                      id = id,
                                                      title = title)

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The parent collection node.
        self.collection_node = collection_node

        # The parent project.
        self.project = project

        # The available plugins of the collection node.
        self.plugins = plugins
        for curPlugin in self.plugins:
            curPlugin.parent = self

        self.init_user_interface()

        # Get the processing nodes from the project.
        self.processingNodes = self.project.getProcessingNodes(('common', 'TraceDisplay'))


        # Create the display option.
        self.displayManager = DisplayManager(parent = self,
                                             inventory = project.geometry_inventory)

        # Create the dataManager.
        self.dataManager = DataManager(self)

        # Add some custom hooks.
        self.hook_manager.add_hook(name = 'after_plot',
                                   description = 'Called after the data was plotted in the views.')
        self.hook_manager.add_hook(name = 'after_plot_station',
                                   description = 'Called after the data of a station was plotted in the views.',
                                   passed_args = {'station': 'The station, that was plotted.',})
        self.hook_manager.add_hook(name = 'time_limit_changed',
                                   description = 'Called after the time limit of the displayed time-span was changed.')

        # Create the events library.
        self.event_library = ev_core.Library(name = self.collection_node.rid)

        # A temporary plugin register to swap two plugins.
        self.plugin_to_restore = None

        # Register the plugin shortcuts. This has to be done after the various
        # manager instances were created.
        # TODO: register the keyboard shortcuts when the plugin is actevated.
        # TODO: unregister the shortcuts when deactivating the plugin.
        for curPlugin in self.plugins:
            curPlugin.register_keyboard_shortcuts()
            curPlugin.initialize_preferences()


        self.initKeyEvents()

        # Display the data.
        self.update_display()


    @property
    def visible_data(self):
        ''' The currently visible data.
        '''
        return self.dataManager.get_proc_stream(scnl = self.displayManager.getSCNL(source = 'show'))


    @property
    def original_data(self):
        ''' The current original data.
        '''
        return self.dataManager.get_orig_stream(scnl = self.displayManager.getSCNL(source = 'show'))


    @property
    def processing_stack(self):
        ''' The processing stack.
        '''
        return self.dataManager.processingStack


    def init_user_selection(self):
        if self.collectionNode.property['start_time']:
            pass


    def init_user_interface(self):
        ''' Create the graphical user interface.
        '''
        # Initialize the ribbon bar using the loaded plugins.
        self.init_ribbon_bar()

        # Add the datetime info to the viewport sizer.
        # TODO: Add a method in the PsysmonDockingFrame class to insert
        # elements into the viewport_sizer.
        self.datetimeInfo = container.TdDatetimeInfo(parent=self.center_panel)
        #self.viewport_sizer.SetItemPosition(self.viewport, wx.GBPosition(0,1))
        self.viewport_sizer.Detach(self.viewport)
        self.viewport_sizer.Add(self.datetimeInfo,
                                pos=(0,0),
                                flag=wx.EXPAND|wx.ALL,
                                border=0)
        self.viewport_sizer.Add(self.viewport,
                                pos = (1,0),
                                flag = wx.EXPAND|wx.ALL,
                                border = 0)
        self.viewport_sizer.RemoveGrowableRow(0)
        self.viewport_sizer.AddGrowableRow(1)


        # Tell the docking manager to commit all changes.
        self.mgr.Update()


    def initKeyEvents(self):
        ''' Initialize the key event bindings.

        '''
        # The released modifier key.
        self.modifier_key_up = None
        self.pressed_keys = []

        #self.shortcutManager.addAction(('WXK_COMMAND', 'WXK_SPACE'), self.swap_tool)
        #self.shortcutManager.addAction(('WXK_COMMAND', 'WXK_SPACE'), self.restore_tool, kind = 'up')

        self.shortcut_manager.add_shortcut(origin_rid = self.collection_node.rid,
                                           key_combination = ('WXK_ESCAPE',),
                                           action = self.deactivate_tool)


    def advanceTime(self, time_step = None):
        ''' Advance the display time by one step. 
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.advanceTime(time_step = time_step)
        self.update_display()
        if oldFocus is not None:
            oldFocus.SetFocus()


    def advanceTimePercentage(self, step = 100):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.advanceTimePercentage(step)
        self.update_display()
        oldFocus.SetFocus()


    def decreaseTime(self):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.decreaseTime()
        self.update_display()
        oldFocus.SetFocus()


    def decreaseTimePercentage(self, step = 100):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.decreaseTimePercentage(step)
        self.update_display()
        oldFocus.SetFocus()


    def growTimePeriod(self, ratio = 50):
        ''' Grow the time period by a given ratio.
        '''
        self.displayManager.growTimePeriod(ratio)
        self.update_display()


    def shrinkTimePeriod(self, ratio = 50):
        ''' Grow the time period by a given ratio.
        '''
        self.displayManager.shrinkTimePeriod(ratio)
        self.update_display()


    def swap_tool(self):
        ''' Swap the tool with one defined in the preferences.
        '''
        if self.plugin_to_restore is not None:
            return

        swap_tool_name = 'zoom'

        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')
        try:
            active_plugin = active_plugin[0]
        except:
            active_plugin = None

        if active_plugin is not None and active_plugin.name == swap_tool_name:
            # The swap tool is already active.
            return

        swap_plugin = [x for x in self.plugins if x.name == swap_tool_name]
        if len(swap_plugin) != 1:
            raise RuntimeError("Can't find the swap plugin.")
        swap_plugin = swap_plugin[0]

        self.plugin_to_restore = active_plugin

        if active_plugin:
            self.deactivate_interactive_plugin(active_plugin)
        self.activate_interactive_plugin(swap_plugin)


    def restore_tool(self):
        ''' Restore a tool which was previousely swapped.
        '''
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) == 0:
            return
        elif len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')

        active_plugin = active_plugin[0]
        self.deactivate_interactive_plugin(active_plugin)
        if self.plugin_to_restore is not None:
            self.activate_interactive_plugin(self.plugin_to_restore)
            self.plugin_to_restore = None


    def deactivate_tool(self):
        ''' Deactivate the currently active interactive plugin.
        '''
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']

        if len(active_plugin) == 0:
            return
        elif len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')

        active_plugin = active_plugin[0]
        self.deactivate_interactive_plugin(active_plugin)



    def setDuration(self, duration):
        ''' Set a new duration of the displayed time period.
        '''
        self.displayManager.setDuration(duration)
        self.update_display()


    def setStartTime(self, startTime):
        ''' Set the new start time of the displayed time period.
        '''
        self.displayManager.setStartTime(startTime)
        self.update_display()


    def onKeyDown(self, event):
        ''' Handle a key down event.

        '''
        keyCode = event.GetKeyCode()
        keyName = keyMap.get(keyCode, None)

        if keyName in ['WXK_SHIFT', 'WXK_COMMAND', 'WXK_ALT']:
            # Don't handle the key modifier as individual key events.
            return

        self.logger.debug('Keycode: %d', keyCode)

        if keyName is None:
            if keyCode < 256:
                if keyCode == 0:
                    keyName = "NUL"
                elif keyCode < 27:
                    keyName = "Ctrl-%s" % chr(ord('A') + keyCode-1)
                else:
                    keyName = "\"%s\"" % chr(keyCode)
            else:
                keyName = "(%s)" % keyCode

        if keyName and keyName not in self.pressed_keys:
            self.pressed_keys.append(keyName)



        # Process the modifiers.
        pressedKey = []
        modString = ""
        for mod, ch in [(event.ControlDown(), 'WXK_COMMAND'),
                        (event.AltDown(),     'WXK_ALT'),
                        (event.ShiftDown(),   'WXK_SHIFT'),
                        (event.MetaDown(),    'META')]:
            if mod:
                pressedKey.append(ch)
                modString += ch + " + "

        pressedKey.append(keyName)
        #print "pressed key: %s." % pressedKey
        #print "self.pressed_keys: %s." % self.pressed_keys
        self.logger.debug('pressed key: %s - %s', keyCode, pressedKey)
        shortcuts = self.shortcut_manager.get_shortcut(key_combination = tuple(pressedKey), kind = 'down')

        for cur_shortcut in shortcuts:
            if cur_shortcut.action_kwargs is None:
                cur_shortcut.action()
            else:
                cur_shortcut.action(**cur_shortcut.action_kwargs)


    def onKeyUp(self, event):
        ''' Handle a key release event.
        '''
        self.logger.debug('Releasing key.')
        keyCode = event.GetKeyCode()
        keyName = keyMap.get(keyCode, None)

        if keyName in ['WXK_SHIFT', 'WXK_COMMAND', 'WXK_ALT']:
            if self.pressed_keys:
                # Store the released modifier.
                #print "KEY UP of %s." % keyName
                self.modifier_key_up = keyName
            return

        self.logger.debug('Keycode: %d', keyCode)

        if keyName is None:
            if keyCode < 256:
                if keyCode == 0:
                    keyName = "NUL"
                elif keyCode < 27:
                    keyName = "Ctrl-%s" % chr(ord('A') + keyCode-1)
                else:
                    keyName = "\"%s\"" % chr(keyCode)
            else:
                keyName = "(%s)" % keyCode

        if keyName:
            self.pressed_keys.remove(keyName)

        # Process the modifiers.
        pressedKey = []
        modString = ""
        for mod, ch in [(event.ControlDown(), 'WXK_COMMAND'),
                        (event.AltDown(),     'WXK_ALT'),
                        (event.ShiftDown(),   'WXK_SHIFT'),
                        (event.MetaDown(),    'META')]:
            if mod:
                pressedKey.append(ch)
                modString += ch + " + "

        if self.modifier_key_up:
            pressedKey.append(self.modifier_key_up)
            self.modifier_key_up = None

        pressedKey.append(keyName)
        #print "released key: %s." % pressedKey
        #print "self.pressed_keys: %s." % self.pressed_keys
        self.logger.debug('Released key: %s - %s', keyCode, pressedKey)

        shortcuts = self.shortcut_manager.get_shortcut(key_combination = tuple(pressedKey), kind = 'up')

        for cur_shortcut in shortcuts:
            if cur_shortcut.action_kwargs is None:
                cur_shortcut.action()
            else:
                cur_shortcut.action(**cur_shortcut.action_kwargs)


    def onSetFocus(self, event):
        ''' Handle a key down event.

        '''
        self.logger.debug('Setting focus.')


    def register_view_plugin(self, plugin):
        ''' Handle special requests of view plugins.
        '''
        if plugin.get_virtual_stations():
            # Check if the plugin needs a virtual display channel.
            for cur_name, cur_channels in plugin.get_virtual_stations().iteritems():
                self.displayManager.show_virtual_station(name = cur_name,
                                                         plugin = plugin,
                                                         channels = cur_channels)
        elif hasattr(plugin, 'required_data_channels'):
            # Check if the plugin needs a virtual display channel.
            # Create the virtual display channel.
            self.displayManager.show_virtual_channel(plugin)
            self.viewport.register_view_plugin(plugin, limit_group = [plugin.rid,])
        else:
            self.viewport.register_view_plugin(plugin, limit_group = ['channel_container',])


    def unregister_view_plugin(self, plugin):
        ''' Handle special requests of the view plugins.
        '''
        if plugin.get_virtual_stations():
            for cur_name in plugin.get_virtual_stations():
                self.displayManager.hide_virtual_station(name = cur_name,
                                                         plugin = plugin)
        elif hasattr(plugin, 'required_data_channels'):
            self.displayManager.hide_virtual_channel(plugin)
        self.viewport.remove_node(name = plugin.rid, recursive = True)
        #self.displayManager.removeViewTool(plugin)


    def update_display(self):
        ''' Update the display.

        '''
        # Create the necessary containers.
        # TODO: Call these method only, if the displayed stations or
        if self.displayManager.stationsChanged:
            self.displayManager.createContainers() 
            #self.viewport.sortStations(snl=[(x[0],x[2],x[3]) for x in self.displayManager.getSCNL('show')])
            self.displayManager.stationsChanged = False
            self.logger.debug("Resetting stationsChanged to False.")

        # Update the viewport to show the changes.
        self.viewport.SetupScrolling()
        self.viewport.Refresh()
        self.viewport.Update()

        self.dataManager.requestStream(startTime = self.displayManager.startTime,
                                       endTime = self.displayManager.endTime,
                                       scnl = self.displayManager.getSCNL('show'))


        if self.dataManager.origStream:
            # TODO: Apply the processing stack before plotting the data.
            self.dataManager.processStream()


        # Plot the data using the view tools.
        viewPlugins = [x for x in self.plugins if x.mode == 'view' and x.active]

        for curPlugin in viewPlugins:
            curPlugin.plot(self.displayManager, self.dataManager)

        # Hide those views which don't contain any data.
        # TODO: This part destroys the scrolling.
        #for cur_station in self.displayManager.showStations:
        #    for cur_channel in cur_station.channels:
        #        if not cur_channel.container.data_plotted:
        #            self.viewPort.hideChannel([cur_channel.getSCNL(),])
        #        else:
        #            self.viewPort.showChannel([cur_channel.getSCNL(),])


        # Call the hooks of the plugins.
        self.call_hook('after_plot')


        # Update the time information panel.
        self.datetimeInfo.setTime(self.displayManager.startTime, 
                                  self.displayManager.endTime, 
                                  None)
        self.datetimeInfo.Refresh()





class DisplayManager(object):


    def __init__(self, parent, inventory):

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The parent tracedisplay instance.
        self.parent = parent

        # The inventory of the available geometry.
        self.inventory = inventory

        self.pref_manager = self.parent.collection_node.pref_manager

        # The timespan to show.
        self.startTime = self.pref_manager.get_value('start_time')
        self.endTime = self.startTime + self.pref_manager.get_value('duration')
        #self.endTime = UTCDateTime('2010-08-31 08:05:00')


        # The display mode (network, array).
        self.display_mode = self.pref_manager.get_value('display_mode')


        # All arrays contained in the inventory.
        self.availableArrays = []

        # All stations that are contained in the inventory.
        self.availableStations = []

        # All unique channels contained in the available stations.
        self.availableChannels = []


        # The currently shown arrays (list of DisplayArray instances).
        self.showArrays = []

        # The currently shown stations (list of DisplayStation instances).
        self.showStations = []

        # The virtual stations currently shown (list of VirtualDisplayStation
        # instances).
        self.show_virtual_stations = []

        # Indicates if the station configuration has changed.
        self.stationsChanged = False

        # Fill the available- and current station lists.
        for curNetwork in self.inventory.networks:
            for curStation in curNetwork.stations:
                self.availableStations.append(DisplayStation(curStation))

                for curChannel in curStation.channels:
                    if curChannel.name not in self.availableChannels:
                        self.availableChannels.append(curChannel.name)

        # Fill the available arrays list.
        for cur_array in self.inventory.arrays:
            array_snl = [x.snl for x in cur_array.stations]
            array_stations = [x for x in self.availableStations if x.snl in array_snl]
            self.availableArrays.append(DisplayArray(array = cur_array,
                                                     stations = array_stations))


        # The channels currently shown.
        show_channels = self.pref_manager.get_value('show_channels')
        self.showChannels = [x for x in show_channels if x in self.availableChannels]

        # The virtual channels currently shown.
        self.show_virtual_channels = []


        # The views currently shown. (viewName, viewType)
        # TODO: This should be selected by the user in the edit dialog.
        #self.showViews = [('seismogram', 'seismogram')]
        # Create the views based on the active view tools.
        viewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active]


        if self.display_mode == 'network':
            # Select the stations to show.
            show_stations = self.pref_manager.get_value('show_stations')
            for curStation in self.availableStations:
                if curStation.label in show_stations:
                    station2Add = curStation
                    station2Add.addChannel(self.showChannels)
                    for curChannel in station2Add.channels:
                        for curPlugin in viewPlugins:
                            view_class = curPlugin.getViewClass()
                            if view_class is not None:
                                curChannel.addView(curPlugin.name, view_class)
                    self.showStations.append(station2Add)
            self.stationsChanged = True
            self.logger.debug("Setting stationsChanged to True.")

            self.sort_show_stations()
        elif self.display_mode == 'array':
            # Select the arrays to show.
            # TODO: Make this a user preference.
            show_arrays = self.pref_manager.get_value('show_arrays')
            for cur_array in self.availableArrays:
                if cur_array.name in show_arrays:
                    self.showArrays.append(cur_array)

                    for cur_station in cur_array.stations:
                        cur_station.addChannel(self.showChannels)
                        for cur_channel in cur_station.channels:
                            for cur_plugin in viewPlugins:
                                view_class = curPlugin.getViewClass()
                                if view_class is not None:
                                    cur_channel.addView(cur_plugin.name, view_class)

                        if cur_station not in self.showStations:
                            self.showStations.append(cur_station)
                            self.stationsChanged = True


        # The trace color settings.
        clrList = wx.lib.colourdb.getColourInfoList()
        channelNames = ['HHZ', 'HHN', 'HHE']
        colorNames = ['TURQUOISE', 'CADETBLUE', 'SEAGREEN']
        self.channelColors = [tuple(x[1:4]) for x in clrList if x[0] in colorNames]
        self.channelColors = dict(zip(channelNames, self.channelColors))



    def advanceTime(self, time_step = None):
        ''' Advance the time by one step.

        '''
        if time_step is None:
            interval = self.endTime - self.startTime
            self.startTime = self.endTime
            self.endTime = self.startTime + interval
        else:
            interval = self.endTime - self.startTime
            self.startTime = self.startTime + time_step
            self.endTime = self.startTime + interval

        self.parent.call_hook('time_limit_changed')


    def advanceTimePercentage(self, step):
        ''' Decrease the time by one step.

        '''
        interval = self.endTime - self.startTime
        time_step = interval * step/100.
        self.advanceTime(time_step = time_step)


    def decreaseTime(self, time_step = None):
        ''' Decrease the time by one step.

        '''
        if time_step is None:
            interval = self.endTime - self.startTime
            self.endTime = self.startTime
            self.startTime = self.startTime - interval
        else:
            interval = self.endTime - self.startTime
            self.startTime = self.startTime - time_step
            self.endTime = self.startTime + interval
        self.parent.call_hook('time_limit_changed')


    def decreaseTimePercentage(self, step):
        ''' Decrease the time by one step.

        '''
        interval = self.endTime - self.startTime
        time_step = interval * step/100.
        self.decreaseTime(time_step = time_step)


    def growTimePeriod(self, ratio = 50):
        ''' Grow the time period by a given ratio.
        '''
        duration = self.endTime - self.startTime
        growAmount = duration * ratio/100.0
        self.setTimeLimits(self.startTime - growAmount/2.0,
                           self.endTime + growAmount/2.0)


    def shrinkTimePeriod(self, ratio = 50):
        ''' Grow the time period by a given ratio.
        '''
        duration = self.endTime - self.startTime
        shrinkAmount = duration * ratio/100.0
        self.setTimeLimits(self.startTime + shrinkAmount/2.0,
                           self.endTime - shrinkAmount/2.0)


    def show_next_station(self):
        ''' Show the next station listed in the available stations.
        '''
        cur_station = self.showStations[-1]
        ind = self.availableStations.index(cur_station) + 1
        if ind < len(self.availableStations):
            self.hideStation(cur_station.getSNL())
            self.showStation(self.availableStations[ind].getSNL())


    def show_prev_station(self):
        ''' Show the previous station listed in the available stations.
        '''
        cur_station = self.showStations[0]
        ind = self.availableStations.index(cur_station) - 1
        if ind >= 0:
            self.hideStation(cur_station.getSNL())
            self.showStation(self.availableStations[ind].getSNL())


    def setDuration(self, duration):
        ''' Set the duration of the displayed time period.

        '''
        self.endTime = self.startTime + duration


    def setStartTime(self, startTime):
        ''' Set the start time of the displayed time period.
        '''
        duration = self.endTime - self.startTime
        self.startTime = startTime
        self.endTime = startTime + duration
        self.parent.call_hook('time_limit_changed')


    def setTimeLimits(self, startTime, endTime):
        ''' Set the start- and endTime of the displayed time period.

        '''
        self.startTime = startTime
        self.endTime = endTime
        self.parent.call_hook('time_limit_changed')



    def hideArray(self, name):
        ''' Remove the specified array from the shown arrays.

        Parameters
        ----------
        name : String
            The name of the array which should be hidden.
        '''
        array_to_remove = [x for x in self.showArrays if name == x.name]

        for cur_array in array_to_remove:
            for cur_station in cur_array.stations:
                self.hideStation(cur_station.snl)
            self.showArrays.remove(cur_array)
            self.parent.viewport.remove_node(array = cur_array.name)


    def showArray(self, name):
        ''' Show the specified array.

        Parameters
        ----------
        name : String
            The name of the array which should be hidden.
        '''
        array_to_show = [x for x in self.availableArrays if name == x.name]

        for cur_array in array_to_show:
            self.showArrays.append(cur_array)

            # Create the array containers.
            cur_array_container = self.createArrayContainer(cur_array)
            for cur_station in cur_array.stations:
                self.showStationInContainer(snl = cur_station.snl, parent_container = cur_array_container)


        self.parent.viewport.Refresh()
        self.parent.viewport.Update()


    def hideStation(self, snl):
        ''' Remove the specified station from the shown stations.

        Parameters
        ----------
        snl : tuple (String, String, String)
            The station, network, location code of the station which should be hidden.
        '''
        stat2Remove = [x for x in self.showStations if snl == x.getSNL()]

        for curStation in stat2Remove:
            self.showStations.remove(curStation)
            self.parent.viewport.remove_node(station = curStation.name,
                                             network = curStation.network,
                                             location = curStation.location,
                                             recursive = True)



    def showStation(self, snl):
        ''' Show the specified station in the display.

        Parameters
        ----------
        snl : tuple (String, String, String)
            The station, network, location code of the station which should be hidden.
        '''

        # Check if the station is part of one or more arrays that are currently
        # shown.
        parent_container = []
        if self.display_mode == 'array':
            for cur_array in self.availableArrays:
                if snl in [x.snl for x in cur_array.stations]:
                    cur_container = self.createArrayContainer(array = cur_array)
                    parent_container.append(cur_container)

        if not parent_container:
            parent_container.append(self.parent.viewport)

        for cur_container in parent_container:
            self.showStationInContainer(snl = snl,
                                        parent_container = cur_container)

        self.parent.viewport.Refresh()
        self.parent.viewport.Update()


    def showStationInContainer(self, snl, parent_container):
        ''' Show the station in the selected container.
        '''

        viewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active
                       and not hasattr(x, 'required_data_channels')
                       and not x.get_virtual_stations()]
        virtualViewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active
                              and hasattr(x, 'required_data_channels')
                              and not x.get_virtual_stations()]
        interactive_plugins = [x for x in self.parent.plugins if x.mode == 'interactive' and x.active]

        # Get the selected station and set all currently active
        # channels.
        station2Show = self.getAvailableStation(snl)
        self.addShowStation(station2Show)

        # Check if the station has the demanded channels.
        station_channels = self.inventory.get_channel(station = snl[0],
                                                      network = snl[1],
                                                      location = snl[2])
        channel_names = [x.name for x in station_channels if x.name in self.showChannels]
        station2Show.addChannel(channel_names)

        for curChannel in station2Show.channels:
            for curPlugin in viewPlugins:
                view_class = curPlugin.getViewClass()
                if view_class is not None:
                    curChannel.addView(curPlugin.name, view_class)

        # Create the necessary channel containers.
        stationContainer = self.createStationContainer(station2Show, parent_container = parent_container)
        for curChannel in station2Show.channels:
            curChanContainer = self.createChannelContainer(stationContainer, curChannel)
            for cur_plugin in viewPlugins:
                curChanContainer.create_plugin_view(cur_plugin, limit_group = ['channel_container',])

        # Create necessary virtual channel containers.
        for cur_plugin in virtualViewPlugins:
            self.show_virtual_channels.append(cur_plugin.name)
            cur_channel = station2Show.add_virtual_channel(cur_plugin.name, cur_plugin)
            cur_channel_container = self.createChannelContainer(stationContainer,
                                                                cur_channel,
                                                                group = cur_plugin.rid)
            cur_channel_container.create_plugin_view(cur_plugin)

        # Sort the nodes in the viewport.
        # TODO: Sorting doesn't work when using the arry display. Nodes which
        # don't fit one of the sort_keys are lost in the viewport.
        #keys = ('station', 'network', 'location')
        #sort_order = [dict(zip(keys, x)) for x in self.getSNL(source = 'show')]
        #parent_container.sort_nodes(order = sort_order)


        # Request the data.
        scnl = station2Show.getSCNL()
        curStream = self.parent.dataManager.hasData(self.startTime, 
                                                    self.endTime, 
                                                    scnl)

        if not curStream:
            # The data is not yet available in the data manager. Add the
            # needed data to the data manager.
            curStream = self.parent.dataManager.addStream(self.startTime, 
                                                          self.endTime,
                                                          scnl)

            # Run the processing stack on the new data.
            self.parent.dataManager.processStream(self, scnl = station2Show.getSCNL())


        # Plot the data of the station only using the view tools.
        for curPlugin in viewPlugins:
            curPlugin.plotStation(displayManager = self.parent.displayManager,
                           dataManager = self.parent.dataManager,
                           station = [station2Show,])

        # Hide those views which don't contain any data.
        # TODO: This destroys the scrolling when adding new channels. See also
        # the updatedisplay method.
        # Don't hide the complete channel. Just hide the data axes in the view.
        #for cur_channel in station2Show.channels:
        #    if not cur_channel.container.data_plotted:
        #        self.parent.viewPort.hideChannel([cur_channel.getSCNL(),])
        #    else:
        #        self.parent.viewPort.showChannel([cur_channel.getSCNL(),])


        # Call the hooks of the plugins.
        self.parent.call_hook('after_plot_station', station = [station2Show,])

        # If an interactive plugin is active, register the hooks for the added
        # station.
        if len(interactive_plugins) == 1:
            cur_plugin = interactive_plugins[0]
            self.parent.viewport.register_mpl_event_callbacks(cur_plugin.getHooks())
        self.parent.viewport.SetFocus()


    def showChannel(self, channel):
        ''' Show a channel in the display.

        Parameters
        ----------
        channel : String
            The channel name which should be shown.
        '''

        if channel not in self.showChannels:
            self.showChannels.append(channel)

        viewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active
                       and not hasattr(x, 'required_data_channels')
                       and not x.get_virtual_stations()]

        for curStation in self.showStations:
            # Check if the station has the demanded channels.
            station_channels = self.inventory.get_channel(station = curStation.name,
                                                          network = curStation.network,
                                                          location = curStation.location)
            channel_names = [x.name for x in station_channels if x.name in self.showChannels]
            if channel in channel_names:
                curStation.addChannel([channel,])
                for curChannel in curStation.channels:
                    for curPlugin in viewPlugins:
                        view_class = curPlugin.getViewClass()
                        if view_class is not None:
                            curChannel.addView(curPlugin.name, view_class)

            # Create the necessary containers.
            stationContainer = self.createStationContainer(curStation)
            for curChannel in curStation.channels:
                curChanContainer = self.createChannelContainer(stationContainer, curChannel)
                for cur_plugin in viewPlugins:
                    curChanContainer.create_plugin_view(cur_plugin, limit_group = ['channel_container'])

        # TODO: Only update the data of the added channel.
        self.stationsChanged = True
        self.logger.debug("Setting stationsChanged to True.")
        self.parent.update_display()


    def show_virtual_station(self, name, plugin, channels):
        ''' Show a virtual station in the display.

        Parameters
        ----------
        name : String
            The name of the virtual station to show.

        plugin : ViewPlugin
            The plugin requesting the virtual station.

        channels : List of String
            The virtual channels of the station.
        '''

        for cur_array in self.showArrays:
            cur_station = cur_array.add_virtual_station(name)
            array_container = self.createArrayContainer(cur_array)
            cur_station_container = self.createStationContainer(station = cur_station,
                                                                parent_container = array_container,
                                                                group = plugin.rid)
            for cur_channel_name in channels:
                cur_channel = cur_station.add_virtual_channel(cur_channel_name, plugin)
                cur_channel_container = self.createChannelContainer(cur_station_container,
                                                                    cur_channel,
                                                                    group = plugin.rid)
                # TODO: Create the view of the channel.
                cur_channel_container.create_plugin_view(plugin)

            self.show_virtual_stations.append(cur_station)



    def hide_virtual_station(self, name, plugin):
        ''' Hide a virtual station in the display.

        '''
        for cur_array in self.showArrays:
            cur_array.remove_virtual_station(name)
            array_container = self.parent.viewport.get_node(array = cur_array.name)

            for cur_container in array_container:
                cur_container.remove_node(group = plugin.rid)

        stat_to_remove = [x for x in self.show_virtual_stations if name == x.name]
        for cur_station in stat_to_remove:
            self.show_virtual_stations.remove(cur_station)


    def show_virtual_channel(self, plugin):
        ''' Show a virtual channel in the display.

        Parameters
        ----------
        plugin : ViewPlugin
            The plugin requesting the virtual channel.
        '''

        if plugin.name not in self.show_virtual_channels:
            self.show_virtual_channels.append(plugin.name)
        for cur_station in self.showStations:
            cur_channel = cur_station.add_virtual_channel(plugin.name, plugin)
            station_container = self.createStationContainer(cur_station)
            cur_channel_container = self.createChannelContainer(station_container,
                                                                cur_channel,
                                                                group = plugin.rid)
            cur_channel_container.create_plugin_view(plugin)



    def hideChannel(self, channel):
        ''' Hide a channel in the display.

        Parameters
        ----------
        channel : String
            The name of the channel which should be hidden.
        '''
        for curStation in self.showStations:
            removedSCNL = curStation.removeChannel([channel])
            for cur_scnl in removedSCNL:
                station_container = self.parent.viewport.get_node(group = 'station_container',
                                                                  station = cur_scnl[0],
                                                                  network = cur_scnl[2],
                                                                  location = cur_scnl[3])

                for cur_container in station_container:
                    cur_container.remove_node(station = cur_scnl[0],
                                              channel = cur_scnl[1],
                                              network = cur_scnl[2],
                                              location = cur_scnl[3])

        self.showChannels.remove(channel)


    def hide_virtual_channel(self, plugin):
        ''' Hide a virtual channel in the display.

        '''
        for cur_station in self.showStations:
            removed_scnl = cur_station.remove_virtual_channel(plugin.name)
            for cur_scnl in removed_scnl:
                station_container = self.parent.viewport.get_node(group = 'station_container',
                                                                  station = cur_scnl[0],
                                                                  network = cur_scnl[2],
                                                                  location = cur_scnl[3])

                for cur_container in station_container:
                    cur_container.remove_node(group = plugin.rid)
                    #cur_container.remove_node(name = plugin.rid)




    def getSNL(self, source='available'):
        ''' Get the station,network,location (SNL) code of the selected station set.

        Parameters
        ----------
        source : String
            The source for which the SNL code should be built.
            (available, show; default=available)
             - available: all available stations
             - show: the currently displayed stations only

        Returns
        -------
        snl : List of SNL tuples
            The snl codes of the specified station set.
        '''
        snl = []

        if source == 'show':
            curList = self.showStations
        elif source == 'available':
            curList = self.availableStations

        for curStation in curList:
            snl.append(curStation.getSNL())

        return snl



    def getSCNL(self, source='available'):
        ''' The the station, channel, network, location (SCNL) code of the selected station set.

        Parameters
        ----------
        source : String
            The source for which the SNL code should be built.
            (available, show; default=available)
             - available: all available stations
             - show: the currently displayed stations only

        Returns
        -------
        scnl : List of SCNL tuples
            The SCNL codes of the specified station set.

        ''' 
        scnl = []

        if source == 'show':
            curList = self.showStations
        elif source == 'available':
            curList = self.availableStations

        for curStation in curList:
            scnl.extend(curStation.getSCNL())

        return scnl



    def getAvailableStation(self, snl):
        ''' Get the station with the specified SNL code from the available stations.

        Parameters
        ----------
        snl : SNL tuple (station, network, location)
            The SNL code of the station to be searched for.

        Returns
        -------
        station : :class: `DisplayStation`
            The station in the availableStations set matching the specified SNL code. None if the station is not found. 
        '''
        for curStation in self.availableStations:
            if curStation.getSNL() == snl:
                return curStation

        return None


    def addShowStation(self, station):
        ''' Add a station to the showStations list.

        Parameters
        ----------
        station : :class:`DisplayStation`
            The station to be added to the showStations list.
        '''
        if station not in self.showStations:
            self.showStations.append(station)
            self.sort_show_stations()

        self.stationsChanged = True
        self.logger.debug("Setting stationsChanged to True.")


    def sort_show_stations(self):
        ''' Sort the showen stations.
        '''
        sort_mode = self.pref_manager.get_value('sort_stations')
        if sort_mode == 'by name':
            self.showStations = sorted(self.showStations, key = attrgetter('name'))
            self.availableStations = sorted(self.availableStations, key = attrgetter('name'))



    def createContainers(self):
        ''' Create all display elements needed to plot the shown stations.

        '''
        if self.display_mode == 'network':
            for curStation in self.showStations:
                curStatContainer = self.createStationContainer(curStation)
                # TODO: Create the station related view container node. This is
                # used for views which use data which is not directly related to a
                # single channel (e.g. polarization analysis). If the station-data
                # view container is not used by a plugin, hide it. The station-data
                # view container should be of the same size and layout as the
                # channel-view container.
                for curChannel in curStation.channels:
                    curChanContainer = self.createChannelContainer(curStatContainer, curChannel)
                    #for curViewName, (curViewType, ) in curChannel.views.items():
                    #    self.createViewContainer(curChanContainer, curViewName, curViewType)

                #self.createMultichannelContainer(curStatContainer)
        elif self.display_mode == 'array':
            for cur_array in self.showArrays:
                cur_array_container = self.createArrayContainer(cur_array)
                for cur_station in cur_array.stations:
                    cur_stat_container = self.createStationContainer(cur_station,
                                                                     parent_container = cur_array_container)
                    for cur_channel in cur_station.channels:
                        cur_chan_container = self.createChannelContainer(cur_stat_container,
                                                                         cur_channel)




    def createArrayContainer(self, array):
        ''' Create a container for an array.
        '''
        viewport = self.parent.viewport

        # Check if the container already exists in the viewport.
        array_container = viewport.get_node(array = array.name)

        if not array_container:
            props = psysmon.core.util.AttribDict()
            props.array = array.name

            annotation_area = container.StationAnnotationArea(viewport,
                                                              id = wx.ID_ANY,
                                                              label = array.name,
                                                              color = 'white')

            array_container = psysmon.core.gui_view.ContainerNode(parent = viewport,
                                                                  name = array.name,
                                                                  props = props,
                                                                  annotation_area = annotation_area,
                                                                  color = 'white',
                                                                  group = 'array_container')
            viewport.add_node(array_container)
            array_container.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)
            array_container.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyUp)
        else:
            array_container = array_container[0]

        return array_container


    def createStationContainer(self, station, parent_container = None, group = 'station_container'):
        ''' Create the station container of the specified station.

        '''
        if parent_container is None:
            parent_container = self.parent.viewport

        # Check if the container already exists in the parent container.
        statContainer = parent_container.get_node(station = station.name,
                                                  network = station.network,
                                                  location = station.location)
        if not statContainer:
            props = psysmon.core.util.AttribDict()
            props.station = station.name
            props.network = station.network
            props.location = station.location
            annotation_area = container.StationAnnotationArea(self.parent.viewport,
                                                              id = wx.ID_ANY,
                                                              label = ':'.join(station.getSNL()),
                                                              color = 'white')
            statContainer = psysmon.core.gui_view.ContainerNode(parent = self.parent.viewport,
                                                                name = ':'.join(station.getSNL()),
                                                                props = props,
                                                                annotation_area = annotation_area,
                                                                color = 'white',
                                                                group = group)
            parent_container.add_node(statContainer)
            statContainer.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)
            statContainer.Bind(wx.EVT_KEY_UP, self.parent.onKeyUp)
        else:
            statContainer = statContainer[0]

        return statContainer


    def createChannelContainer(self, stationContainer, channel, group = 'channel_container'):
        '''

        '''
        # Check if the container already exists in the station.
        chanContainer = stationContainer.get_node(channel = channel.name)

        if not chanContainer:
            if channel.name in self.channelColors:
                curColor = self.channelColors[channel.name]
            else:
                curColor = (0, 0, 0)

            props = psysmon.core.util.AttribDict()
            props.station = channel.parent.name
            props.location = channel.parent.location
            props.network = channel.parent.network
            props.channel = channel.name
            props.channel_color = curColor
            annotation_area = container.ChannelAnnotationArea(parent = stationContainer,
                                                              label = channel.name,
                                                              color = curColor)
            chanContainer = psysmon.core.gui_view.ViewContainerNode(parent = stationContainer,
                                                                    name = channel.name,
                                                                    props = props,
                                                                    annotation_area = annotation_area,
                                                                    color = 'white',
                                                                    group = group)
            stationContainer.add_node(chanContainer)
            #channel.container = chanContainer
        else:
            chanContainer = chanContainer[0]

        return chanContainer



    def OLD_createViewContainer(self, channelContainer, name, viewClass):
        '''

        '''
        # Check if the container already exists in the channel.
        viewContainer = channelContainer.get_node(name = name)

        if not viewContainer:
            viewContainer = viewClass(channelContainer,
                                      id = wx.ID_ANY,
                                      props = channelContainer.props,
                                      name = name)

            channelContainer.add_node(viewContainer)
            channelContainer.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)
            channelContainer.Bind(wx.EVT_KEY_UP, self.parent.onKeyUp)

        return viewContainer


    def getViewContainer(self, **kwargs):
        ''' Get the view container of the specified search terms.

        '''
        # TODO: Remove this method by replacing the getViewContainer calls with
        # the viewport.get_node call.
        return self.parent.viewport.get_node(**kwargs)


    def removeViewTool(self, plugin):
        ''' Remove the views created by the plugin.

        '''
        for curStation in self.showStations:
            for curChannel in curStation.channels:
                channelContainers = self.parent.viewport.get_node(station = curChannel.parent.name,
                                                                  channel = curChannel.name,
                                                                  network = curChannel.parent.network,
                                                                  location = curChannel.parent.location,
                                                                  group = 'channel_container')
                curChannel.removeView(plugin.name, 'my View')
                for curContainer in channelContainers:
                    curContainer.remove_node(plugin.rid)



class DisplayArray(object):
    ''' Handling the arrays used in tracedisplay array mode.
    '''

    def __init__(self, array, stations):
        ''' Initialize the instance.

        Parameters
        ----------
        array : 'class':`~psysmon.packages.geometry.inventory.Array`
            The parent inventory array.

        stations : list of 'class':`~DisplayStation`
            The stations contained in the array.

        '''
        # The parent array.
        self.array = array

        # The stations contained in the array.
        self.stations = stations

        # The virtual stations of the array.
        self.virtual_stations = []

    @property
    def name(self):
        return self.array.name


    def add_virtual_station(self, name):
        ''' Add a virtual station to the array.
        '''
        cur_station = VirtualDisplayStation(parent = self,
                                            name = name)
        self.virtual_stations.append(cur_station)
        return cur_station


    def remove_virtual_station(self, name):
        ''' Remove a virtual station from the array.
        '''
        stations_to_remove = [x for x in self.virtual_stations if x.name in name]
        for cur_station in stations_to_remove:
            self.virtual_stations.remove(cur_station)



class DisplayStation(object):
    ''' Handling the stations used in tracedisplay.

    Attributes
    ----------
    station : 'class':`~psysmon.packages.geometry.inventory.Station`
        The parent inventory station.
    name : String
        The name of the station.
    network : String
        The name of the network code.
    location : String
        The location identifier of the station ('--', '00', '01', ...)
    obspy_location : String
        The location identifier of the station (None, '00', '01', ...) in obspy 
        style. The '--' location string is translated into the None value.
    channels : List of 'class':`~DisplayChannel`
        The channels contained in the station.
    '''

    def __init__(self, station):
        ''' The constructor.

        Parameters
        ----------
        station : 'class':`~psysmon.packages.geometry.inventory.Station`
            The parent inventory station.
        '''
        # The parent station.
        self.station = station

        # The name of the station.
        self.name = station.name

        # The network code.
        self.network = station.network

        # The location code.
        self.location = station.location

        # The channels contained in the station.
        self.channels = []

        # The virtual channels contained in the station.
        self.virtual_channels = []

    @property
    def label(self):
        return self.name + ':' + self.network + ':' + self.location

    @property
    def snl(self):
        return self.station.snl


    def addChannel(self, channelName):
        ''' Add a channel to the station.

        Check if the channel with name *channelName* is already contained in the 
        station. If not, create a new :class:`~DisplayChannel` instance and 
        add it to the channels list.

        Parameters
        ----------
        channelName : List of String
            The name of the channel to add.
        '''
        if isinstance(channelName, basestring):
            channelName = [channelName, ]

        channelNames = self.getChannelNames()
        for curName in channelName:
            if curName not in channelNames:
                curChannel = DisplayChannel(self, curName)
                self.channels.append(curChannel)


    def add_virtual_channel(self, name, plugin):
        ''' Add a virtual channel to the station.
        '''
        cur_channel = VirtualDisplayChannel(self, name, plugin)
        self.virtual_channels.append(cur_channel)
        return cur_channel


    def removeChannel(self, channelName):
        ''' Remove a channel from the station.

        Remove the channel(s) with name *channelName* from the channels list.

        Parameters
        ----------
        channelName : List of String
            The names of the channel to remove from the station.

        Returns
        -------
        removedSCNL : List of SCNL tuples
            The SCNL codes of the removed channels.
        '''
        removedSCNL = []

        if isinstance(channelName, basestring):
            channelName = [channelName, ]

        channels_to_remove = [x for x in self.channels if x.name in channelName]
        for curChannel in channels_to_remove:
            self.channels.remove(curChannel)
            removedSCNL.append((self.name, curChannel.name, self.network, self.location))

        return removedSCNL


    def remove_virtual_channel(self, name):
        ''' Remove a virtual channel to the station.
        '''
        removedSCNL = []
        channels_to_remove = [x for x in self.virtual_channels if x.name in name]
        for cur_channel in channels_to_remove:
            self.virtual_channels.remove(cur_channel)
            removedSCNL.append((self.name, cur_channel.name, self.network, self.location))

        return removedSCNL



    def getSCNL(self):
        ''' Get the SCNL code of the channels of the station.

        The station, channel, network, location (SCNL) code of the channels is 
        widely used in seismological data processing.

        Returns
        -------
        scnl : List of SCNL tuples
            The SCNL code as a tuple (station, channel, network, location).
        '''
        scnl = []
        for curChannel in self.channels:
            scnl.append((self.name, curChannel.name, self.network, self.location))

        for curChannel in self.virtual_channels:
            cur_scnl_list = curChannel.getSCNL()
            for cur_scnl in cur_scnl_list:
                if cur_scnl not in scnl:
                    scnl.append(cur_scnl)

        return scnl



    def getSNL(self):
        ''' The the SNL code of the station.

        To easily identify a station, the station, network, location (SNL) code 
        can be used.

        Returns
        -------
        snl : Tuple
            The SNL code of the station (station, network, location).
        '''
        return (self.name, self.network, self.location)


    def getChannelNames(self):
        ''' Get a list of the channel names contained in the station.

        Returns
        -------
        channel_names : List of strings
            The names of the channels contained in the station.
        '''
        return [x.name for x in self.channels]


    def get_obspy_location(self):
        ''' Translate the '--' location into None.

        Obspy uses the None value for the '--' location identifiere. It's 
        convenient to keep the '--' location string for exporting data, 
        requesting data from remote servers and so on. This method can be 
        used when the obspy styled location is needed.

        Use the obspy_location attribute of the class.

        Returns
        -------
        obspy_location : String
            The translation of the location string into a version, that 
            obspy can work with.
        '''
        if self.location == '--':
            return None
        else:
            return self.location


    # The obspy package creates a None location from the '--' location string.
    # Use the obspy_location property to translate the standard location string 
    # to the obspy version.
    obspy_location = property(get_obspy_location)


class VirtualDisplayStation(object):
    ''' A virtual display station.

    The virtual display station uses data from multiple real stations within a
    display group like an array. View plugins can request virtual channels
    within the virtual station.
    '''

    def __init__(self, parent, name, network = 'VV', location = '00'):
        ''' Initialize the instance.
        '''
        # The parent group object.
        self.parent = parent

        # The network of the virtual station.
        self.network = network

        # The location of the virtual station.
        self.location = location

        # The name of the virtual station.
        self.name = name

        # The virtual channels of the station.
        self.virtual_channels = []

    @property
    def obspy_location(self):
        ''' Translate the '--' location into None.

        Obspy uses the None value for the '--' location identifiere. It's 
        convenient to keep the '--' location string for exporting data, 
        requesting data from remote servers and so on. This method can be 
        used when the obspy styled location is needed.

        Use the obspy_location attribute of the class.

        Returns
        -------
        obspy_location : String
            The translation of the location string into a version, that 
            obspy can work with.
        '''
        if self.location == '--':
            return None
        else:
            return self.location

    def getSNL(self):
        ''' The the SNL code of the station.

        To easily identify a station, the station, network, location (SNL) code 
        can be used.

        Returns
        -------
        snl : Tuple
            The SNL code of the station (station, network, location).
        '''
        return (self.name, self.network, self.location)


    def add_virtual_channel(self, name, plugin):
        ''' Add a virtual channel to the station.
        '''
        cur_channel = VirtualDisplayChannel(self, name, plugin)
        self.virtual_channels.append(cur_channel)
        return cur_channel



class DisplayChannel(object):

    def __init__(self, parent, name):

        self.parent = parent

        self.name = name

        self.views = {}

        # The display containers of the channel.
        #self.container = None


    @property
    def scnl(self):
        return (self.parent.name, self.name, self.parent.network, self.parent.location)

    def addView(self, name, viewType):
        if name not in self.views.iterkeys():
            self.views[name] = (viewType, )


    def removeView(self, name, viewType):
        if name in self.views.iterkeys():
            self.views.pop(name)

    #TODO: Replace all getSCNL calls with the scnl attribute.
    def getSCNL(self):
        return (self.parent.name, self.name, self.parent.network, self.parent.location)



class VirtualDisplayChannel(object):
    ''' A virtual display channel.

    A virtual dispay channel can be created by a view plugin. The virtual channel uses
    data from multiple real channels (e.g. HHZ, HHN, HHE).
    The virtual channel is directly linked to a view plugin and it is created when the 
    plugin is activated. The view plugin has to provide a property that returns the
    needed data channels.
    '''

    def __init__(self, parent, name, plugin):
        ''' Initialize the instance.
        '''
        # The parent station holding the channel.
        self.parent = parent

        # The name of the channel.
        self.name = name

        # The plugin related to the virtual channel.
        self.plugin = plugin


    def getSCNL(self):
        return [(self.parent.name, x, self.parent.network, self.parent.location) for x in self.plugin.required_data_channels]






class DataManager():

    def __init__(self, parent):

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.parent = parent

        self.project = parent.project

        #self.waveclient = self.project.waveclient['main client']
        #self.waveclient = self.project.waveclient['earthworm']

        self.origStream = Stream()

        self.procStream = Stream()

        self.processingStack = ProcessingStack('my stack',
                                                self.project)
        detrend_node = [x for x in self.parent.processingNodes if x.name == 'detrend'][0]
        self.processingStack.addNode(detrend_node)
        #convert_to_sensor_units_node = [x for x in self.parent.processingNodes if x.name == 'convert to sensor units'][0]
        #self.processingStack.addNode(convert_to_sensor_units_node)


    def requestStream(self, startTime, endTime, scnl):
        ''' Request a data stream from the waveclient.

        This method overwrites the existing stream.
        '''
        self.origStream = self.project.request_data_stream(start_time = startTime,
                                                           end_time = endTime,
                                                           scnl = scnl)



    def hasData(self, startTime, endTime, scnl):
        ''' Check if the data for the specified station and time period has 
        already been loaded by the dataManager.
        '''

        curStream = Stream()

        for curStat, curChan, curNet, curLoc in scnl:
            curStream += self.origStream.select(station = curStat, 
                                                network = curNet, 
                                                location = curLoc, 
                                                channel = curChan)

        return curStream



    def addStream(self, startTime, endTime, scnl):
        ''' Add a stream to the existing stream.

        '''
        if not isinstance(scnl, list):
            scnl = [scnl, ]

        cur_stream = self.project.request_data_stream(start_time = startTime,
                                                      end_time = endTime,
                                                      scnl = scnl)

        self.origStream = self.origStream + cur_stream
        return cur_stream


    def processStream(self, stack = None, scnl = None):
        ''' Process the data stream using the passed processing stack.

        '''
        # Copy the origStream to the procStream.

        # Execute the processing stack.
        # Pass the procStream to the execute functon of the processing
        # stack.

        # TODO: Add the real processing stack class.
        if not scnl:
            # No SCNL is specified, process the whole stream.
            self.procStream = self.origStream.copy()
            #self.procStream.detrend(type = 'constant')
            self.processingStack.execute(self.procStream)
        else:
            # Process the stream of the specified scnl only.
            for curScnl in scnl:
                curStream = self.origStream.select(station = curScnl[0],
                                                   channel = curScnl[1],
                                                   network = curScnl[2],
                                                   location = curScnl[3])
                curStream = curStream.copy()
                self.processingStack.execute(curStream)
                self.procStream += curStream



    def get_proc_stream(self, scnl):
        ''' Get the processed stream matching the scnl codes.
        '''
        cur_stream = Stream()

        for curStat, curChan, curNet, curLoc in scnl:
            cur_stream += self.procStream.select(station = curStat,
                                                 network = curNet,
                                                 location = curLoc,
                                                 channel = curChan)

        return cur_stream


    def get_orig_stream(self, scnl):
        ''' Get the original stream matching the scnl codes.
        '''
        cur_stream = Stream()

        for curStat, curChan, curNet, curLoc in scnl:
            if curLoc == '--':
                # Convert location to obspy convention.
                curLoc = None

            cur_stream += self.origStream.select(station = curStat,
                                                 network = curNet,
                                                 location = curLoc,
                                                 channel = curChan)

        return cur_stream





