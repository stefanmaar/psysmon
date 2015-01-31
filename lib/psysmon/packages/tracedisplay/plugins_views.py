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
from matplotlib.patches import Rectangle
import psysmon
from psysmon.core.plugins import AddonPlugin
from psysmon.core.plugins import CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
from container import View
from obspy.imaging.spectrogram import spectrogram
import psysmon.core.preferences_manager as preferences_manager



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



class SeismogramPlotter(AddonPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor.

        '''
        AddonPlugin.__init__(self,
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
        item = preferences_manager.CheckBoxPrefItem(name = 'show envelope',
                                                value = False
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
            curView = displayManager.getViewContainer(curChannel.getSCNL(), self.name)
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
                             show_envelope = self.pref_manager.get_value('show envelope'))

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



    def plot(self, stream, color, show_envelope = False):
        ''' Plot the seismogram.
        '''
        #display_size = wx.GetDisplaySize()
        axes_width = self.dataAxes.get_window_extent().width
        data_plot_limit = axes_width * 0.75
        self.logger.debug('data_plot_limit: %f', data_plot_limit)
        #data_plot_limit = 1e20
        for trace in stream:
            if trace.stats.npts > data_plot_limit and (len(trace) / trace.stats.sampling_rate) > 20:
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
                    trace_envelope = np.abs(trace_data)

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
                    trace_envelope = np.abs(trace_data)

            self.t0 = trace.stats.starttime

            self.logger.debug('len(trace_data): %d', len(trace_data))

            if self.line is None:
                self.line, = self.dataAxes.plot(timeArray, trace_data, color = color)
            else:
                self.line.set_xdata(timeArray)
                self.line.set_ydata(trace_data)

            if show_envelope is True:
                if self.envelope_line is None:
                    self.envelope_line, = self.dataAxes.plot(timeArray, trace_envelope, color = 'r')
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
            self.dataAxes.set_ylim(bottom = -yLim, top = yLim)
            self.logger.debug('yLim: %s', yLim)

        # Add the time scale bar.
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


############## DEMO PLUGIN FOR VIEWS ##########################################

class DemoPlotter(AddonPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        AddonPlugin.__init__(self,
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
            curView = displayManager.getViewContainer(curChannel.getSCNL(), self.name)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

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





class SpectrogramPlotter(AddonPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        AddonPlugin.__init__(self,
                             name = 'spectrogram plotter',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.twitter_icon_16


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
            curView = displayManager.getViewContainer(curChannel.getSCNL(), self.name)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

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

