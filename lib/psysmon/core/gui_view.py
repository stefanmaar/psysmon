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
import operator
import warnings

import wx
import wx.lib.scrolledpanel
import wx.lib.stattext

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


    def get_node(self, name = None, group = None, node_type = None, recursive = True, **kwargs):
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
        if recursive:
            for cur_node in self.node_list:
                ret_nodes.extend(cur_node.get_node(name = name, group = group, node_type = node_type, **kwargs))

        if node_type is not None:
            if node_type == 'view':
                ret_nodes = [x for x in ret_nodes if isinstance(x, ViewNode)]
            elif node_type == 'container':
                ret_nodes = [x for x in ret_nodes if not isinstance(x, ViewNode)]

        return ret_nodes


    def remove_node(self, name = None, group = None, recursive = False, **kwargs):
        ''' Remove a container node.
        '''
        nodes_to_remove = self.get_node(recursive = False, name = name, group = group, **kwargs)
        for cur_node in nodes_to_remove:
            self.node_list.remove(cur_node)
            self.sizer.Remove(cur_node)
            cur_node.Destroy()

        if recursive:
            for cur_node in self.node_list:
                cur_node.remove_node(recursive = recursive,
                                     name = name,
                                     group = group,
                                     **kwargs)

        self.rearrange_nodes()
        self.sizer.Layout()


    def register_mpl_event_callbacks(self, hooks):
        ''' Set the event callback of the matplotlib canvas.
        '''
        cid_list = []
        for cur_node in self.node_list:
            cur_cid = cur_node.register_mpl_event_callbacks(hooks, self)
            cid_list.extend(cur_cid)
        return cid_list


    def clear_mpl_event_callbacks(self, event_name = None):
        ''' Clear the event callbacks of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.clear_mpl_event_callbacks(event_name = event_name)


    def register_view_plugin(self, plugin, limit_group = None):
        ''' Create the views needed by the plugin.
        '''

        for cur_node in self.node_list:
            if isinstance(cur_node, ContainerNode):
                cur_node.register_view_plugin(plugin, limit_group = limit_group)
            elif isinstance(cur_node, ViewContainerNode):
                cur_node.create_plugin_view(plugin, limit_group = limit_group)


    def sort_nodes(self, keys = None, order = None):
        ''' Sort the containers nodes.
        '''
        if order:
            sorted_nodes = []
            for cur_order in order:
                cur_node = self.get_node(recursive = False, **cur_order)
                sorted_nodes.extend(cur_node)

            self.node_list = sorted_nodes
            self.rearrange_nodes()



    def rearrange_nodes(self):
        ''' Rearrange the container nodes in the sizer.

        Detach and reattach the container nodes to the sizer
        according to the order in the node_list.
        '''
        for cur_node in self.node_list:
            self.sizer.Hide(cur_node)
            self.sizer.Detach(cur_node)

        for cur_node in self.node_list:
            self.sizer.Add(cur_node, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)
            cur_node.Show()

        self.SetupScrolling()





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


    def remove_node(self, name = None, group = None, recursive = False, **kwargs):
        ''' Remove a container node.
        '''
        nodes_to_remove = self.get_node(recursive = False, name = name, group = group, **kwargs)
        for cur_node in nodes_to_remove:
            self.node_list.remove(cur_node)
            self.container_sizer.Remove(cur_node)
            cur_node.Destroy()

        if recursive:
            for cur_node in self.node_list:
                cur_node.remove_node(name = name)

        self.rearrange_nodes()
        self.container_sizer.Layout()


    def get_node(self, name = None, group = None, node_type = None, recursive = True, **kwargs):
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
        if recursive:
            for cur_node in self.node_list:
                ret_nodes.extend(cur_node.get_node(name = name, group = group, node_type = node_type, **kwargs))

        if node_type is not None:
            if node_type == 'view':
                ret_nodes = [x for x in ret_nodes if isinstance(x, ViewNode)]
            elif node_type == 'container':
                ret_nodes = [x for x in ret_nodes if not isinstance(x, ViewNode)]

        return ret_nodes


    def rearrange_nodes(self):
        ''' Rearrange the container nodes in the sizer.

        Detach and reattach the container nodes to the sizer
        according to the order in the node_list.
        '''
        for cur_node in self.node_list:
            self.container_sizer.Hide(cur_node)
            self.container_sizer.Detach(cur_node)

        for cur_node in self.node_list:
            self.container_sizer.Add(cur_node, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)
            cur_node.Show()

        cur_size = self.GetSize()
        child_size = self.container_sizer.GetSize()
        if child_size[1] > cur_size[1]:
            self.SetMinSize(child_size)
            self.container_sizer.Layout()


    def register_mpl_event_callbacks(self, hooks, parent):
        ''' Set the event callback of the matplotlib canvas in the views.
        '''
        cid_list = []
        for cur_node in self.node_list:
            cur_cid = cur_node.register_mpl_event_callbacks(hooks, parent)
            cid_list.extend(cur_cid)
        return cid_list


    def clear_mpl_event_callbacks(self, event_name = None):
        ''' Clear the event callbacks of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.clear_mpl_event_callbacks(event_name = event_name)


    def register_view_plugin(self, plugin, limit_group = None):
        ''' Create the views needed by the plugin.
        '''
        for cur_node in self.node_list:
            if isinstance(cur_node, ContainerNode):
                cur_node.register_view_plugin(plugin, limit_group = limit_group)
            elif isinstance(cur_node, ViewContainerNode):
                cur_node.create_plugin_view(plugin, limit_group = limit_group)


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in all children of this node.
        '''
        for cur_node in self.node_list:
            cur_node.plot_annotation_vline(x = x, parent_rid = parent_rid,
                                           key = key, **kwargs)


    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical line in all children of this node.
        '''
        for cur_node in self.node_list:
            cur_node.plot_annotation_vspan(x_start = x_start,
                                           x_end = x_end,
                                           parent_rid = parent_rid,
                                           key = key,
                                           **kwargs)

    def draw(self):
        ''' Draw all child nodes.
        '''
        for cur_node in self.node_list:
            cur_node.draw()


    def clear_annotation_artist(self, **kwargs):
        ''' Delete annotation artits all views of the channel.
        '''
        for cur_node in self.node_list:
            cur_node.clear_annotation_artist(**kwargs)



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


    def get_node(self, name = None, group = None, node_type = None, **kwargs):
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

        if node_type is not None:
            if node_type == 'view':
                ret_nodes = [x for x in ret_nodes if isinstance(x, ViewNode)]
            elif node_type == 'container':
                ret_nodes = [x for x in ret_nodes if not isinstance(x, ViewNode)]

        return ret_nodes


    def rearrange_nodes(self):
        pass


    def register_mpl_event_callbacks(self, hooks, parent):
        ''' Set the event callback of the matplotlib canvas in the views.
        '''
        cid_list = []
        for cur_node in self.node_list:
            cur_cid = cur_node.set_mpl_event_callbacks(hooks, parent)
            cid_list.extend(cur_cid)
        return cid_list


    def clear_mpl_event_callbacks(self, event_name = None):
        ''' Clear the event callbacks of the matplotlib canvas in the views.
        '''
        for cur_node in self.node_list:
            cur_node.clear_mpl_event_callbacks(event_name = event_name)


    def create_plugin_view(self, plugin, limit_group = None):
        ''' Create the views needed by the plugin.
        '''
        if limit_group is None:
            limit_group = []

        # Check if the view already exists.
        cur_view_node = self.get_node(name = plugin.rid)

        if not cur_view_node:
            view_class = plugin.getViewClass()
            if len(limit_group) == 0 or self.group in limit_group:
                if view_class is not None:
                    cur_view_node = view_class(parent = self,
                                               name = plugin.rid,
                                               props = self.props,
                                               color = 'white')
                    self.add_node(cur_view_node)


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in all children of this node.
        '''
        for cur_node in self.node_list:
            cur_node.plot_annotation_vline(x = x, parent_rid = parent_rid,
                                           key = key, **kwargs)


    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical line in all children of this node.
        '''
        for cur_node in self.node_list:
            cur_node.plot_annotation_vspan(x_start = x_start,
                                           x_end = x_end,
                                           parent_rid = parent_rid,
                                           key = key,
                                           **kwargs)

    def draw(self):
        ''' Draw all child nodes.
        '''
        for cur_node in self.node_list:
            cur_node.draw()


    def clear_annotation_artist(self, **kwargs):
        ''' Delete annotation artits all views of the channel.
        '''
        for cur_node in self.node_list:
            cur_node.clear_annotation_artist(**kwargs)




