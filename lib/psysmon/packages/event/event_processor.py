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
from plugins_event_selector import EventListField
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack
from psysmon.core.processingStack import ResultBag
import core as ev_core



## Documentation for class importWaveform
# 
# 
class EventProcessorNode(CollectionNode):

    name = 'event processor'
    mode = 'editable'
    category = 'Event'
    tags = ['stable',]

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

        self.catalogs = []

        self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_processing_stack_preferences()
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

        processor.process(start_time = self.pref_manager.get_value('start_time'),
                          end_time = self.pref_manager.get_value('end_time'),
                          station_names = self.pref_manager.get_value('stations'),
                          channel_names = self.pref_manager.get_value('channels'),
                          event_catalog = self.pref_manager.get_value('event_catalog'),
                          event_ids = event_ids)




    def create_selector_preferences(self):
        ''' Create the preference items of the event selection section.
        '''
        self.pref_manager.add_page('event selector')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'selection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).',
                                           position = 2)
        self.pref_manager.add_item(pagename = 'event selector',
                                   item = item)

        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           group = 'selection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).',
                                           position = 1)
        self.pref_manager.add_item(pagename = 'event selector',
                                   item = item)

        item = psy_pm.SingleChoicePrefItem(name = 'event_catalog',
                                          label = 'event catalog',
                                          group = 'event selection',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select an event catalog for which to load the events.')
        self.pref_manager.add_item(pagename = 'event selector',
                                   item = item)

        item = psy_pm.CheckBoxPrefItem(name = 'select_individual',
                                       label = 'select individual events',
                                       group = 'event selection',
                                       value = False,
                                       tool_tip = 'Do a manual selection of the events to process.',
                                       hooks = {'on_value_change': self.on_select_individual})
        self.pref_manager.add_item(pagename = 'event selector',
                                   item = item)

        item = psy_pm.ActionItem(name = 'load_events',
                                 label = 'load events',
                                 group = 'event selection',
                                 mode = 'button',
                                 action = self.on_load_events,
                                 tool_tip = 'Load events from the database.')
        self.pref_manager.add_item(pagename = 'event selector',
                                   item = item)

        item = psy_pm.CustomPrefItem(name = 'events',
                                     label = 'events',
                                     group = 'event selection',
                                     value = [],
                                     gui_class = EventListField,
                                     tool_tip = 'The available events. Selected events will be used for processing.')
        self.pref_manager.add_item(pagename = 'event selector',
                                   item = item)



    def create_component_selector_preferences(self):
        ''' Create the preference items of the component selection section.

        '''
        self.pref_manager.add_page('components')

        # The stations to process.
        item = psy_pm.MultiChoicePrefItem(name = 'stations',
                                          label = 'stations',
                                          group = 'components to process',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the processing.')
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        # The channels to process.
        item = psy_pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          group = 'components to process',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the processing.')
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)


    def create_processing_stack_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        self.pref_manager.add_page('processing stack')

        item = psy_pm.CustomPrefItem(name = 'processing_stack',
                                     label = 'processing stack',
                                     group = 'event processing',
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

        self.result_bag = ResultBag()


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
        event_lib = ev_core.Library('events')
        event_lib.load_catalog_from_db(self.project, name = event_catalog)
        catalog = event_lib.catalogs[event_catalog]
        if event_ids is None:
            # Load the events for the given time span from the database.
            catalog.load_events(project = self.project,
                                start_time = start_time,
                                end_time = end_time)
        else:
            # Load the events with the given ids from the database. Ignore the
            # time-span.
            catalog.load_events(event_id = event_ids)


        # Get the channels to process.
        channels = []
        for cur_station in station_names:
            for cur_channel in channel_names:
                channels.extend(self.project.geometry_inventory.get_channel(station = cur_station,
                                                                            name = cur_channel))


        scnl = [x.scnl for x in channels]

        for cur_event in catalog.events:
            # Load the waveform data for the event and the given stations and
            # channels.
            # TODO: Add a feature which allows adding a window before and after
            # the event time limits.
            cur_start_time = cur_event.start_time
            cur_end_time = cur_event.end_time
            stream = self.request_stream(start_time = cur_start_time,
                                         end_time = cur_end_time,
                                         scnl = scnl)

            # Execute the processing stack.
            self.processing_stack.execute(stream)

            # Put the results of the processing stack into the results bag.
            results = self.processing_stack.get_results()
            resource_id = self.project.rid + cur_event.rid
            self.result_bag.add(resource_id = resource_id,
                                results = results)


        # Save the processing results to files.
        self.result_bag.save(output_dir = self.output_dir, scnl = scnl)


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
