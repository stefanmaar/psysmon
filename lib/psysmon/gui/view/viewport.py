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

import numpy as np
import wx
import wx.lib.scrolledpanel

import psysmon
from psysmon.gui.view.viewnode import ViewNode
from psysmon.gui.view.containernode import ContainerNode
from psysmon.gui.view.view_containernode import ViewContainerNode



class Viewport(wx.lib.scrolledpanel.ScrolledPanel):
    '''
    The generic viewport.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent=parent, id=id,
                                                    style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.SetBackgroundColour('white')

        # The list of view container controlled by the viewport.
        self.node_list = []

        self.SetupScrolling()

        #self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)


    def on_left_down(self, event):
        self.logger.debug("on_left_down in viewport. event: %s", event)
        event.ResumePropagation(30)
        event.Skip()


    def on_set_focus(self, event):
        self.logger.debug("on_set_focus in viewport. event: %s", event)
        event.ResumePropagation(30)
        event.Skip()


    def on_key_down(self, event):
        self.logger.debug("on_key_down in viewport. event: %s", event)
        event.ResumePropagation(30)
        event.Skip()


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
        if position is not None:
            self.sizer.Insert(index = position,
                              window = node,
                              proportion = 1,
                              flag = wx.EXPAND | wx.TOP | wx.BOTTOM,
                              border = 1)
        else:
            self.sizer.Add(node, 1,
                           flag = wx.EXPAND | wx.TOP | wx.BOTTOM,
                           border = 1)
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

        for cur_key, cur_value in kwargs.items():
            ret_nodes = [x for x in ret_nodes if cur_key in x.props and getattr(x.props, cur_key) == cur_value]

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
            self.sizer.Detach(cur_node)
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
                cur_node.register_view_plugin(plugin,
                                              limit_group = limit_group)
            elif isinstance(cur_node, ViewContainerNode):
                cur_node.create_plugin_view(plugin,
                                            limit_group = limit_group)


    def sort_nodes(self, keys, order):
        ''' Sort the containers nodes.
        '''
        sorted_nodes = []
        order = np.array(order)
        for k in np.arange(order.shape[1]):
            cur_values = order[:, k]
            request = dict(zip(keys, cur_values))
            cur_node = self.get_node(recursive = False,
                                     **request)
            sorted_nodes.extend(cur_node)

        if sorted_nodes:
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
            self.sizer.Add(cur_node, 1, flag = wx.EXPAND | wx.TOP | wx.BOTTOM,
                           border = 1)
            cur_node.Show()

        self.SetupScrolling()
