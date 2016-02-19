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
import container
import psysmon.core.preferences_manager as pref_manager
import psysmon.core.gui_preference_dialog as psy_guiprefdlg
import psysmon.core.plugins
import psysmon.core.util
import psysmon.packages.event.core as ev_core

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

        pref_item = pref_manager.DateTimeEditPrefItem(name = 'start_time',
                                    label = 'start time',
                                    value = UTCDateTime('2012-07-09T00:00:00'),
                                    group = 'time range')
        self.pref_manager.add_item(item = pref_item)

        pref_item = pref_manager.FloatSpinPrefItem(name = 'duration',
                                    label = 'duration',
                                    value = 300.,
                                    limit = (0, 86400),
                                    group = 'time range')
        self.pref_manager.add_item(item = pref_item)

        # TODO: Set the limit of the multichoice preference based on the
        # available channels.
        pref_item = pref_manager.MultiChoicePrefItem(name = 'show_channels',
                                                     label = 'channels',
                                                     limit = ('HHZ', 'HHN', 'HHE'),
                                                     value = ['HHZ',],
                                                     group = 'component selection')
        self.pref_manager.add_item(item = pref_item)

        # TODO: Set the limit of the multichoice preference based on the
        # available stations.
        pref_item = pref_manager.MultiChoicePrefItem(name = 'show_stations',
                                                     label = 'stations',
                                                     limit = ('ALBA', 'BISA', 'SITA'),
                                                     value = ['ALBA'],
                                                     group = 'component selection')
        self.pref_manager.add_item(item = pref_item)

        pref_item = pref_manager.SingleChoicePrefItem(name = 'sort_stations',
                                                      label = 'sort stations',
                                                      limit = ('by name',),
                                                      value = 'by name',
                                                      group = 'component selection')
        self.pref_manager.add_item(item = pref_item)


    def edit(self):
        stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
        self.pref_manager.set_limit('show_stations', stations)

        channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
        self.pref_manager.set_limit('show_channels', channels)

        dlg = psy_guiprefdlg.ListbookPrefDialog(preferences = self.pref_manager)
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




