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
import mpl_toolkits.axes_grid1 as axesgrid



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
        self.start_new_measurement = True

        # Create the preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        cm_group = pref_page.add_group('channel map')

        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'channel_map_x',
                                          label = 'x',
                                          value = '',
                                          limit = ['HHE', 'HHN', 'HHZ'],
                                          tool_tip = 'Select the x component channel.')
        cm_group.add_item(item)

        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'channel_map_y',
                                          label = 'y',
                                          value = '',
                                          limit = ['HHE', 'HHN', 'HHZ'],
                                          tool_tip = 'Select the y component channel.')
        cm_group.add_item(item)

        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'channel_map_z',
                                          label = 'z',
                                          value = '',
                                          limit = ['HHE', 'HHN', 'HHZ'],
                                          tool_tip = 'Select the z component channel.')
        cm_group.add_item(item)



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
        self.cleanup()
        psysmon.core.plugins.InteractivePlugin.deactivate(self)


    def initialize_preferences(self):
        ''' Intitialize the preferences depending on runtime variables.
        '''
        # Set the limits of the event_catalog field.
        channels = sorted(self.parent.displayManager.availableChannels)
        self.pref_manager.set_limit('channel_map_x', channels)
        self.pref_manager.set_limit('channel_map_y', channels)
        self.pref_manager.set_limit('channel_map_z', channels)

        east_channels = [x for x in channels if x.lower().endswith('e')]
        north_channels = [x for x in channels if x.lower().endswith('n')]
        vertical_channels = [x for x in channels if x.lower().endswith('z')]
        if 'HHE' in channels:
            self.pref_manager.set_value('channel_map_x', 'HHE')
        elif len(east_channels) > 0:
            self.pref_manager.set_value('channel_map_x', east_channels[0])
        elif len(channels) > 1:
            self.pref_manager.set_value('channel_map_x', channels[0])

        if 'HHN' in channels:
            self.pref_manager.set_value('channel_map_y', 'HHN')
        elif len(north_channels) > 0:
            self.pref_manager.set_value('channel_map_y', north_channels[0])
        elif len(channels) > 1:
            self.pref_manager.set_value('channel_map_y', channels[0])

        if 'HHZ' in channels:
            self.pref_manager.set_value('channel_map_z', 'HHZ')
        elif len(vertical_channels) > 0:
            self.pref_manager.set_value('channel_map_z', vertical_channels[0])
        elif len(channels) > 1:
            self.pref_manager.set_value('channel_map_z', channels[0])


    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        self.frame.Destroy()
        self.station_container.clear_annotation_artist(parent_rid = self.rid)
        self.station_container.draw()


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
            # TODO: Check for the required 3-component traces.


            # Initialize the time window.
            self.start_time = obspy.core.utcdatetime.UTCDateTime(event.xdata)
            self.end_time = obspy.core.utcdatetime.UTCDateTime(event.xdata)

            # Clear the particle motion plot.
            self.frame.clear_axes()

            # Plot the time window start line in all channel views of the
            # station.
            self.station_container = self.parent.viewport.get_node(station = cur_view.props.station,
                                                                   network = cur_view.props.network,
                                                                   location = cur_view.props.location,
                                                                   recursive = False)
            if len(self.station_container) > 0:
                self.station_container = self.station_container[0]

            # Clear all annotation lines.
            self.station_container.clear_annotation_artist(parent_rid = self.rid)

            # Plot the time window start lines.
            self.station_container.plot_annotation_vline(x = event.xdata, parent_rid = self.rid, key = 'begin_line')
            self.station_container.draw()

            # Save the axes backgrounds for blit animation.
            self.station_container.save_blit_background()

            # Register the motion_notify_event.
            hook = {}
            hook['motion_notify_event'] = self.plot_particle_motion
            cur_view.set_mpl_event_callbacks(hook, parent = parent)



    def on_button_release(self, event, parent):
        ''' Handle the mouse button release event.
        '''
        # Clear the motion notify callbacks.
        self.view.clear_mpl_event_callbacks('motion_notify_event')
        self.start_new_measurement = True


    def plot_particle_motion(self, event, parent = None):
        ''' Update the particle motion plot.
        '''
        # Draw the time window endline first for smooth animation.
        self.station_container.restore_blit_background()
        self.station_container.plot_annotation_vline(x = event.xdata, parent_rid = self.rid, key = 'end_line')
        self.station_container.draw_blit_artists(parent_rid = self.rid, key = 'end_line')
        self.station_container.blit()


        # Now compute draw the particle motion.
        self.end_time = obspy.core.utcdatetime.UTCDateTime(event.xdata)
        props = self.view.props
        proc_stream = self.parent.visible_data
        x_stream = proc_stream.select(station = props.station,
                                      channel = self.pref_manager.get_value('channel_map_x'),
                                      network = props.network,
                                      location = props.location)
        y_stream = proc_stream.select(station = props.station,
                                      channel = self.pref_manager.get_value('channel_map_y'),
                                      network = props.network,
                                      location = props.location)
        z_stream = proc_stream.select(station = props.station,
                                      channel = self.pref_manager.get_value('channel_map_z'),
                                      network = props.network,
                                      location = props.location)

        x_stream = x_stream.slice(starttime = self.start_time, endtime = self.end_time)
        y_stream = y_stream.slice(starttime = self.start_time, endtime = self.end_time)
        z_stream = z_stream.slice(starttime = self.start_time, endtime = self.end_time)


        self.frame.plot_xy(x_stream.traces[0].data, y_stream.traces[0].data, self.start_new_measurement)
        self.frame.plot_xz(x_stream.traces[0].data, z_stream.traces[0].data, self.start_new_measurement)
        self.frame.plot_yz(y_stream.traces[0].data, z_stream.traces[0].data, self.start_new_measurement)
        self.start_new_measurement = False

        self.frame.set_axes_limits()

        # Compute the polarization features.
        component_data = {}
        time_array = np.arange(0, x_stream.traces[0].stats.npts)
        time_array = time_array * 1/x_stream.traces[0].stats.sampling_rate
        time_array = time_array + x_stream.traces[0].stats.starttime.timestamp
        component_data['time'] = time_array
        component_data['x'] = x_stream.traces[0].data
        component_data['y'] = y_stream.traces[0].data
        component_data['z'] = z_stream.traces[0].data
        features = psysmon.packages.polarization_analysis.core.compute_complex_covariance_matrix_windowed(component_data)
        self.frame.set_feature_annotation(features)

        # Update the frame display.
        # TODO: Make it a blit animation.
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

        #self.grid = axesgrid.AxesGrid(self.figure, 111,
        #                              nrows_ncols = (2, 2),
        #                              axes_pad = 0,
        #                              label_mode = "1")

        self.axes = {}
        self.axes['xy'] = self.figure.add_subplot(111)
        self.axes['xy'].set_aspect('equal')
        self.divider = axesgrid.make_axes_locatable(self.axes['xy'])
        self.axes['yz'] = self.divider.append_axes("right", size = "100%", pad = 0, sharey = self.axes['xy'])
        self.axes['xz'] = self.divider.append_axes("bottom", size = "100%", pad = 0, sharex = self.axes['xy'])
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

        # The particle motion start markers.
        self.start_markers = {}
        self.start_markers['xy'] = None
        self.start_markers['xz'] = None
        self.start_markers['yz'] = None

        # The feature annotation.
        self.feature_text = None


    def annotate_axes(self):
        ''' Annotate the axes.
        '''
        self.axes['xy'].set_xlabel('x')
        self.axes['xy'].set_ylabel('y')
        self.axes['xy'].xaxis.set_label_position('top')
        self.axes['xy'].xaxis.set_tick_params(labeltop = False, labelbottom = False)

        self.axes['xz'].set_xlabel('x')
        self.axes['xz'].set_ylabel('z')

        self.axes['yz'].set_xlabel('z')
        self.axes['yz'].set_ylabel('y')
        self.axes['yz'].get_xaxis().set_label_position('top')
        self.axes['yz'].get_yaxis().set_label_position('right')
        self.axes['yz'].xaxis.set_tick_params(labeltop = False, labelbottom = False)
        self.axes['yz'].yaxis.set_tick_params(labelleft = False, labelright = True)


    def clear_axes(self):
        ''' Clear all plots in the axes.
        '''
        for cur_key, cur_axes in self.axes.iteritems():
            if self.lines[cur_key] is not None:
                cur_axes.lines.remove(self.lines[cur_key])
                del self.lines[cur_key]
                self.lines[cur_key] = None

            if self.start_markers[cur_key] is not None:
                cur_axes.lines.remove(self.start_markers[cur_key])
                del self.start_markers[cur_key]
                self.start_markers[cur_key] = None




    def plot_xy(self, x_data, y_data, start_marker = False):
        ''' Plot the xy particle motion.
        '''
        self.plot(x = x_data, y = y_data, mode = 'xy', start_marker = start_marker)


    def plot_xz(self, x_data, z_data, start_marker = False):
        ''' Plot the xy particle motion.
        '''
        self.plot(x = x_data, y = z_data, mode = 'xz', start_marker = start_marker)


    def plot_yz(self, y_data, z_data, start_marker = False):
        ''' Plot the xy particle motion.
        '''
        self.plot(x = z_data, y = y_data, mode = 'yz', start_marker = start_marker)


    def plot(self, x, y, mode, start_marker = False):
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

        if start_marker:
            cur_lines = cur_axes.plot(x[0], y[0], 'ro')
            self.start_markers[mode] = cur_lines[0]





    def set_feature_annotation(self, features):
        '''
        '''
        if self.feature_text is not None:
            self.axes['xz'].texts.remove(self.feature_text)


        azimuth = np.rad2deg(features['azimuth'])
        if azimuth < 0:
            azimuth = azimuth + 180

        msg = "Polarization features:\n\n"
        msg += "polarization strength: %f" % features['pol_strength'] + '\n'
        msg += "ellipticity: %f" % features['ellipticity'] + '\n'
        msg += "apparent azimuth: %f / %f" % (azimuth, azimuth + 180) + "\n"
        msg += "apparent incidence: %f" % np.rad2deg(features['incidence']) + "\n"
        self.feature_text = self.axes['xz'].text(1.1, 0.95, msg,
                                                 verticalalignment = 'top',
                                                 horizontalalignment = 'left',
                                                 transform = self.axes['xz'].transAxes,
                                                 size = 10)

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



