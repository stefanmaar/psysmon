from __future__ import division
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

from builtins import str
from builtins import range
from past.utils import old_div
import logging
import wx
import numpy as np
import scipy
import scipy.signal
import matplotlib as mpl
from matplotlib.patches import Rectangle
import psysmon
from psysmon.core.plugins import ViewPlugin
from psysmon.core.plugins import CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.gui.view as psy_view
import psysmon.core.preferences_manager as preferences_manager
import psysmon.core.signal
import obspy.signal
from obspy.imaging.spectrogram import spectrogram
import obspy.imaging


class SeismogramPlotter(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                            name = 'seismogram',
                            category = 'view',
                            tags = None)

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons.waveform_icon_16

        # Set the shortcut string.
        self.accelerator_string = 'CTRL+S'
        self.pref_accelerator_string = 'ALT+S'

        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        style_group = pref_page.add_group('style')
        scale_group = pref_page.add_group('scaling')
        disp_group = pref_page.add_group('display')

        # Show or hide the seismogram envelope.
        item = preferences_manager.CheckBoxPrefItem(name = 'show_wiggle_trace',
                                                    label = 'show wiggle trace',
                                                    value = True,
                                                    tool_tip = 'Show the seismogram wiggle trace.')
        style_group.add_item(item)

        # Show or hide the seismogram envelope.
        item = preferences_manager.CheckBoxPrefItem(name = 'show_envelope',
                                                    label = 'show envelope',
                                                    value = False,
                                                    tool_tip = 'Show the seismogram envelope.')
        style_group.add_item(item)

        # The envelope style.
        item = preferences_manager.SingleChoicePrefItem(name = 'envelope_style',
                                                        label = 'envelope style',
                                                        limit = ('top', 'bottom', 'top-bottom', 'filled'),
                                                        value = 'top',
                                                        tool_tip = 'The style of the envelope.')
        style_group.add_item(item)

        # Set the scaling mode.
        item = preferences_manager.SingleChoicePrefItem(name = 'scaling_mode',
                                                        label = 'scaling',
                                                        limit = ('channel', 'station', 'window', 'manual'),
                                                        value = 'channel',
                                                        tool_tip = 'Set the scaling mode.')
        scale_group.add_item(item)

        # Set the manual scaling value.
        item = preferences_manager.FloatSpinPrefItem(name = 'manual_y_lim',
                                                     label = 'manual y limit',
                                                     value = 10,
                                                     limit = (0, None),
                                                     spin_format = '%e')
        scale_group.add_item(item)

        # Set the limit when the display changes to the min-max method.
        item = preferences_manager.FloatSpinPrefItem(name = 'minmax_limit',
                                                     label = 'min-max limit [s]',
                                                     value = 20.,
                                                     limit = (0, None),
                                                     digits = 1,
                                                     increment = 1,
                                                     tool_tip = 'For windows larger than the min-max limit, not all samples are shown. The plotted samples are reduced using a min-max algorithm.')
        disp_group.add_item(item)



    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream
        scaling_mode = self.pref_manager.get_value('scaling_mode')
        y_lim = None

        # TODO: Do the scaling of the axes limits after the data was plotted.
        # The plot method has to return the max data value which is used to
        # compute the axes limits. At the end, the y-limits of the axes ar set.
        if scaling_mode == 'window':
            abs_values = [np.max(np.abs(x)) for x in stream.traces]
            y_lim = np.max(abs_values)
        elif scaling_mode == 'manual':
            y_lim = self.pref_manager.get_value('manual_y_lim')

        for curChannel in channels:
            if scaling_mode == 'station':
                stat_stream = stream.select(station = curChannel.parent.name,
                                            network = curChannel.parent.network)
                abs_values = [np.max(np.abs(x)) for x in stat_stream.traces]
                y_lim = np.max(abs_values)

            views = displayManager.getViewContainer(station = curChannel.parent.name,
                                                    channel = curChannel.name,
                                                    network = curChannel.parent.network,
                                                    location = curChannel.parent.location,
                                                    name = self.rid)
            for curView in views:
                if stream:
                    if curChannel.parent.location == '--':
                        cur_location = None
                    else:
                        cur_location = curChannel.parent.location

                    curStream = stream.select(station = curChannel.parent.name,
                                              channel = curChannel.name,
                                              network = curChannel.parent.network,
                                              location = cur_location)
                else:
                    curStream = None

                if curStream:
                    lineColor = [x/255.0 for x in curView.props.channel_color]
                    curView.plot(curStream, lineColor,
                                 end_time = displayManager.endTime,
                                 duration = displayManager.endTime - displayManager.startTime,
                                 show_wiggle_trace = self.pref_manager.get_value('show_wiggle_trace'),
                                 show_envelope = self.pref_manager.get_value('show_envelope'),
                                 envelope_style = self.pref_manager.get_value('envelope_style'),
                                 minmax_limit = self.pref_manager.get_value('minmax_limit'),
                                 y_lim = y_lim
                                 )

                curView.setXLimits(left = displayManager.startTime.timestamp,
                                   right = displayManager.endTime.timestamp)
                curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return SeismogramView








