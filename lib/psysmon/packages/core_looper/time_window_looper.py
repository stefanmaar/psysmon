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

from builtins import str
from builtins import range
from builtins import object
import copy
import json
import logging
import os
from past.utils import old_div

import numpy as np
import psysmon
import psysmon.core.packageNodes as package_nodes
import obspy.core
import psysmon.core.json_util as json_util
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
        self.create_processing_preferences()


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
        dlg = ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the time-span elements depending on the 'set
        # collection time-span' collection node.
        if 'set collection time-span' in [x.name for x in self.parentCollection.nodes]:
            item = self.pref_manager.get_item('start_time')[0]
            item.disable_gui_element()
            item = self.pref_manager.get_item('end_time')[0]
            item.disable_gui_element()
        else:
            item = self.pref_manager.get_item('start_time')[0]
            item.enable_gui_element()
            item = self.pref_manager.get_item('end_time')[0]
            item.enable_gui_element()

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

        # Save the collection settings to the processor output
        # directory if it exists.
        # TODO: Place the creation of the execution metadata dictionary
        # to the CollectionNode class. 
        if os.path.exists(processor.output_dir):
            exec_meta = {}
            exec_meta['rid'] = self.rid
            exec_meta['execution_time'] = UTCDateTime().isoformat()
            exec_meta['node_settings'] = self.get_settings()
            settings_filename = 'execution_metadata.json'
            settings_filepath = os.path.join(processor.output_dir, settings_filename)
            with open(settings_filepath, 'w') as fp:
                json.dump(exec_meta,
                          fp = fp,
                          cls = json_util.GeneralFileEncoder)

        window_mode = self.pref_manager.get_value('window_mode')

        if self.parentCollection.runtime_att.start_time:
            start_time = self.parentCollection.runtime_att.start_time
        else:
            start_time = self.pref_manager.get_value('start_time')

        if self.parentCollection.runtime_att.end_time:
            end_time = self.parentCollection.runtime_att.end_time
        else:
            end_time = self.pref_manager.get_value('end_time')

        if window_mode == 'whole':
            window_length = end_time - start_time
            overlap = 0.
        elif window_mode == 'free':
            window_length = self.pref_manager.get_value('window_length')
            overlap = self.pref_manager.get_value('window_overlap')
        elif window_mode == 'daily':
            start_time = UTCDateTime(start_time.year, start_time.month, start_time.day)
            end_time = UTCDateTime(end_time.year, end_time.month, end_time.day)
            window_length = 86400.
            overlap = 0.
        elif window_mode == 'weekly':
            start_time = UTCDateTime(start_time.year, start_time.month, start_time.day) - start_time.weekday * 86400
            end_time = UTCDateTime(end_time.year, end_time.month, end_time.day) +  (7 - end_time.weekday) * 86400
            window_length = 86400. * 7
            overlap = 0.


        processor.process(looper_nodes = self.children,
                          start_time = start_time,
                          end_time = end_time,
                          station_names = self.pref_manager.get_value('stations'),
                          channel_names = self.pref_manager.get_value('channels'),
                          window_length = window_length,
                          overlap = overlap,
                          chunked = self.pref_manager.get_value('process_chunked'),
                          chunk_window_length = self.pref_manager.get_value('chunk_win_length'))

        return not processor.node_execution_error



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
                                           limit = ('free', 'daily', 'weekly', 'whole'),
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


    def create_processing_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        ps_page = self.pref_manager.add_page('processing')
        ch_group = ps_page.add_group('chunked')

        item = psy_pm.CheckBoxPrefItem(name = 'process_chunked',
                                       label = 'use chunked processing',
                                       value = False,
                                       tool_tip = 'For large time windows splitting the time window into smaller chunks is more memory efficient. Not all looper child nodes support chunked processing.')
        ch_group.add_item(item)

        item = psy_pm.IntegerSpinPrefItem(name = 'chunk_win_length',
                                          label = 'chunk window length [s]',
                                          value = 3600,
                                          limit = [0, 1209600],
                                          tool_tip = 'The length of the chunked window.')
        ch_group.add_item(item)



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

        self.node_execution_error = False

        if self.parent_rid is not None:
            rid_dir = self.parent_rid.replace('/', '-').replace(':', '-')
            if rid_dir.startswith('-'):
                rid_dir = rid_dir[1:]
            if rid_dir.endswith('-'):
                rid_dir = rid_dir[:-1]
            self.output_dir = os.path.join(output_dir, rid_dir)
        else:
            self.output_dir = output_dir

        # Create the output directory.
        os.makedirs(self.output_dir)



    #@profile(immediate=True)
    def process(self, looper_nodes, start_time, end_time, station_names, channel_names, window_length, overlap,
                chunked = False, chunk_window_length = None):
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
        overlap = float(overlap)

        # Check for correct argument values:
        if end_time <= start_time:
            self.logger.error("The end_time %s is smaller than the start_time %s.", end_time.isoformat(), start_time.isoformat())
            raise ValueError("The end_time %s is smaller than the start_time %s." % (end_time.isoformat(), start_time.isoformat()))

        if overlap >= 100:
            self.logger.error("Overlap %f is larger or equal to 100.", overlap)
            raise ValueError("Overlap %f is larger or equal to 100." % overlap)

        window_step = 1 - overlap / 100.

        # Compute the start times of the sliding windows.
        windowlist_start = [start_time, ]
        n_windows = old_div(np.floor(end_time - start_time), (window_length * window_step))
        windowlist_start = [start_time + x * (window_length * window_step) for x in range(0, int(n_windows))]

        try:
            if chunked:
                self.process_chunked(looper_nodes, windowlist_start, station_names,
                                     channel_names, window_length, chunk_window_length)
            else:
                self.process_whole(looper_nodes, windowlist_start, station_names, channel_names, window_length)
        finally:
            pass



    def process_chunked(self, looper_nodes, windowlist_start, station_names, channel_names, window_length, chunk_length):
        ''' Start the processing.

        Parameters
        ----------
        looper_nodes : list of
            The looper nodes to execute.

        windowlist_start: list of :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start times of the windows to process.

        station_names : list of Strings
            The names of the stations to process.

        channel_names : list of Strings
            The names of the channels to process.

        window_length : float
            The length of the sliding windwow in seconds.

        chunk_length : float
            The lenght of the chunk window in seconds.
        '''
        # Check if any of the looper nodes needs waveform data.
        waveform_needed = np.any([x.need_waveform_data for x in looper_nodes])

        # Get the channels to process.
        channels = []
        for cur_station in station_names:
            cur_name, cur_net, cur_loc = cur_station.split(':')
            for cur_channel in channel_names:
                channels.extend(self.project.geometry_inventory.get_channel(station = cur_name,
                                                                            network = cur_net,
                                                                            location = cur_loc,
                                                                            name = cur_channel))

        n_chunk_windows =  np.ceil(old_div(window_length, chunk_length))

        pre_stream_length = [x.pre_stream_length for x in looper_nodes]
        post_stream_length = [x.post_stream_length for x in looper_nodes]
        pre_stream_length = max(pre_stream_length)
        post_stream_length = max(post_stream_length)

        for cur_channel in channels:
            for k, cur_window_start in enumerate(windowlist_start):
                self.logger.info("Processing time window from %s to %s", cur_window_start, cur_window_start + window_length)
                chunk_windowlist = [cur_window_start, ]
                chunk_windowlist = [cur_window_start + x * chunk_length for x in range(0, int(n_chunk_windows))]

                for m, cur_chunk_start in enumerate(chunk_windowlist):
                    cur_chunk_end = cur_chunk_start + chunk_length
                    if cur_chunk_end > (cur_window_start + window_length):
                        cur_chunk_end = cur_window_start + window_length
                    self.logger.info("Processing chunk for %s from %s to %s.", cur_channel.scnl_string, cur_chunk_start, cur_chunk_end)


                    if waveform_needed:
                        stream = self.project.request_data_stream(start_time = cur_chunk_start - pre_stream_length,
                                                                  end_time = cur_chunk_end + post_stream_length,
                                                                  scnl = [cur_channel.scnl,])
                    else:
                        stream = None

                    # Execute the looper nodes.
                    resource_id = self.parent_rid + '/time_window/' + cur_window_start.isoformat() + '-' + (cur_window_start+window_length).isoformat()
                    process_limits = (cur_chunk_start, cur_chunk_end)
                    for cur_node in looper_nodes:
                        if k == 0:
                            # TODO: Call the reset method of the node.
                            try:
                                cur_node.sculpture_layer = None
                            except:
                                pass
                        cur_node.execute_chunked(chunk_count = m + 1,
                                                 total_chunks = len(chunk_windowlist),
                                                 stream = stream,
                                                 process_limits = process_limits,
                                                 origin_resource = resource_id)
                        # Get the results of the node.
                        if cur_node.result_bag:
                            if len(cur_node.result_bag.results) > 0:
                                for cur_result in cur_node.result_bag.results:
                                    cur_result.base_output_dir = self.output_dir
                                    cur_result.save()

                                cur_node.result_bag.clear()



    def process_whole(self, looper_nodes, windowlist_start, station_names, channel_names, window_length):
        ''' Start the processing.

        Parameters
        ----------
        looper_nodes : list of
            The looper nodes to execute.

        windowlist_start: list of :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start times of the windows to process.

        station_names : list of Strings
            The names of the stations to process.

        channel_names : list of Strings
            The names of the channels to process.

        window_length : float
            The length of the sliding windwow in seconds.
        '''
        n_windows = len(windowlist_start)

        # Check if any of the looper nodes needs waveform data.
        waveform_needed = np.any([x.need_waveform_data for x in looper_nodes])

        # Get the channels to process.
        channels = []
        for cur_station in station_names:
            cur_name, cur_net, cur_loc = cur_station.split(':')
            for cur_channel in channel_names:
                channels.extend(self.project.geometry_inventory.get_channel(station = cur_name,
                                                                            network = cur_net,
                                                                            location = cur_loc,
                                                                            name = cur_channel))
        scnl = [x.scnl for x in channels]
        try:
            for k, cur_window_start in enumerate(windowlist_start):
                # Get the pre- and post timewindow time required by the looper
                # children. The pre- and post timewindow times could be needed because
                # of effects due to filter buildup.
                pre_stream_length = [x.pre_stream_length for x in looper_nodes]
                post_stream_length = [x.post_stream_length for x in looper_nodes]
                pre_stream_length = max(pre_stream_length)
                post_stream_length = max(post_stream_length)

                self.logger.info("Processing sliding window %d/%d.", k+1, n_windows)

                if waveform_needed:
                    self.logger.info("Initial stream request for time-span: %s to %s for scnl: %s.", cur_window_start.isoformat(),
                                                                                        (cur_window_start + window_length).isoformat(),
                                                                                         str(scnl))
                    stream = self.project.request_data_stream(start_time = cur_window_start - pre_stream_length,
                                                              end_time = cur_window_start + window_length + post_stream_length,
                                                              scnl = scnl)
                    stream = stream.split()
                else:
                    stream = None

                # Execute the looper nodes.
                resource_id = self.parent_rid + '/time_window/' + cur_window_start.isoformat() + '-' + (cur_window_start+window_length).isoformat()
                process_limits = (cur_window_start, cur_window_start + window_length)

                try:
                    for cur_node in looper_nodes:
                        if not cur_node.initialized:
                            self.logger.debug("Initializing node %s.", cur_node.name)
                            cur_node.initialize(process_limits = process_limits,
                                                origin_resource = resource_id,
                                                channels = channels)
                            self.logger.debug("Finished the initialization.")

                        self.logger.debug("Executing node %s.", cur_node.name)
                        cur_node.execute(stream = stream,
                                         process_limits = process_limits,
                                         origin_resource = resource_id,
                                         channels = channels)
                        self.logger.debug("Finished execution of node %s.", cur_node.name)

                        # Get the results of the node.
                        if cur_node.result_bag:
                            if len(cur_node.result_bag.results) > 0:
                                self.logger.debug("Saving the results.")
                                for cur_result in cur_node.result_bag.results:
                                    cur_result.base_output_dir = self.output_dir
                                    cur_result.save()

                                cur_node.result_bag.clear()
                                self.logger.debug("Finished saving of the results.")
                except Exception:
                    self.node_execution_error = True
                    self.logger.exception("Error when executing a looper node. Skipping this time window.")


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

        # Call the cleanup method for all nodes.
        for cur_node in looper_nodes:
            cur_node.cleanup(origin_resource = resource_id)

            # Get the remaining results of the node and save them.
            if cur_node.result_bag:
                for cur_result in cur_node.result_bag.results:
                    cur_result.base_output_dir = self.output_dir
                    cur_result.save()

            cur_node.result_bag.clear()

