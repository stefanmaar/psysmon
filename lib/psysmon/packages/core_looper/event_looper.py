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
from __future__ import division

#from profilehooks import profile

from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import json
import os
import copy
import logging

import numpy as np
import psysmon
import psysmon.core.packageNodes as package_nodes
import obspy.core
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.json_util as json_util
#from psysmon.core.processingStack import ResultBag
import psysmon.packages.event.core as event_core

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.core.gui_preference_dialog as gui_preference_dialog
    import psysmon.packages.event.plugins_event_selector as plugins_event_selector
    
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
        self.create_filter_preferences()
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
            channels = sorted([x.scnl for x in self.project.geometry_inventory.get_channel()])
            self.pref_manager.set_limit('scnl_list', channels)

        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        self.on_select_individual()

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

        processor = EventProcessor(project = self.project,
                                   output_dir = output_dir,
                                   parent_rid = self.rid)

        if self.pref_manager.get_value('select_individual') is True:
            events = self.pref_manager.get_value('events')
            event_ids = [x.id for x in events]
        else:
            event_ids = None

        if self.parentCollection.runtime_att.start_time:
            start_time = self.parentCollection.runtime_att.start_time
        else:
            start_time = self.pref_manager.get_value('start_time')

        if self.parentCollection.runtime_att.end_time:
            end_time = self.parentCollection.runtime_att.end_time
        else:
            end_time = self.pref_manager.get_value('end_time')

        event_tags = self.pref_manager.get_value('event_tag')
        if event_tags:
            event_tags = [event_tags,]
        else:
            event_tags = None


        processor.process(looper_nodes = self.children,
                          start_time = start_time,
                          end_time = end_time,
                          processing_interval = self.pref_manager.get_value('processing_interval'),
                          scnl = self.pref_manager.get_value('scnl_list'),
                          event_catalog = self.pref_manager.get_value('event_catalog'),
                          event_ids = event_ids,
                          event_types = self.pref_manager.get_value('event_type'),
                          event_tags = event_tags)




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

        # Check for headless option when assigning the GUI class to the custom field.
        if psysmon.wx_available:
            gui_class = plugins_event_selector.EventListField
        else:
            gui_class = None
        item = psy_pm.CustomPrefItem(name = 'events',
                                     label = 'events',
                                     value = [],
                                     gui_class = gui_class,
                                     tool_tip = 'The available events. Selected events will be used for processing.')
        event_group.add_item(item)


    def create_component_selector_preferences(self):
        ''' Create the preference items of the component selection section.

        '''
        components_page = self.pref_manager.add_page('components')
        comp_to_process_group = components_page.add_group('components to process')

        # The SCNL list
        pref_item = psy_pm.ListCtrlEditPrefItem(name = 'scnl_list',
                                           label = 'SCNL',
                                           value = [],
                                           column_labels = ['station', 'channel', 'network', 'location'],
                                           tool_tip = 'Select the components to process.'
                                          )
        comp_to_process_group.add_item(pref_item)



    def create_filter_preferences(self):
        ''' Create the filter preferences.
        '''
        pref_page = self.pref_manager.add_page('Filter')
        type_group = pref_page.add_group('type')
        tag_group = pref_page.add_group('tag')

        # TODO: Add a more advanced filter options providing the possibility of
        # combinig multiple values with logical operators.

        # The event types to search for.
        item = psy_pm.MultiChoicePrefItem(name = 'event_type',
                                           label = 'event type',
                                           limit = (),
                                           value = [],
                                           tool_tip = 'The event types to load.')
        type_group.add_item(item)

        # The event tags to search for.
        item = psy_pm.TextEditPrefItem(name = 'event_tag',
                                       label = 'event tag',
                                       value = '',
                                       tool_tip = 'The tag to search for.')
        tag_group.add_item(item)



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
            n_intervals = old_div((int_end - int_start), length)
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        if interval == 'day':
            length = seconds_per_day
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + length
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day)
            n_intervals = old_div((int_end - int_start), length)
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        elif interval == 'week':
            length = seconds_per_day*7
            int_start = UTCDateTime(start_time.year, start_time.month, start_time.day) + (6 - start_time.weekday) * seconds_per_day
            int_end = UTCDateTime(end_time.year, end_time.month, end_time.day) - end_time.weekday * seconds_per_day
            n_intervals = old_div((int_end - int_start), length)
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
            year_list = list(range(start_year, end_year + 1))
            for k, cur_year in enumerate(year_list):
                if k == 0:
                    month_dict[year_list[0]] = list(range(start_month, end_month))
                elif k == len(year_list) - 1:
                    month_dict[year_list[0]] = list(range(1, end_month))
                else:
                    month_dict[year_list[0]] = list(range(1, 12))

            for cur_year, month_list in month_dict.items():
                for cur_month in month_list:
                    interval_start.append(UTCDateTime(year = cur_year, month = cur_month))

        interval_start.append(end_time)
        return interval_start


    #@profile(immediate=True)
    def process(self, looper_nodes, start_time, end_time, processing_interval,
                scnl, event_catalog, event_ids = None,
                event_types = None, event_tags = None):
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

        scnl : list of Strings
            The scnl codes of the components to process.

        event_catalog : String
            The name of the event catalog to process.

        event_ids : List of Integer
            If individual events are specified, this list contains the database IDs of the events
            to process.
        '''
        self.logger.info("Processing whole timespan %s to %s.", start_time.isoformat(), end_time.isoformat())

        # Use only the enabled looper nodes.
        looper_nodes = [x for x in looper_nodes if x.enabled]

        if not looper_nodes:
            self.logger.warning("No looper nodes found.")
            return

        if event_tags is None:
            event_tags = []

        if event_types is None:
            event_types = []


        interval_start = self.compute_intervals(start_time = start_time,
                                                end_time = end_time,
                                                interval = processing_interval)

        event_lib = event_core.Library('events')
        event_lib.load_catalog_from_db(self.project, name = event_catalog)
        catalog = event_lib.catalogs[event_catalog]

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
                                    min_event_length = 1,
                                    event_tags = event_tags)
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
                continue

            # Get the channels to process.
            channels = []
            #for cur_station in station_names:
            #    for cur_channel in channel_names:
            #        channels.extend(self.project.geometry_inventory.get_channel(station = cur_station,
            #                                                                    name = cur_channel))
            for cur_scnl in scnl:
                channels.extend(self.project.geometry_inventory.get_channel(network=cur_scnl[2],
                                                                            station=cur_scnl[0],
                                                                            location=cur_scnl[3],
                                                                            name=cur_scnl[1]))
            scnl = [x.scnl for x in channels]

            n_events = len(catalog.events)
            try:
                for k, cur_event in enumerate(sorted(catalog.events, key = lambda x: x.start_time)):
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

                    cur_window_start = cur_event.start_time
                    cur_window_end = cur_event.end_time


                    # Execute the looper nodes.
                    resource_id = self.parent_rid + '/event_processor/' + str(cur_event.db_id)
                    process_limits = (cur_window_start, cur_window_end)
                    waveform_loaded = False
                    stream = None
                    for cur_node in looper_nodes:
                        if not cur_node.initialized:
                            cur_node.initialize()

                        # Load the waveform data when it is needed by a looper
                        # node.
                        if not waveform_loaded and cur_node.need_waveform_data:
                            stream = self.project.request_data_stream(start_time=cur_window_start-pre_event_length,
                                                                      end_time=cur_window_end+post_event_length,
                                                                      scnl=scnl)
                            waveform_loaded = True


                        self.logger.debug("Executing node %s.", cur_node.name)
                        ret = cur_node.execute(stream = stream,
                                               process_limits = process_limits,
                                               origin_resource = resource_id,
                                               channels = channels,
                                               event = cur_event)

                        self.logger.debug("Finished execution of node %s.", cur_node.name)

                        # Get the results of the node.
                        if cur_node.result_bag:
                            if len(cur_node.result_bag.results) > 0:
                                for cur_result in cur_node.result_bag.results:
                                    cur_result.event_id = cur_event.db_id
                                    cur_result.base_output_dir = self.output_dir
                                    cur_result.save()

                                cur_node.result_bag.clear()

                        # Handle the looper child return value.
                        if ret and ret == 'abort':
                            break
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

        # Save the collection settings to the result directory if it exists.
        if os.path.exists(self.output_dir):
            exec_meta = {}
            exec_meta['rid'] = self.parent_rid
            exec_meta['node_settings'] = looper_nodes[0].parent.get_settings()
            settings_filename = 'execution_metadata.json'
            settings_filepath = os.path.join(self.output_dir, settings_filename)
            with open(settings_filepath, 'w') as fp:
                json.dump(exec_meta,
                          fp = fp,
                          cls = json_util.GeneralFileEncoder)