class SeismogramView(psy_view.viewnode.ViewNode):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None, lineColor=(1,0,0), **kwargs):
        ''' Initialize the instance.
        '''
        psy_view.viewnode.ViewNode.__init__(self,
                                            parent=parent,
                                            id=id,
                                            parent_viewport = parent_viewport,
                                            name=name,
                                            **kwargs)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.t0 = None
        self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None
        self.scale_bar_text = None
        self.scale_bar_amp = None
        self.scale_bar_amp_text = []

        self.line = None

        self.envelope_line_top = None
        self.envelope_line_bottom = None
        self.envelope_collection_filled = None

        self.axes.set_frame_on(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)



    def plot(self, stream, color, duration, end_time, show_wiggle_trace = True, show_envelope = False,
             envelope_style = 'top', minmax_limit = 20, limit_scale = 1, y_lim = None):
        ''' Plot the seismogram.
        '''
        #display_size = wx.GetDisplaySize()
        axes_width = self.axes.get_window_extent().width
        data_plot_limit = axes_width * limit_scale
        self.logger.debug('data_plot_limit: %f', data_plot_limit)
        #data_plot_limit = 1e20
        for trace in stream:
            if trace.stats.npts > data_plot_limit and (old_div(len(trace), trace.stats.sampling_rate)) > minmax_limit:
                # Plot minmax values
                self.logger.info('Plotting in minmax mode.')
                sample_step = 2 * np.ceil(old_div(len(trace.data), data_plot_limit))
                self.logger.debug("len(trace.data): %f", len(trace.data))
                self.logger.debug('sample_step: %f', sample_step)
                trace_data = self.compute_minmax_data(trace.data, sample_step)
                time_step = old_div(sample_step, trace.stats.sampling_rate)
                minmax_time = np.array([trace.stats.starttime.timestamp + x * time_step for x in range(int(np.floor(old_div(len(trace.data), sample_step))))])
                minmax_time = minmax_time.repeat(2)
                timeArray = minmax_time

                if show_envelope is True:
                    comp_trace = scipy.signal.hilbert(trace_data)
                    trace_envelope = np.sqrt(np.real(comp_trace)**2 + np.imag(comp_trace)**2)

            else:
                self.logger.info('Plotting in FULL mode.')
                timeArray = np.arange(0, trace.stats.npts)
                timeArray = old_div(timeArray, trace.stats.sampling_rate)
                timeArray = timeArray + trace.stats.starttime.timestamp

                # Check if the data is a ma.maskedarray
                if np.ma.count_masked(trace.data):
                    timeArray = np.ma.array(timeArray, mask=trace.data.mask)

                trace_data = trace.data

                if show_envelope is True:
                    comp_trace = scipy.signal.hilbert(trace_data)
                    trace_envelope = np.sqrt(np.real(comp_trace)**2 + np.imag(comp_trace)**2)


            self.t0 = trace.stats.starttime

            self.logger.debug('len(trace_data): %d', len(trace_data))

            if show_wiggle_trace:
                if self.line is None:
                    self.line, = self.axes.plot(timeArray, trace_data, color = color, label = 'seismogram')
                else:
                    self.line.set_xdata(timeArray)
                    self.line.set_ydata(trace_data)
            else:
                if self.line is not None:
                    self.axes.lines.remove(self.line)
                    self.line = None

            if show_envelope is True:
                if envelope_style == 'top' or envelope_style == 'top-bottom':
                    if self.envelope_line_top is None:
                        self.envelope_line_top, = self.axes.plot(timeArray, trace_envelope, color = 'saddlebrown', label = 'seismogram_envelope')
                    else:
                        self.envelope_line_top.set_xdata(timeArray)
                        self.envelope_line_top.set_ydata(trace_envelope)

                if envelope_style == 'bottom' or envelope_style == 'top-bottom':
                    if self.envelope_line_bottom is None:
                        self.envelope_line_bottom, = self.axes.plot(timeArray, -trace_envelope, color = 'saddlebrown', label = 'seismogram_envelope')
                    else:
                        self.envelope_line_bottom.set_xdata(timeArray)
                        self.envelope_line_bottom.set_ydata(-trace_envelope)

                if envelope_style == 'filled':
                    if self.envelope_collection_filled is not None:
                        self.axes.collections.remove(self.envelope_collection_filled)

                    self.envelope_collection_filled = self.axes.fill_between(x = timeArray,
                                                                         y1 = trace_envelope.flatten(),
                                                                         y2 = -trace_envelope.flatten(),
                                                                         color = 'lightgrey', edgecolor = 'lightgrey',
                                                                         label = 'seismogram_envelope')

                if envelope_style == 'top':
                    if self.envelope_line_bottom:
                        self.axes.lines.remove(self.envelope_line_bottom)
                        self.envelope_line_bottom = None
                    if self.envelope_collection_filled:
                        self.axes.collections.remove(self.envelope_collection_filled)
                        self.envelope_collection_filled = None
                elif envelope_style == 'bottom':
                    if self.envelope_line_top:
                        self.axes.lines.remove(self.envelope_line_top)
                        self.envelope_line_top = None
                    if self.envelope_collection_filled:
                        self.axes.collections.remove(self.envelope_collection_filled)
                        self.envelope_collection_filled = None
                elif envelope_style == 'top-bottom':
                    if self.envelope_collection_filled:
                        self.axes.collections.remove(self.envelope_collection_filled)
                        self.envelope_collection_filled = None
                elif envelope_style == 'filled':
                    if self.envelope_line_top:
                        self.axes.lines.remove(self.envelope_line_top)
                        self.envelope_line_top = None
                    if self.envelope_line_bottom:
                        self.axes.lines.remove(self.envelope_line_bottom)
                        self.envelope_line_bottom = None

            else:
                if self.envelope_line_top:
                    self.axes.lines.remove(self.envelope_line_top)
                    self.envelope_line_top = None
                if self.envelope_line_bottom:
                    self.axes.lines.remove(self.envelope_line_bottom)
                    self.envelope_line_bottom = None
                if self.envelope_collection_filled:
                    self.axes.collections.remove(self.envelope_collection_filled)
                    self.envelope_collection_filled = None


            if y_lim is None:
                y_lim = np.max(np.abs(trace.data))
            if show_envelope is True:
                env_max = np.max(trace_envelope)
                y_lim = np.max([y_lim, env_max])
            self.axes.set_ylim(bottom = -y_lim, top = y_lim)
            self.logger.debug('y_lim: %s', y_lim)

        self.axes.set_frame_on(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        scale_length = self.add_time_scalebar(duration = duration)
        self.add_amplitude_scalebar(scale_length = scale_length, unit = trace.stats.unit)


    def add_time_scalebar(self, duration):
        ''' Add a time scalebar to the axes.
        '''
        if duration > 1:
            order = len(str(int(np.floor(duration)))) - 1
            scale_length = 1 * 10**(order-1)
        elif duration == 1:
            scale_length = 0.1
        else:
            order = len(str(int(np.floor(old_div(1,duration))))) - 1
            scale_length = 1 * (10.** ((order+1) * -1))

        if self.scaleBar:
            self.scaleBar.remove()

        if self.scale_bar_text:
            self.scale_bar_text.remove()

        self.scaleBar = self.axes.axvspan(self.t0.timestamp,
                                          self.t0.timestamp + scale_length,
                                          color = '0.75')

        ylim = self.axes.get_ylim()
        self.scale_bar_text = self.axes.text(x = self.t0.timestamp + scale_length,
                                             y = ylim[1],
                                             s = '%g s' % scale_length,
                                             verticalalignment = 'top')

        return scale_length


    def add_amplitude_scalebar(self, scale_length, unit):
        ''' Add an amplitude scalebar to the axes.
        '''
        ylim = self.axes.get_ylim()
        scale_max = np.max(np.abs(ylim))

        scale_max = scale_max / 2.

        if self.scale_bar_amp:
            self.scale_bar_amp.remove()

        for cur_text in self.scale_bar_amp_text:
            cur_text.remove()
        self.scale_bar_amp_text = []

        self.scale_bar_amp = Rectangle((self.t0, -scale_max),
                                  width = scale_length,
                                  height = 2 * scale_max,
                                  edgecolor = 'none',
                                  facecolor = '0.9',
                                  transform = self.axes.transData)
        self.axes.add_patch(self.scale_bar_amp)

        self.scale_bar_amp_text.append(self.axes.text(x = self.t0.timestamp + scale_length,
                                                 y = scale_max,
                                                 s = '%g %s' % (scale_max, unit),
                                                 verticalalignment = 'center',
                                                 horizontalalignment = 'left',
                                                 rotation = 'horizontal',
                                                 #bbox=dict(facecolor = 'white', edgecolor = 'white')
                                                 ))

        self.scale_bar_amp_text.append(self.axes.text(x = self.t0.timestamp + scale_length,
                                                 y = -scale_max,
                                                 s = '%g %s' % (-scale_max, unit),
                                                 verticalalignment = 'center',
                                                 horizontalalignment = 'left',
                                                 rotation = 'horizontal',
                                                 #bbox=dict(facecolor = 'white', edgecolor = 'white')
                                                 ))


    def add_time_scalebar_old(self, duration, end_time):
        ''' Add a time scalebar to the axes.
        '''
        y_lim = self.axes.get_ylim()
        y_lim = np.abs(y_lim[0])

        if duration > 1:
            order = len(str(int(np.floor(duration)))) - 1
            scale_length = 1 * 10**(order-1)
        elif duration == 1:
            scale_length = 0.1
        else:
            order = len(str(int(np.floor(old_div(1,duration))))) - 1
            scale_length = 1 * (10.** ((order+1) * -1))

        units_per_pixel = old_div((2*y_lim), self.axes.get_window_extent().height)
        scale_height = 5 * units_per_pixel
        if self.scaleBar:
            self.scaleBar.remove()
        self.scaleBar = Rectangle((end_time.timestamp - scale_length,
                                  -y_lim+scale_height/2.0),
                                  width=scale_length,
                                  height=scale_height,
                                  edgecolor = 'none',
                                  facecolor = '0.75')
        self.axes.add_patch(self.scaleBar)



    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.axes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        #self.logger.debug('Set limits: %f, %f', left, right)
        self.axes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.axes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.axes.get_window_extent().width
        return  width / float(timeRange)


    def compute_minmax_data(self, data, sample_step):
        '''

        '''
        n_step = np.floor(old_div(len(data), sample_step))
        data = data[:int(n_step * sample_step)]
        data = data.reshape(int(n_step), int(sample_step))

        # Calculate extreme_values and put them into new array.
        min_data = data.min(axis=1)
        max_data = data.max(axis=1)
        min_data = np.ma.resize(min_data, (len(min_data), 1))
        max_data = np.ma.resize(max_data, (len(max_data), 1))
        minmax_data = np.ma.zeros((int(n_step) * 2, 1), dtype=np.float)
        minmax_data[0:len(minmax_data):2] = min_data
        minmax_data[1:len(minmax_data):2] = max_data

        return minmax_data


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in the data axes.
        '''
        annotation_artist = self.get_annotation_artist(mode = 'vline',
                                            parent_rid = parent_rid,
                                            key = key)

        ylim = self.axes.get_ylim()

        if annotation_artist:
            annotation_artist = annotation_artist[0]
            line_artist = annotation_artist.line_artist[0]
            if len(annotation_artist.text_artist) == 1:
                label_artist = annotation_artist.text_artist[0]
            else:
                label_artist = None
            if line_artist:
                line_artist.set_xdata(x)
            if label_artist:
                label_artist.set_position((x, ylim[1]))
        else:
            line_artist = self.axes.axvline(x = x, **kwargs)
            if 'label' in iter(kwargs.keys()):
                props = dict(boxstyle = 'round',
                             facecolor = 'wheat',
                             alpha = 0.8)
                label_artist = self.axes.text(x = x,
                                              y = ylim[1],
                                              s = kwargs['label'],
                                              verticalalignment = 'top',
                                              bbox = props)
            else:
                label_artist = None

            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vline',
                                                                    parent_rid = parent_rid,
                                                                    key = key)
            if label_artist is not None:
                annotation_artist.add_artist([line_artist, label_artist])
            else:
                annotation_artist.add_artist([line_artist, ])
            self.annotation_artists.append(annotation_artist)

        return (line_artist, label_artist)



    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        annotation_artist = self.get_annotation_artist(mode = 'vspan',
                                                       parent_rid = parent_rid,
                                                       key = key)

        if annotation_artist:
            annotation_artist = annotation_artist[0]
            patch_artist = annotation_artist.patch_artist[0]
            label_artist = annotation_artist.text_artist[0]
            if patch_artist:
                polygon = []
                polygon.append([x_start, 0])
                polygon.append([x_start, 1])
                polygon.append([x_end, 1])
                polygon.append([x_end, 0])
                polygon.append([x_start, 0])
                patch_artist.set_xy(polygon)
            if label_artist:
                ylim = self.axes.get_ylim()
                label_artist.set_position((x_start, ylim[1]))
        else:
            vspan_artist = self.axes.axvspan(x_start, x_end, **kwargs)
            if 'label' in iter(kwargs.keys()):
                ylim = self.axes.get_ylim()
                label_artist = self.axes.text(x = x_start,
                                              y = ylim[1],
                                              s = kwargs['label'],
                                              verticalalignment = 'top')
            else:
                label_artist = None
            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vspan',
                                                                    parent_rid = parent_rid,
                                                                    key = key)
            annotation_artist.add_artist([vspan_artist, label_artist])
            self.annotation_artists.append(annotation_artist)



    def measure(self, event):
        ''' Measure the seismogram line.
        '''
        if event.inaxes is None:
            return

        if self.line is None:
            return

        xdata = self.line.get_xdata()
        ydata = self.line.get_ydata()
        ind_x = np.argmin(np.abs(xdata - event.xdata))
        snap_x = xdata[ind_x]
        snap_y = ydata[ind_x]

        if isinstance(snap_y, np.ma.MaskedArray):
            snap_y = snap_y[0]

        measurement = {}
        measurement['label'] = 'seismogram'
        measurement['xy'] = (snap_x, snap_y)
        measurement['units'] = '???'
        measurement['axes'] = self.axes

        return measurement


############## DEMO PLUGIN FOR VIEWS ##########################################

class DemoPlotter(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                             name = 'demo plotter',
                             category = 'view',
                             tags = None
                            )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons.attention_icon_16


    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            views = displayManager.getViewContainer(station = curChannel.parent.name,
                                                      channel = curChannel.name,
                                                      network = curChannel.parent.network,
                                                      location = curChannel.parent.location,
                                                      name = self.rid)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

            for curView in views:
                if curStream:
                    #lineColor = [x/255.0 for x in curChannel.container.color]
                    curView.plot(curStream, [0.3, 0, 0])

                curView.setXLimits(left = displayManager.startTime.timestamp,
                                   right = displayManager.endTime.timestamp)
                curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return DemoView



class DemoView(psy_view.viewnode.ViewNode):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None, lineColor=(1,0,0), **kwargs):
        psy_view.viewnode.ViewNode.__init__(self, parent=parent, id=id, parent_viewport=parent_viewport, name=name, **kwargs)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.t0 = None
        self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None

        self.line = None



    def plot(self, stream, color):


        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = old_div(timeArray * 1,trace.stats.sampling_rate)
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                try:
                    timeArray = np.ma.array(timeArray,
                                            mask = trace.data.mask)
                except Exception:
                    timeArray = np.ma.array(timeArray[:-1],
                                            mask=trace.data.mask)


            if not self.line:
                self.line, = self.axes.plot(timeArray, trace.data * -1, color = color)
            else:
                self.line.set_xdata(timeArray)
                #self.line.set_ydata(trace.data * -1)
                self.line.set_ydata(old_div(trace.data, np.log10(np.abs(trace.data))))

            self.axes.set_frame_on(False)
            self.axes.get_xaxis().set_visible(False)
            self.axes.get_yaxis().set_visible(False)
            yLim = np.max(np.abs(trace.data))
            self.axes.set_ylim(bottom = -yLim, top = yLim)


        # Add the scale bar.
        scaleLength = 10
        unitsPerPixel = old_div((2*yLim), self.axes.get_window_extent().height)
        scaleHeight = 3 * unitsPerPixel
        if self.scaleBar:
            self.scaleBar.remove()
        self.scaleBar = Rectangle((timeArray[-1] - scaleLength,
                                  -yLim+scaleHeight/2.0),
                                  width=scaleLength,
                                  height=scaleHeight,
                                  edgecolor = 'none',
                                  facecolor = '0.75')
        self.axes.add_patch(self.scaleBar)
        #self.axes.axvspan(timeArray[0], timeArray[0] + 10, facecolor='0.5', alpha=0.5)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.axes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.axes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.axes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.axes.get_window_extent().width
        return  width / float(timeRange)


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in the data axes.
        '''
        annotation_artist = self.get_annotation_artist(mode = 'vline',
                                                       parent_rid = parent_rid,
                                                       key = key)

        if annotation_artist:
            annotation_artist = annotation_artist[0]
            line_artist = annotation_artist.line_artist[0]
            label_artist = annotation_artist.text_artist[0]
            if line_artist:
                line_artist.set_xdata(x)
            if label_artist:
                label_artist.set_position((x, 0))
        else:
            line_artist = self.axes.axvline(x = x, **kwargs)
            if 'label' in iter(kwargs.keys()):
                ylim = self.axes.get_ylim()
                label_artist = self.axes.text(x = x, y = 0, s = kwargs['label'])
            else:
                label_artist = None

            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vline',
                                                                       parent_rid = parent_rid,
                                                                       key = key)
            annotation_artist.add_artist([line_artist, label_artist])
            self.annotation_artists.append(annotation_artist)



    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        annotation_artist = self.get_annotation_artist(mode = 'vspan',
                                                       parent_rid = parent_rid,
                                                       key = key)

        if annotation_artist:
            annotation_artist = annotation_artist[0]
            patch_artist = annotation_artist.patch_artist[0]
            label_artist = annotation_artist.text_artist[0]
            if patch_artist:
                polygon = []
                polygon.append([x_start, 0])
                polygon.append([x_start, 1])
                polygon.append([x_end, 1])
                polygon.append([x_end, 0])
                polygon.append([x_start, 0])
                patch_artist.set_xy(polygon)
            if label_artist:
                ylim = self.axes.get_ylim()
                label_artist.set_position((x_start, ylim[1]))
        else:
            vspan_artist = self.axes.axvspan(x_start, x_end, **kwargs)
            if 'label' in iter(kwargs.keys()):
                ylim = self.axes.get_ylim()
                label_artist = self.axes.text(x = x_start, y = ylim[1],
                                                  s = kwargs['label'],
                                                  verticalalignment = 'top')
            else:
                label_artist = None
            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vspan',
                                                                       parent_rid = parent_rid,
                                                                       key = key)
            annotation_artist.add_artist([vspan_artist, label_artist])
            self.annotation_artists.append(annotation_artist)





