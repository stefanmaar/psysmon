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

import copy
import logging
import psysmon
from psysmon.core.packageNodes import CollectionNode
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from plugins_event_selector import EventListField
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack



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
        self.create_processing_chain_preferences()

    def edit(self):
        # Initialize the available catalogs.
        self.load_catalogs()
        catalog_names = [x.name for x in self.catalogs]
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            self.pref_manager.set_value('event_catalog', catalog_names[0])

        # Initialize the available processing nodes.
        processing_nodes = self.project.getProcessingNodes(('common', ))
        if self.pref_manager.get_value('processing_stack') is None:
                detrend_node_template = [x for x in processing_nodes if x.name == 'detrend'][0]
                detrend_node = copy.deepcopy(detrend_node_template)
                self.pref_manager.set_value('processing_stack', [detrend_node, ])
        self.pref_manager.set_limit('processing_stack', processing_nodes)


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
        output_dir = ''

        processor = EventProcessor(project = self.project,
                                  processing_stack = processing_stack,
                                  output_dir = output_dir)

        if self.pref_manager.get_value('select_individual') is True:
            events = self.pref_manager.get_value('events')
            event_ids = [x.id for x in events]
        else:
            event_ids = None

        processor.process(start_time = self.pref_manager.get_value('start_time'),
                          end_time = self.pref_manager.get_value('end_time'),
                          stations = self.pref_manager.get_value('stations'),
                          channels = self.pref_manager.get_value('channels'),
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


    def create_processing_chain_preferences(self):
        ''' Create the preference items of the processing chain section.
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

    def __init__(self, project, output_dir, processing_stack = None):
        ''' Initialize the instance.

        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.project = project

        self.processing_stack = processing_stack

        self.ouput_dir = output_dir


    def process(self, start_time, end_time, stations, channels, event_ids = None):
        ''' Start the detection.

        Parameters
        ----------
        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan for which to detect the events.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan for which to detect the events.

        stations : list of Strings
            The names of the stations to process.

        channels : list of Strings
            The names of the channels to process.

        interval : float
            The interval into which the time span is split to run successive detections.

        '''
        events = []
        if event_ids is None:
            # Load the events for the given time span from the database.
            pass
        else:
            # Load the events with the given ids from the database. Ignore the
            # time-span.
            pass



        for cur_event in events:
            # Load the waveform data for the event and the given stations and
            # channels.
            stream = self.load_event_waveform(scnl)

            # Execute the processing stack.
            self.processing_stack.execute(stream)

            # Put the results of the processing stack into the results bag.
            results = self.processing_stack.get_results()
            self.result_bag.add(results)


        # Save the processing results to files.
        self.result_bag.save(output_dir = self.output_dir)
