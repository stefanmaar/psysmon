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

import os
import copy
import logging
import psysmon
from psysmon.core.packageNodes import CollectionNode
import obspy.core
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack
from psysmon.core.processingStack import ResultBag



## Documentation for class WindowProcessorNode
# 
# 
class SlidingWindowProcessorNode(CollectionNode):

    name = 'sliding window processor'
    mode = 'editable'
    category = 'Process'
    tags = ['stable',]

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

        #self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_processing_stack_preferences()
        self.create_output_preferences()


    def edit(self):
        # Initialize the available processing nodes.
        processing_nodes = self.project.getProcessingNodes((self.__class__.__name__, 'common'))
        if self.pref_manager.get_value('processing_stack') is None:
                detrend_node_template = [x for x in processing_nodes if x.name == 'detrend'][0]
                detrend_node = copy.deepcopy(detrend_node_template)
                self.pref_manager.set_value('processing_stack', [detrend_node, ])
        self.pref_manager.set_limit('processing_stack', processing_nodes)

        # Initialize the components.
        # TODO: Make the station selection SNL coded.
        if self.project.geometry_inventory:
            stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
            self.pref_manager.set_limit('stations', stations)

            channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
            self.pref_manager.set_limit('channels', channels)

        # Create the edit dialog.
        dlg = ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput={}):
        processing_stack = ProcessingStack(name = 'pstack',
                                           project = self.project,
                                           nodes = self.pref_manager.get_value('processing_stack'),
                                           parent = self)

        # Get the output directory from the pref_manager. If no directory is
        # specified create one based on the node resource id.
        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        processor = SlidingWindowProcessor(project = self.project,
                                           processing_stack = processing_stack,
                                           output_dir = output_dir,
                                           parent_rid = self.rid)


        # Compute the processing intervals.
        output_interval = self.pref_manager.get_value('output_interval')
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        seconds_per_day = 86400
        interval_start = [start_time, ]
        interval_end = []
        if output_interval == 'daily':
            interval = seconds_per_day
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + interval
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day)
            n_intervals = (int_end - int_start) / interval
            interval_start.extend([int_start + x * interval for x in range(0, int(n_intervals))])
        elif output_interval == 'weekly':
            interval = seconds_per_day*7
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + (6 - start_time.weekday) * seconds_per_day
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day) - end_time.weekday * seconds_per_day
            n_intervals = (int_end - int_start) / interval
            interval_start.extend([int_start + x * interval for x in range(0, int(n_intervals))])
        elif output_interval == 'monthly':
            start_year = start_time.year
            start_month = start_time.month + 1
            if start_month > 12:
                start_year = start_year + 1
                start_month = 1
            end_year = end_time.year
            end_month = end_time.month

            month_dict = {}
            year_list = range(start_year, end_year + 1)
            for k, cur_year in enumerate(year_list):
                if k == 0:
                    month_dict[year_list[0]] = range(start_month, end_month)
                elif k == len(year_list) - 1:
                    month_dict[year_list[0]] = range(1, end_month)
                else:
                    month_dict[year_list[0]] = range(1, 12)

            for cur_year, month_list in month_dict.iteritems():
                for cur_month in month_list:
                    interval_start.append(UTCDateTime(year = cur_year, month = cur_month))

        interval_start.append(end_time)


        for k, cur_start_time in enumerate(interval_start[:-1]):
            processor.process(start_time = cur_start_time,
                              end_time = interval_start[k+1],
                              station_names = self.pref_manager.get_value('stations'),
                              channel_names = self.pref_manager.get_value('channels'),
                              window_length = self.pref_manager.get_value('window_length'),
                              overlap = self.pref_manager.get_value('window_overlap'))




    def create_component_selector_preferences(self):
        ''' Create the preference items of the component selection section.

        '''
        self.pref_manager.add_page('components')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'process time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).',
                                           position = 1)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           group = 'process time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).',
                                           position = 2)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        item = psy_pm.IntegerSpinPrefItem(name = 'window_length',
                                          label = 'window length [s]',
                                          group = 'process time span',
                                          value = 300,
                                          limit = [0, 86400],
                                          tool_tip = 'The sliding window length in seconds.',
                                          position = 3)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        item = psy_pm.IntegerSpinPrefItem(name = 'window_overlap',
                                          label = 'window overlap [%]',
                                          group = 'process time span',
                                          value = 50,
                                          limit = [0, 99],
                                          tool_tip = 'The overlap of two successive sliding windows in percent.',
                                          position = 4)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)


        # The stations to process.
        item = psy_pm.MultiChoicePrefItem(name = 'stations',
                                          label = 'stations',
                                          group = 'components to process',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the processing.',
                                          position = 1)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        # The channels to process.
        item = psy_pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          group = 'components to process',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the processing.',
                                          position = 2)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)


    def create_processing_stack_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        self.pref_manager.add_page('processing stack')

        item = psy_pm.CustomPrefItem(name = 'processing_stack',
                                     label = 'processing stack',
                                     group = 'time window processing',
                                     value = None,
                                     gui_class = PStackEditField,
                                     tool_tip = 'Edit the processing stack nodes.')
        self.pref_manager.add_item(pagename = 'processing stack',
                                   item = item)


    def create_output_preferences(self):
        ''' Create the preference items of the output section.

        '''
        self.pref_manager.add_page('output')

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        group = 'output',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the processing results.'
                                       )
        self.pref_manager.add_item(pagename = 'output',
                                   item = item)

        item = psy_pm.SingleChoicePrefItem(name = 'output_interval',
                                          label = 'output interval',
                                          group = 'output',
                                          limit = ('daily', 'weekly', 'monthly'),
                                          value = 'monthly',
                                          tool_tip = 'The interval for which to save the results.')
        self.pref_manager.add_item(pagename = 'output',
                                   item = item)




