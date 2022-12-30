from __future__ import print_function
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

import psysmon
from psysmon.core.plugins import ViewPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.gui.view as psy_view
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
                            category = 'view',
                            tags = None)

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        # Define the plugin icons.
        self.icons['active'] = icons.hand_pro_icon_16

        # Set the shortcut string.
        self.accelerator_string = 'CTRL+D'
        self.pref_accelerator_string = 'ALT+D'

        # Create the preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('general')
        thr_group = pref_page.add_group('threshold')
        sc_group = pref_page.add_group('stop criterium')
        filter_group = pref_page.add_group('filter')

        # The CF type.
        item = preferences_manager.SingleChoicePrefItem(name = 'cf_type',
                                                        label = 'cf type',
                                                        limit = ('abs', 'square', 'envelope', 'envelope^2'),
                                                        value = 'square',
                                                        tool_tip = 'The type of the characteristic function.')
        gen_group.add_item(item)


        # STA length
        item = preferences_manager.FloatSpinPrefItem(name = 'sta_length',
                                                     label = 'STA length [s]',
                                                     value = 1,
                                                     limit = (0, 3600),
                                                     tool_tip = 'The length of the short term average window.')
        gen_group.add_item(item)


        # LTA length
        item = preferences_manager.FloatSpinPrefItem(name = 'lta_length',
                                                     label = 'LTA length [s]',
                                                     value = 5,
                                                     limit = (0, 3600),
                                                     tool_tip = 'The length of the long term average window.')
        gen_group.add_item(item)


        # Threshold value
        item = preferences_manager.FloatSpinPrefItem(name = 'thr',
                                                     label = 'Threshold',
                                                     value = 3,
                                                     limit = (0, 100),
                                                     tool_tip = 'The threshold value used to detect a signal start. Trigger signal if STA/LTA > THR.')
        thr_group.add_item(item)

        # Fine threshold value
        item = preferences_manager.FloatSpinPrefItem(name = 'fine_thr',
                                                     label = 'Fine threshold',
                                                     value = 2,
                                                     limit = (0, 100),
                                                     tool_tip = 'A threshold value used to refine the signal start after a positive trigger. The threshold function is search in reverse to get to a value below the fine threshold.')
        thr_group.add_item(item)

        # Turn limit.
        item = preferences_manager.FloatSpinPrefItem(name = 'turn_limit',
                                                     label = 'turn limit',
                                                     value = 0.05,
                                                     limit = (0, 10),
                                                     tool_tip = 'The turning limit when to stop the event begin refinement if the fine threshold is not reached in strict downward motion. It is defined as a threshold function difference.')
        thr_group.add_item(item)


        # stop growth
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_growth',
                                                     label = 'stop grow ratio',
                                                     value = 0.001,
                                                     digits = 6,
                                                     limit = (0, 0.1),
                                                     tool_tip = 'The ratio with which the stop value is grown to ensure to reach the stop criterium at some time.')
        sc_group.add_item(item)

        # stop growth exponent
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_growth_exp',
                                                     label = 'stop grow exponent',
                                                     value = 1,
                                                     digits = 1,
                                                     limit = (0.1, 100),
                                                     tool_tip = 'The exponent of the stop grow function. The higher, the faster the stop function grows.')
        sc_group.add_item(item)

        # stop growth increase percentage
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_growth_inc',
                                                     label = 'stop grow increase [%]',
                                                     value = 0.001,
                                                     digits = 6,
                                                     limit = (0, 100),
                                                     tool_tip = 'The increase of the stop grow value after each sample. The higher, the faster the stop growth value increases.')
        sc_group.add_item(item)

        # stop growth increase percentage
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_growth_inc_begin',
                                                     label = 'stop grow inc. begin [s]',
                                                     value = 10,
                                                     digits = 3,
                                                     limit = (0, 100000),
                                                     tool_tip = "When to start growing the stop grow value using the stop grow increase. The time is in seconds relative to the time the STA falls below the LTA.")
        sc_group.add_item(item)

        # Stop criterium delay.
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_win_length',
                                                     label = 'Stop window length [s]',
                                                     value = 0.5,
                                                     limit = (0, 100),
                                                     tool_tip = 'The length of the time window in front of the event trigger used to compute the initial value of the stop criterium.')
        sc_group.add_item(item)

        item = preferences_manager.SingleChoicePrefItem(name = 'stop_win_mode',
                                                        label = 'Stop window mode',
                                                        value = 'median',
                                                        limit = ('min', 'mean', 'median'),
                                                        tool_tip = 'The mode used to compute the initial stop criterium using the stop window.')
        sc_group.add_item(item)


        # Detection reject length
        item = preferences_manager.FloatSpinPrefItem(name = 'reject_length',
                                                     label = 'reject lenght [s]',
                                                     value = 0.5,
                                                     limit = (0, 10000),
                                                     tool_tip = 'Detections with a smaller length are rejected [s].')
        filter_group.add_item(item)




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
        fine_thr = self.pref_manager.get_value('fine_thr')
        turn_limit = self.pref_manager.get_value('turn_limit')
        cf_type = self.pref_manager.get_value('cf_type')
        stop_win_length = self.pref_manager.get_value('stop_win_length')
        stop_win_mode = self.pref_manager.get_value('stop_win_mode')
        stop_growth = self.pref_manager.get_value('stop_growth')
        stop_growth_exp = self.pref_manager.get_value('stop_growth_exp')
        stop_growth_inc = self.pref_manager.get_value('stop_growth_inc')
        stop_growth_inc_begin = self.pref_manager.get_value('stop_growth_inc_begin')
        reject_length = self.pref_manager.get_value('reject_length')


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
                                  fine_thr = fine_thr,
                                  turn_limit = turn_limit,
                                  cf_type = cf_type,
                                  stop_win_length = stop_win_length,
                                  stop_win_mode = stop_win_mode,
                                  stop_growth = stop_growth,
                                  stop_growth_exp = stop_growth_exp,
                                  stop_growth_inc = stop_growth_inc,
                                  stop_growth_inc_begin = stop_growth_inc_begin,
                                  reject_length = reject_length)

                cur_view.setXLimits(left = display_manager.startTime.timestamp,
                                    right = display_manager.endTime.timestamp)
                cur_view.draw()



    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return DetectStaLtaView








