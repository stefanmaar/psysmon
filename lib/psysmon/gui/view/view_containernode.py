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

import wx

import psysmon
import psysmon.core.util
from psysmon.gui.view.viewnode import ViewNode


class ViewContainerNode(wx.Panel):
    ''' A container holding a ViewNode class.

    '''
    def __init__(self, name, group = None, parent=None, id=wx.ID_ANY,
                 parent_viewport=None, props = None,
                 annotation_area = None, color = 'red'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)
        
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
        self.sizer = wx.GridBagSizer(0, 0)
        self.container_sizer = wx.BoxSizer(wx.VERTICAL)

        if annotation_area:
            annotation_area.Reparent(self)
            self.sizer.Add(self.annotation_area,
                           pos = (0, 0),
                           # span = (2, 1),
                           flag = wx.ALL | wx.EXPAND,
                           border = 0)
            self.sizer.Add(self.container_sizer,
                           pos = (0, 1),
                           flag = wx.ALL | wx.EXPAND,
                           border = 0)
            self.sizer.AddGrowableCol(1)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)
        else:
            self.sizer.Add(self.container_sizer,
                           pos = (0, 0),
                           flag = wx.ALL | wx.EXPAND,
                           border = 0)
            self.sizer.AddGrowableCol(0)
            self.sizer.AddGrowableRow(0)
            self.SetSizer(self.sizer)

        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        #self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        #self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)

                  
    def on_key_down(self, event):
        self.logger.debug("on_key_down in view container %s. id: %s; event: %s", self.name, self.GetId(), event)
        event.ResumePropagation(30)
        event.Skip()

    def on_set_focus(self, event):
        self.logger.debug("on_set_focus in view container node %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()


    def on_enter_window(self, event):
        self.logger.debug("on_enter_window in view container node %s. event: %s", self.name, event)


    def on_left_down(self, event):
        self.logger.debug("on_left_down in view containter node %s. event: %s", self.name, event)
   

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
            self.container_sizer.Add(node, 1,
                                     flag = wx.EXPAND | wx.TOP | wx.BOTTOM,
                                     border = 1)

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
            self.container_sizer.Detach(cur_node)
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

        for cur_key, cur_value in kwargs.items():
            ret_nodes = [x for x in ret_nodes if cur_key in x.props and getattr(x.props, cur_key) == cur_value]

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
        artists = []
        for cur_node in self.node_list:
            cur_artist = cur_node.plot_annotation_vline(x = x,
                                                        parent_rid = parent_rid,
                                                        key = key,
                                                        **kwargs)
            artists.append(cur_artist)
        return artists


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


    def save_blit_background(self):
        ''' Get the background of the axes.
        '''
        for cur_node in self.node_list:
            cur_node.save_blit_background()


    def restore_blit_background(self):
        ''' Restore the axes background for blit animation.
        '''
        for cur_node in self.node_list:
            cur_node.restore_blit_background()


    def draw_blit_artists(self, **kwargs):
        ''' Draw the specified artist.
        '''
        for cur_node in self.node_list:
            cur_node.draw_blit_artists(**kwargs)


    def blit(self):
        ''' Draw blit animation.
        '''
        for cur_node in self.node_list:
            cur_node.blit()