class SpectrogramPlotter(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                            name = 'spectrogram',
                            category = 'view',
                            tags = None)

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons._3x3_grid_2_icon_16

        # Set the shortcut string.
        self.accelerator_string = 'CTRL+E'
        self.pref_accelerator_string = 'ALT+E'

        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        specgram_group = pref_page.add_group('specgram')
        display_group = pref_page.add_group('display')

        # The specgram window length.
        item = preferences_manager.FloatSpinPrefItem(name = 'win_length',
                                                     label = 'window length [s]',
                                                     value = 1,
                                                     limit = (0, None),
                                                     digits = 1,
                                                     increment = 1,
                                                     tool_tip = 'The window length of the spectrogram in seconds. The window length is extended to the next power of two samples fitting best the specified window length.')
        specgram_group.add_item(item)

        # The window overlap
        item = preferences_manager.FloatSpinPrefItem(name = 'overlap',
                                                     label = 'overlap',
                                                     value = 0.5,
                                                     limit = (0, 0.95),
                                                     digits = 2,
                                                     increment = 0.1,
                                                     tool_tip = 'The overlap of the specgram time windows in a range of 0 (no overlap) to 0.99 (almost full overlap).')
        specgram_group.add_item(item)

        # The amplitude mode.
        item = preferences_manager.SingleChoicePrefItem(name = 'amplitude_mode',
                                                        label = 'amplitude mode',
                                                        limit = ('normal', 'dB', 'square'),
                                                        value = 'dB',
                                                        tool_tip = 'The mode of the amplitude scaling.')
        specgram_group.add_item(item)

        # The colormap.
        item = preferences_manager.SingleChoicePrefItem(name = 'cmap',
                                                        label = 'colormap',
                                                        limit = ('viridis', 'inferno', 'plasma', 'magma', 'gray'),
                                                        value = 'viridis',
                                                        tool_tip = 'The colormap used to color the spectrogram.')
        display_group.add_item(item)

    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            views = displayManager.getViewContainer(station = curChannel.parent.name,
                                                      channel = curChannel.name,
                                                      network = curChannel.parent.network,
                                                      location = curChannel.parent.location,
                                                      name = self.rid)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

            for curView in views:
                if curStream:
                    #lineColor = [x/255.0 for x in curChannel.container.color]
                    curView.plot(curStream,
                                 win_length = self.pref_manager.get_value('win_length'),
                                 overlap = self.pref_manager.get_value('overlap'),
                                 amp_mode = self.pref_manager.get_value('amplitude_mode'),
                                 cmap = self.pref_manager.get_value('cmap'))

                curView.setXLimits(left = displayManager.startTime.timestamp,
                                   right = displayManager.endTime.timestamp)
                curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return SpectrogramView



