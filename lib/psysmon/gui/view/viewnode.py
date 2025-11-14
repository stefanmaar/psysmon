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
import warnings

import wx

import psysmon
import psysmon.core.util
from psysmon.gui.view.plotpanel import PlotPanel
from psysmon.gui.view.plotpanel import ViewAnnotationPanel


class ViewNode(wx.Panel):
    ''' A view.

    '''
    def __init__(self, name, group = None, parent=None, id=wx.ID_ANY,
                 parent_viewport=None, props = None, color = 'green',
                 n_axes = 1):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

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

        self.plot_panel = PlotPanel(self, color='violet', n_axes = n_axes,
                                    name = name)
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
        #self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        #self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        #self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

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
        #self.SetFocus()
        #self.Refresh()

    def on_leave_window(self, event):
        self.logger.debug("on_leave_window in view %s. event: %s", self.name, event)
        self.SetBackgroundColour(self.color)
        self.Refresh()

    def on_set_focus(self, event):
        self.logger.debug("on_set_focus in view %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()

    def on_key_down(self, event):
        self.logger.debug("on_key_down in view %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()

    def on_key_up(self, event):
        self.logger.debug("on_key_up in view %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()

    def on_left_down(self, event):
        self.logger.debug("on_left_down in view %s. event: %s", self.name, event)
        event.Skip()


    def set_mpl_event_callbacks(self, hooks, parent):

        added_cids = []
        for cur_key, cur_callback in hooks.items():
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
            if event_name in iter(self.mpl_cids.keys()):
                cid_list = self.mpl_cids[event_name]
        else:
            for cur_key, cur_cid_list in self.mpl_cids.items():
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
                cur_line_artist.remove()

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

        for cur_key, cur_value in kwargs.items():
            if cur_key in valid_keys:
                ret_artist = [x for x in ret_artist if getattr(x, cur_key) == cur_value or cur_value is None]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_artist



    def set_n_axes(self, n_axes):
        ''' Set the number of axes created in the view.
        '''
        self.plot_panel.set_n_axes(n_axes)


    def save_blit_background(self):
        ''' Get the background of the axes.
        '''
        self.plot_panel.save_blit_background()


    def restore_blit_background(self):
        ''' Restore the axes background for blit animation.
        '''
        self.plot_panel.restore_blit_background()


    def draw_blit_artists(self, **kwargs):
        ''' Draw the specified artist.
        '''
        artists = self.get_annotation_artist(**kwargs)
        for cur_artis in artists:
            self.plot_panel.draw_blit_artists(artists)


    def blit(self):
        ''' Draw blit animation.
        '''
        self.plot_panel.canvas.blit()
        self.plot_panel.canvas.Update()


    def measure(self, event):
        ''' Create a measurement of the data plotted in the view.
        '''
        return None