class ViewNode(wx.Panel):
    ''' A view.

    '''
    def __init__(self, name, group = None, parent=None, id=wx.ID_ANY, parent_viewport=None, props = None, color = 'green', n_axes = 1):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The name of the container.
        self.name = name

        # The group of the container.
        self.group = group

        # The viewPort containing the channel.
        self.parent_viewport = parent_viewport

        # The properties of the container.
        if props:
            self.props = props
        else:
            self.props = psysmon.core.util.AttribDict()

        # The annotation artists of the view.
        self.annotation_artists = []

        self.color = color
        self.SetBackgroundColour(self.color)

        self.plot_panel = PlotPanel(self, color='violet', n_axes = n_axes)
        self.annotation_area = ViewAnnotationPanel(parent = self,
                                                   color = 'grey80')

        self.SetMinSize(self.plot_panel.GetMinSize())

        # A list of matplotlib event connection ids. The key is the name of the
        # event.
        self.mpl_cids = {}

        # TODO: Enable the selection of vertical or horizontal stacking of the
        # plot_panel and annotation_area.
        self.sizer = wx.GridBagSizer(0,0)

        # TODO: Add an attribute to show or hide the annotation area.
        if self.annotation_area:
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
        event.ResumePropagation(2)
        event.Skip()

    def on_key_up(self, event):
        self.logger.debug("on_key_up in view %s. event: %s", self.name, event)
        event.ResumePropagation(2)
        event.Skip()

    def on_left_down(self, event):
        self.logger.debug("on_left_down in view %s. event: %s", self.name, event)
        event.Skip()


    def set_mpl_event_callbacks(self, hooks, parent):

        added_cids = []
        for cur_key, cur_callback in hooks.iteritems():
            cur_cid = self.plot_panel.canvas.mpl_connect(cur_key, lambda evt, parent = parent, callback = cur_callback: callback(evt, parent))
            if cur_key in self.mpl_cids:
                self.mpl_cids[cur_key].append(cur_cid)
            else:
                self.mpl_cids[cur_key] = [cur_cid,]
            added_cids.append(cur_cid)

        return added_cids


    def clear_mpl_event_callbacks(self, event_name = None):

        cid_list = []
        if event_name is not None:
            if event_name in self.mpl_cids.keys():
                cid_list = self.mpl_cids[event_name]
        else:
            for cur_key, cur_cid_list in self.mpl_cids.iteritems():
                cid_list.extend(cur_cid_list)

        for cur_cid in cid_list:
            self.plot_panel.canvas.mpl_disconnect(cur_cid)


    def set_annotation(self, text):
        ''' Set the text in the annotation area of the view.
        '''
        if self.annotation_area:
            self.annotation_area.setLabel(text)



    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in the data axes.
        '''
        pass


    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        pass



    def clear_annotation_artist(self, mode = None, parent_rid = None, key = None):
        ''' Delete annotation artits from the view.
        '''
        artists_to_remove = self.get_annotation_artist(mode = mode,
                                                       parent_rid = parent_rid,
                                                       key = key)
        for cur_artist in artists_to_remove:
            for cur_line_artist in cur_artist.line_artist:
                self.axes.lines.remove(cur_line_artist)

            for cur_patch_artist in cur_artist.patch_artist:
                self.axes.patches.remove(cur_patch_artist)

            for cur_text_artist in cur_artist.text_artist:
                self.axes.texts.remove(cur_text_artist)

            self.annotation_artists.remove(cur_artist)




    def get_annotation_artist(self, **kwargs):
        ''' Get the annotation artist.
        '''
        ret_artist = self.annotation_artists

        valid_keys = ['mode', 'parent_rid', 'key']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_artist = [x for x in ret_artist if getattr(x, cur_key) == cur_value or cur_value is None]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_artist



    def set_n_axes(self, n_axes):
        ''' Set the number of axes created in the view.
        '''
        self.plot_panel.set_n_axes(n_axes)


class PlotPanel(wx.Panel):
    """
    The PlotPanel
    """
    def __init__( self, parent, name = None, color=None, dpi=None, n_axes = 1, **kwargs ):
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

        # TODO: Create multiple axes on request.
        self._axes = []
        axes_height = 1 / float(n_axes)
        for k in range(n_axes):
            self._axes.append(self.figure.add_axes([0, k * axes_height, 1, axes_height]))
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


    @property
    def axes(self):
        ''' The axes of the panel.

        If only one axis is present, return the axes, otherwise return a list of axes.
        '''
        if len(self._axes) == 1:
            return self._axes[0]
        else:
            return self._axes


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


    def set_n_axes(self, n_axes):
        ''' Set the number of axes provided by the plot panel.
        '''
        # Delete the existing axes.
        for cur_ax in self._axes:
            self.figure.delaxes(cur_ax)
        self._axes = []

        # Create the new number of axes.
        axes_height = 1 / float(n_axes)
        for k in range(n_axes):
            self._axes.append(self.figure.add_axes([0, k * axes_height, 1, axes_height]))



    def draw(self):
        ''' Draw the canvas to make the changes visible.
        '''
        self.canvas.draw()


    def update_display(self):
        ''' Update the display of the docking frame.

        '''
        assert False, 'The update_display method must be defined!'



class ViewAnnotationPanel(wx.Panel):
    '''
    The view annotation area.

    This area can be used to plot anotations for the view. This might be 
    some statistic values (e.g. min, max), the axes limits or some 
    other custom info.
    '''
    def __init__(self, parent, size=(200,-1), color=None):
        wx.Panel.__init__(self, parent, size=size)
        self.SetBackgroundColour(color)
        self.SetMinSize((200, -1))


	# Create a test label.
        self.label = wx.lib.stattext.GenStaticText(self, wx.ID_ANY, "view annotation area", (20, 10))
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)

	# Add the label to the sizer.
	sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label, 1, wx.EXPAND|wx.ALL, border=0)
	self.SetSizer(sizer)


    def setLabel(self, text):
        ''' Set the text of the annotation label.
        '''
        self.label.SetLabelText(text)
        self.label.Refresh()


class AnnotationArtist(object):
    ''' Matplotlib instances used to annotate the data in the view axes.
    '''

    def __init__(self, mode, parent_rid, key):
        self.mode = mode

        self.parent_rid = parent_rid

        self.key = key

        self.line_artist = []

        self.text_artist = []

        self.patch_artist = []

        self.image_artist = []


    def add_artist(self, artist_list):
        ''' Add an artist.
        '''
        for cur_artist in artist_list:
            if isinstance(cur_artist, mpl.lines.Line2D):
                self.line_artist.append(cur_artist)
            elif isinstance(cur_artist, mpl.patches.Patch):
                self.patch_artist.append(cur_artist)
            elif isinstance(cur_artist, mpl.text.Text):
                self.text_artist.append(cur_artist)
            else:
                raise RuntimeError('Unknown artist type.')
