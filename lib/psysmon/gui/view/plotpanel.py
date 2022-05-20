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

import matplotlib as mpl
try:
    from matplotlib.backends.backend_wxagg import FigureCanvas
except Exception:
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import wx


class PlotPanel(wx.Panel):
    """
    The PlotPanel
    """
    def __init__(self, parent, name = None, color=None,
                 dpi=None, n_axes = 1, **kwargs):
        # initialize Panel
        if 'id' not in iter(kwargs.keys()):
            kwargs['id'] = wx.ID_ANY
        if 'style' not in iter(kwargs.keys()):
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__(self, parent, **kwargs)
        self.SetMinSize((100, 40))

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The name of the plot panel.
        self.name = name

        # initialize matplotlib stuff
        self.figure = mpl.figure.Figure(None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)

        # The axes.
        self._axes = []
        axes_height = 1 / n_axes
        for k in range(n_axes):
            self._axes.append(self.figure.add_axes([0, k * axes_height,
                                                    1, axes_height]))
        self.canvas.SetMinSize((30, 10))
        self.SetBackgroundColour('white')

        # The axes backgrounds for blit animation.
        self.blit_backgrounds = []

        # Add the canvas to the sizer.
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.canvas.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus2)
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        #self.canvas.Bind(wx.EVT_KEY_UP, self.on_key_up)
        #self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        #self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        #self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)


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
        self.logger.debug("on_set_focus in plot_panel canvas %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()

    def on_set_focus2(self, event):
        self.logger.debug("on_set_focus2 in plot_panel %s. event: %s", self.name, event)
        event.ResumePropagation(30)
        event.Skip()
        
    def on_key_down(self, event):
        self.logger.debug("on_key_down in plot_panel %s. id: %s; event: %s", self.name, self.GetId(), event)
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


    def set_color(self, rgbtuple=None):
        ''' Set figure and canvas colours to be the same.
        '''
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get()
        clr = [c / 255. for c in rgbtuple]
        self.figure.set_facecolor(clr)
        self.figure.set_edgecolor(clr)
        self.canvas.SetBackgroundColour(wx.Colour(*rgbtuple))
        self.canvas.Refresh()


    def set_n_axes(self, n_axes):
        ''' Set the number of axes provided by the plot panel.
        '''
        # Delete the existing axes.
        for cur_ax in self._axes:
            self.figure.delaxes(cur_ax)
        self._axes = []

        # Create the new number of axes.
        axes_height = 1 / n_axes
        for k in range(n_axes):
            self._axes.append(self.figure.add_axes([0, k * axes_height,
                                                    1, axes_height]))



    def draw(self):
        ''' Draw the canvas to make the changes visible.
        '''
        self.canvas.draw()


    def save_blit_background(self):
        ''' Save the axes background for animation.
        '''
        self.blit_backgrounds = []
        for cur_axes in self._axes:
            self.blit_backgrounds.append(self.canvas.copy_from_bbox(cur_axes.bbox))


    def restore_blit_background(self):
        ''' Restore the axes background for animation.
        '''
        for k, cur_bg in enumerate(self.blit_backgrounds):
            self.canvas.restore_region(cur_bg, bbox = self._axes[k].bbox)


    def draw_blit_artists(self, artists):
        ''' Draw the artist for animation.
        '''
        for cur_artist in artists:
            for cur_line_artist in cur_artist.line_artist:
                cur_line_artist.axes.draw_artist(cur_line_artist)

            for cur_text_artist in cur_artist.text_artist:
                cur_text_artist.axes.draw_artist(cur_text_artist)


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
    def __init__(self, parent, size=(200, -1), color=None):
        wx.Panel.__init__(self, parent, size=size)
        self.SetBackgroundColour(color)
        self.SetMinSize((200, -1))


        # Create a test label.
        self.label = wx.lib.stattext.GenStaticText(self, wx.ID_ANY,
                                                   "view annotation area",
                                                   (20, 10))
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)

        # Add the label to the sizer.
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label, 1, wx.EXPAND | wx.ALL, border=0)
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
