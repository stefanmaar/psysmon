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
import scipy
import scipy.signal
from matplotlib.patches import Rectangle
import psysmon
from psysmon.core.plugins import ViewPlugin
from psysmon.core.plugins import CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
from container import View
from container import AnnotationArtist
from obspy.imaging.spectrogram import spectrogram
import psysmon.core.preferences_manager as preferences_manager
import obspy.signal



class Refresh(CommandPlugin):
    ''' Refresh all views.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        CommandPlugin.__init__(self,
                               name = 'refresh views',
                               category = 'visualize',
                               tags = ['view', 'refresh'],
                               position_pref = 1
                               )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.refresh_icon_16


    def run(self):
        ''' Export the visible data to the project server.
        '''
        self.parent.updateDisplay()



class SeismogramPlotter(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                             name = 'plot seismogram',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.waveform_icon_16

        # Add the plugin preferences.
        item = preferences_manager.CheckBoxPrefItem(name = 'show_envelope',
                                                    label = 'show envelope',
                                                    value = False
                                                   )
        self.pref_manager.add_item(item = item)

        item = preferences_manager.FloatSpinPrefItem(name = 'minmax_limit',
                                                     label = 'min-max limit [s]',
                                                     value = 20.,
                                                     limit = (0, None),
                                                     digits = 1,
                                                     increment = 1
                                                    )
        self.pref_manager.add_item(item = item)



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
                                                      name = self.name)
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
                    lineColor = [x/255.0 for x in curChannel.container.color]
                    curView.plot(curStream, lineColor,
                                 end_time = displayManager.endTime,
                                 duration = displayManager.endTime - displayManager.startTime,
                                 show_envelope = self.pref_manager.get_value('show_envelope'),
                                 minmax_limit = self.pref_manager.get_value('minmax_limit')
                                 )

                curView.setXLimits(left = displayManager.startTime.timestamp,
                                   right = displayManager.endTime.timestamp)
                curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return SeismogramView








class SeismogramView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        ''' Initialize the instance.
        '''
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.t0 = None
	self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None

        self.line = None

        self.envelope_line = None



    def plot(self, stream, color, duration, end_time, show_envelope = False, minmax_limit = 20, limit_scale = 10):
        ''' Plot the seismogram.
        '''
        #display_size = wx.GetDisplaySize()
        axes_width = self.dataAxes.get_window_extent().width
        data_plot_limit = axes_width * 0.75 * limit_scale
        self.logger.debug('data_plot_limit: %f', data_plot_limit)
        #data_plot_limit = 1e20
        for trace in stream:
            if trace.stats.npts > data_plot_limit and (len(trace) / trace.stats.sampling_rate) > minmax_limit:
                # Plot minmax values
                self.logger.info('Plotting in minmax mode.')
                sample_step = np.ceil(len(trace.data) / data_plot_limit)
                self.logger.debug("len(trace.data): %f", len(trace.data))
                self.logger.debug('sample_step: %f', sample_step)
                trace_data = self.compute_minmax_data(trace.data, sample_step)
                time_step = sample_step / trace.stats.sampling_rate
                minmax_time = np.array([trace.stats.starttime.timestamp + x * time_step for x in range(int(np.floor(len(trace.data) / sample_step)))])
                minmax_time = minmax_time.repeat(2)
                timeArray = minmax_time

                if show_envelope is True:
                    comp_trace = scipy.signal.hilbert(trace_data)
                    trace_envelope = np.sqrt(np.real(comp_trace)**2 + np.imag(comp_trace)**2)

            else:
                self.logger.info('Plotting in FULL mode.')
                timeArray = np.arange(0, trace.stats.npts)
                timeArray = timeArray / trace.stats.sampling_rate
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

            if self.line is None:
                self.line, = self.dataAxes.plot(timeArray, trace_data, color = color, label = 'seismogram')
            else:
                self.line.set_xdata(timeArray)
                self.line.set_ydata(trace_data)

            if show_envelope is True:
                if self.envelope_line is None:
                    self.envelope_line, = self.dataAxes.plot(timeArray, trace_envelope, color = 'r', label = 'seismogram_envelope')
                else:
                    self.envelope_line.set_xdata(timeArray)
                    self.envelope_line.set_ydata(trace_envelope)
            elif self.envelope_line is not None:
                self.dataAxes.lines.remove(self.envelope_line)
                self.envelope_line = None


            self.dataAxes.set_frame_on(False)
            self.dataAxes.get_xaxis().set_visible(False)
            self.dataAxes.get_yaxis().set_visible(False)
            yLim = np.max(np.abs(trace.data))
            if show_envelope is True:
                env_max = np.max(trace_envelope)
                yLim = np.max([yLim, env_max])
            self.dataAxes.set_ylim(bottom = -yLim, top = yLim)
            self.logger.debug('yLim: %s', yLim)

        self.add_time_scalebar(duration = duration, end_time = end_time)


    def add_time_scalebar(self, duration, end_time):
        ''' Add a time scalebar to the axes.
        '''
        y_lim = self.dataAxes.get_ylim()
        y_lim = np.abs(y_lim[0])

        if duration > 1:
            order = len(str(int(np.floor(duration)))) - 1
            scale_length = 1 * 10**(order-1)
        elif duration == 1:
            scale_length = 0.1
        else:
            order = len(str(int(np.floor(1/duration)))) - 1
            scale_length = 1 * (10.** ((order+1) * -1))

        units_per_pixel = (2*y_lim) / self.dataAxes.get_window_extent().height
        scale_height = 5 * units_per_pixel
        if self.scaleBar:
            self.scaleBar.remove()
        self.scaleBar = Rectangle((end_time.timestamp - scale_length,
                                  -y_lim+scale_height/2.0),
                                  width=scale_length,
                                  height=scale_height,
                                  edgecolor = 'none',
                                  facecolor = '0.75')
        self.dataAxes.add_patch(self.scaleBar)



    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.dataAxes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        #self.logger.debug('Set limits: %f, %f', left, right)
        self.dataAxes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.dataAxes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.dataAxes.get_window_extent().width
        return  width / float(timeRange)


    def compute_minmax_data(self, data, sample_step):
        '''

        '''
        n_step = np.floor(len(data) / sample_step)
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
        self.logger.info('Plotting a annotation line %s, %s.', parent_rid, key)
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
            line_artist = self.dataAxes.axvline(x = x, **kwargs)
            if 'label' in kwargs.keys():
                ylim = self.dataAxes.get_ylim()
                label_artist = self.dataAxes.text(x = x, y = 0, s = kwargs['label'])
            else:
                label_artist = None

            annotation_artist = AnnotationArtist(mode = 'vline',
                                                 parent_rid = parent_rid,
                                                 key = key)
            annotation_artist.add_artist([line_artist, label_artist])
            self.annotation_artists.append(annotation_artist)



    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        self.logger.info('Plotting a annotation vspan %s, %s.', parent_rid, key)
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
                ylim = self.dataAxes.get_ylim()
                label_artist.set_position((x_start, ylim[1]))
        else:
            vspan_artist = self.dataAxes.axvspan(x_start, x_end, **kwargs)
            if 'label' in kwargs.keys():
                ylim = self.dataAxes.get_ylim()
                label_artist = self.dataAxes.text(x = x_start, y = ylim[1],
                                                  s = kwargs['label'],
                                                  verticalalignment = 'top')
            else:
                label_artist = None
            annotation_artist = AnnotationArtist(mode = 'vspan',
                                                 parent_rid = parent_rid,
                                                 key = key)
            annotation_artist.add_artist([vspan_artist, label_artist])
            self.annotation_artists.append(annotation_artist)



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
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

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
                                                      name = self.name)
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



class DemoView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.t0 = None
	self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None

        self.line = None



    def plot(self, stream, color):


        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray * 1/trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                timeArray = np.ma.array(timeArray[:-1], mask=trace.data.mask)


            if not self.line:
                self.line, = self.dataAxes.plot(timeArray, trace.data * -1, color = color)
            else:
                self.line.set_xdata(timeArray)
                #self.line.set_ydata(trace.data * -1)
                self.line.set_ydata(trace.data / np.log10(np.abs(trace.data)))

            self.dataAxes.set_frame_on(False)
            self.dataAxes.get_xaxis().set_visible(False)
            self.dataAxes.get_yaxis().set_visible(False)
            yLim = np.max(np.abs(trace.data))
            self.dataAxes.set_ylim(bottom = -yLim, top = yLim)


        # Add the scale bar.
        scaleLength = 10
        unitsPerPixel = (2*yLim) / self.dataAxes.get_window_extent().height
        scaleHeight = 3 * unitsPerPixel
        if self.scaleBar:
            self.scaleBar.remove()
        self.scaleBar = Rectangle((timeArray[-1] - scaleLength,
                                  -yLim+scaleHeight/2.0),
                                  width=scaleLength,
                                  height=scaleHeight,
                                  edgecolor = 'none',
                                  facecolor = '0.75')
        self.dataAxes.add_patch(self.scaleBar)
        #self.dataAxes.axvspan(timeArray[0], timeArray[0] + 10, facecolor='0.5', alpha=0.5)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.dataAxes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.dataAxes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.dataAxes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.dataAxes.get_window_extent().width
        return  width / float(timeRange)


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in the data axes.
        '''
        self.logger.info('Plotting a annotation line %s, %s.', parent_rid, key)
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
            line_artist = self.dataAxes.axvline(x = x, **kwargs)
            if 'label' in kwargs.keys():
                ylim = self.dataAxes.get_ylim()
                label_artist = self.dataAxes.text(x = x, y = 0, s = kwargs['label'])
            else:
                label_artist = None

            annotation_artist = AnnotationArtist(mode = 'vline',
                                                 parent_rid = parent_rid,
                                                 key = key)
            annotation_artist.add_artist([line_artist, label_artist])
            self.annotation_artists.append(annotation_artist)



    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        self.logger.info('Plotting a annotation vspan %s, %s.', parent_rid, key)
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
                ylim = self.dataAxes.get_ylim()
                label_artist.set_position((x_start, ylim[1]))
        else:
            vspan_artist = self.dataAxes.axvspan(x_start, x_end, **kwargs)
            if 'label' in kwargs.keys():
                ylim = self.dataAxes.get_ylim()
                label_artist = self.dataAxes.text(x = x_start, y = ylim[1],
                                                  s = kwargs['label'],
                                                  verticalalignment = 'top')
            else:
                label_artist = None
            annotation_artist = AnnotationArtist(mode = 'vspan',
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
                             name = 'spectrogram plotter',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons._3x3_grid_2_icon_16


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
                                                      name = self.name)
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
        return SpectrogramView



