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
import psysmon.core.packageNodes as package_nodes
import obspy.core
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.result import ResultBag


## Documentation for class WindowProcessorNode
# 
# 
class TimeWindowLooperNode(package_nodes.LooperCollectionNode):

    name = 'time window looper'
    mode = 'looper'
    category = 'Batch processing'
    tags = ['stable', 'looper']

    def __init__(self, **args):
        package_nodes.LooperCollectionNode.__init__(self, **args)

        #self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_output_preferences()


    def edit(self):
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
        # Get the output directory from the pref_manager. If no directory is
        # specified create one based on the node resource id.
        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        processor = SlidingWindowProcessor(project = self.project,
                                           output_dir = output_dir,
                                           parent_rid = self.rid)

        processor.process(looper_nodes = self.children,
                          start_time = self.pref_manager.get_value('start_time'),
                          end_time = self.pref_manager.get_value('end_time'),
                          station_names = self.pref_manager.get_value('stations'),
                          channel_names = self.pref_manager.get_value('channels'),
                          window_length = self.pref_manager.get_value('window_length'),
                          overlap = self.pref_manager.get_value('window_overlap'))



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

        item = psy_pm.IntegerSpinPrefItem(name = 'window_length',
                                          label = 'window length [s]',
                                          value = 300,
                                          limit = [0, 86400],
                                          tool_tip = 'The sliding window length in seconds.')
        process_time_span_group.add_item(item)

        item = psy_pm.IntegerSpinPrefItem(name = 'window_overlap',
                                          label = 'window overlap [%]',
                                          value = 50,
                                          limit = [0, 99],
                                          tool_tip = 'The overlap of two successive sliding windows in percent.')
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


    def create_processing_stack_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        ps_page = self.pref_manager.add_page('processing stack')
        tw_group = ps_page.add_group('time window processing')

        item = psy_pm.CustomPrefItem(name = 'processing_stack',
                                     label = 'processing stack',
                                     value = None,
                                     gui_class = PStackEditField,
                                     tool_tip = 'Edit the processing stack nodes.')
        tw_group.add_item(item)


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


        item = psy_pm.SingleChoicePrefItem(name = 'output_interval',
                                          label = 'output interval',
                                          limit = ('daily', 'weekly', 'monthly'),
                                          value = 'monthly',
                                          tool_tip = 'The interval for which to save the results.')
        output_group.add_item(item)



class SlidingWindowProcessor(object):

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



    #@profile(immediate=True)
    def process(self, looper_nodes, start_time, end_time, station_names, channel_names, window_length, overlap):
        ''' Start the processing.

        Parameters
        ----------
        looper_nodes : list of
            The looper nodes to execute.

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


        # Compute the start times of the sliding windows.
        windowlist_start = [start_time, ]
        n_windows = (end_time - start_time) / (window_length * overlap)
        windowlist_start = [start_time + x * (window_length * overlap) for x in range(0, int(n_windows))]

        try:
            for k, cur_window_start in enumerate(windowlist_start):
                # Get the pre- and post timewindow time required by the looper
                # children. The pre- and post timewindow times could be needed because
                # of effects due to filter buildup.
                pre_stream_length = [x.pre_stream_length for x in looper_nodes]
                post_stream_length = [x.post_stream_length for x in looper_nodes]
                pre_stream_length = max(pre_stream_length)
                post_stream_length = max(post_stream_length)

                self.logger.info("Processing sliding window %d/%d.", k, n_windows)

                self.logger.info("Initial stream request for time-span: %s to %s.", cur_window_start.isoformat(),
                                                                                    (cur_window_start + window_length).isoformat())
                stream = self.request_stream(start_time = cur_window_start - pre_stream_length,
                                             end_time = cur_window_start + window_length + post_stream_length,
                                             scnl = scnl)

                # Execute the looper nodes.
                resource_id = self.parent_rid + '/time_window/' + cur_window_start.isoformat() + '-' + (cur_window_start+window_length).isoformat()
                process_limits = (cur_window_start, cur_window_start + window_length)
                for cur_node in looper_nodes:
                    if k == 0:
                        # TODO: Call the reset method of the node.
                        try:
                            cur_node.sculpture_layer = None
                        except:
                            pass
                    cur_node.execute(stream = stream,
                                     process_limits = process_limits,
                                     origin_resource = resource_id)
                    # Get the results of the node.
                    if cur_node.result_bag:
                        for cur_result in cur_node.result_bag.results:
                            cur_result.save(output_dir = self.output_dir)


                # Handle the results.

                # Put the results of the processing stack into the results bag.
                #results = self.processing_stack.get_results()

                # TODO: Add a field to the processing node edit dialog to
                # select the formats in which the result should be saved.
                # Be sure to distinguish between results that can be combined
                # in a list (e.g. value results), or those, that provide a
                # single output format (like the grid_2d result).
                #if not os.path.exists(self.output_dir):
                #    os.makedirs(self.output_dir)

                #for cur_result in results:
                #    cur_result.save(formats = ['ascii_grid',], output_dir = self.output_dir)
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
