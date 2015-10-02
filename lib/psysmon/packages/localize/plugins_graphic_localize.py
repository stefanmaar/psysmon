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
from operator import itemgetter, attrgetter

import wx
try:
    from agw import ribbon as ribbon
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.ribbon as ribbon

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import psysmon
import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons
import psysmon.core.preferences_manager as preferences_manager


class PluginGraphicLocalizer(plugins.CommandPlugin):
    ''' Localize an event origin using graphical methods.
    '''
    nodeClass = 'common'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'graphical localization',
                                       category = 'localize',
                                       tags = ['localize', 'circle', 'hyperble', 'tdoa', 'time difference of arrival'])

        # Create the logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.localize_graphical_icon_16

        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio', 
                                                       value = 20,
                                                       limit = (1, 99)
                                                      )
        self.pref_manager.add_item(item = item)


    def run(self):
        ''' Initialize the graphical localizer dialog and show it.
        '''
        # TODO: Add the localization method to the dialog attributes.
        # Or even better create a GraphicLocalizer class which does all the
        # computation and pass an instance to the dialog.

        # Get the selected event.
        selected_event_info = self.parent.get_shared_info(name = 'selected_event')
        if selected_event_info:
            selected_event_id = selected_event_info[0].value['id']
            selected_event_catalog_name = selected_event_info[0].value['catalog_name']
        else:
            selected_event_id = None
            selected_event_catalog_name = None

        # Get the selected pick catalog name.
        selected_pick_catalog_info = self.parent.get_shared_info(name = 'selected_pick_catalog')
        if selected_pick_catalog_info:
            selected_pick_catalog_name = selected_pick_catalog_info[0].value['catalog_name']
        else:
            selected_pick_catalog_name = None

        dlg = GraphicLocalizerDialog(project = self.parent.project,
                                     parent = self.parent,
                                     event_id = selected_event_id,
                                     event_catalog_name = selected_event_catalog_name,
                                     pick_catalog_name = selected_pick_catalog_name,
                                     id = wx.ID_ANY)

        dlg.Show()






class PsysmonDockingFrame(wx.Frame):
    ''' A base class for a frame holding AUI docks.
    '''

    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = 'docking frame', size = (1000, 600)):
        ''' Initialize the instance.
        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # The docking manager.
        self.mgr = wx.aui.AuiManager(self)

        # Create the tool ribbon bar.
        self.ribbon = ribbon.RibbonBar(self, wx.ID_ANY)


    def init_ribbon_bar(self):
        ''' Initialize the ribbon bar with the plugins.
        '''
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



class MapViewPanel(wx.Panel):
    '''
    The MapViewPanel class.

    This class creates a panel holding a mpl_toolkits.basemap map.
    This map is used to display the stations contained in the inventory.

    :ivar sizer: The sizer used for the panel layout.
    :ivar mapFigure: The matplotlib figure holding the map axes.
    :ivar mapAx: The matplotlib axes holding the Basemap.
    :ivar mapCanvas: The wxPython figureCanvas holding the matplotlib figure.
    :ivar map: The station map (`~mpl_toolkits.basemap.Basemap`).
    '''
    def __init__(self, parent, id=wx.ID_ANY):
        '''
        The constructor.

        Create an instance of the MapViewPanel class.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.geometry.MapViewPanel`
        :param parent: The parent object containing the panel.
        :type self: A wxPython window.
        :param id: The id of the panel.
        :type id: 
        '''
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.sizer = wx.GridBagSizer(0, 0)

        self.map_figure = Figure((8,4), dpi=75, facecolor='white')
        self.map_ax = self.map_figure.add_subplot(111)
        self.map_ax.set_aspect('equal')
        self.map_canvas = FigureCanvas(self, -1, self.map_figure)

        self.sizer.Add(self.map_canvas, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=0)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizerAndFit(self.sizer)




class GraphicLocalizerDialog(PsysmonDockingFrame):
    ''' The dialog window of the graphical localization plugin.

    Similar to the tracedisplay it uses the AUI Manager and plugins.
    '''

    def __init__(self, project, parent = None, event_id = None,
                 event_catalog_name = None, pick_catalog_name = None,
                 id = wx.ID_ANY, title = 'graphical localizer', size = (1000, 600)):
        ''' Initialize the instance.
        '''
        PsysmonDockingFrame.__init__(self,
                                     parent = parent,
                                     id = id,
                                     title = title)

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The psysmon project.
        self.project = project

        # The instance which created the dialog.
        self.parent = parent

        # Get the available plugins and filter them for the needed ones.
        needed_plugins = []
        self.plugins = self.project.getPlugins(('common', 'GraphicalLocalizer'))
        self.plugins = [x for x in self.plugins if x.name in needed_plugins]

        # Initialize the user interface.
        self.init_user_interface()


    def init_user_interface(self):
        ''' Create the graphical user interface.
        '''
        # Create the center panel holding the plot axes.
        self.map_panel = MapViewPanel(self)

        self.mgr.AddPane(self.map_panel,
                         wx.aui.AuiPaneInfo().Name('map').CenterPane())

        self.mgr.AddPane(self.ribbon,
                         wx.aui.AuiPaneInfo().Top().
                                              Name('palette').
                                              Caption('palette').
                                              Layer(1).
                                              Row(0).
                                              Position(0).
                                              BestSize(wx.Size(-1,50)).
                                              MinSize(wx.Size(-1,80)).
                                              CloseButton(False))

        # Initialize the ribbon bar using the loaded plugins.
        self.init_ribbon_bar()

        # Tell the docking manager to commit all the changes.
        self.mgr.Update()




class CircleLocalizer(object):
    ''' Localize an event using the circle method.
    '''
    def __init__(self, geom_inventory, picks, axes):
        ''' Initialize the instance.

        Parameters
        ----------
        geom_inventory : 
            The geometry inventory.

        picks : list of Pick
            The traveltime picks to use for the localization.

        axes : 
            The matplotlib axes where to plot the circles.

        '''
        pass