class SpectrogramView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.t0 = None


    def plot(self, stream, color):


        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray * 1/trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                timeArray = np.ma.array(timeArray[:-1], mask=trace.data.mask)

            if self.dataAxes.images:
                self.dataAxes.images.pop()


            spectrogram(trace.data, 
                        samp_rate = trace.stats.sampling_rate,
                        axes = self.dataAxes)


            extent = self.dataAxes.images[0].get_extent()
            newExtent = (extent[0] + trace.stats.starttime.timestamp,
                         extent[1] + trace.stats.starttime.timestamp,
                         extent[2],
                         extent[3])
            self.dataAxes.images[0].set_extent(newExtent)
            self.dataAxes.set_frame_on(False)



    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.dataAxes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.dataAxes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    #def getScalePixels(self):
    #    yLim = self.dataAxes.get_xlim()
    #    timeRange = yLim[1] - yLim[0]
    #    width = self.dataAxes.get_window_extent().width
    #    return  width / float(timeRange)



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
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

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
                                                      name = self.name)
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



class FrequencySpectrumView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, psdColor=(0, 0, 0), nhnmColor = (1, 0, 0), nlnmColor = (0, 1, 0)):
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

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

        self.show_noise_model = True



    def plot(self, stream):

        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray * 1/trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                timeArray = np.ma.array(timeArray[:-1], mask=trace.data.mask)

            # Compute the power amplitude density spectrum.
            # As defined by Havskov and Alguacil (page 164), the power density spectrum can be
            # written as 
            #   P = 2* 1/T * deltaT^2 * abs(F_dft)^2
            #   
            n_fft = len(trace.data)
            delta_t = 1 / trace.stats.sampling_rate
            T = (len(trace.data) - 1) * delta_t
            Y = scipy.fft(trace.data, n_fft)
            psd = 2 * delta_t**2 / T * np.abs(Y)**2
            psd = 10 * np.log10(psd)
            frequ = trace.stats.sampling_rate * np.arange(0,n_fft) / float(n_fft)

            left_fft = np.ceil(n_fft / 2.)

            # Plot the psd.
            if not self.lines['psd']:
                self.lines['psd'], = self.dataAxes.plot(frequ[:left_fft], psd[:left_fft], color = self.line_colors['psd'])
            else:
                self.lines['psd'].set_xdata(frequ[:left_fft])
                self.lines['psd'].set_ydata(psd[:left_fft])

            cur_unit = trace.stats.unit

            # Plot the noise model.
            if self.show_noise_model:
                self.plot_noise_model(cur_unit)

            # Set the axis limits.
            if cur_unit == 'm/s':
                self.dataAxes.set_ylim(bottom = -220, top = -80)
                cur_unit_label = '(m/s)^2/Hz in dB'
            elif cur_unit == 'm/s^2':
                self.dataAxes.set_ylim(bottom = -220, top = -80)
                cur_unit_label = '(m/s^2)^2/Hz in dB'
            elif cur_unit == 'counts':
                cur_unit_label = 'counts^2/Hz in dB'
            else:
                cur_unit_label = '???^2/Hz in dB'

            self.dataAxes.set_xscale('log')
            self.dataAxes.set_xlim(left = 1e-3, right = trace.stats.sampling_rate)
            self.dataAxes.set_frame_on(False)
            self.dataAxes.tick_params(axis = 'x', pad = -20)
            self.dataAxes.tick_params(axis = 'y', pad = -40)

            annot_string = 'X-axis: frequency\nX-units: Hz\n\nY-axis: psd\nY-units: %s' % cur_unit_label
            self.setAnnotation(annot_string)
            #self.dataAxes.get_xaxis().set_visible(False)
            #self.dataAxes.get_yaxis().set_visible(False)


    def plot_noise_model(self, unit):
        p_nhnm, nhnm = obspy.signal.spectral_estimation.get_NHNM()
        p_nlnm, nlnm = obspy.signal.spectral_estimation.get_NLNM()

        # obspy returns the NLNM and NHNM values in acceleration.
        # Convert them to the current unit (see Bormann (1998)).
        if unit == 'm':
            nhnm = nhnm + 40 * np.log10(p_nhnm/ (2 * np.pi))
            nlnm = nlnm + 40 * np.log10(p_nlnm/ (2 * np.pi))
        elif unit == 'm/s':
            nhnm = nhnm + 20 * np.log10(p_nhnm/ (2 * np.pi))
            nlnm = nlnm + 20 * np.log10(p_nlnm/ (2 * np.pi))
        elif unit != 'm/s^2':
            nhnm = None
            nlnm = None
            self.logger.error('The NLNM and NHNM is not available for the unit: %s.', unit)

        if nlnm is not None:
            if not self.lines['nlnm']:
                self.lines['nlnm'], = self.dataAxes.plot(1/p_nlnm, nlnm, color = self.line_colors['nlnm'])
            else:
                self.lines['nlnm'].set_xdata(1/p_nlnm)
                self.lines['nlnm'].set_ydata(nlnm)
        if nhnm is not None:
            if not self.lines['nhnm']:
                self.lines['nhnm'], = self.dataAxes.plot(1/p_nhnm, nhnm, color = self.line_colors['nhnm'])
            else:
                self.lines['nhnm'].set_xdata(1/p_nhnm)
                self.lines['nhnm'].set_ydata(nhnm)


    def clear_lines(self):
        for cur_line in self.lines.itervalues():
            if cur_line:
                cur_line.set_xdata([])
                cur_line.set_ydata([])

    #def setYLimits(self, bottom, top):
    #    ''' Set the limits of the y-axes.
    #    '''
    #    self.dataAxes.set_ylim(bottom = bottom, top = top)


    #def setXLimits(self, left, right):
    #    ''' Set the limits of the x-axes.
    #    '''
    #    self.logger.debug('Set limits: %f, %f', left, right)
    #    self.dataAxes.set_xlim(left = left, right = right)
    #
    #    # Adjust the scale bar.