class SpectrogramView(psy_view.viewnode.ViewNode):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None, lineColor=(1,0,0), **kwargs):
        psy_view.viewnode.ViewNode.__init__(self, parent=parent, id=id, parent_viewport=parent_viewport, name=name, **kwargs)

        # Create the logging logger instance with the correct name.
        self.logger = psysmon.get_logger(self)

        self.axes.set_frame_on(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)


    def plot(self, stream, win_length = 1.0, overlap = 0.5, amp_mode = 'normal', cmap = 'viridis'):
        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray / trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                try:
                    timeArray = np.ma.array(timeArray,
                                            mask = trace.data.mask)
                except Exception:
                    timeArray = np.ma.array(timeArray[:-1],
                                            mask=trace.data.mask)

            if self.axes.images:
                self.axes.images.pop()

            self.spectrogram(data = trace.data,
                             samp_rate = trace.stats.sampling_rate,
                             start_time = trace.stats.starttime.timestamp,
                             wlen = win_length,
                             overlap = overlap,
                             amp_mode = amp_mode,
                             cmap = cmap)

        self.axes.set_frame_on(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)


    def spectrogram(self, data, samp_rate, wlen, overlap = 0.9, amp_mode = 'normal',
                    clip=[0.0, 1.0], start_time = 0, cmap = 'viridis'):
        samp_rate = float(samp_rate)
        wlen = float(wlen)
        overlap = float(overlap)

        nfft = int(psysmon.core.signal.nearest_pow_2(wlen * samp_rate))

        specgram, freq, time = mpl.mlab.specgram(data,
                                                 Fs = samp_rate,
                                                 NFFT = nfft,
                                                 noverlap = int(nfft *  overlap))

        # Save the frequency and time array in the instance.
        self.freq = freq
        self.time = start_time + time

        # calculate half bin width
        halfbin_time = (time[1] - time[0]) / 2.0
        halfbin_freq = (freq[1] - freq[0]) / 2.0

        # Apply the amplitude mode and remove the frequency 0 bin.
        if amp_mode == 'normal':
            specgram = np.sqrt(specgram[1:, :])
        elif amp_mode == 'dB':
            specgram = 10 * np.log10(specgram[1:, :])
        elif amp_mode == 'square':
            specgram = specgram[1:, :]
        else:
            raise ValueError("Value %s for amp_mode not allowed." % amp_mode)
        self.freq = self.freq[1:]

        # Compute the image extent.
        extent = (self.time[0] - halfbin_time, self.time[-1] + halfbin_time,
                  self.freq[0] - halfbin_freq, self.freq[-1] + halfbin_freq)

        # Show the spectrogram as an image.
        #cmap = obspy.imaging.cm.obspy_sequential
        self.axes.imshow(specgram,
                         interpolation = 'nearest',
                         origin = 'lower',
                         extent = extent,
                         aspect = 'auto',
                         cmap = cmap)
        # TODO: Add an option to select logarithmic scaling.
        #self.axes.set_yscale('log')



    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.axes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.axes.set_xlim(left = left, right = right)

        # Adjust the scale bar.


    def measure(self, event):
        ''' Measure the spectrogram line.
        '''
        if event.inaxes is None:
            return

        if len(self.axes.images) == 0:
            return

        ind_x = np.argmin(np.abs(self.time - event.xdata))
        ind_y = np.argmin(np.abs(self.freq - event.ydata))
        snap_x = self.time[ind_x]
        snap_y = self.freq[ind_y]

        #specgram = self.axes.images[0].get_array()

        measurement = {}
        measurement['label'] = 'frequency'
        measurement['xy'] = (snap_x, snap_y)
        #measurement['z'] = specgram[ind_y,ind_x]
        measurement['units'] = 'Hz'
        measurement['axes'] = self.axes

        return measurement



