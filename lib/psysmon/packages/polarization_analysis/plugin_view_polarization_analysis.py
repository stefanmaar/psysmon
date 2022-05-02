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

from past.utils import old_div
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
import psysmon.gui.view as psy_view
import psysmon.core.preferences_manager as preferences_manager
import psysmon.packages.polarization_analysis.core



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

        self.channel_map = {'z': 'HHZ', 'y':'HHN', 'x':'HHE'}

        # TODO: Somehow make it possible to add multiple views to the virtual
        # channel. Each view should contain a certain polarization feature. The
        # features can change depending on the selected computation method. The
        # created views therefore have to be created dynamically. Maybe use the
        # shared information for that?

        # TODO: Add the possibility to define an azimuth offset from north.
        # TODO: Add the possibility to define an inclination offset.

        # Create the preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        win_group = pref_page.add_group('window')

        # The window length.
        item = preferences_manager.FloatSpinPrefItem(name = 'window_length',
                                                     label = 'window length [s]',
                                                     value = 0.5,
                                                     limit = (0, 3600))
        win_group.add_item(item)


        # The window overlap.
        item = preferences_manager.FloatSpinPrefItem(name = 'window_overlap',
                                                     label = 'window overlap',
                                                     value = 0.5,
                                                     limit = (0, 0.99),
                                                     spin_format = '%f')
        win_group.add_item(item)


    @property
    def required_data_channels(self):
        ''' This plugin needs to create a virtual channel.
        '''
        # TODO: Get the needed channels from preference items.
        return list(self.channel_map.values())



    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        self.logger.debug('Plotting station of polarization analysis.')
        stream = dataManager.procStream

        window_length = self.pref_manager.get_value('window_length')
        overlap = self.pref_manager.get_value('window_overlap')

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
                    cur_view.plot(cur_stream, self.channel_map,
                                  window_length = window_length,
                                  overlap = overlap)

                cur_view.setXLimits(left = displayManager.startTime.timestamp,
                                    right = displayManager.endTime.timestamp)
                #cur_view.setYLimits(bottom = 0, top = 1)
                cur_view.draw()



    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return PolarizationAnalysisView








class PolarizationAnalysisView(psy_view.viewnode.ViewNode):
    '''
    A polarization analysis view.

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
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Create multiple axes.
        self.set_n_axes(4)

        self.lineColor = [x/255.0 for x in lineColor]

        #self.lines = {'z': None, 'ns': None, 'ew': None}
        #self.lines = {'linearity': None, 'planarity': None}
        self.lines = {}

        ax_labels = ['in', 'az', 'el', 'ps']

        for k, cur_ax in enumerate(self.axes):
            cur_ax.set_frame_on(True)
            cur_ax.get_xaxis().set_visible(False)
            cur_ax.get_yaxis().set_visible(False)
            cur_ax.text(x = 0.01, y = 0.97, s = ax_labels[k],
                        va = 'top', transform = cur_ax.transAxes)



    def plot(self, stream, channel_map, window_length, overlap, method = 'covariance_matrix'):
        ''' Plot the polarization analysis
        '''
        component_data = {}
        sps = []
        # Get the data of the three components.
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

            if component == 'z':
                component_data['time'] = time_array
            component_data[component] = cur_trace.data


        # Convert the window length from seconds to samples.
        # TODO: Add a check for equal sps.
        sps = list(set(sps))
        if len(sps) > 1:
            self.logger.error("The three components don't have equal sampling rates.")
            return
        window_length_smp = window_length * sps[0]

        # Compute the polarization analysis using the selected method.
        features = psysmon.packages.polarization_analysis.core.compute_complex_covariance_matrix_windowed(component_data, window_length_smp, overlap)

        time_array = features.pop('time')
        plot_features = ['incidence', 'azimuth', 'ellipticity', 'pol_strength']
        axes_limits = [(0, np.pi/2.), (-np.pi/2., np.pi/2.), (0 ,1), (0, 1)]
        for k, cur_feature_name in enumerate(plot_features):
            if cur_feature_name in iter(self.lines.keys()):
                self.axes[k].collections.remove(self.lines[cur_feature_name])
            cur_data = features[cur_feature_name]
            self.lines[cur_feature_name] = self.axes[k].fill_between(x = time_array,
                                                                     y1 = cur_data,
                                                                     color = 'lightgrey',
                                                                     edgecolor = 'lightgrey',
                                                                     label = cur_feature_name)

            self.axes[k].set_ylim(axes_limits[k])

        msg = '\n'.join(plot_features[::-1])
        self.set_annotation(msg)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        for cur_ax in self.axes:
            cur_ax.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        #self.logger.debug('Set limits: %f, %f', left, right)
        for cur_ax in self.axes:
            cur_ax.set_xlim(left = left, right = right)

        # Adjust the scale bar.


    def measure(self, event):
        ''' Measure the polrization attributes.
        '''
        selected_axes = event.inaxes
        if selected_axes is None:
            self.logger.debug("###############Event not in axes.")
            return

        measurements = []
        for cur_axes in self.axes[::-1]:
            cur_path = cur_axes.collections[0].get_paths()[0]
            xdata = cur_path.vertices[:,0]
            ydata = cur_path.vertices[:,1]
            ind_x = np.searchsorted(xdata, [event.xdata])[0]
            snap_x = xdata[ind_x]
            snap_y = ydata[ind_x]

            if isinstance(snap_y, np.ma.MaskedArray):
                snap_y = snap_y[0]

            cur_measurement = {}
            cur_measurement['label'] = cur_axes.collections[0].get_label()
            cur_measurement['xy'] = (snap_x, snap_y)
            cur_measurement['units'] = '???'
            cur_measurement['axes'] = cur_axes
            measurements.append(cur_measurement)

        return measurements