class DetectStaLtaView(psy_view.viewnode.ViewNode):
    '''
    A STA/LTA detection features view.

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

        # Create multiple axes.
        #self.set_n_axes(3)

        self.lineColor = [x/255.0 for x in lineColor]

        self.lines = {}
        self.lines['cf'] = None
        self.lines['sta'] = None
        self.lines['lta'] = None
        self.lines['thrf'] = None
        self.lines['lta * thr'] = None
        self.lines['lta_orig'] = None
        self.lines['lta_orig * thr'] = None
        self.lines['stop_crit'] = None

        self.marker_lines = []
        self.range_spans = []



    def plot(self, stream, sta_len, lta_len, thr, fine_thr, turn_limit, cf_type,
             stop_win_length, stop_win_mode, stop_growth, stop_growth_exp,
             stop_growth_inc, stop_growth_inc_begin,
             reject_length):
        ''' Plot the STA/LTA features.
        '''
        plot_detection_marker = True
        plot_lta_replace_marker = False
        plot_stop_window = True
        #plot_features = ['sta', 'lta * thr']
        plot_features = ['sta', 'lta * thr', 'lta_orig * thr', 'stop_crit']
        #plot_features = ['thrf']

        detector = detect.StaLtaDetector(thr = thr, cf_type = cf_type, fine_thr = fine_thr,
                                         turn_limit = turn_limit, stop_growth = stop_growth,
                                         stop_growth_exp = stop_growth_exp,
                                         stop_growth_inc = stop_growth_inc)

        for cur_trace in stream:
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

            n_sta = int(sta_len * cur_trace.stats.sampling_rate)
            n_lta = int(lta_len * cur_trace.stats.sampling_rate)
            stop_win_length_smp = int(stop_win_length * cur_trace.stats.sampling_rate)
            fine_thr_win_smp = int(detector.fine_thr_win * cur_trace.stats.sampling_rate)

            detector.n_sta = n_sta
            detector.n_lta = n_lta
            detector.stop_growth_inc_begin = int(stop_growth_inc_begin * cur_trace.stats.sampling_rate)
            detector.reject_length = reject_length * cur_trace.stats.sampling_rate
            detector.set_data(cur_trace.data)
            detector.compute_cf()
            detector.compute_sta_lta()
            detection_markers = detector.compute_event_limits(stop_win_length = stop_win_length_smp,
                                                              stop_win_mode = stop_win_mode,
                                                              fine_thr_win = fine_thr_win_smp)

            y_lim_min = []
            y_lim_max = []
            for cur_feature in plot_features:
                cur_line = self.lines[cur_feature]
                #if cur_feature == 'cf':
                cur_time = time_array
                #else:
                #    cur_time = time_array[detector.n_lta:-detector.n_sta]

                if cur_feature == 'lta * thr':
                    cur_data = detector.lta * detector.thr
                elif cur_feature == 'lta_orig * thr':
                    cur_data = detector.lta_orig * detector.thr
                elif cur_feature == 'thrf':
                    cur_data = detector.sta / detector.lta
                else:
                    cur_data = getattr(detector, cur_feature)

                if cur_feature != 'stop_crit':
                    cur_min_data = np.min(cur_data[detector.valid_ind:])
                    cur_max_data = np.max(cur_data[detector.valid_ind:])


                y_lim_min.append(cur_min_data)
                y_lim_max.append(cur_max_data)

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

            y_lim = [np.min(y_lim_min), np.max(y_lim_max)]
            self.axes.set_ylim(bottom = y_lim[0], top = y_lim[1])
            #self.axes.set_ylim(bottom = 0, top = detector.thr)
            self.axes.set_yscale('log')

            # Clear the marker lines.
            for cur_line in self.marker_lines:
                self.axes.lines.remove(cur_line)
            # Clear the range spans.
            for cur_span in self.range_spans:
                cur_span.remove()
            self.marker_lines = []
            self.range_spans = []

            if plot_detection_marker:
                for det_start_ind, det_end_ind in detection_markers:
                    det_start_time = cur_trace.stats.starttime + old_div(det_start_ind, cur_trace.stats.sampling_rate)
                    cur_line = self.axes.axvline(x = det_start_time.timestamp, color = 'r')
                    self.marker_lines.append(cur_line)

                    if not np.isnan(det_end_ind):
                        det_end_time = det_start_time + old_div((det_end_ind - det_start_ind), cur_trace.stats.sampling_rate)
                        cur_line = self.axes.axvline(x = det_end_time.timestamp, color = 'b')
                        self.marker_lines.append(cur_line)

            if plot_stop_window:
                for det_start_ind, det_end_ind in detection_markers:
                    det_start_time = cur_trace.stats.starttime + det_start_ind / cur_trace.stats.sampling_rate
                    win_start = det_start_time - stop_win_length
                    win_end = det_start_time
                    cur_span = self.axes.axvspan(xmin = win_start,
                                                 xmax = win_end,
                                                 color = 'gray',
                                                 alpha = 0.3)
                    self.range_spans.append(cur_span)

            if plot_lta_replace_marker:
                for det_start_ind, det_end_ind in detector.replace_limits:
                    #det_start_time = cur_trace.stats.starttime + (n_lta - 1 + det_start_ind) / cur_trace.stats.sampling_rate
                    det_start_time = cur_trace.stats.starttime + old_div(det_start_ind, cur_trace.stats.sampling_rate)
                    det_end_time = det_start_time + old_div((det_end_ind - det_start_ind), cur_trace.stats.sampling_rate)

                    cur_line = self.axes.axvline(x = det_start_time.timestamp, color = 'y')
                    self.marker_lines.append(cur_line)
                    cur_line = self.axes.axvline(x = det_end_time.timestamp, color = 'm')
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
            if 'label' in iter(kwargs.keys()):
                label_artist = self.axes.text(x = x, y = 0, s = kwargs['label'])
            else:
                label_artist = None

            annotation_artist = psy_view.plotpanel.AnnotationArtist(mode = 'vline',
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