############## FREQUENCY SPECTRUM VIEW ##########################################

class FrequencySpectrumPlotter(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                             name = 'frequency spectrum view',
                             category = 'view',
                             tags = None
                            )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons.chart_bar_icon_16


    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            views = displayManager.getViewContainer(station = curChannel.parent.name,
                                                      channel = curChannel.name,
                                                      network = curChannel.parent.network,
                                                      location = curChannel.parent.location,
                                                      name = self.rid)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

            for curView in views:
                if curStream:
                    #lineColor = [x/255.0 for x in curChannel.container.color]
                    curView.plot(curStream)
                else:
                    curView.clear_lines()

                #curView.setXLimits(left = displayManager.startTime.timestamp,
                #                   right = displayManager.endTime.timestamp)
                curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return FrequencySpectrumView



class FrequencySpectrumView(psy_view.viewnode.ViewNode):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None, psdColor=(0, 0, 0), nhnmColor = (1, 0, 0), nlnmColor = (0, 1, 0), **kwargs):
        psy_view.viewnode.ViewNode.__init__(self, parent=parent, id=id, parent_viewport=parent_viewport, name=name, **kwargs)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.t0 = None
        self.line_colors = {}
        self.line_colors['psd'] = psdColor
        self.line_colors['nhnm'] = nhnmColor
        self.line_colors['nlnm'] = nlnmColor

        self.scaleBar = None

        self.lines = {}
        self.lines['psd'] = None
        self.lines['nhnm'] = None
        self.lines['nlnm'] = None

        self.show_noise_model = False



    def plot(self, stream):

        for trace in stream:
            self.logger.debug('Computing PSD for trace %s.', trace)
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = old_div(timeArray * 1,trace.stats.sampling_rate)
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                try:
                    timeArray = np.ma.array(timeArray,
                                            mask = trace.data.mask)
                except Exception:
                    timeArray = np.ma.array(timeArray[:-1],
                                            mask=trace.data.mask)

            # Compute the power amplitude density spectrum.
            # As defined by Havskov and Alguacil (page 164), the power density spectrum can be
            # written as 
            #   P = 2* 1/T * deltaT^2 * abs(F_dft)^2
            #   
            n_fft = len(trace.data)
            delta_t = 1 / trace.stats.sampling_rate
            T = (len(trace.data) - 1) * delta_t
            Y = scipy.fft.fft(trace.data,
                              n = n_fft)
            psd = (2 * delta_t**2 / T) * np.abs(Y)**2
            psd = 10 * np.log10(psd)
            frequ = trace.stats.sampling_rate * np.arange(0, n_fft) / float(n_fft)

            left_fft = int(np.ceil(n_fft / 2.))


            # Try the matlab psd function.
            import matplotlib.mlab as mlab
            m_n_fft = 8192
            m_pad_to = None
            m_left_fft = int(np.ceil(m_n_fft / 2.))
            if len(trace.data) < m_n_fft:
                m_n_fft = old_div(len(trace.data), 4)
                m_pad_to = 8192
                m_left_fft = int(np.ceil(m_pad_to / 2.))
            m_overlap = m_n_fft * 0.75
            (m_psd, m_frequ) = mlab.psd(trace.data,
                                        Fs = trace.stats.sampling_rate,
                                        NFFT = m_n_fft,
                                        noverlap = m_overlap,
                                        detrend = 'constant',
                                        scale_by_freq = True,
                                        pad_to = m_pad_to)
            m_psd = 10 * np.log10(m_psd)
            self.logger.debug('m_frequ: %s', m_frequ)
            self.logger.debug('m_psd: %s', m_psd)

            min_frequ = 1
            max_frequ = None

            if max_frequ is None:
                max_frequ = trace.stats.sampling_rate / 2

            left_frequ = frequ[1:left_fft]
            left_psd = psd[1:left_fft]
            m_left_frequ = m_frequ[1:m_left_fft]
            m_left_psd = m_psd[1:m_left_fft]
            
            mask = (left_frequ >= min_frequ) & (left_frequ <= max_frequ)
            m_mask = (m_left_frequ >= min_frequ) & (m_left_frequ <= max_frequ)

            # Plot the psd.
            if not self.lines['psd']:
                self.lines['psd'], = self.axes.plot(left_frequ[mask],
                                                    left_psd[mask],
                                                    color = self.line_colors['psd'])
                self.lines['m_psd'], = self.axes.plot(m_left_frequ[m_mask],
                                                      m_left_psd[m_mask],
                                                      color = 'r')
            else:
                self.lines['psd'].set_xdata(left_frequ[mask])
                self.lines['psd'].set_ydata(left_psd[mask])
                self.lines['m_psd'].set_xdata(m_left_frequ[m_mask])
                self.lines['m_psd'].set_ydata(m_left_psd[m_mask])

            cur_unit = trace.stats.unit

            self.logger.info('max: %s', max(left_psd[mask]))
            self.logger.info('min: %s', min(left_psd[mask]))

            # Plot the noise model.
            if self.show_noise_model:
                self.plot_noise_model(cur_unit)

            # Set the axis limits.
            if cur_unit == 'm/s':
                self.axes.set_ylim(bottom = -220, top = -80)
                cur_unit_label = '(m/s)^2/Hz in dB'
            elif cur_unit == 'm/s^2':
                self.axes.set_ylim(bottom = -220, top = -80)
                cur_unit_label = '(m/s^2)^2/Hz in dB'
            elif cur_unit == 'counts':
                self.axes.set_ylim(bottom = min(left_psd[mask]),
                                   top = max(left_psd[mask]))
                cur_unit_label = 'counts^2/Hz in dB'
            else:
                cur_unit_label = '???^2/Hz in dB'

            # Styling of the axis.
            self.axes.set_xscale('log')
            self.axes.set_xlim(left = min_frequ,
                               right = max_frequ)
            self.axes.xaxis.grid(True,
                                 which = 'both')
            #self.axes.set_frame_on(False)
            self.axes.tick_params(axis = 'x', pad = -20)
            self.axes.tick_params(axis = 'y', pad = -40)

            annot_string = 'X-axis: frequency\nX-units: Hz\n\nY-axis: psd\nY-units: %s' % cur_unit_label
            self.set_annotation(annot_string)



    def plot_noise_model(self, unit):
        p_nhnm, nhnm = obspy.signal.spectral_estimation.get_nhnm()
        p_nlnm, nlnm = obspy.signal.spectral_estimation.get_nlnm()

        # obspy returns the NLNM and NHNM values in acceleration.
        # Convert them to the current unit (see Bormann (1998)).
        if unit == 'm':
            nhnm = nhnm + 40 * np.log10(old_div(p_nhnm, (2 * np.pi)))
            nlnm = nlnm + 40 * np.log10(old_div(p_nlnm, (2 * np.pi)))
        elif unit == 'm/s':
            nhnm = nhnm + 20 * np.log10(old_div(p_nhnm, (2 * np.pi)))
            nlnm = nlnm + 20 * np.log10(old_div(p_nlnm, (2 * np.pi)))
        elif unit != 'm/s^2':
            nhnm = None
            nlnm = None
            self.logger.error('The NLNM and NHNM is not available for the unit: %s.', unit)

        if nlnm is not None:
            if not self.lines['nlnm']:
                self.lines['nlnm'], = self.axes.plot(old_div(1,p_nlnm), nlnm, color = self.line_colors['nlnm'])
            else:
                self.lines['nlnm'].set_xdata(old_div(1,p_nlnm))
                self.lines['nlnm'].set_ydata(nlnm)
        if nhnm is not None:
            if not self.lines['nhnm']:
                self.lines['nhnm'], = self.axes.plot(old_div(1,p_nhnm), nhnm, color = self.line_colors['nhnm'])
            else:
                self.lines['nhnm'].set_xdata(old_div(1,p_nhnm))
                self.lines['nhnm'].set_ydata(nhnm)


    def clear_lines(self):
        for cur_line in self.lines.values():
            if cur_line:
                cur_line.set_xdata([])
                cur_line.set_ydata([])

    #def setYLimits(self, bottom, top):
    #    ''' Set the limits of the y-axes.
    #    '''
    #    self.axes.set_ylim(bottom = bottom, top = top)


    #def setXLimits(self, left, right):
    #    ''' Set the limits of the x-axes.
    #    '''
    #    self.logger.debug('Set limits: %f, %f', left, right)
    #    self.axes.set_xlim(left = left, right = right)
    #
    #    # Adjust the scale bar.




