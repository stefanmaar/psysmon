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

import numpy as np
import obspy.core.utcdatetime
import matplotlib as mpl
try:
    from matplotlib.backends.backend_wxagg import FigureCanvas
except:
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas



import psysmon.core.plugins
import psysmon.artwork.icons as icons

class ParticleMotion(psysmon.core.plugins.InteractivePlugin):
    '''
    '''

    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.InteractivePlugin.__init__(self,
                                                        name = 'particle motion',
                                                        category = 'analyze',
                                                        tags = None)

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.emotion_smile_icon_16
        self.cursor = wx.CURSOR_CROSS

        self.frame = None
        self.start_time = None
        self.end_time = None

        # TODO: Make this a preference.
        self.channel_map = {'z': 'HHZ', 'y':'HHN', 'x':'HHE'}


    def activate(self):
        ''' Activate the plugin.
        '''
        psysmon.core.plugins.InteractivePlugin.activate(self)
        # Create a frame holding the plot panel. A simple figure is not
        # working.
        self.frame = ParticleMotionFrame()
        self.frame.Show()

    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        psysmon.core.plugins.InteractivePlugin.deactivate(self)
        self.cleanup()


    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        self.frame.Destroy()


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.on_button_press
        hooks['button_release_event'] = self.on_button_release

        return hooks


    def on_button_press(self, event, parent = None):
        ''' Handle the button press events.
        '''
        if event.inaxes is None:
            return

        viewport = parent

        cur_view = event.canvas.GetGrandParent()
        self.view = cur_view

        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # Skipt the right mouse button.
            return
        else:
            # Check for the required 3-component traces.

            # Initialize the time window.
            self.start_time = obspy.core.utcdatetime.UTCDateTime(event.xdata)
            self.end_time = obspy.core.utcdatetime.UTCDateTime(event.xdata)

            # Clear the particle motion plot.
            self.frame.clear_axes()

            # Call the plot_particle_motion method.
            self.plot_start_points(event, parent)

            # Register the motion_notify_event.
            hook = {}
            hook['motion_notify_event'] = self.plot_particle_motion
            cur_view.set_mpl_event_callbacks(hook, parent = parent)


    def on_button_release(self, event, parent):
        ''' Handle the mouse button release event.
        '''
        # Clear the motion notify callbacks.
        self.view.clear_mpl_event_callbacks('motion_notify_event')


    def plot_start_points(self, event, parent = None):
        ''' Plot the start point markers.
        '''
        pass


    def plot_particle_motion(self, event, parent = None):
        ''' Update the particle motion plot.
        '''
        self.end_time = obspy.core.utcdatetime.UTCDateTime(event.xdata)
        props = self.view.props
        proc_stream = self.parent.visible_data
        x_stream = proc_stream.select(station = props.station,
                                      channel = self.channel_map['x'],
                                      network = props.network,
                                      location = props.location)
        y_stream = proc_stream.select(station = props.station,
                                      channel = self.channel_map['y'],
                                      network = props.network,
                                      location = props.location)
        z_stream = proc_stream.select(station = props.station,
                                      channel = self.channel_map['z'],
                                      network = props.network,
                                      location = props.location)

        x_stream = x_stream.slice(starttime = self.start_time, endtime = self.end_time)
        y_stream = y_stream.slice(starttime = self.start_time, endtime = self.end_time)
        z_stream = z_stream.slice(starttime = self.start_time, endtime = self.end_time)

        self.frame.plot_xy(x_stream.traces[0].data, y_stream.traces[0].data)
        self.frame.plot_xz(x_stream.traces[0].data, z_stream.traces[0].data)
        self.frame.plot_yz(y_stream.traces[0].data, z_stream.traces[0].data)

        self.frame.set_axes_limits()

        self.frame.canvas.draw()
        self.frame.Refresh()
        self.frame.Update()


class ParticleMotionFrame(wx.Frame):
    '''
    '''

    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = 'particle motion', size = (600, 600), dpi = 90):
        ''' Initialize the instance.
        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # initialize matplotlib stuff
        self.figure = mpl.figure.Figure(None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.axes = {}
        self.axes['xy'] = self.figure.add_subplot(2, 2, 1)
        self.axes['xz'] = self.figure.add_subplot(2, 2, 3)
        self.axes['yz'] = self.figure.add_subplot(2, 2, 4)
        self.annotate_axes()

        self.canvas.SetMinSize((30, 10))
        self.SetBackgroundColour('white')

	# Add the canvas to the sizer.
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        # The particle motion lines.
        self.lines = {}
        self.lines['xy'] = None
        self.lines['xz'] = None
        self.lines['yz'] = None


    def annotate_axes(self):
        ''' Annotate the axes.
        '''
        self.axes['xy'].set_xlabel('x')
        self.axes['xy'].set_ylabel('y')

        self.axes['xz'].set_xlabel('x')
        self.axes['xz'].set_ylabel('z')

        self.axes['yz'].set_xlabel('y')
        self.axes['yz'].set_ylabel('z')

        for cur_axes in self.axes.itervalues():
            cur_axes.set_aspect('equal', adjustable = 'box')


    def clear_axes(self):
        ''' Clear all plots in the axes.
        '''
        for cur_key, cur_axes in self.axes.iteritems():
            if self.lines[cur_key] is not None:
                cur_axes.lines.remove(self.lines[cur_key])
                del self.lines[cur_key]
                self.lines[cur_key] = None


    def plot_xy(self, x_data, y_data):
        ''' Plot the xy particle motion.
        '''
        self.plot(x = x_data, y = y_data, mode = 'xy')


    def plot_xz(self, x_data, z_data):
        ''' Plot the xy particle motion.
        '''
        self.plot(x = x_data, y = z_data, mode = 'xz')


    def plot_yz(self, y_data, z_data):
        ''' Plot the xy particle motion.
        '''
        self.plot(x = y_data, y = z_data, mode = 'yz')


    def plot(self, x, y, mode):
        ''' Plot data in the corresponding axes.

        '''
        cur_axes = self.axes[mode]
        cur_line = self.lines[mode]
        if cur_line is None:
            cur_lines = cur_axes.plot(x, y, 'k')
            self.lines[mode] = cur_lines[0]
        else:
            cur_line.set_xdata(x)
            cur_line.set_ydata(y)


    def set_axes_limits(self):
        ''' Adjust the axes limits.
        '''
        max_amp = []
        for cur_line in self.lines.itervalues():
            cur_x_max = np.max(np.abs(cur_line.get_xdata()))
            cur_y_max = np.max(np.abs(cur_line.get_ydata()))
            max_amp.append(np.max([cur_x_max, cur_y_max]))
        max_amp = np.max(max_amp)

        for cur_axes in self.axes.itervalues():
            cur_axes.set_xlim((-max_amp, max_amp))
            cur_axes.set_ylim((-max_amp, max_amp))