class TraceDisplayDlg(wx.Frame):
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
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

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


        # Get the processing nodes from the project.
        self.processingNodes = self.project.getProcessingNodes(('common', 'TraceDisplay'))

        # Create the display option.
        self.displayManager = DisplayManager(parent = self,
                                             inventory = project.geometry_inventory)

        # Create the shortcut options.
        self.shortcutManager = ShortcutManager()

        # Create the dataManager.
        self.dataManager = DataManager(self)

        # Create the events library.
        self.event_library = ev_core.Library(name = self.collection_node.rid)

        # Create the plugins shared information bag, which holds all the
        # information, that's shared by the tracedisplay plugins.
        self.plugins_information_bag = psysmon.core.plugins.SharedInformationBag()

        # A temporary plugin register to swap two plugins.
        self.plugin_to_restore = None

        # Create the hook manager and fill it with the allowed hooks.
        self.hook_manager = psysmon.core.util.HookManager(self)
        self.hook_manager.add_hook(name = 'after_plot',
                                   description = 'Called after the data was plotted in the views.')
        self.hook_manager.add_hook(name = 'after_plot_station',
                                   description = 'Called after the data of a station was plotted in the views.',
                                   passed_args = {'station': 'The station, that was plotted.',})
        self.hook_manager.add_hook(name = 'time_limit_changed',
                                   description = 'Called after the time limit of the displayed time-span was changed.')
        self.hook_manager.add_hook(name = 'plugin_activated',
                                   description = 'Called after a plugin was activated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'plugin_deactivated',
                                   description = 'Called after a plugin was deactivated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'shared_information_added',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'origin_rid': 'The resource id of the source of the shared information.',
                                                  'name': 'The name of the shared information.'})
        self.hook_manager.add_hook(name = 'shared_information_updated',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'updated_info': 'The shared information instance which was updated.'})
        self.hook_manager.add_view_hook(name = 'button_press_event',
                                        description = 'The matplotlib button_press_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'button_release_event',
                                        description = 'The matplotlib button_release_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'motion_notify_event',
                                        description = 'The matplotlib motion_notify_event in the view axes.')

        # Register the plugin shortcuts. This has to be done after the various
        # manager instances were created.
        for curPlugin in self.plugins:
            curPlugin.register_keyboard_shortcuts()

        # Initialize the user interface.
        self.initUI()
        self.initKeyEvents()

        # Display the data.
        self.updateDisplay()

        # Show the frame. 
        self.Show(True)

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


    def initUI(self):
        ''' Build the userinterface.

        '''
        self.logger.debug('Initializing the GUI')

        self.mgr = wx.aui.AuiManager(self)

        #self.toolPanels = fpb.FoldPanelBar(parent=self, 
        #                                   id=wx.ID_ANY,
        #                                   pos = wx.DefaultPosition,
        #                                   size=wx.DefaultSize,
        #                                   agwStyle=fpb.FPB_VERTICAL)

        #self.foldPanelBar = psygui.FoldPanelBarSplitter(parent=self)
        #self.foldPanelBar = psygui.FoldPanelBar(parent=self)

        #self.foldPanelBar.SetBackgroundColour('white')

        self.eventInfo = wx.Panel(parent=self, id=wx.ID_ANY)
        self.eventInfo.SetBackgroundColour('khaki')

        # Create the status bar.
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -3])
        self.statusbar.SetStatusText("Ready, go go.", 0)
        self.statusbar.SetStatusText("Tracedisplay", 1)

        # Create the toolRibbonBar
        self.ribbon = ribbon.RibbonBar(self, wx.ID_ANY)
        #self.home = ribbon.RibbonPage(self.ribbon, wx.ID_ANY, "general")

        # The station display area contains the datetimeInfo and the viewPort.
        # TODO: Maybe create a seperate class for this.
        self.viewportSizer = wx.GridBagSizer()
        self.centerPanel = wx.Panel(parent=self, id=wx.ID_ANY)
        self.datetimeInfo = container.TdDatetimeInfo(parent=self.centerPanel)
        self.viewPort =  container.TdViewPort(parent = self.centerPanel)
        self.viewportSizer.Add(self.datetimeInfo, 
                               pos=(0,0), 
                               flag=wx.EXPAND|wx.ALL, 
                               border=0)
        self.viewportSizer.Add(self.viewPort,
                               pos=(1,0),
                               flag = wx.EXPAND|wx.ALL, 
                               border = 0)
        self.viewportSizer.AddGrowableRow(1)
        self.viewportSizer.AddGrowableCol(0)
        self.centerPanel.SetSizer(self.viewportSizer)


        self.mgr.AddPane(self.centerPanel, 
                         wx.aui.AuiPaneInfo().Name('seismograms').
                                              CenterPane())

        self.mgr.AddPane(self.eventInfo,
                         wx.aui.AuiPaneInfo().Top().
                                              Name('event information').
                                              Layer(0).
                                              Row(0).
                                              Position(0))


        self.mgr.AddPane(self.ribbon,
                         wx.aui.AuiPaneInfo().Top().
                                              Name('palette').
                                              Caption('palette').
                                              Layer(1).
                                              Row(0).
                                              Position(0).
                                              BestSize(wx.Size(-1,50)).
                                              MinSize(wx.Size(-1,80)))


        # Build the ribbon bar based on the plugins.
        # First create all the pages according to the category.
        self.ribbonPages = {}
        self.ribbonPanels = {}
        self.ribbonToolbars = {}
        self.foldPanels = {}
        for curGroup, curCategory in sorted([(x.group, x.category) for x in self.plugins], key = itemgetter(0,1)):
            if curGroup not in self.ribbonPages.keys():
                self.logger.debug('Creating page %s', curGroup)
                self.ribbonPages[curGroup] = ribbon.RibbonPage(self.ribbon, wx.ID_ANY, curGroup)

            if curCategory not in self.ribbonPanels.keys():
                self.ribbonPanels[curCategory] = ribbon.RibbonPanel(self.ribbonPages[curGroup],
                                                                    wx.ID_ANY,
                                                                    curCategory,
                                                                    wx.NullBitmap,
                                                                    wx.DefaultPosition,
                                                                    wx.DefaultSize,
                                                                    agwStyle=ribbon.RIBBON_PANEL_NO_AUTO_MINIMISE)
                # TODO: Find out what I wanted to do with these lines!?!
                if curCategory == 'interactive':
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)
                else:
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)


        # Fill the ribbon bar with the plugin buttons.
        option_plugins = [x for x in self.plugins if x.mode == 'option']
        command_plugins = [x for x in self.plugins if x.mode == 'command']
        interactive_plugins = [x for x in self.plugins if x.mode == 'interactive']
        view_plugins = [x for x in self.plugins if x.mode == 'view']
        id_counter = 0

        for curPlugin in sorted(option_plugins, key = attrgetter('position_pref', 'name')):
                # Create a tool.
                curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter, 
                                                                          bitmap = curPlugin.icons['active'].GetBitmap(), 
                                                                          help_string = curPlugin.name,
                                                                          kind = ribbon.RIBBON_BUTTON_TOGGLE)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED, 
                                                             lambda evt, curPlugin=curPlugin : self.onOptionToolClicked(evt, curPlugin), id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(command_plugins, key = attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)
                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.onCommandToolDropdownClicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.onCommandToolClicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        for curPlugin in sorted(interactive_plugins, key = attrgetter('position_pref', 'name')):
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                help_string = curPlugin.name)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.onInteractiveToolClicked(evt, curPlugin),
                                                             id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                             lambda evt, curPlugin=curPlugin: self.onInteractiveToolDropdownClicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(view_plugins, key = attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)

                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.onViewToolDropdownClicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.onViewToolClicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        self.ribbon.Realize()

        # Tell the manager to commit all the changes.
        self.mgr.Update()

        self.SetBackgroundColour('white')
        self.viewPort.SetFocus()


    def initKeyEvents(self):
        ''' Initialize the key event bindings.

        '''
        # The released modifier key.
        self.modifier_key_up = None
        self.pressed_keys = []

        self.logger.debug('Binding key events.')
        self.viewPort.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.viewPort.Bind(wx.EVT_KEY_UP, self.onKeyUp)

        self.shortcutManager.addAction(('WXK_RIGHT',), self.advanceTime)
        self.shortcutManager.addAction(('WXK_SHIFT', 'WXK_RIGHT',), self.advanceTimePercentage, step = 25)
        self.shortcutManager.addAction(('WXK_COMMAND', 'WXK_RIGHT',), self.advanceTimePercentage, step = 10)
        self.shortcutManager.addAction(('WXK_ALT', 'WXK_RIGHT',), self.advanceTimePercentage, step = 1)
        self.shortcutManager.addAction(('WXK_LEFT',), self.decreaseTime)
        self.shortcutManager.addAction(('WXK_SHIFT', 'WXK_LEFT',), self.decreaseTimePercentage, step = 25)
        self.shortcutManager.addAction(('WXK_COMMAND', 'WXK_LEFT',), self.decreaseTimePercentage, step = 10)
        self.shortcutManager.addAction(('WXK_ALT', 'WXK_LEFT',), self.decreaseTimePercentage, step = 1)
        self.shortcutManager.addAction(('"-"',), self.growTimePeriod)
        self.shortcutManager.addAction(('WXK_SHIFT', '"-"',), self.growTimePeriod, ratio = 25)
        self.shortcutManager.addAction(('WXK_COMMAND', '"-"',), self.growTimePeriod, ratio = 10)
        self.shortcutManager.addAction(('WXK_ALT', '"-"',), self.growTimePeriod, ratio = 1)
        self.shortcutManager.addAction(('"+"',), self.shrinkTimePeriod)
        self.shortcutManager.addAction(('WXK_SHIFT', '"+"',), self.shrinkTimePeriod, ratio = 25)
        self.shortcutManager.addAction(('WXK_COMMAND', '"+"',), self.shrinkTimePeriod, ratio = 10)
        self.shortcutManager.addAction(('WXK_ALT', '"+"',), self.shrinkTimePeriod, ratio = 1)
        self.shortcutManager.addAction(('WXK_COMMAND', 'WXK_SPACE'), self.swap_tool)
        self.shortcutManager.addAction(('WXK_COMMAND', 'WXK_SPACE'), self.restore_tool, kind = 'up')
        self.shortcutManager.addAction(('WXK_ESCAPE',), self.deactivate_tool)


    def advanceTime(self, time_step = None):
        ''' Advance the display time by one step. 
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.advanceTime(time_step = time_step)
        self.updateDisplay()
        if oldFocus is not None:
            oldFocus.SetFocus()


    def advanceTimePercentage(self, step = 100):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.advanceTimePercentage(step)
        self.updateDisplay()
        oldFocus.SetFocus()


    def decreaseTime(self):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.decreaseTime()
        self.updateDisplay()
        oldFocus.SetFocus()


    def decreaseTimePercentage(self, step = 100):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.decreaseTimePercentage(step)
        self.updateDisplay()
        oldFocus.SetFocus()


    def growTimePeriod(self, ratio = 50):
        ''' Grow the time period by a given ratio.
        '''
        self.displayManager.growTimePeriod(ratio)
        self.updateDisplay()


    def shrinkTimePeriod(self, ratio = 50):
        ''' Grow the time period by a given ratio.
        '''
        self.displayManager.shrinkTimePeriod(ratio)
        self.updateDisplay()


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
        self.updateDisplay()
        print "##### end of set duration"


    def setStartTime(self, startTime):
        ''' Set the new start time of the displayed time period.
        '''
        self.displayManager.setStartTime(startTime)
        self.updateDisplay()



    def deactivate_interactive_plugin(self, plugin):
        ''' Deactivate an interactive plugin.
        '''
        if plugin.mode != 'interactive':
            return
        self.viewPort.clearEventCallbacks()
        self.viewPort.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        plugin.deactivate()
        self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)


    def activate_interactive_plugin(self, plugin):
        ''' Activate an interactive plugin.
        '''
        plugin.activate()
        if plugin.active:
            if plugin.cursor is not None:
                if isinstance(plugin.cursor, wx.lib.embeddedimage.PyEmbeddedImage):
                    image = plugin.cursor.GetImage()
                    # since this image didn't come from a .cur file, tell it where the hotspot is
                    img_size = image.GetSize()
                    image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, img_size[0] * plugin.cursor_hotspot[0])
                    image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, img_size[1] * plugin.cursor_hotspot[1])

                    # make the image into a cursor
                    self.viewPort.SetCursor(wx.CursorFromImage(image))
                else:
                    try:
                        self.viewPort.SetCursor(wx.StockCursor(plugin.cursor))
                    except:
                        pass

            self.logger.debug('Clicked the interactive tool: %s', plugin.name)

            # Get the hooks and register the matplotlib hooks in the viewport.
            hooks = plugin.getHooks()
            allowed_matplotlib_hooks = self.hook_manager.view_hooks.keys()

            for cur_key in hooks.keys():
                if cur_key not in allowed_matplotlib_hooks:
                    hooks.pop(cur_key)

            # Set the callbacks of the views.
            self.viewPort.clearEventCallbacks()
            self.viewPort.registerEventCallbacks(hooks, self.dataManager, self.displayManager)
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)



    def onOptionToolClicked(self, event, plugin):
        ''' Handle the click of an option plugin toolbar button.

        Show or hide the foldpanel of the plugin.
        '''
        self.logger.debug('Clicked the option tool: %s', plugin.name)

        cur_toolbar = event.GetEventObject()
        if cur_toolbar.GetToolState(event.GetId()) != ribbon.RIBBON_TOOLBAR_TOOL_TOGGLED:
            if plugin.name not in self.foldPanels.keys():
                # The panel of the option tool does't exist. Create it and add
                # it to the panel manager.
                curPanel = plugin.buildFoldPanel(self)
                self.mgr.AddPane(curPanel,
                                 wx.aui.AuiPaneInfo().Right().
                                                      Name(plugin.name).
                                                      Caption(plugin.name).
                                                      Layer(2).
                                                      Row(0).
                                                      Position(0).
                                                      BestSize(wx.Size(300,-1)).
                                                      MinSize(wx.Size(200,100)).
                                                      MinimizeButton(True).
                                                      MaximizeButton(True).
                                                      CloseButton(False))
                # TODO: Add a onOptionToolPanelClose method to handle clicks of
                # the CloseButton in the AUI pane of the option tools. If the
                # pane is closed, the toggle state of the ribbonbar button has
                # be changed. The according event is aui.EVT_AUI_PANE_CLOSE.
                self.mgr.Update()
                self.foldPanels[plugin.name] = curPanel
            else:
                if not self.foldPanels[plugin.name].IsShown():
                    curPanel = self.foldPanels[plugin.name]
                    self.mgr.GetPane(curPanel).Show()
                    self.mgr.Update()
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
        else:
            if self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Hide()
                self.mgr.Update()

            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)




    def onCommandToolClicked(self, event, plugin):
        ''' Handle the click of a command plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the command tool: %s', plugin.name)
        plugin.run()




    def onInteractiveToolClicked(self, event, plugin):
        ''' Handle the click of an interactive plugin toolbar button.

        Activate the tool.
        '''
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')
        elif len(active_plugin) == 1:
            active_plugin = active_plugin[0]
            self.deactivate_interactive_plugin(active_plugin)
        self.activate_interactive_plugin(plugin)



    def onViewToolClicked(self, event, plugin):
        ''' Handle the click of an view plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the view tool: %s', plugin.name)

        if plugin.active == True:
            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
            self.displayManager.removeViewTool(plugin)
        else:
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.displayManager.registerViewTool(plugin)

        self.updateDisplay()



    def onViewToolDropdownClicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an view plugin toolbar button.

        '''
        self.logger.debug('Clicked the view tool dropdown button: %s', plugin.name)
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin : self.onEditToolPreferences(evt, plugin), item)
        event.PopupMenu(menu)


    def onCommandToolDropdownClicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an command plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin : self.onEditToolPreferences(evt, plugin), item)
        event.PopupMenu(menu)



    def onInteractiveToolDropdownClicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an interactive plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin : self.onEditToolPreferences(evt, plugin), item)
        event.PopupMenu(menu)


    def onEditToolPreferences(self, event, plugin):
        ''' Handle the edit preferences dropdown click.

        '''
        self.logger.debug('Dropdown clicked -> editing preferences.')

        if plugin.name not in self.foldPanels.keys():
            #curPanel = plugin.buildFoldPanel(self.foldPanelBar)
            #foldPanel = self.foldPanelBar.addPanel(curPanel, plugin.icons['active'])

            curPanel = plugin.buildFoldPanel(self)
            self.mgr.AddPane(curPanel,
                             wx.aui.AuiPaneInfo().Right().
                                                  Name(plugin.name).
                                                  Caption(plugin.name).
                                                  Layer(2).
                                                  Row(0).
                                                  Position(0).
                                                  BestSize(wx.Size(300,-1)).
                                                  MinSize(wx.Size(200,100)).
                                                  MinimizeButton(True).
                                                  MaximizeButton(True))
            self.mgr.Update()
            self.foldPanels[plugin.name] = curPanel
        else:
            if not self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Show()
                self.mgr.Update()


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
        print "pressed key: %s." % pressedKey
        print "self.pressed_keys: %s." % self.pressed_keys
        self.logger.debug('pressed key: %s - %s', keyCode, pressedKey)
        action, kwargs = self.shortcutManager.getAction(tuple(pressedKey))

        if action and kwargs:
            action(**kwargs)
        elif action:
            action()


    def onKeyUp(self, event):
        ''' Handle a key release event.
        '''
        self.logger.debug('Releasing key.')
        keyCode = event.GetKeyCode()
        keyName = keyMap.get(keyCode, None)

        if keyName in ['WXK_SHIFT', 'WXK_COMMAND', 'WXK_ALT']:
            if self.pressed_keys:
                # Store the released modifier.
                print "KEY UP of %s." % keyName
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
        print "released key: %s." % pressedKey
        print "self.pressed_keys: %s." % self.pressed_keys
        self.logger.debug('Released key: %s - %s', keyCode, pressedKey)
        action, kwargs = self.shortcutManager.getAction(tuple(pressedKey), kind = 'up')

        if action and kwargs:
            action(**kwargs)
        elif action:
            action()


    def onSetFocus(self, event):
        ''' Handle a key down event.

        '''
        self.logger.debug('Setting focus.')



    def updateDisplay(self):
        ''' Update the display.

        '''
        # Create the necessary containers.
        # TODO: Call these method only, if the displayed stations or
        if self.displayManager.stationsChanged:
            self.displayManager.createContainers() 
            self.viewPort.sortStations(snl=[(x[0],x[1],x[2]) for x in self.displayManager.getSCNL('show')])
            self.displayManager.stationsChanged = False

        # TODO: Request the needed data from the wave client.
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
        for cur_station in self.displayManager.showStations:
            for cur_channel in cur_station.channels:
                if not cur_channel.container.data_plotted:
                    self.viewPort.hideChannel([cur_channel.getSCNL(),])
                else:
                    self.viewPort.showChannel([cur_channel.getSCNL(),])



        # Call the hooks of the plugins.
        self.call_hook('after_plot')

        # Update the viewport to show the changes.
        self.viewPort.Refresh()
        self.viewPort.Update()

        # Update the time information panel.
        self.datetimeInfo.setTime(self.displayManager.startTime, 
                                  self.displayManager.endTime, 
                                  None)
        self.datetimeInfo.Refresh()



    def call_hook(self, hook_name, **kwargs):
        ''' Call the hook of the plugins.
        '''
        active_plugins = [x for x in self.plugins if x.active]
        self.hook_manager.call_hook(receivers = active_plugins,
                                    hook_name = hook_name,
                                    **kwargs)


    def add_shared_info(self, origin_rid, name, value):
        ''' Add a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information

        value : Dictionary
            The value of the shared information
        '''
        self.plugins_information_bag.add_info(origin_rid = origin_rid,
                                              name = name,
                                              value = value)
        self.call_hook('shared_information_added',
                       origin_rid = origin_rid,
                       name = name)


    def notify_shared_info_change(self, updated_info):
        ''' Notify tracedisplay, that a shared informtion was changed.
        '''
        self.call_hook('shared_information_updated',
                       updated_info = updated_info)


    def get_shared_info(self, **kwargs):
        ''' Get a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information
        '''
        return self.plugins_information_bag.get_info(**kwargs)