############## DEMO PLUGIN FOR ARRAY VIEWS ##########################################

class ArrayDemoPlotter(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                             name = 'array_demo plotter',
                             category = 'view',
                             tags = None
                            )

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons.burst_icon_16

    def get_virtual_stations(self):
        return {'DEMO': ['CH1', 'CH2']}



    def plot(self, displayManager, dataManager):
        ''' Plot all available virtual stations.

        '''
        # Process the virtual stations only.
        self.plotStation(displayManager, dataManager, displayManager.show_virtual_stations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.virtual_channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            array = curChannel.parent.parent
            array_node = self.parent.viewport.get_node(array = array.name)[0]
            views = array_node.get_node(name = self.rid,
                                        channel = curChannel.name,
                                        station = curChannel.parent.name,
                                        network = curChannel.parent.network,
                                        location = curChannel.parent.location)

            # Get the data of all stations shown in the array.
            cur_stream = obspy.core.Stream()
            request_channel = 'HHZ'
            for cur_station in array.stations:
                cur_stream += stream.select(station = cur_station.name,
                                            channel = request_channel,
                                            network = cur_station.network,
                                            location = cur_station.location)

            for curView in views:
                if cur_stream:
                    curView.plot(cur_stream)

                curView.setXLimits(left = displayManager.startTime.timestamp,
                                   right = displayManager.endTime.timestamp)
                curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return ArrayDemoView



class ArrayDemoView(psy_view.viewnode.ViewNode):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None, lineColor=(1,0,0), **kwargs):
        psy_view.viewnode.ViewNode.__init__(self, parent=parent, id=id, parent_viewport=parent_viewport, name=name, **kwargs)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.t0 = None
        self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None

        self.lines = []



    def plot(self, stream):
        ''' Plot all normalized traces of the stream.
        '''
        for cur_line in self.lines:
            self.axes.lines.remove(cur_line)
        self.lines = []
        self.axes.set_color_cycle(None)

        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = old_div(timeArray * 1,trace.stats.sampling_rate)
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                try:
                    timeArray = np.ma.array(timeArray,
                                            mask = trace.data.mask)
                except Exception:
                    timeArray = np.ma.array(timeArray[:-1],
                                            mask=trace.data.mask)

            cur_max = np.max(np.abs(trace.data))

            cur_line = self.axes.plot(timeArray, old_div(trace.data, cur_max))
            self.lines.extend(cur_line)

            self.axes.set_frame_on(False)
            self.axes.get_xaxis().set_visible(False)
            self.axes.get_yaxis().set_visible(False)

        self.axes.set_ylim(bottom = -1, top = 1)



    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.axes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.axes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.axes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.axes.get_window_extent().width
        return  width / float(timeRange)


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in the data axes.
        '''
        annotation_artist = self.get_annotation_artist(mode = 'vline',
                                                       parent_rid = parent_rid,
                                                       key = key)

        if annotation_artist:
            annotation_artist = annotation_artist[0]
            line_artist = annotation_artist.line_artist[0]
            label_artist = annotation_artist.text_artist[0]
            if line_artist:
                line_artist.set_xdata(x)
            if label_artist:
                label_artist.set_position((x, 0))
        else:
            line_artist = self.axes.axvline(x = x, **kwargs)
            if 'label' in iter(kwargs.keys()):
                ylim = self.axes.get_ylim()
                label_artist = self.axes.text(x = x, y = 0, s = kwargs['label'])
            else:
                label_artist = None

            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vline',
                                                                       parent_rid = parent_rid,
                                                                       key = key)
            annotation_artist.add_artist([line_artist, label_artist])
            self.annotation_artists.append(annotation_artist)



    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        annotation_artist = self.get_annotation_artist(mode = 'vspan',
                                                       parent_rid = parent_rid,
                                                       key = key)

        if annotation_artist:
            annotation_artist = annotation_artist[0]
            patch_artist = annotation_artist.patch_artist[0]
            label_artist = annotation_artist.text_artist[0]
            if patch_artist:
                polygon = []
                polygon.append([x_start, 0])
                polygon.append([x_start, 1])
                polygon.append([x_end, 1])
                polygon.append([x_end, 0])
                polygon.append([x_start, 0])
                patch_artist.set_xy(polygon)
            if label_artist:
                ylim = self.axes.get_ylim()
                label_artist.set_position((x_start, ylim[1]))
        else:
            vspan_artist = self.axes.axvspan(x_start, x_end, **kwargs)
            if 'label' in iter(kwargs.keys()):
                ylim = self.axes.get_ylim()
                label_artist = self.axes.text(x = x_start, y = ylim[1],
                                                  s = kwargs['label'],
                                                  verticalalignment = 'top')
            else:
                label_artist = None
            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vspan',
                                                                       parent_rid = parent_rid,
                                                                       key = key)
            annotation_artist.add_artist([vspan_artist, label_artist])
            self.annotation_artists.append(annotation_artist)
