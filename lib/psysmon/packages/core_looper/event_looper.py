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
import psysmon.packages.event.core as ev_core



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

        self.catalogs = []

        self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_output_preferences()


    def edit(self):
        # Initialize the available catalogs.
        self.load_catalogs()
        catalog_names = [x.name for x in self.catalogs]
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('event_catalog') not in catalog_names:
                self.pref_manager.set_value('event_catalog', catalog_names[0])

        # Initialize the available processing nodes.
        processing_nodes = self.project.getProcessingNodes(('common', ))
        if self.pref_manager.get_value('processing_stack') is None:
                detrend_node_template = [x for x in processing_nodes if x.name == 'detrend'][0]
                detrend_node = copy.deepcopy(detrend_node_template)
                self.pref_manager.set_value('processing_stack', [detrend_node, ])
        self.pref_manager.set_limit('processing_stack', processing_nodes)

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
        processing_stack = ProcessingStack(name = 'pstack',
                                           project = self.project,
                                           nodes = self.pref_manager.get_value('processing_stack'))

        # Get the output directory from the pref_manager. If no directory is
        # specified create one based on the node resource id.
        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        processor = EventProcessor(project = self.project,
                                   processing_stack = processing_stack,
                                   output_dir = output_dir,
                                   parent_rid = self.rid)

        if self.pref_manager.get_value('select_individual') is True:
            events = self.pref_manager.get_value('events')
            event_ids = [x.id for x in events]
        else:
            event_ids = None


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



    def load_catalogs(self):
        ''' Load the event catalogs from the database.

        '''
        db_session = self.project.getDbSession()
        try:
            cat_table = self.project.dbTables['event_catalog'];
            query = db_session.query(cat_table.id,
                                     cat_table.name,
                                     cat_table.description,
                                     cat_table.agency_uri,
                                     cat_table.author_uri,
                                     cat_table.creation_time)
            self.catalogs = query.all()

        finally:
            db_session.close()


    def on_load_events(self, event):
        ''' Handle a click on the load_events ActionItem Button.
        '''
        event_table = self.project.dbTables['event']
        cat_table = self.project.dbTables['event_catalog']
        db_session = self.project.getDbSession()
        try:
            start_time = self.pref_manager.get_value('start_time')
            end_time = self.pref_manager.get_value('end_time')
            catalog_name = self.pref_manager.get_value('event_catalog')
            query = db_session.query(event_table.id,
                                     event_table.start_time,
                                     event_table.end_time,
                                     event_table.public_id,
                                     event_table.description,
                                     event_table.agency_uri,
                                     event_table.author_uri,
                                     event_table.comment,
                                     event_table.tags).\
                                     filter(event_table.start_time >= start_time.timestamp).\
                                     filter(event_table.start_time <= end_time.timestamp).\
                                     filter(event_table.ev_catalog_id == cat_table.id).\
                                     filter(cat_table.name == catalog_name)

            events = query.all()
            pref_item = self.pref_manager.get_item('events')[0]
            field = pref_item.gui_element[0]
            field.set_events(events)


        finally:
            db_session.close()


    def on_select_individual(self):
        if self.pref_manager.get_value('select_individual') is True:
            self.pref_manager.get_item('events')[0].enable_gui_element()
            self.pref_manager.get_item('load_events')[0].enable_gui_element()
        else:
            self.pref_manager.get_item('events')[0].disable_gui_element()
            self.pref_manager.get_item('load_events')[0].disable_gui_element()




