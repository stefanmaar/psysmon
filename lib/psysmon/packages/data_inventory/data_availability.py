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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The importWaveform module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classes of the importWaveform dialog window.
'''
from __future__ import division

from builtins import range
from builtins import object
from past.utils import old_div
import os
import logging

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import psysmon
import psysmon.core.packageNodes as package_nodes
import psysmon.core.util as util
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
import psysmon.gui.dialog.pref_listbook as psy_lb
import seaborn as sns

sns.set_style('whitegrid')
sns.set_style('ticks')
sns.set_context('paper')

## Documentation for class WindowProcessorNode
# 
# 
class DataAvailabilityNode(package_nodes.CollectionNode):

    name = 'data availability'
    mode = 'editable'
    category = 'data inventory'
    tags = ['stable']

    def __init__(self, **args):
        package_nodes.CollectionNode.__init__(self, **args)

        #self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_output_preferences()


    def edit(self):
        # Initialize the components.
        if self.project.geometry_inventory:
            stations = sorted([x.name + ':' + x.network + ':' + x.location for x in self.project.geometry_inventory.get_station()])
            self.pref_manager.set_limit('stations', stations)

            channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
            self.pref_manager.set_limit('channels', channels)

        # Update the preference item gui elements based on the current
        # selections.
        self.on_window_mode_selected()

        # Create the edit dialog.
        dlg = psy_lb. ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput={}):
        # Get the output directory from the pref_manager. If no directory is
        # specified create one based on the node resource id.
        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        processor = AvailabilityProcessor(project = self.project,
                                          output_dir = output_dir,
                                          parent_rid = self.rid)

        window_mode = self.pref_manager.get_value('window_mode')
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        window_start_times = []
        window_end_times = []
        if window_mode == 'free':
            window_length = self.pref_manager.get_value('window_length')
        elif window_mode == 'daily':
            start_time = UTCDateTime(start_time.year, start_time.month, start_time.day)
            end_time = UTCDateTime(end_time.year, end_time.month, end_time.day)
            window_length = 86400.
        elif window_mode == 'weekly':
            start_time = UTCDateTime(start_time.year, start_time.month, start_time.day) - start_time.weekday * 86400
            end_time = UTCDateTime(end_time.year, end_time.month, end_time.day) +  (7 - end_time.weekday) * 86400
            window_length = 86400. * 7
        elif window_mode == 'monthly':
            start_time = UTCDateTime(start_time.year, start_time.month, start_time.day)
            end_time = UTCDateTime(end_time.year, end_time.month, end_time.day)
            window_length = None
            window_start_times = util.compute_month_list(start_time, end_time)
            window_end_times = [util.add_month(x) for x in window_start_times]

        processor.process(start_time = start_time,
                          end_time = end_time,
                          station_names = self.pref_manager.get_value('stations'),
                          channel_names = self.pref_manager.get_value('channels'),
                          window_length = window_length,
                          window_start_times = window_start_times,
                          window_end_times = window_end_times)



    def create_component_selector_preferences(self):
        ''' Create the preference items of the component selection section.

        '''
        components_page = self.pref_manager.add_page('components')
        comp_to_process_group = components_page.add_group('components to process')
        process_time_span_group = components_page.add_group('process time span')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        process_time_span_group.add_item(item)

        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        process_time_span_group.add_item(item)

        item = psy_pm.SingleChoicePrefItem(name = 'window_mode',
                                           label = 'window mode',
                                           limit = ('free', 'daily', 'weekly', 'monthly'),
                                           value = 'free',
                                           hooks = {'on_value_change': self.on_window_mode_selected},
                                           tool_tip = 'The mode of the window computation.')
        process_time_span_group.add_item(item)

        item = psy_pm.IntegerSpinPrefItem(name = 'window_length',
                                          label = 'window length [s]',
                                          value = 300,
                                          limit = [0, 1209600],
                                          tool_tip = 'The sliding window length in seconds.')
        process_time_span_group.add_item(item)


        # The stations to process.
        item = psy_pm.MultiChoicePrefItem(name = 'stations',
                                          label = 'stations',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the processing.')
        comp_to_process_group.add_item(item)

        # The channels to process.
        item = psy_pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the processing.')
        comp_to_process_group.add_item(item)



    def create_output_preferences(self):
        ''' Create the preference items of the output section.

        '''
        output_page = self.pref_manager.add_page('output')
        output_group = output_page.add_group('output')

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the processing results.'
                                       )
        output_group.add_item(item)


    def on_window_mode_selected(self):
        '''
        '''
        if self.pref_manager.get_value('window_mode') == 'free':
            self.pref_manager.get_item('window_length')[0].enable_gui_element()
        elif self.pref_manager.get_value('window_mode') == 'daily':
            item = self.pref_manager.get_item('window_length')[0]
            item.disable_gui_element()
        elif self.pref_manager.get_value('window_mode') == 'weekly':
            item = self.pref_manager.get_item('window_length')[0]
            item.disable_gui_element()



class AvailabilityProcessor(object):

    def __init__(self, project, output_dir, parent_rid = None):
        ''' Initialize the instance.

        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.project = project

        self.parent_rid = parent_rid

        if self.parent_rid is not None:
            rid_dir = self.parent_rid.replace('/', '-').replace(':', '-')
            if rid_dir.startswith('-'):
                rid_dir = rid_dir[1:]
            if rid_dir.endswith('-'):
                rid_dir = rid_dir[:-1]
            self.output_dir = os.path.join(output_dir, rid_dir)
        else:
            self.output_dir = output_dir


        # The data availability.
        self.availability = {}



    #@profile(immediate=True)
    def process(self, start_time, end_time, station_names, channel_names, window_length, window_start_times = None, window_end_times = None):
        ''' Start the processing.

        Parameters
        ----------
        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan for which to detect the events.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan for which to detect the events.

        station_names : list of Strings
            The names of the stations to process.

        channel_names : list of Strings
            The names of the channels to process.

        window_length : float
            The length of the sliding windwow in seconds.
        '''
        self.logger.info("Processing timespan %s to %s.", start_time.isoformat(), end_time.isoformat())

        if not window_start_times:
            window_length = float(window_length)

            # Check for correct argument values:
            if end_time <= start_time:
                self.logger.error("The end_time %s is smaller than the start_time %s.", end_time.isoformat(), start_time.isoformat())
                raise ValueError("The end_time %s is smaller than the start_time %s." % (end_time.isoformat(), start_time.isoformat()))

            # Compute the start times of the sliding windows.
            windowlist_start = [start_time, ]
            n_windows = old_div(np.floor(end_time - start_time), window_length)
            windowlist_start = np.array([start_time + x * window_length for x in range(0, int(n_windows))])
            windowlist_end = windowlist_start + window_length
        else:
            windowlist_start = window_start_times
            windowlist_end = window_end_times

        self.process_whole(windowlist_start, windowlist_end, station_names, channel_names)


    def process_whole(self, windowlist_start, window_list_end, station_names, channel_names):
        ''' Start the processing.

        Parameters
        ----------
        windowlist_start: list of :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start times of the windows to process.

        station_names : list of Strings
            The names of the stations to process.

        channel_names : list of Strings
            The names of the channels to process.

        window_length : float
            The length of the sliding windwow in seconds.
        '''
        # Check and create the output directory.
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Get the channels to process.
        channels = []
        for cur_station in station_names:
            cur_name, cur_net, cur_loc = cur_station.split(':')
            for cur_channel in channel_names:
                channels.extend(self.project.geometry_inventory.get_channel(station = cur_name,
                                                                            network = cur_net,
                                                                            location = cur_loc,
                                                                            name = cur_channel))
        try:
            db_session = self.project.getDbSession()
            t_traceheader = self.project.dbTables['traceheader']
            for k, cur_window_start in enumerate(windowlist_start):
                cur_window_end = window_list_end[k]
                self.availability = {}
                for cur_channel in channels:
                    # Get the streams assigned to the channel for the requested
                    # time-span.
                    assigned_streams = cur_channel.get_stream(start_time = cur_window_start,
                                                              end_time = cur_window_end)

                    if len(assigned_streams) == 0:
                        self.logger.warning("No assigned streams found for SCNL %s.", cur_channel.scnl_string)

                    headers = []
                    for cur_timebox in assigned_streams:
                        cur_rec_stream = cur_timebox.item

                        # Get the database data for the given scnl and time-span.
                        query = db_session.query(t_traceheader)
                        query = query.filter(t_traceheader.recorder_serial == cur_rec_stream.serial)
                        query = query.filter(t_traceheader.stream == cur_rec_stream.name)
                        query = query.filter(t_traceheader.begin_time + old_div(t_traceheader.numsamp * 1,t_traceheader.sps) > cur_timebox.start_time.timestamp)
                        query = query.filter(t_traceheader.begin_time + old_div(t_traceheader.numsamp * 1,t_traceheader.sps) > cur_window_start.timestamp)
                        if cur_timebox.end_time:
                            query = query.filter(t_traceheader.begin_time < cur_timebox.end_time.timestamp)
                        query = query.filter(t_traceheader.begin_time < cur_window_end.timestamp)
                        headers.extend(query.all())

                    self.compute_availability(channel = cur_channel,
                                              traceheaders = headers,
                                              start_time = cur_window_start,
                                              end_time = cur_window_end)

                self.plot_availability(channels = channels,
                                       start_time = cur_window_start,
                                       end_time = cur_window_end)
        finally:
            # Add the time-span directory to the output directory.
            #if k != len(catalog.events) - 1:
            #    cur_end_time = cur_event.end_time
            #else:
            #    cur_end_time = end_time
            #timespan_dir = start_time.strftime('%Y%m%dT%H%M%S') + '_to_' + cur_end_time.strftime('%Y%m%dT%H%M%S')
            #cur_output_dir = os.path.join(self.output_dir, timespan_dir)
            # Save the processing results to files.
            #result_bag.save(output_dir = cur_output_dir, scnl = scnl)
            pass



    def compute_availability(self, channel, traceheaders, start_time, end_time, gap_limit = 1):
        ''' Compute the data availability for a given time span.
        '''

        self.logger.info("Computing the availability from %s to %s.", start_time.isoformat(), end_time.isoformat())
        if len(traceheaders) > 0:
            traceheaders = sorted(traceheaders, key = lambda x: x.begin_time)
            header_start = np.array([UTCDateTime(x.begin_time) for x in traceheaders])
            header_end = np.array([UTCDateTime(x.begin_time) + old_div((x.numsamp - 1) * 1,x.sps) for x in traceheaders])
            gap = header_start[1:] - header_end[:-1] - np.array([old_div(1,x.sps) for x in traceheaders])[1:]
            gap = np.append([0], gap)

            # TODO: handle overlapping data.
            overlap = gap.copy()
            overlap[overlap > 0] = 0

            gap[gap < 0] = 0
            gap_start = header_start - gap

            time = np.insert(header_end, np.arange(len(header_start)), header_start)
            time = np.insert(time, np.arange(2, len(time) - 1, 2), gap_start[1:])
            time = np.insert(time, np.arange(3, len(time) - 1, 3), gap_start[1:] + gap[1:])

            has_data = np.zeros(len(time))
            has_data[::4] = 1
            has_data[1::4] = 1

            if time[0] > start_time:
                time = np.append([start_time, time[0]], time)
                has_data = np.append([0,0], has_data)

            if time[-1] < end_time:
                time = np.append(time, [time[-1], end_time])
                has_data = np.append(has_data, [0, 0])

        else:
            time = np.array([start_time, end_time])
            has_data = np.array([0, 0])

        self.availability[channel.scnl] = np.vstack([time, has_data])


    def plot_availability(self, channels, start_time, end_time):
        channels = channels[::-1]
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)

        for k, cur_channel in enumerate(channels):
            cur_time = self.availability[cur_channel.scnl][0]
            cur_time = [x.datetime for x in cur_time]
            cur_has_data = self.availability[cur_channel.scnl][1]
            cur_data_ok = np.ma.array(np.zeros(cur_has_data.shape), mask = cur_has_data == False)
            cur_data_bad = np.ma.array(np.zeros(cur_has_data.shape), mask = cur_has_data == True)
            ax.plot(cur_time, cur_data_ok + k, 'k', linewidth = 1, solid_capstyle = 'butt')
            ax.plot(cur_time, cur_data_bad + k, 'r', linewidth = 10, solid_capstyle = 'butt')

        ax.set_yticks(np.arange(len(channels)))
        xtick_labels = [x.scnl_string for x in channels]
        ax.set_yticklabels(xtick_labels)
        ax.set_xlabel('time')
        ax.set_xlim((start_time.datetime, end_time.datetime))

        plot_length = end_time - start_time
        plot_length_days = old_div(plot_length, 86400)
        if plot_length_days > 14 and plot_length_days < 70:
            ax.xaxis.set_major_locator(mpl.dates.WeekdayLocator())
            ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%Y-%m-%d'))

        #ax.set_title('data availability week {0:s}-{1:04d}'.format(start_time.strftime('%W'), start_time.year))
        # TODO: Add the time information to the title.
        ax.set_title('data availability {0:s} - {1:s}'.format(start_time.isoformat(), end_time.isoformat()))
        fig.tight_layout()

        fig_filename = 'data_availability_{0:s}_{1:s}.png'.format(start_time.strftime('%Y%m%d_%H%M%S'),
                                                            end_time.strftime('%Y%m%d_%H%M%S'))
        fig_filename = os.path.join(self.output_dir, fig_filename)
        self.logger.info("Saving availability file to %s.", fig_filename)
        fig.savefig(fig_filename, dpi = 300)
        fig.clear()
        del fig


