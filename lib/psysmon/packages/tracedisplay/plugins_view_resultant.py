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

from builtins import zip
import logging
import wx
import numpy as np
import obspy.core
import matplotlib as mpl
import matplotlib.pyplot as plt
import psysmon
from psysmon.core.plugins import ViewPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.gui.view as psy_view
import psysmon.core.preferences_manager as preferences_manager
import psysmon.packages.polarization_analysis.core



class Resultant(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                            name = 'resultant',
                            category = 'view',
                            tags = None)

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons.emotion_smile_icon_16

        # Create the preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        cm_group = pref_page.add_group('channel map')

        SingleChoicePrefItem = psysmon.core.preferences_manager.SingleChoicePrefItem
        item = SingleChoicePrefItem(name = 'channel_map_x',
                                    label = 'x',
                                    value = '',
                                    limit = ['HHE', 'HHN', 'HHZ'],
                                    tool_tip = 'Select the x component channel.')
        cm_group.add_item(item)

        item = SingleChoicePrefItem(name = 'channel_map_y',
                                    label = 'y',
                                    value = '',
                                    limit = ['HHE', 'HHN', 'HHZ'],
                                    tool_tip = 'Select the y component channel.')
        cm_group.add_item(item)

        item = SingleChoicePrefItem(name = 'channel_map_z',
                                    label = 'z',
                                    value = '',
                                    limit = ['HHE', 'HHN', 'HHZ'],
                                    tool_tip = 'Select the z component channel.')
        cm_group.add_item(item)
        
        
    @property
    def channel_map(self):
        ''' The channels used for the x, y, z components.
        '''
        channel_map = {'x': self.pref_manager.get_value('channel_map_x'),
                       'y': self.pref_manager.get_value('channel_map_y'),
                       'z': self.pref_manager.get_value('channel_map_z')}
        return channel_map
        
    @property
    def required_data_channels(self):
        ''' This plugin needs to create a virtual channel.
        '''
        # TODO: Get the needed channels from preference items.
        return list(self.channel_map.values())


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


    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        self.logger.debug('Plotting station of resultant view.')
        stream = dataManager.procStream

        #window_length = self.pref_manager.get_value('window_length')
        #overlap = self.pref_manager.get_value('window_overlap')

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
                #cur_view.setYLimits(bottom = 0, top = 1)
                cur_view.draw()



    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return ResultantView


class ResultantView(psy_view.viewnode.ViewNode):
    '''
    A resultant view.

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

        self.line_color = [x / 255.0 for x in lineColor]

        self.line = None
        self.line_resamp = None



    def plot(self, stream, channel_map):
        ''' Plot the resultant.
        '''
        component_data = {}
        sps = []

        # Get the data of the components.
        for component, channel_name in channel_map.items():
            cur_stream = stream.select(channel = channel_name)
            cur_trace = cur_stream.traces[0]
            sps.append(cur_trace.stats.sampling_rate)

            time_array = np.arange(0, cur_trace.stats.npts)
            time_array = time_array / cur_trace.stats.sampling_rate
            time_array = time_array + cur_trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(cur_trace.data):
                try:
                    time_array = np.ma.array(time_array,
                                             mask=cur_trace.data.mask)
                except Exception:
                    time_array = np.ma.array(time_array[:-1],
                                             mask=cur_trace.data.mask)

            if component == 'x':
                component_data['time'] = time_array
            component_data[component] = cur_trace.data


        # Convert the window length from seconds to samples.
        # TODO: Add a check for equal sps.
        sps = list(set(sps))
        if len(sps) > 1:
            self.logger.error("The three components don't have equal sampling rates.")
            return
        else:
            sps = sps[0]

        x_data = np.array(component_data['x'])
        y_data = np.array(component_data['y'])

        res = np.sqrt(x_data**2 + y_data**2)

        def strided_app(a, L, S):  # Window len = L, Stride len/stepsize = S
            nrows = ((a.size - L) // S) + 1
            n = a.strides[0]
            return np.lib.stride_tricks.as_strided(a,
                                                   shape=(nrows, L),
                                                   strides=(S * n, n))

        # Reduce to a 10 seconds max.
        win_len_sec = 1
        win_len = int(np.floor(win_len_sec * sps))
        strided_data = strided_app(res, win_len, win_len)
        res_resamp = np.max(strided_data, axis = 1)
        time_resamp = [cur_trace.stats.starttime + x * win_len_sec for x in range(len(res_resamp))]
        time_resamp = np.array(time_resamp)
        time_resamp += win_len_sec / 2

        x_data = component_data['time']
        y_data = res
        if not self.line:
            self.line, = self.axes.plot(x_data,
                                        y_data,
                                        color = self.line_color)
        else:
            self.line.set_xdata(x_data)
            self.line.set_ydata(y_data)

        x_data = time_resamp
        y_data = res_resamp
        if not self.line_resamp:
            self.line_resamp, = self.axes.plot(x_data,
                                               y_data,
                                               color = 'red',
                                               marker = 'o')
        else:
            self.line_resamp.set_xdata(x_data)
            self.line_resamp.set_ydata(y_data)

        self.axes.set_frame_on(False)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        yLim = np.max(np.abs(y_data))
        yLim += yLim * 0.05
        self.axes.set_ylim(bottom = 0, top = yLim)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.axes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.axes.set_xlim(left = left, right = right)


    def measure(self, event):
        ''' Measure the seismogram line.
        '''
        if event.inaxes is None:
            return

        if self.line is None:
            return

        xdata = self.line_resamp.get_xdata()
        ydata = self.line_resamp.get_ydata()
        ind_x = np.argmin(np.abs(xdata - event.xdata))
        snap_x = xdata[ind_x]
        snap_y = ydata[ind_x]

        if isinstance(snap_y, np.ma.MaskedArray):
            snap_y = snap_y[0]

        measurement = {}
        measurement['label'] = 'resultant'
        measurement['xy'] = (snap_x, snap_y)
        measurement['units'] = '???'
        measurement['axes'] = self.axes

        return measurement
