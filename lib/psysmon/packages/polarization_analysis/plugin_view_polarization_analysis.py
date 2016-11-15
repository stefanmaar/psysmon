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
import obspy.core
from matplotlib.patches import Rectangle
import psysmon
from psysmon.core.plugins import ViewPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.gui_view
import psysmon.core.preferences_manager as preferences_manager



class PolarizationAnalysis(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                             name = 'polarization analysis',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.glasses_icon_16

        self.channel_map = {'z': 'HHZ', 'ns':'HHN', 'ew':'HHE'}

        # TODO: Add the possibility to define an azimuth offset from north.
        # TODO: Add the possibility to define an inclination offset.


    @property
    def required_data_channels(self):
        ''' This plugin needs to create a virtual channel.
        '''
        # TODO: Get the needed channels from preference items.
        return self.channel_map.values()



    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        self.logger.debug('Plotting station of polarization analysis.')
        stream = dataManager.procStream

        for cur_station in station:
            views = self.parent.viewport.get_node(station = cur_station.name,
                                                  network = cur_station.network,
                                                  location = cur_station.location,
                                                  name = self.rid)
            cur_stream = obspy.core.Stream()
            for cur_channel in self.required_data_channels:
                cur_stream += stream.select(station = cur_station.name,
                                            channel = cur_channel,
                                            network = cur_station.network,
                                            location = cur_station.location)

            for cur_view in views:
                if cur_stream:
                    cur_view.plot(cur_stream, self.channel_map)

                cur_view.setXLimits(left = displayManager.startTime.timestamp,
                                    right = displayManager.endTime.timestamp)
                cur_view.draw()



    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return PolarizationAnalysisView








class PolarizationAnalysisView(psysmon.core.gui_view.ViewNode):
    '''
    A polarization analysis view.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None, lineColor=(1,0,0), **kwargs):
        ''' Initialize the instance.
        '''
        psysmon.core.gui_view.ViewNode.__init__(self,
                                                parent=parent,
                                                id=id,
                                                parent_viewport = parent_viewport,
                                                name=name,
                                                **kwargs)

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

	self.lineColor = [x/255.0 for x in lineColor]

        self.lines = {'z': None, 'ns': None, 'ew': None}

        self.axes.set_frame_on(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)



    def plot(self, stream, channel_map):
        ''' Plot the polarization analysis
        '''

        for component, channel_name in channel_map.iteritems():
            cur_stream = stream.select(channel = channel_name)

            for cur_trace in cur_stream:
                time_array = np.arange(0, cur_trace.stats.npts)
                time_array = time_array * 1/cur_trace.stats.sampling_rate
                time_array = time_array + cur_trace.stats.starttime.timestamp

                # Check if the data is a ma.maskedarray
                if np.ma.count_masked(cur_trace.data):
                    time_array = np.ma.array(time_array[:-1], mask=cur_trace.data.mask)

                if self.lines[component] is None:
                    self.lines[component], = self.axes.plot(time_array, cur_trace.data)
                else:
                    self.lines[component].set_xdata(time_array)
                    self.lines[component].set_ydata(cur_trace.data)

                self.axes.set_frame_on(False)
                self.axes.get_xaxis().set_visible(False)
                self.axes.get_yaxis().set_visible(False)
                yLim = np.max(np.abs(cur_trace.data))
                self.axes.set_ylim(bottom = -yLim, top = yLim)


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