class EventProcessor(object):

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
    def process(self, start_time, end_time, station_names, channel_names, event_catalog, event_ids = None):
        ''' Start the detection.

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

        event_catalog : String
            The name of the event catalog to process.

        event_ids : List of Integer
            If individual events are specified, this list contains the database IDs of the events
            to process.
        '''
        self.logger.info("Processing timespan %s to %s.", start_time.isoformat(), end_time.isoformat())

        result_bag = ResultBag()

        event_lib = ev_core.Library('events')
        event_lib.load_catalog_from_db(self.project, name = event_catalog)
        catalog = event_lib.catalogs[event_catalog]
        if event_ids is None:
            # Load the events for the given time span from the database.
            # TODO: Remove the hardcoded min_event_length value and create
            # user-selectable filter fields.
            catalog.load_events(project = self.project,
                                start_time = start_time,
                                end_time = end_time,
                                min_event_length = 1)
        else:
            # Load the events with the given ids from the database. Ignore the
            # time-span.
            catalog.load_events(event_id = event_ids)

        # Abort the execution if no events are available for the time span.
        if not catalog.events:
            if event_ids is None:
                self.logger.info('No events found for the timespan %s to %s.', start_time.isoformat(), end_time.isoformat())
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
        active_timespan = ()
        try:
            for k, cur_event in enumerate(catalog.events):
                self.logger.info("Processing event %d (%d/%d).", cur_event.db_id, k, n_events)

                # Load the waveform data for the event and the given stations and
                # channels.
                # TODO: Add a feature which allows adding a window before and after
                # the event time limits.
                pre_event_time = 20
                post_event_time = 10

                # TODO: Make the length of the waveform load interval user
                # selectable.
                waveform_load_interval = 3600

                # When many short events with small gaps inbetween are processed,
                # it is very ineffective to load the waveform for each event. Load
                # a larger time-span and then request the waveform data from the
                # waveclient stock.
                timespan_begin = UTCDateTime(cur_event.start_time.year, cur_event.start_time.month, cur_event.start_time.day, cur_event.start_time.hour)
                timespan_end = UTCDateTime(cur_event.end_time.year, cur_event.end_time.month, cur_event.end_time.day, cur_event.start_time.hour) + waveform_load_interval
                if not active_timespan:
                    self.logger.info("Initial stream request for hourly time-span: %s to %s.", timespan_begin.isoformat(),
                                                                                          timespan_end.isoformat())
                    stream = self.request_stream(start_time = timespan_begin,
                                                 end_time = timespan_end,
                                                 scnl = scnl)
                    active_timespan = (timespan_begin, timespan_end)


                cur_start_time = cur_event.start_time - pre_event_time
                cur_end_time = cur_event.end_time + post_event_time

                if not (((cur_start_time >= active_timespan[0]) and (cur_start_time <= active_timespan[1])) and ((cur_end_time >= active_timespan[0]) and (cur_end_time <= active_timespan[1]))):
                    self.logger.info("Requesting stream for hourly time-span: %s to %s.", timespan_begin.isoformat(),
                                                                                          timespan_end.isoformat())
                    stream = self.request_stream(start_time = timespan_begin,
                                                 end_time = timespan_end,
                                                 scnl = scnl)
                    active_timespan = (timespan_begin, timespan_end)


                stream = self.request_stream(start_time = cur_start_time,
                                             end_time = cur_end_time,
                                             scnl = scnl)

                # Execute the processing stack.
                # TODO: The 0.5 seconds where added because there's currently no
                # access to the event detection of the individual channels. Make
                # sure, that this hard-coded value is turned into a user-selectable
                # one or removed completely.
                process_limits = (cur_event.start_time - 0.5, cur_event.end_time)
                self.processing_stack.execute(stream = stream,
                                              process_limits = process_limits)

                # Put the results of the processing stack into the results bag.
                results = self.processing_stack.get_results()
                resource_id = self.project.rid + cur_event.rid
                result_bag.add(resource_id = resource_id,
                                    results = results)

        finally:
            # Add the time-span directory to the output directory.
            if k != len(catalog.events) - 1:
                cur_end_time = cur_event.end_time
            else:
                cur_end_time = end_time
            timespan_dir = start_time.strftime('%Y%m%dT%H%M%S') + '_to_' + cur_end_time.strftime('%Y%m%dT%H%M%S')
            cur_output_dir = os.path.join(self.output_dir, timespan_dir)
            # Save the processing results to files.
            result_bag.save(output_dir = cur_output_dir, scnl = scnl)


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