class ShortcutManager:


    def __init__(self):
        ''' The constructor

        '''
        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # A dictionary holding the actions bound to a certain key combination.
        # The key of the dictionary is a tuple of none or more modifiers keys 
        # and the pressed key.
        self.actions = {}

        self.kwargs = {}


    def addAction(self, keyCombination, action, kind = 'down', **kwargs):
        ''' Add an action to the shortcut options.

        Parameters
        ----------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        action : Method
            The method which should be executed when the key is pressed.

        kind : String
            The kind of mouse event (up, down).

        '''
        self.actions[(kind, keyCombination)] = action
        self.kwargs[(kind, keyCombination)] = kwargs


    def getAction(self, keyCombination, kind = 'down'):
        ''' Get the action bound to the keyCombination.

        Paramters
        ---------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        kind : String
            The kind of mouse event (up, down).

        Returns
        -------
        action : Method
            The method which should be executed when the key is pressed.
            None if no action is found.
        '''
        self.logger.debug("Searching for: %s", keyCombination)
        self.logger.debug("Available actions: %s", self.actions)
        action = self.actions.get((kind, keyCombination), None)
        kwargs = self.kwargs.get((kind, keyCombination), None)

        return (action, kwargs)



class DisplayManager(object):


    def __init__(self, parent, inventory):

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
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

        # All stations that are contained in the inventory.
        self.availableStations = []

        # All unique channels contained in the available stations.
        self.availableChannels = []

        # The currently shown stations.
        # This is a list of DisplayStations instances.
        self.showStations = []

        # Indicates if the station configuration has changed.
        self.stationsChanged = False

        # Fill the available- and current station lists.
        for curNetwork in self.inventory.networks:
            for curStation in curNetwork.stations:
                self.availableStations.append(DisplayStation(curStation))

                for curChannel in curStation.channels:
                    if curChannel.name not in self.availableChannels:
                        self.availableChannels.append(curChannel.name)


        # The channels currently shown.
        # TODO: This should be selected by the user in the edit dialog.
        show_channels = self.pref_manager.get_value('show_channels')
        self.showChannels = [x for x in show_channels if x in self.availableChannels]

        # The views currently shown. (viewName, viewType)
        # TODO: This should be selected by the user in the edit dialog.
        #self.showViews = [('seismogram', 'seismogram')]
        # Create the views based on the active view tools.
        viewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active]


        # Limit the stations to show.
        # TODO: This should be selected by the user in the edit dialog.
        #self.showStations = [('GILA', 'HHZ', 'ALPAACT', '00'),
        #                     ('SITA', 'HHZ', 'ALPAACT', '00'),
        #                     ('GUWA', 'HHZ', 'ALPAACT', '00')]
        show_stations = self.pref_manager.get_value('show_stations')
        for curStation in self.availableStations:
            if curStation.name in show_stations:
                station2Add = curStation
                station2Add.addChannel(self.showChannels)
                for curChannel in station2Add.channels:
                    for curPlugin in viewPlugins:
                        view_class = curPlugin.getViewClass()
                        if view_class is not None:
                            curChannel.addView(curPlugin.name, view_class)
                self.showStations.append(station2Add)
        self.stationsChanged = True

        self.sort_show_stations()


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



    def hideStation(self, snl):
        ''' Remove the specified station from the showed stations.

        Parameters
        ----------
        snl : tuple (String, String, String)
            The station, network, location code of the station which should be hidden.
        '''


        stat2Remove = [x for x in self.showStations if snl == x.getSNL()]

        for curStation in stat2Remove:
            self.showStations.remove(curStation)
            self.parent.viewPort.removeStation(curStation.getSNL())



    def showStation(self, snl):
        ''' Show the specified station in the display.

        Parameters
        ----------
        snl : tuple (String, String, String)
            The station, network, location code of the station which should be hidden.
        '''

        viewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active]
        interactive_plugins = [x for x in self.parent.plugins if x.mode == 'interactive' and x.active]

        # Get the selected station and set all currently active
        # channels.
        station2Show = self.getAvailableStation(snl)
        self.addShowStation(station2Show)
        station2Show.addChannel(self.showChannels)
        for curChannel in station2Show.channels:
            for curPlugin in viewPlugins:
                view_class = curPlugin.getViewClass()
                if view_class is not None:
                    curChannel.addView(curPlugin.name, view_class)

        # Create the necessary containers.
        stationContainer = self.createStationContainer(station2Show)
        for curChannel in station2Show.channels:
            curChanContainer = self.createChannelContainer(stationContainer, curChannel)
            for curViewName, (curViewType, ) in curChannel.views.items():
                self.createViewContainer(curChanContainer, curViewName, curViewType)

        # Update the display
        self.parent.viewPort.sortStations(snl = self.getSNL(source='show'))
        self.parent.viewPort.Refresh()


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
        for cur_channel in station2Show.channels:
            if not cur_channel.container.data_plotted:
                self.parent.viewPort.hideChannel([cur_channel.getSCNL(),])
            else:
                self.parent.viewPort.showChannel([cur_channel.getSCNL(),])


        # Call the hooks of the plugins.
        self.parent.call_hook('after_plot_station', station = [station2Show,])

        # If an interactive plugin is active, register the hooks for the added
        # station.
        if len(interactive_plugins) == 1:
            cur_plugin = interactive_plugins[0]
            self.parent.viewPort.registerEventCallbacks(cur_plugin.getHooks(),
                                                        self.parent.dataManager,
                                                        self.parent.displayManager)



    def showChannel(self, channel):
        ''' Show a channel in the display.

        Parameters
        ----------
        channel : String
            The channel name which should be shown.
        '''
        if channel not in self.showChannels:
            self.showChannels.append(channel)

        viewPlugins = [x for x in self.parent.plugins if x.mode == 'view' and x.active]

        for curStation in self.showStations:
             curStation.addChannel([channel])
             for curChannel in curStation.channels:
                 for curPlugin in viewPlugins:
                    view_class = curPlugin.getViewClass()
                    if view_class is not None:
                        curChannel.addView(curPlugin.name, view_class)

        # TODO: Only update the data of the added channel.
        self.stationsChanged = True
        self.parent.updateDisplay() 



    def hideChannel(self, channel):
        ''' Hide a channel in the display.

        Parameters
        ----------
        channel : String
            The name of the channel which should be hidden.
        '''
        for curStation in self.showStations:
            removedSCNL = curStation.removeChannel([channel])
            self.parent.viewPort.removeChannel(removedSCNL)

        self.showChannels.remove(channel)


    def registerViewTool(self, plugin):
        ''' Create the views needed by the plugin.
        '''
        for curStation in self.showStations:
            for curChannel in curStation.channels:
                view_class = plugin.getViewClass()
                if view_class is not None:
                    curChannel.addView(plugin.name, view_class)
                    channelContainer = self.parent.viewPort.getChannelContainer(station = curChannel.parent.name,
                                                                                channel = curChannel.name,
                                                                                network = curChannel.parent.network,
                                                                                location = curChannel.parent.location)
                    for curChannelContainer in channelContainer:
                        self.createViewContainer(curChannelContainer, plugin.name, view_class)


    def removeViewTool(self, plugin):
        ''' Remove the views created by the plugin.

        '''
        for curStation in self.showStations:
            for curChannel in curStation.channels:
                channelContainers = self.parent.viewPort.getChannelContainer(station = curChannel.parent.name,
                                                                               channel = curChannel.name,
                                                                               network = curChannel.parent.network,
                                                                               location = curChannel.parent.location)
                curChannel.removeView(plugin.name, 'my View')
                for curContainer in channelContainers:
                    curContainer.removeView(plugin.name)






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
        for curStation in self.showStations:
            curStatContainer = self.createStationContainer(curStation)
            for curChannel in curStation.channels:
                curChanContainer = self.createChannelContainer(curStatContainer, curChannel)
                for curViewName, (curViewType, ) in curChannel.views.items():
                    self.createViewContainer(curChanContainer, curViewName, curViewType)



    def createStationContainer(self, station):
        ''' Create the station container of the specified station.

        '''
        viewport = self.parent.viewPort

        # Check if the container already exists in the viewport.
        statContainer = viewport.getStation(name = station.name,
                                            network = station.network,
                                            location = station.location)
        if not statContainer:
            statContainer = container.StationContainer(parent = viewport,
                                                id = wx.ID_ANY,
                                                name = station.name,
                                                network = station.network,
                                                location = station.location,
                                                color = 'white')
            viewport.addStation(statContainer)
            statContainer.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)
            statContainer.Bind(wx.EVT_KEY_UP, self.parent.onKeyUp)
        else:
            statContainer = statContainer[0]

        return statContainer



    def createChannelContainer(self, stationContainer, channel):
        '''

        '''
        # Check if the container already exists in the station.
        chanContainer = stationContainer.getChannel(name = channel.name)

        if not chanContainer:
            if self.channelColors.has_key(channel.name):
                curColor = self.channelColors[channel.name]
            else:
                curColor = (0, 0, 0)

            chanContainer = container.ChannelContainer(stationContainer,
                                                       id = wx.ID_ANY,
                                                       name = channel.name,
                                                       color=curColor)
            stationContainer.addChannel(chanContainer)
            channel.container = chanContainer
        else:
            chanContainer = chanContainer[0]

        return chanContainer



    def createViewContainer(self, channelContainer, name, viewClass):
        '''

        '''
        # Check if the container already exists in the channel.
        viewContainer = channelContainer.getView(name = name)

        if not viewContainer:
            viewContainer = viewClass(channelContainer,
                                      id = wx.ID_ANY,
                                      name = name)

            channelContainer.addView(viewContainer)
            channelContainer.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)
            channelContainer.Bind(wx.EVT_KEY_UP, self.parent.onKeyUp)

        return viewContainer


    def getViewContainer(self, station = None,
                         channel = None, network = None,
                         location = None, name = None):
        ''' Get the view container of the specified search terms.

        '''
        return self.parent.viewPort.getViewContainer(station = station,
                                                     channel = channel,
                                                     network = network,
                                                     location = location,
                                                     name = name)



