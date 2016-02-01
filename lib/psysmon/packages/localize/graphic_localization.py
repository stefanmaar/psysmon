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
'''
The graphical localization module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import logging
import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import psysmon
import psysmon.core.packageNodes as packageNodes
import psysmon.core.gui as gui
import psysmon.packages.event.core as ev_core


class GraphicLocalizationNode(packageNodes.CollectionNode):

    name = 'graphic localization'
    mode = 'editable'
    category = 'Event'
    tags = ['development',]


    def __init__(self, **args):
        packageNodes.CollectionNode.__init__(self, **args)


    def edit(self):
        ''' Edit the preferences of the collection node.
        '''
        pass


    def execute(self, prevNodeOutput = {}):
        ''' Execute the collection node.
        '''
        app = gui.PSysmonApp()

        dlg = GraphicLocalizerDialog(collection_node = self,
                                     project = self.project,
                                     parent = None,
                                     event_id = None,
                                     event_catalog_name = None,
                                     pick_catalog_name = None,
                                     id = wx.ID_ANY)

        dlg.Show()
        app.MainLoop()


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




class GraphicLocalizerDialog(gui.PsysmonDockingFrame):
    ''' The dialog window of the graphical localization plugin.

    Similar to the tracedisplay it uses the AUI Manager and plugins.
    '''

    def __init__(self, collection_node, project, parent = None, event_id = None,
                 event_catalog_name = None, pick_catalog_name = None,
                 id = wx.ID_ANY, title = 'graphical localizer', size = (1000, 600)):
        ''' Initialize the instance.
        '''
        gui.PsysmonDockingFrame.__init__(self,
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
        self.collection_node = collection_node

        # Get the available plugins and filter them for the needed ones.
        needed_plugins = ['select event',]
        self.plugins = self.project.getPlugins(('common', 'GraphicLocalizer'))
        self.plugins = [x for x in self.plugins if x.name in needed_plugins]
        for cur_plugin in self.plugins:
            cur_plugin.parent = self

        # Create the events library.
        self.event_library = ev_core.Library(name = self.collection_node.rid)

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





