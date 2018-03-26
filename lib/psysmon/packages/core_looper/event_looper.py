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
The event looper.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classes of the importWaveform dialog window.
'''

#from profilehooks import profile

import os
import copy
import logging

import numpy as np
import psysmon
import psysmon.core.packageNodes as package_nodes
import obspy.core
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.packages.event.plugins_event_selector import EventListField
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack
#from psysmon.core.processingStack import ResultBag
import psysmon.packages.event.core as event_core



## Documentation for class importWaveform
# 
# 
class EventLooperNode(package_nodes.LooperCollectionNode):

    name = 'event looper'
    mode = 'looper'
    category = 'Batch processing'
    tags = ['stable', 'looper']

    def __init__(self, **args):
        package_nodes.LooperCollectionNode.__init__(self, **args)

        # The event catalog library
        self.event_library = event_core.Library('binder')

        self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_processing_preferences()
        self.create_output_preferences()


    def edit(self):
        # Initialize the event catalog preference item.
        catalog_names = sorted(self.event_library.get_catalogs_in_db(self.project))
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('event_catalog') not in catalog_names:
                self.pref_manager.set_value('event_catalog', catalog_names[0])

        # Initialize the components.
        if self.project.geometry_inventory:
            stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
            self.pref_manager.set_limit('stations', stations)

            channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
            self.pref_manager.set_limit('channels', channels)

        # Create the edit dialog.
        dlg = ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput={}):
        # Get the output directory from the pref_manager. If no directory is
        # specified create one based on the node resource id.
        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        processor = EventProcessor(project = self.project,
                                   output_dir = output_dir,
                                   parent_rid = self.rid)

        if self.pref_manager.get_value('select_individual') is True:
            events = self.pref_manager.get_value('events')
            event_ids = [x.id for x in events]
        else:
            event_ids = None

        processor.process(looper_nodes = self.children,
                          start_time = self.pref_manager.get_value('start_time'),
                          end_time = self.pref_manager.get_value('end_time'),
                          processing_interval = self.pref_manager.get_value('processing_interval'),
                          station_names = self.pref_manager.get_value('stations'),
                          channel_names = self.pref_manager.get_value('channels'),
                          event_catalog = self.pref_manager.get_value('event_catalog'),
                          event_ids = event_ids)




    def create_selector_preferences(self):
        ''' Create the preference items of the event selection section.
        '''
        events_page = self.pref_manager.add_page('events')
        time_group = events_page.add_group('time span')
        event_group = events_page.add_group('event selection')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        time_group.add_item(item)

        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        time_group.add_item(item)

        item = psy_pm.SingleChoicePrefItem(name = 'event_catalog',
                                          label = 'event catalog',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select an event catalog for which to load the events.')
        event_group.add_item(item)

        item = psy_pm.CheckBoxPrefItem(name = 'select_individual',
                                       label = 'select individual events',
                                       value = False,
                                       tool_tip = 'Do a manual selection of the events to process.',
                                       hooks = {'on_value_change': self.on_select_individual})
        event_group.add_item(item)

        item = psy_pm.ActionItem(name = 'load_events',
                                 label = 'load events',
                                 mode = 'button',
                                 action = self.on_load_events,
                                 tool_tip = 'Load events from the database.')
        event_group.add_item(item)

        item = psy_pm.CustomPrefItem(name = 'events',
                                     label = 'events',
                                     value = [],
                                     gui_class = EventListField,
                                     tool_tip = 'The available events. Selected events will be used for processing.')
        event_group.add_item(item)


    def create_component_selector_preferences(self):
        ''' Create the preference items of the component selection section.

        '''
        components_page = self.pref_manager.add_page('components')
        comp_to_process_group = components_page.add_group('components to process')

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



    def create_processing_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        ps_page = self.pref_manager.add_page('processing')
        mode_group = ps_page.add_group('mode')

        item = psy_pm.SingleChoicePrefItem(name = 'processing_interval',
                                          label = 'processing interval',
                                          limit = ('hour', 'day', 'week', 'month', 'whole'),
                                          value = 'day',
                                          tool_tip = 'The interval of the processing.')
        mode_group.add_item(item)


    def on_load_events(self, event):
        ''' Handle a click on the load_events ActionItem Button.
        '''
        # TODO: The looper node can't be deep-copied when executing, if events have been
        # loaded.
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        catalog_name = self.pref_manager.get_value('event_catalog')
        self.event_library.load_catalog_from_db(project = self.project,
                                                name = catalog_name)
        event_catalog = self.event_library.catalogs[catalog_name]
        event_catalog.load_events(project = self.project,
                                  start_time = start_time,
                                  end_time = end_time)


        pref_item = self.pref_manager.get_item('events')[0]
        field = pref_item.gui_element[0]
        field.set_events(event_catalog.events)


    def on_select_individual(self):
        if self.pref_manager.get_value('select_individual') is True:
            self.pref_manager.get_item('events')[0].enable_gui_element()
            self.pref_manager.get_item('load_events')[0].enable_gui_element()
        else:
            self.pref_manager.get_item('events')[0].disable_gui_element()
            self.pref_manager.get_item('load_events')[0].disable_gui_element()




class EventProcessor(object):

    def __init__(self, project, output_dir, parent_rid = None):
        ''' Initialize the instance.

        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.project = project

        # The timespan for which waveform data is available.
        self.active_timespan = ()

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


    def compute_intervals(self, start_time, end_time, interval):
        ''' Compute the processing interval times.

        Parameters
        ----------
        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan for which to detect the events.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan for which to detect the events.

        interval : String or Float
            The interval which is used to handle a set of events. If a float is
            passed, it is interpreted as the inteval length in seconds.
            (whole, hour, day, week, month or a float value)
        '''
        seconds_per_day = 86400
        interval_start = [start_time, ]
        interval = interval.lower()
        if interval == 'hour':
            length = 3600
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + length
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day)
            n_intervals = (int_end - int_start) / length
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        if interval == 'day':
            length = seconds_per_day
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + length
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day)
            n_intervals = (int_end - int_start) / length
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        elif interval == 'week':
            length = seconds_per_day*7
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + (6 - start_time.weekday) * seconds_per_day
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day) - end_time.weekday * seconds_per_day
            n_intervals = (int_end - int_start) / length
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        elif interval == 'month':
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
        return interval_start


    #@profile(immediate=True)
    def process(self, looper_nodes, start_time, end_time, processing_interval,
                station_names, channel_names, event_catalog, event_ids = None):
        ''' Start the detection.

        Parameters
        ----------
        looper_nodes : list of
            The looper nodes to execute.

        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan for which to detect the events.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan for which to detect the events.

        processing_interval : String or Float
            The interval which is used to handle a set of events. If a float is
            passed, it is interpreted as the inteval length in seconds.
            (whole, hour, day, week, month or a float value)

        station_names : list of Strings
            The names of the stations to process.

        channel_names : list of Strings
            The names of the channels to process.

        event_catalog : String
            The name of the event catalog to process.

        event_ids : List of Integer
            If individual events are specified, this list contains the database IDs of the events
            to process.
        '''
        self.logger.info("Processing whole timespan %s to %s.", start_time.isoformat(), end_time.isoformat())

        if not looper_nodes:
            self.logger.warning("No looper nodes found.")
            return

        interval_start = self.compute_intervals(start_time = start_time,
                                                end_time = end_time,
                                                interval = processing_interval)

        event_lib = event_core.Library('events')
        event_lib.load_catalog_from_db(self.project, name = event_catalog)
        catalog = event_lib.catalogs[event_catalog]

        # Check if any of the looper nodes needs waveform data.
        waveform_needed = np.any([x.need_waveform_data for x in looper_nodes])

        for k, cur_start_time in enumerate(interval_start[:-1]):
            cur_end_time = interval_start[k + 1]
            self.logger.info("Processing interval timespan %s to %s.",
                             cur_start_time.isoformat(),
                             cur_end_time.isoformat())
            catalog.clear_events()

            if event_ids is None:
                # Load the events for the given time span from the database.
                # TODO: Remove the hardcoded min_event_length value and create
                # user-selectable filter fields.
                catalog.load_events(project = self.project,
                                    start_time = cur_start_time,
                                    end_time = cur_end_time,
                                    min_event_length = 1)
            else:
                # Load the events with the given ids from the database. Ignore the
                # time-span.
                catalog.load_events(event_id = event_ids)

            # Abort the execution if no events are available for the time span.
            if not catalog.events:
                if event_ids is None:
                    self.logger.info('No events found for the timespan %s to %s.', cur_start_time.isoformat(), cur_end_time.isoformat())
                else:
                    self.logger.info('No events found for the specified event IDs: %s.', event_ids)
                return

            # Get the channels to process.
            channels = []
            for cur_station in station_names:
                for cur_channel in channel_names:
                    channels.extend(self.project.geometry_inventory.get_channel(station = cur_station,
                                                                                name = cur_channel))
            scnl = [x.scnl for x in channels]

            n_events = len(catalog.events)
            try:
                for k, cur_event in enumerate(catalog.events):
                    self.logger.info("Processing event %d (%d/%d).", cur_event.db_id, k, n_events)

                    # Assign the channel instance to the detections.
                    cur_event.assign_channel_to_detections(self.project.geometry_inventory)

                    # Get the pre- and post timewindow time required by the looper
                    # children. The pre- and post timewindow times could be needed because
                    # of effects due to filter buildup.
                    pre_event_length = [x.pre_stream_length for x in looper_nodes]
                    post_event_length = [x.post_stream_length for x in looper_nodes]
                    pre_event_length = max(pre_event_length)
                    post_event_length = max(post_event_length)

                    cur_window_start = cur_event.start_time - pre_event_length
                    cur_window_end = cur_event.end_time + post_event_length

                    if waveform_needed:
                        stream = self.request_stream(start_time = cur_window_start,
                                                     end_time = cur_window_end,
                                                     scnl = scnl)
                    else:
                        stream = None


                    # Execute the looper nodes.
                    resource_id = self.parent_rid + '/event_processor/' + str(cur_event.db_id)
                    process_limits = (cur_window_start, cur_window_end)
                    for cur_node in looper_nodes:
                        if k == 0:
                            cur_node.initialize()

                        self.logger.debug("Executing node %s.", cur_node.name)
                        cur_node.execute(stream = stream,
                                         process_limits = process_limits,
                                         origin_resource = resource_id,
                                         channels = channels,
                                         event = cur_event)

                        self.logger.debug("Finished execution of node %s.", cur_node.name)

                        # Get the results of the node.
                        if cur_node.result_bag:
                            if len(cur_node.result_bag.results) > 0:
                                for cur_result in cur_node.result_bag.results:
                                    cur_result.base_output_dir = self.output_dir
                                    cur_result.save()

                                cur_node.result_bag.clear()
            finally:
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