class SlidingWindowProcessor(object):

    def __init__(self, project, output_dir, processing_stack = None, parent_rid = None):
        ''' Initialize the instance.

        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.project = project

        self.processing_stack = processing_stack

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



    #@profile(immediate=True)
    def process(self, start_time, end_time, station_names, channel_names, window_length, overlap):
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

        overlap : float
            The overlap of the window in percent.
        '''
        self.logger.info("Processing timespan %s to %s.", start_time.isoformat(), end_time.isoformat())

        window_length = float(window_length)
        overlap = 1 - float(overlap) / 100.

        result_bag = ResultBag()

        # Get the channels to process.
        channels = []
        for cur_station in station_names:
            for cur_channel in channel_names:
                channels.extend(self.project.geometry_inventory.get_channel(station = cur_station,
                                                                            name = cur_channel))
        scnl = [x.scnl for x in channels]


        # TODO: Compute the start times of the sliding windows.
        windowlist_start = [start_time, ]
        n_windows = (end_time - start_time) / (window_length * overlap)
        windowlist_start = [start_time + x * (window_length * overlap) for x in range(0, int(n_windows))]

        try:
            for k, cur_window_start in enumerate(windowlist_start):
                self.logger.info("Processing sliding window %d/%d.", k, n_windows)

                self.logger.info("Initial stream request for time-span: %s to %s.", cur_window_start.isoformat(),
                                                                                    (cur_window_start + window_length).isoformat())
                stream = self.request_stream(start_time = cur_window_start,
                                             end_time = cur_window_start + window_length,
                                             scnl = scnl)

                # Execute the processing stack.
                resource_id = self.parent_rid + '/time_window/' + cur_window_start.isoformat() + '-' + (cur_window_start+window_length).isoformat()
                process_limits = (cur_window_start, cur_window_start + window_length)
                self.processing_stack.execute(stream = stream,
                                              process_limits = process_limits,
                                              origin_resource = resource_id)

                # Put the results of the processing stack into the results bag.
                results = self.processing_stack.get_results()

                # TODO: Add a field to the processing node edit dialog to
                # select the formats in which the result should be saved.
                # Be sure to distinguish between results that can be combined
                # in a list (e.g. value results), or those, that provide a
                # single output format (like the grid_2d result).
                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)

                for cur_result in results:
                    cur_result.save(formats = ['ascii_grid',], output_dir = self.output_dir)
                #resource_id = self.project.rid + cur_event.rid
                #result_bag.add(resource_id = resource_id,
                #                    results = results)

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


    def request_stream(self, start_time, end_time, scnl):
        ''' Request a data stream from the waveclient.

        '''
        data_sources = {}
        for cur_scnl in scnl:
            if cur_scnl in self.project.scnlDataSources.keys():
                if self.project.scnlDataSources[cur_scnl] not in data_sources.keys():
                    data_sources[self.project.scnlDataSources[cur_scnl]] = [cur_scnl, ]
                else:
                    data_sources[self.project.scnlDataSources[cur_scnl]].append(cur_scnl)
            else:
                if self.project.defaultWaveclient not in data_sources.keys():
                    data_sources[self.project.defaultWaveclient] = [cur_scnl, ]
                else:
                    data_sources[self.project.defaultWaveclient].append(cur_scnl)

        stream = obspy.core.Stream()

        for cur_name in data_sources.iterkeys():
            curWaveclient = self.project.waveclient[cur_name]
            curStream =  curWaveclient.getWaveform(startTime = start_time,
                                                   endTime = end_time,
                                                   scnl = scnl)
            stream += curStream

        return stream
