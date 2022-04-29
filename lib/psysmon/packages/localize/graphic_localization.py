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

from builtins import object
import logging
import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import psysmon
import psysmon.core.packageNodes as packageNodes
import psysmon.core.gui as gui
import psysmon.gui.main.app as psy_app


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
        app = psy_app.PsysmonApp()

        dlg = GraphicLocalizerDialog(collection_node = self,
                                     project = self.project,
                                     parent = None,
                                     event_id = None,
                                     event_catalog_name = None,
                                     pick_catalog_name = None,
                                     id = wx.ID_ANY)

        dlg.Show()
        app.MainLoop()



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
        needed_plugins = ['select event', 'select picks', 'circle method', 'map view',
                          'export result', 'tdoa method', 'clear map']
        self.plugins = self.project.getPlugins(('common', 'GraphicLocalizationNode'))
        self.plugins = [x for x in self.plugins if x.name in needed_plugins]
        for cur_plugin in self.plugins:
            cur_plugin.parent = self

        # Initialize the user interface.
        self.init_user_interface()

        # Update the display.
        self.update_display()


    def init_user_interface(self):
        ''' Create the graphical user interface.
        '''
        # Create the center panel holding the plot axes.
        #self.map_panel = MapViewPanel(self)

        # Initialize the ribbon bar using the loaded plugins.
        self.init_ribbon_bar()

        # Add a default view container.
        # TODO: For the future, for each selected event a view container could
        # be created - don't know if that makes sense.
        container_node = psysmon.core.gui_view.ViewContainerNode(name = 'default',
                                                                 parent = self.viewport,
                                                                 color = 'lightgrey')
        self.viewport.add_node(container_node)

        # Tell the docking manager to commit all the changes.
        self.mgr.Update()


    def update_display(self):
        ''' Update the display.
        '''
        # Plot the data using the view tools.
        view_plugins = [x for x in self.plugins if x.mode == 'view' and x.active]
        for cur_plugin in view_plugins:
            cur_plugin.plot()




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





