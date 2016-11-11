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
The view framework to visualize data.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

'''


import logging

import wx
import wx.lib.scrolledpanel

import matplotlib as mpl
try:
    from matplotlib.backends.backend_wxagg import FigureCanvas
except:
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

import psysmon.core.util


class Viewport(wx.lib.scrolledpanel.ScrolledPanel):
    '''
    The generic viewport.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.SetBackgroundColour('white')

        # The list of view container controlled by the viewport.
        self.node_list = []

        self.SetupScrolling()

        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)



    def on_left_down(self, event):
        self.logger.debug("##### LEFT DOWN IN GENERIC VIEWPORT #######")


    def add_node(self, node, position=None):
        '''
        Add a Container instance to the viewport.

        Parameters
        ----------
        node

        position

        '''
        node.Reparent(self)
        self.node_list.append(node)
        self.sizer.Add(node, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)
        self.SetupScrolling()


    def get_node(self, name = None, group = None, **kwargs):
        ''' Get a node instance.

        Parameters
        ----------
        '''
        ret_nodes = [x for x in self.node_list]

        if name:
            ret_nodes = [x for x in ret_nodes if x.name == name]

        if group:
            ret_nodes = [x for x in ret_nodes if x.group == group]

        for cur_key, cur_value in kwargs.iteritems():
            ret_nodes = [x for x in ret_nodes if x.props.has_key(cur_key) and getattr(x.props, cur_key) == cur_value]

        # Add all child nodes.
        for cur_node in self.node_list:
            ret_nodes.extend(cur_node.get_node(name = name, group = group, **kwargs))

        return ret_nodes


    def register_mpl_event_callbacks(self, hooks):
        ''' Set the event callback of the matplotlib canvas.
        '''
        for cur_node in self.node_list:
            cur_node.set_mpl_event_callbacks(hooks, self)


    def clear_mpl_event_callbacks(self):
        ''' Clear the event callbacks of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.clear_mpl_event_callbacks()


    def register_view_plugin(self, plugin):
        ''' Create the views needed by the plugin.
        '''
        for cur_node in self.node_list:
            if isinstance(cur_node, ContainerNode):
                cur_node.register_view_plugin(plugin)
            elif isinstance(cur_node, ViewContainerNode):
                cur_node.create_plugin_view(plugin)



class ContainerNode(wx.Panel):
    ''' A container holding another container.

    '''
    def __init__(self, name, group = None, parent=None, id=wx.ID_ANY, parent_viewport=None, props = None, annotation_area = None, color = 'red'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The name of the container.
        self.name = name

        # The group of the container.
        if group:
            self.group = group
        else:
            self.group = ''

        # The viewPort containing the channel.
        self.parent_viewport = parent_viewport

        # The properties of the container.
        if props:
            self.props = props
        else:
            self.props = psysmon.core.util.AttribDict()

        # A list containing child container nodes.
        self.node_list = []

        self.SetBackgroundColour(color)

        self.annotation_area = annotation_area

        # TODO: Enable the selection of vertical or horizontal stacking of the
        # other containers.
        self.sizer = wx.GridBagSizer(0,0)
        self.container_sizer = wx.BoxSizer(wx.VERTICAL)

        if annotation_area:
            annotation_area.Reparent(self)
            self.sizer.Add(self.annotation_area, pos=(0,0), span=(2,1), flag=wx.ALL|wx.EXPAND, border=0)
            self.sizer.Add(self.container_sizer, pos = (0,1), flag=wx.ALL|wx.EXPAND, border = 0)
            self.sizer.AddGrowableCol(1)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)
        else:
            self.sizer.Add(self.container_sizer, pos = (0,0), flag=wx.ALL|wx.EXPAND, border = 0)
            self.sizer.AddGrowableCol(0)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)


    def add_node(self, node):
        ''' Add a container node.

        Parameters
        ----------
        node : class `~psysmon.core.gui_view.Container`
            The container node to be added.
        '''
        if not isinstance(node, ContainerNode) and not isinstance(node, ViewContainerNode):
            raise TypeError("The node needs to be a ContainerNode or ViewContainerNode instance.")

        node.Reparent(self)
        if node not in self.node_list:
            self.node_list.append(node)

        if self.node_list:
            self.container_sizer.Add(node, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)

        self.sizer.Layout()

        cur_size = self.GetSize()
        child_size = self.container_sizer.GetSize()
        if child_size[1] > cur_size[1]:
            self.SetMinSize(child_size)
            self.container_sizer.Layout()


    def remove_node(self, name):
        ''' Remove a container.

        Parameters
        ----------
        name : String
            The name of the container to remove.
        '''
        for cur_node in [x for x in self.node_list if x.name == name]:
            self.node_list.remove(cur_node)
            self.container_sizer.Remove(cur_node)
            cur_node.Destroy()

        self.rearrange_container()
        self.container_sizer.Layout()


    def get_node(self, name = None, group = None, **kwargs):
        ''' Get a node instance.

        Parameters
        ----------
        '''
        ret_nodes = [x for x in self.node_list]

        if name:
            ret_nodes = [x for x in ret_nodes if x.name == name]

        if group:
            ret_nodes = [x for x in ret_nodes if x.group == group]

        for cur_key, cur_value in kwargs.iteritems():
            ret_nodes = [x for x in ret_nodes if x.props.has_key(cur_key) and getattr(x.props, cur_key) == cur_value]

        # Add all child nodes.
        for cur_node in self.node_list:
            ret_nodes.extend(cur_node.get_node(name = name, group = group, **kwargs))

        return ret_nodes


    def rearrange_container(self):
        pass


    def register_mpl_event_callbacks(self, hooks, parent):
        ''' Set the event callback of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.set_mpl_event_callbacks(hooks, parent)


    def clear_mpl_event_callbacks(self):
        ''' Clear the event callbacks of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.clear_mpl_event_callbacks()


    def register_view_plugin(self, plugin):
        ''' Create the views needed by the plugin.
        '''
        for cur_node in self.node_list:
            cur_node.create_plugin_view(plugin)



class ViewContainerNode(wx.Panel):
    ''' A container holding a ViewNode class.

    '''
    def __init__(self, name, group = None, parent=None, id=wx.ID_ANY, parent_viewport=None, props = None, annotation_area = None, color = 'red'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The name of the container.
        self.name = name

        # The group of the container.
        if group:
            self.group = group
        else:
            self.group = ''

        # The viewPort containing the channel.
        self.parent_viewport = parent_viewport

        # The properties of the container.
        if props:
            self.props = props
        else:
            self.props = psysmon.core.util.AttribDict()

        # A list containing child container nodes.
        self.node_list = []

        self.SetBackgroundColour(color)

        self.annotation_area = annotation_area

        # TODO: Enable the selection of vertical or horizontal stacking of the
        # other containers.
        self.sizer = wx.GridBagSizer(0,0)
        self.container_sizer = wx.BoxSizer(wx.VERTICAL)

        if annotation_area:
            annotation_area.Reparent(self)
            self.sizer.Add(self.annotation_area, pos=(0,0), span=(2,1), flag=wx.ALL|wx.EXPAND, border=0)
            self.sizer.Add(self.container_sizer, pos = (0,1), flag=wx.ALL|wx.EXPAND, border = 0)
            self.sizer.AddGrowableCol(1)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)
        else:
            self.sizer.Add(self.container_sizer, pos = (0,0), flag=wx.ALL|wx.EXPAND, border = 0)
            self.sizer.AddGrowableCol(0)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)


    def add_node(self, node):
        ''' Add a view node.

        Parameters
        ----------
        node : class `~psysmon.core.gui_view.ViewNode`
            The container node to be added.
        '''
        if not isinstance(node, ViewNode):
            raise TypeError("The node needs to be a ViewNode instance.")

        node.Reparent(self)
        if node not in self.node_list:
            self.node_list.append(node)

        if self.node_list:
            self.container_sizer.Add(node, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)

        self.sizer.Layout()

        cur_size = self.GetSize()
        child_size = self.container_sizer.GetSize()
        if child_size[1] > cur_size[1]:
            self.SetMinSize(child_size)
            self.container_sizer.Layout()


    def remove_node(self, name):
        ''' Remove a view node.

        Parameters
        ----------
        name : String
            The name of the container to remove.
        '''
        for cur_node in [x for x in self.node_list if x.name == name]:
            self.node_list.remove(cur_node)
            self.container_sizer.Remove(cur_node)
            cur_node.Destroy()

        self.rearrange_nodes()
        self.container_sizer.Layout()


    def get_node(self, name = None, group = None, **kwargs):
        ''' Get a node instance.

        Parameters
        ----------
        '''
        ret_nodes = [x for x in self.node_list]

        if name:
            ret_nodes = [x for x in ret_nodes if x.name == name]

        if group:
            ret_nodes = [x for x in ret_nodes if x.group == group]

        for cur_key, cur_value in kwargs.iteritems():
            ret_nodes = [x for x in ret_nodes if x.props.has_key(cur_key) and getattr(x.props, cur_key) == cur_value]

        return ret_nodes


    def rearrange_nodes(self):
        pass


    def register_mpl_event_callbacks(self, hooks, parent):
        ''' Set the event callback of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.set_mpl_event_callbacks(hooks, parent)


    def clear_mpl_event_callbacks(self):
        ''' Clear the event callbacks of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.clear_mpl_event_callbacks()


    def create_plugin_view(self, plugin):
        ''' Create the views needed by the plugin.
        '''
        # Check if the view already exists.
        cur_view_node = self.get_node(name = plugin.rid)

        if not cur_view_node:
            view_class = plugin.getViewClass()
            if view_class is not None:
                cur_view_node = view_class(parent = self,
                                           name = plugin.rid,
                                           props = self.props,
                                           color = 'white')
                self.add_node(cur_view_node)



class ViewNode(wx.Panel):
    ''' A view.

    '''
    def __init__(self, name, parent=None, id=wx.ID_ANY, parent_viewport=None, props = None, annotation_area = None, color = 'green'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The name of the container.
        self.name = name

        # The viewPort containing the channel.
        self.parent_viewport = parent_viewport

        # The properties of the container.
        if props:
            self.props = props
        else:
            self.props = psysmon.core.util.AttribDict()

        self.color = color
        self.SetBackgroundColour(self.color)

        self.plot_panel = PlotPanel(self, color='violet')
        self.annotation_area = annotation_area

        self.SetMinSize(self.plot_panel.GetMinSize())

        # A list of matplotlib event connection ids.
        self.mpl_cids = []

        # TODO: Enable the selection of vertical or horizontal stacking of the
        # plot_panel and annotation_area.
        self.sizer = wx.GridBagSizer(0,0)

        if annotation_area:
            annotation_area.Reparent(self)
            self.sizer.Add(self.plot_panel, pos = (0,0), flag=wx.ALL|wx.EXPAND, border = 0)
            self.sizer.Add(self.annotation_area, pos=(0,1), flag=wx.ALL|wx.EXPAND, border=1)
            self.sizer.AddGrowableCol(0)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)
        else:
            self.sizer.Add(self.plot_panel, pos = (0,0), flag=wx.ALL|wx.EXPAND, border = 1)
            self.sizer.AddGrowableCol(0)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)

        # Bind the events.
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

    @property
    def axes(self):
        ''' The axes of the matplotlib canvas.
        '''
        return self.plot_panel.axes


    def draw(self):
        ''' Draw the plot panel to make the changes visible.
        '''
        self.plot_panel.draw()


    def on_enter_window(self, event):
        self.logger.debug("on_enter_window in view %s. event: %s", self.name, event)
        #self.SetBackgroundColour('blue')
        self.SetFocus()
        self.Refresh()

    def on_leave_window(self, event):
        self.logger.debug("on_leave_window in view %s. event: %s", self.name, event)
        self.SetBackgroundColour(self.color)
        self.Refresh()

    def on_set_focus(self, event):
        self.logger.debug("on_set_focus in view %s. event: %s", self.name, event)

    def on_key_down(self, event):
        self.logger.debug("on_key_down in view %s. event: %s", self.name, event)
        event.ResumePropagation(1)
        event.Skip()

    def on_key_up(self, event):
        self.logger.debug("on_key_up in view %s. event: %s", self.name, event)
        event.ResumePropagation(1)
        event.Skip()

    def on_left_down(self, event):
        self.logger.debug("on_left_down in view %s. event: %s", self.name, event)
        event.Skip()


    def set_mpl_event_callbacks(self, hooks, parent):

        for cur_key, cur_callback in hooks.iteritems():
            cur_cid = self.plot_panel.canvas.mpl_connect(cur_key, lambda evt, parent = parent, callback = cur_callback: callback(evt, parent))
            self.mpl_cids.append(cur_cid)


    def clear_mpl_event_callbacks(self, cid_list = None):
        if cid_list is None:
            cid_list = self.cids

        for cur_cid in cid_list:
            self.plot_panel.canvas.mpl_disconnect(cur_cid)



class PlotPanel(wx.Panel):
    """
    The PlotPanel
    """
    def __init__( self, parent, name = None, color=None, dpi=None, **kwargs ):
        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__( self, parent, **kwargs )
        self.SetMinSize((100, 40))

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The name of the plot panel.
        self.name = name

        # initialize matplotlib stuff
        self.figure = mpl.figure.Figure(None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.axes = self.figure.add_axes([0,0,1,1])
        self.canvas.SetMinSize((30, 10))
        self.SetBackgroundColour('white')

	# Add the canvas to the sizer.
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.canvas.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus2)
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.canvas.Bind(wx.EVT_KEY_UP, self.on_key_up)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)


    def on_wx_xlick(self, event):
        self.logger.debug("on_wx_xlick in plot_panel %s. event: %s", self.name, event)


    def on_set_focus(self, event):
        self.logger.debug("on_set_focus in plot_panel %s. event: %s", self.name, event)
        self.logger.debug("Event should propagate: %s", event.ShouldPropagate())
        #event.ResumePropagation(1)
        event.Skip()

    def on_set_focus2(self, event):
        self.logger.debug("on_set_focus2 in plot_panel %s. event: %s", self.name, event)

    def on_key_down(self, event):
        self.logger.debug("on_key_down in plot_panel %s. event: %s", self.name, event)
        event.ResumePropagation(1)
        event.Skip()

    def on_key_up(self, event):
        self.logger.debug("on_key_up in plot_panel %s. event: %s", self.name, event)
        event.ResumePropagation(1)
        event.Skip()

    def on_left_down(self, event):
        self.logger.debug("on_left_down in plot_panel %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()


    def set_color( self, rgbtuple=None ):
        ''' Set figure and canvas colours to be the same.
        '''
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        self.canvas.SetBackgroundColour( wx.Colour( *rgbtuple ) )
        self.canvas.Refresh()


    def draw(self):
        ''' Draw the canvas to make the changes visible.
        '''
        self.canvas.draw()


    def update_display(self):
        ''' Update the display of the docking frame.

        '''
        assert False, 'The update_display method must be defined!'
