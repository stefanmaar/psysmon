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

import psysmon
from psysmon.core.plugins import ViewPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.gui_view
import psysmon.core.preferences_manager as preferences_manager
import psysmon.packages.event.detect as detect




class DetectStaLta(ViewPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        ViewPlugin.__init__(self,
                             name = 'STA/LTA detection',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.hand_pro_icon_16


        # STA length
        item = preferences_manager.FloatSpinPrefItem(name = 'sta_length',
                                                     label = 'STA length [s]',
                                                     value = 1,
                                                     limit = (0, 3600))
        self.pref_manager.add_item(item = item)


        # LTA length
        item = preferences_manager.FloatSpinPrefItem(name = 'lta_length',
                                                     label = 'LTA length [s]',
                                                     value = 5,
                                                     limit = (0, 3600))
        self.pref_manager.add_item(item = item)

        # Threshold value
        item = preferences_manager.FloatSpinPrefItem(name = 'thr',
                                                     label = 'Threshold',
                                                     value = 3,
                                                     limit = (0, 100))
        self.pref_manager.add_item(item = item)


        # The CF type.
        item = preferences_manager.SingleChoicePrefItem(name = 'cf_type',
                                                        label = 'cf type',
                                                        limit = ('abs', 'square', 'envelope', 'envelope^2'),
                                                        value = 'square',
                                                        tool_tip = 'The type of the characteristic function.'
                                                       )
        self.pref_manager.add_item(item = item)




    def plot(self, display_manager, data_manager):
        ''' Plot all available stations.

        '''
        self.plotStation(display_manager, data_manager, display_manager.showStations)


    def plotStation(self, display_manager, data_manager, station):
        ''' Plot one or more stations.

        '''
        for cur_station in station:
            self.plot_channel(display_manager, data_manager, cur_station.channels)


    def plot_channel(self, display_manager, data_manager, channels):
        ''' Plot one or more channels.
        '''
        self.logger.debug('Plotting STA/LTA detection functions.')
        stream = data_manager.procStream

        sta_len = self.pref_manager.get_value('sta_length')
        lta_len = self.pref_manager.get_value('lta_length')
        thr = self.pref_manager.get_value('thr')
        cf_type = self.pref_manager.get_value('cf_type')


        for cur_channel in channels:
            views = self.parent.viewport.get_node(station = cur_channel.parent.name,
                                                  channel = cur_channel.name,
                                                  network = cur_channel.parent.network,
                                                  location = cur_channel.parent.location,
                                                  name = self.rid)
            for cur_view in views:
                if stream:
                    if cur_channel.parent.location == '--':
                        cur_location = None
                    else:
                        cur_location = cur_channel.parent.location

                    cur_stream = stream.select(station = cur_channel.parent.name,
                                               channel = cur_channel.name,
                                               network = cur_channel.parent.network,
                                               location = cur_location)
                else:
                    cur_stream = None

                if cur_stream:
                    cur_view.plot(cur_stream,
                                  sta_len = sta_len,
                                  lta_len = lta_len,
                                  thr = thr,
                                  cf_type = cf_type)

                cur_view.setXLimits(left = display_manager.startTime.timestamp,
                                    right = display_manager.endTime.timestamp)
                cur_view.draw()



    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return DetectStaLtaView








class DetectStaLtaView(psysmon.core.gui_view.ViewNode):
    '''
    A STA/LTA detection features view.

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

        # Create multiple axes.
        #self.set_n_axes(3)

	self.lineColor = [x/255.0 for x in lineColor]

        self.lines = {}
        self.lines['cf'] = None
        self.lines['sta'] = None
        self.lines['lta'] = None
        self.lines['thrf'] = None
        self.lines['lta * thr'] = None

        self.marker_lines = []



    def plot(self, stream, sta_len, lta_len, thr, cf_type):
        ''' Plot the STA/LTA features.
        '''
        plot_detection_marker = True
        plot_features = ['sta', 'lta * thr']

        detector = detect.StaLtaDetector(thr = thr, cf_type = cf_type)

        for cur_trace in stream:
            time_array = np.arange(0, cur_trace.stats.npts)
            time_array = time_array * 1/cur_trace.stats.sampling_rate
            time_array = time_array + cur_trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(cur_trace.data):
                time_array = np.ma.array(time_array[:-1], mask=cur_trace.data.mask)

            n_sta = int(sta_len * cur_trace.stats.sampling_rate)
            n_lta = int(lta_len * cur_trace.stats.sampling_rate)

            detector.n_sta = n_sta
            detector.n_lta = n_lta
            detector.set_data(cur_trace.data)
            detector.compute_cf()
            detector.compute_thrf()
            detection_markers = detector.compute_event_limits()

            y_lim = []
            for cur_feature in plot_features:
                cur_line = self.lines[cur_feature]
                if cur_feature == 'cf':
                    cur_time = time_array
                else:
                    cur_time = time_array[detector.n_lta:-detector.n_sta]

                if cur_feature == 'lta * thr':
                    cur_data = detector.lta * detector.thr
                    cur_max_data = np.max(cur_data)
                else:
                    cur_data = getattr(detector, cur_feature)
                    cur_max_data = np.max(getattr(detector, cur_feature))
                y_lim.append(cur_max_data)

                if not cur_line:
                    if cur_feature == 'lta * thr':
                        cur_data = detector.lta * detector.thr
                        artists = self.axes.plot(cur_time, cur_data)
                    else:
                        artists = self.axes.plot(cur_time, cur_data)
                    self.lines[cur_feature] = artists[0]
                else:
                    cur_line.set_xdata(cur_time)
                    cur_line.set_ydata(cur_data)

            y_lim = np.max(y_lim)
            self.axes.set_ylim(bottom = 0, top = y_lim)

            # Clear the marker lines.
            for cur_line in self.marker_lines:
                self.axes.lines.remove(cur_line)
            self.marker_lines = []

            if plot_detection_marker:
                for det_start_ind, det_end_ind in detection_markers:
                    print det_start_ind
                    print det_end_ind
                    det_start_time = cur_trace.stats.starttime + (n_lta - 1 + det_start_ind) / cur_trace.stats.sampling_rate
                    det_end_time = det_start_time + (det_end_ind - det_start_ind) / cur_trace.stats.sampling_rate

                    cur_line = self.axes.axvline(x = det_start_time.timestamp, color = 'r')
                    self.marker_lines.append(cur_line)
                    cur_line = self.axes.axvline(x = det_end_time.timestamp, color = 'b')
                    self.marker_lines.append(cur_line)



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
            if 'label' in kwargs.keys():
                label_artist = self.axes.text(x = x, y = 0, s = kwargs['label'])
            else:
                label_artist = None

            annotation_artist = psysmon.core.gui_view.AnnotationArtist(mode = 'vline',
                                                                       parent_rid = parent_rid,
                                                                       key = key)
            annotation_artist.add_artist([line_artist, label_artist])
            self.annotation_artists.append(annotation_artist)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.axes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.axes.set_xlim(left = left, right = right)


