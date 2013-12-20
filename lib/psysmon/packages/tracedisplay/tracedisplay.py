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
import itertools
from operator import itemgetter, attrgetter
from wx.lib.pubsub import Publisher as pub
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


    def __init__(self):
        psysmon.core.packageNodes.CollectionNode.__init__(self)
        pref_item = pref_manager.TextEditPrefItem(name = 'start_time', label = 'start time', value = UTCDateTime('2012-08-03 00:00:00'))
        self.pref_manager.add_item(item = pref_item)
        pref_item = pref_manager.TextEditPrefItem(name = 'end_time', label = 'end time', value = UTCDateTime('2012-08-03 00:05:00'))
        self.pref_manager.add_item(item = pref_item)
        pref_item = pref_manager.TextEditPrefItem(name = 'show_channels', label = 'channels', value = ['HHZ',])
        self.pref_manager.add_item(item = pref_item)
        pref_item = pref_manager.TextEditPrefItem(name = 'show_stations', label = 'stations', value = ['AP01'])
        self.pref_manager.add_item(item = pref_item)

    def edit(self):
        pass


    def execute(self, prevNodeOutput={}):

        self.logger.debug('Executing TraceDisplay')


        app = psygui.PSysmonApp()

        # Get the plugins for this class.
        plugins = self.project.getPlugins(self.__class__.__name__)

        tdDlg = TraceDisplayDlg(self,
                                project = self.project,
                                parent = None,
                                id = wx.ID_ANY,
                                title = "TraceDisplay Development",
                                plugins = plugins)

        app.MainLoop()


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
        loggerName = __name__ + "." + self.__class__.__name__
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
        inventory = DbInventory.load_inventory(self.project)
        #db_inventory = DbInventory('test', self.project)
        #db_inventory.load_recorders()
        #db_inventory.load_networks()
        #db_inventory.close()
        self.displayManager = DisplayManager(parent = self,
                                             inventory = inventory)

        # Create the shortcut options.
        self.shortcutManager = ShortcutManager()

        # Create the dataManager.
        self.dataManager = DataManager(self)

        # Initialize the user interface.
        self.initUI()
        self.initKeyEvents()

        # Display the data.
        self.updateDisplay()

        # Show the frame. 
        self.Show(True)


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
        for curGroup, curCategory in [(x.group, x.category) for x in self.plugins]:
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
        for k,curPlugin in enumerate(self.plugins):
            if curPlugin.mode == 'option':
                # Create a tool.
                curTool = self.ribbonToolbars[curPlugin.category].AddTool(k, curPlugin.icons['active'].GetBitmap())
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED, 
                                                             lambda evt, curPlugin=curPlugin : self.onOptionToolClicked(evt, curPlugin), id=curTool.id)
            elif curPlugin.mode == 'command':
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(k, curPlugin.icons['active'].GetBitmap())
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.onCommandToolClicked(evt, curPlugin),
                                                             id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                             lambda evt, curPlugin=curPlugin: self.onCommandToolDropdownClicked(evt, curPlugin),
                                                             id=curTool.id)
            elif curPlugin.mode == 'interactive':
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(k, curPlugin.icons['active'].GetBitmap())
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.onInteractiveToolClicked(evt, curPlugin),
                                                             id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                             lambda evt, curPlugin=curPlugin: self.onInteractiveToolDropdownClicked(evt, curPlugin),
                                                             id=curTool.id)
            elif curPlugin.mode == 'addon':
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(k, curPlugin.icons['active'].GetBitmap(), help_string='Hallo Stefan')
                #self.ribbonToolbars[curPlugin.category].SetToolClientData(curTool, 'test')
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.onAddonToolClicked(evt, curPlugin),
                                                             id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                             lambda evt, curPlugin=curPlugin: self.onAddonToolDropdownClicked(evt, curPlugin),
                                                             id=curTool.id)


            # Get all option plugins and build the foldpanels.
            #if curPlugin.mode == 'option':
            #    curPlugin.buildFoldPanel(self.toolPanels)

            # Get all interactive plugins and add them to the toolbar.
            #if curPlugin.mode == 'interactive':
            #    button = curPlugin.buildToolbarButton()
            #    if button:
            #        self.logger.debug(button)

        self.ribbon.Realize()


        # Tell the manager to commit all the changes.
        self.mgr.Update() 

        self.SetBackgroundColour('white')
        self.viewPort.SetFocus()


    def initKeyEvents(self):
        ''' Initialize the key event bindings.

        '''
        self.logger.debug('Binding key events.')
        self.viewPort.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

        self.shortcutManager.addAction(('WXK_RIGHT',), self.advanceTime)
        self.shortcutManager.addAction(('WXK_LEFT',), self.decreaseTime)
        self.shortcutManager.addAction(('"-"',), self.growTimePeriod)
        self.shortcutManager.addAction(('"+"',), self.shrinkTimePeriod)


    def advanceTime(self, time_step = None):
        ''' Advance the display time by one step. 
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.advanceTime(time_step = time_step)
        self.updateDisplay()
        if oldFocus is not None:
            oldFocus.SetFocus()


    def decreaseTime(self):
        ''' Decrease the display time by one step.
        '''
        oldFocus = wx.Window.FindFocus()
        self.displayManager.decreaseTime()
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
    


    def onOptionToolClicked(self, event, plugin):
        ''' Handle the click of an option plugin toolbar button.

        Show or hide the foldpanel of the plugin.
        '''
        self.logger.debug('Clicked the option tool: %s', plugin.name)

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
        self.logger.debug('Clicked the interactive tool: %s', plugin.name)
        hooks = plugin.getHooks()

        # Set the callbacks of the views.
        self.viewPort.registerEventCallbacks(hooks, self.dataManager, self.displayManager)



    def onAddonToolClicked(self, event, plugin):
        ''' Handle the click of an addon plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the addon tool: %s', plugin.name)

        if plugin.active == True:
            plugin.setInactive()
            self.displayManager.removeAddonTool(plugin)
        else:
            plugin.setActive()
            self.displayManager.registerAddonTool(plugin)

        self.updateDisplay()



    def onAddonToolDropdownClicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an addon plugin toolbar button.

        '''
        self.logger.debug('Clicked the addon tool dropdown button: %s', plugin.name)


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


    def onKeyDown(self, event):
        ''' Handle a key down event.

        '''
        keyCode = event.GetKeyCode()
        keyName = keyMap.get(keyCode, None)

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


        # Process the modifiers.
        pressedKey = []
        modString = ""
        for mod, ch in [(event.ControlDown(), 'CTRL'),
                        (event.AltDown(),     'ALT'),
                        (event.ShiftDown(),   'SHIFT'),
                        (event.MetaDown(),    'META')]:
            if mod:
                pressedKey.append(ch)
                modString += ch + " + "

        pressedKey.append(keyName)
        pressedKeyString = modString + keyName
        self.logger.debug('Pressed key: %s - %s', keyCode, pressedKeyString)
        action = self.shortcutManager.getAction(tuple(pressedKey))
        print pressedKey

        if action:
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


        # Plot the data using the addon tools.
        addonPlugins = [x for x in self.plugins if x.mode == 'addon' and x.active]
        for curPlugin in addonPlugins:
            curPlugin.plot(self.displayManager, self.dataManager)


        # Update the viewport to show the changes.
        self.viewPort.Refresh()
        self.viewPort.Update()

        # Update the time information panel.
        self.datetimeInfo.setTime(self.displayManager.startTime, 
                                  self.displayManager.endTime, 
                                  None)
        self.datetimeInfo.Refresh()
        return




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


    def addAction(self, keyCombination, action):
        ''' Add an action to the shortcut options.

        Parameters
        ----------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        action : Method
            The method which should be executed when the key is pressed.

        '''
        self.actions[keyCombination] = action


    def getAction(self, keyCombination):
        ''' Get the action bound to the keyCombination.

        Paramters
        ---------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        Returns
        -------
        action : Method
            The method which should be executed when the key is pressed.
            None if no action is found.
        '''
        self.logger.debug("Searching for: %s", keyCombination)
        self.logger.debug("Available actions: %s", self.actions)
        return self.actions.get(keyCombination, None)



class DisplayManager:


    def __init__(self, parent, inventory):

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The parent tracedisplay instance.
        self.parent = parent

        # The inventory of the available geometry.
        self.inventory = inventory

        pref_manager = self.parent.collection_node.pref_manager

        # The timespan to show.
        self.startTime = pref_manager.get_value('start_time')
        self.endTime = pref_manager.get_value('end_time')
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
                channels = set([x[0].channel_name for x in curStation.sensors])
                self.availableStations.append(DisplayStation(curStation))

                for curChannel in channels:
                    if curChannel not in self.availableChannels:
                        self.availableChannels.append(curChannel)


        # The channels currently shown.
        # TODO: This should be selected by the user in the edit dialog.
        show_channels = pref_manager.get_value('show_channels')
        self.showChannels = [x for x in show_channels if x in self.availableChannels]

        # The views currently shown. (viewName, viewType)
        # TODO: This should be selected by the user in the edit dialog.
        #self.showViews = [('seismogram', 'seismogram')]
        # Create the views based on the active addon tools.
        addonPlugins = [x for x in self.parent.plugins if x.mode == 'addon' and x.active]


        # Limit the stations to show.
        # TODO: This should be selected by the user in the edit dialog.
        #self.showStations = [('GILA', 'HHZ', 'ALPAACT', '00'),
        #                     ('SITA', 'HHZ', 'ALPAACT', '00'),
        #                     ('GUWA', 'HHZ', 'ALPAACT', '00')]
        show_stations = pref_manager.get_value('show_stations')
        for curStation in self.availableStations:
            if curStation.name in show_stations:
                station2Add = DisplayStation(curStation)
                station2Add.addChannel(self.showChannels)
                for curChannel in station2Add.channels:
                    for curPlugin in addonPlugins:
                        curChannel.addView(curPlugin.name, 'my Type')
                self.showStations.append(station2Add)
        self.stationsChanged = True

        self.showStations = sorted(self.showStations, key = attrgetter('name'))



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

        print "##### end of advanceTime"




    def decreaseTime(self):
        ''' Decrease the time by one step.

        '''
        interval = self.endTime - self.startTime
        self.endTime = self.startTime
        self.startTime = self.startTime - interval


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


    def setTimeLimits(self, startTime, endTime):
        ''' Set the start- and endTime of the displayed time period.

        '''
        self.startTime = startTime
        self.endTime = endTime



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

        addonPlugins = [x for x in self.parent.plugins if x.mode == 'addon' and x.active]

        # Get the selected station and set all currently active
        # channels.
        station2Show = self.getAvailableStation(snl)
        self.addShowStation(station2Show)
        station2Show.addChannel(self.showChannels)
        for curChannel in station2Show.channels:
            for curPlugin in addonPlugins:
                curChannel.addView(curPlugin.name, curPlugin.getViewClass())

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


        # Plot the data of the station only using the addon tools.
        for curPlugin in addonPlugins:
            curPlugin.plotStation(displayManager = self.parent.displayManager,
                           dataManager = self.parent.dataManager,
                           station = [station2Show,])



    def showChannel(self, channel):
        ''' Show a channel in the display.

        Parameters
        ----------
        channel : String
            The channel name which should be shown.
        '''
        if channel not in self.showChannels:
            self.showChannels.append(channel)
        
        addonPlugins = [x for x in self.parent.plugins if x.mode == 'addon' and x.active]

        for curStation in self.showStations:
             curStation.addChannel([channel])
             for curChannel in curStation.channels:
                 for curPlugin in addonPlugins:
                     curChannel.addView(curPlugin.name, curPlugin.getViewClass())


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


    def registerAddonTool(self, plugin):
        ''' Create the views needed by the plugin.
        '''
        for curStation in self.showStations:
            for curChannel in curStation.channels:
                curChannel.addView(plugin.name, 'my View')
                curChannelContainer = self.parent.viewPort.getChannelContainer(curChannel.getSCNL())
                self.createViewContainer(curChannelContainer, plugin.name, plugin.getViewClass())


    def removeAddonTool(self, plugin):
        ''' Remove the views created by the plugin.
        
        '''
        for curStation in self.showStations:
            for curChannel in curStation.channels:
                curChannelContainer = self.parent.viewPort.getChannelContainer(curChannel.getSCNL())
                curChannel.removeView(plugin.name, 'my View')
                curChannelContainer.removeView(plugin.name)






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
        
        self.stationsChanged = True


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
        statContainer = viewport.hasStation(station.getSNL())
        if not statContainer:
            statContainer = container.StationContainer(parent = viewport,
                                                id = wx.ID_ANY,
                                                name = station.name,
                                                network = station.network,
                                                location = station.location,
                                                color = 'white')
            viewport.addStation(statContainer)
            statContainer.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)

        return statContainer



    def createChannelContainer(self, stationContainer, channel):
        '''

        '''
        # Check if the container already exists in the station.
        chanContainer = stationContainer.hasChannel(channel.name)
        
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

        return chanContainer
        
         
                
    def createViewContainer(self, channelContainer, name, viewClass):
        '''
        
        '''
        # Check if the container already exists in the channel.
        viewContainer = channelContainer.hasView(name)

        if not viewContainer:
            #viewContainer = container.viewTypeMap[viewType](channelContainer,
            #                                            id = wx.ID_ANY,
            #                                            name = name,
            #                                            lineColor = channelContainer.color)
            viewContainer = viewClass(channelContainer,
                                      id = wx.ID_ANY,
                                      name = name)

            channelContainer.addView(viewContainer)
            channelContainer.Bind(wx.EVT_KEY_DOWN, self.parent.onKeyDown)

        return viewContainer


    def getViewContainer(self, scnl=None, viewName=None):
        ''' Get the view container of a specified scnl code.

        '''
        return self.parent.viewPort.getViewContainer(scnl, viewName)



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
                                                self.project,
                                                self.parent.displayManager.inventory)
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