class DisplayStation():
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



class DisplayChannel():

    def __init__(self, parent, name):

        self.parent = parent

        self.name = name

        self.views = {}

        # The display containers of the channel.
        self.container = None


    def addView(self, name, viewType):
        if name not in self.views.keys():
            self.views[name] = (viewType, )


    def removeView(self, name, viewType):
        if name in self.views.keys():
            self.views.pop(name)

    
    def getSCNL(self):
        return (self.parent.name, self.name, self.parent.network, self.parent.location)





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
        dataSources = {}
        for curScnl in scnl:
            if curScnl in self.project.scnlDataSources.keys():
                if self.project.scnlDataSources[curScnl] not in dataSources.keys():
                    dataSources[self.project.scnlDataSources[curScnl]] = [curScnl, ]
                else:
                    dataSources[self.project.scnlDataSources[curScnl]].append(curScnl)
            else:
                if self.project.defaultWaveclient not in dataSources.keys():
                    dataSources[self.project.defaultWaveclient] = [curScnl, ]
                else:
                    dataSources[self.project.defaultWaveclient].append(curScnl)

        self.origStream = Stream()

        for curName in dataSources.iterkeys():
            self.logger.debug("curName: %s", curName)
            curWaveclient = self.project.waveclient[curName]
            curStream =  curWaveclient.getWaveform(startTime = startTime,
                                                   endTime = endTime,
                                                   scnl = scnl)
            self.origStream += curStream



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
        if scnl in self.project.scnlDataSources.keys():
            dataSource = self.project.scnlDataSources[scnl] 
        else:
            dataSource = self.project.defaultWaveclient

        curWaveClient = self.project.waveclient[dataSource]

        curStream = curWaveClient.getWaveform(startTime = startTime,
                                              endTime = endTime,
                                              scnl = scnl)

        self.origStream = self.origStream + curStream
        return curStream


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





