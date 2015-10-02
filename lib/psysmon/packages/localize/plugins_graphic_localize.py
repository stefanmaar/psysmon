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

import psysmon
import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons


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


    def run(self):
        ''' Initialize the graphical localizer dialog and show it.
        '''
        # TODO: The tracedisplay instance should be available in the dialog.
        dlg = GraphicLocalizerDialog(project = self.parent.project,
                                    parent = self.parent,
                                    id = wx.ID_ANY)

        dlg.Show()




class GraphicLocalizerDialog(wx.Frame):
    ''' The dialog window of the graphical localization plugin.

    Similar to the tracedisplay it uses the AUI Manager and plugins.
    '''

    def __init__(self, project, parent = None, id = wx.ID_ANY,
                 title = 'graphical localizer', size = (1000, 600)):
        ''' Initialize the instance.
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

        # The psysmon project.
        self.project = project

        # The instance which created the dialog.
        self.parent = parent

        # Get the available plugins.
        self.plugins = self.project.getPlugins(('common', 'GraphicalLocalizer'))


        # Initialize the user interface.
        self.init_user_interface()


    def init_user_interface(self):
        ''' Create the graphical user interface.
        '''
        # The docking manager.
        self.mgr = wx.aui.AuiManager(self)


        # Create the tool ribbon bar.
        self.ribbon = ribbon.RibbonBar(self, wx.ID_ANY)

        # Create the center panel holding the plot axes.
        self.center_panel = wx.Panel(parent = self, id = wx.ID_ANY)

        self.mgr.AddPane(self.center_panel,
                         wx.aui.AuiPaneInfo().Name('plot').CenterPane())

        self.mgr.AddPane(self.ribbon,
                         wx.aui.AuiPaneInfo().Top().
                                              Name('palette').
                                              Caption('palette').
                                              Layer(1).
                                              Row(0).
                                              Position(0).
                                              BestSize(wx.Size(-1,50)).
                                              MinSize(wx.Size(-1,80)))

        self.init_ribbon_bar()

        # Tell the docking manager to commit all the changes.
        self.mgr.Update()


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


