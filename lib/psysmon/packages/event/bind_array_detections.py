# -*- coding: utf-8 -*-
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

import logging

import numpy as np
import obspy.core.utcdatetime as utcdatetime

import psysmon
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as pm
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.packages.event.bind as bind
import psysmon.packages.event.core as event_core
import psysmon.packages.event.detect as detect


class BindArrayDetections(package_nodes.CollectionNode):
    ''' Bind detection on array stations to array events.
    '''

    name = 'bind array detections'
    mode = 'looper child'
    category = 'Detection'
    tags = ['development', 'detect', 'bind', 'event', 'array']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.CollectionNode.__init__(self, **args)

        self.create_time_selector_preferences()
        self.create_component_selector_preferences()
        self.create_output_preferences()


    def create_time_selector_preferences(self):
        ''' Create the time span selection preference items.
        '''
        time_span_page = self.pref_manager.add_page('time span')
        process_time_span_group = time_span_page.add_group('process time span')


        item = pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           value = utcdatetime.UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (utcdatetime.UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        process_time_span_group.add_item(item)

        item = pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           value = utcdatetime.UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the selection time span (utcdatetime.UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        process_time_span_group.add_item(item)

        item = pm.SingleChoicePrefItem(name = 'window_mode',
                                           label = 'window mode',
                                           limit = ('free', 'daily', 'weekly'),
                                           value = 'free',
                                           hooks = {'on_value_change': self.on_window_mode_selected},
                                           tool_tip = 'The mode of the window computation.')
        process_time_span_group.add_item(item)

        item = pm.IntegerSpinPrefItem(name = 'window_length',
                                          label = 'window length [s]',
                                          value = 300,
                                          limit = [0, 1209600],
                                          tool_tip = 'The sliding window length in seconds.')
        process_time_span_group.add_item(item)


    def create_component_selector_preferences(self):
        ''' Create the input component preferences.
        '''
        component_page = self.pref_manager.add_page('components')
        array_to_process_group = component_page.add_group('arrays to process')
        detection_group = component_page.add_group('detections to process')

        # The arrays to process.
        item = pm.MultiChoicePrefItem(name = 'arrays',
                                          label = 'arrays',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the processing.')
        array_to_process_group.add_item(item)

        # The channels to process.
        item = pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the processing.')
        array_to_process_group.add_item(item)


        # The detection catalogs to process.
        item = pm.MultiChoicePrefItem(name = 'detection_catalogs',
                                      label = 'detection catalogs',
                                      limit = (),
                                      value = [],
                                      tool_tip = 'The detection catalogs to use for the detection binding.')
        detection_group.add_item(item)


    def create_output_preferences(self):
        ''' Create the output preference items.
        '''
        output_page = self.pref_manager.add_page('output')
        event_group = output_page.add_group('event')

        item = pm.SingleChoicePrefItem(name = 'output_event_catalog',
                                          label = 'event catalog',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The event catalog used to store the created events.')
        event_group.add_item(item)


    def on_window_mode_selected(self):
        ''' Handle the window mode single choice selection.
        '''
        if self.pref_manager.get_value('window_mode') == 'free':
            self.pref_manager.get_item('window_length')[0].enable_gui_element()
        elif self.pref_manager.get_value('window_mode') == 'daily':
            item = self.pref_manager.get_item('window_length')[0]
            item.disable_gui_element()
        elif self.pref_manager.get_value('window_mode') == 'weekly':
            item = self.pref_manager.get_item('window_length')[0]
            item.disable_gui_element()


    def load_detection_catalogs(self):
        ''' Load the detection catalogs from the database.

        '''
        catalogs = []
        db_session = self.project.getDbSession()
        try:
            cat_table = self.project.dbTables['detection_catalog'];
            query = db_session.query(cat_table.id,
                                     cat_table.name,
                                     cat_table.description,
                                     cat_table.agency_uri,
                                     cat_table.author_uri,
                                     cat_table.creation_time)
            catalogs = query.all()
        finally:
            db_session.close()

        return catalogs


    def load_event_catalogs(self):
        ''' Load the event catalogs from the database.
        '''
        catalogs = []
        db_session = self.project.getDbSession()
        try:
            cat_table = self.project.dbTables['event_catalog'];
            query = db_session.query(cat_table.id,
                                     cat_table.name,
                                     cat_table.description,
                                     cat_table.agency_uri,
                                     cat_table.author_uri,
                                     cat_table.creation_time)
            catalogs = query.all()
        finally:
            db_session.close()

        return catalogs


    def edit(self):
        ''' Create the edit dialog.
        '''
        # Initialize the array components.
        if self.project.geometry_inventory:
            arrays = sorted([x.name for x in self.project.geometry_inventory.arrays])
            self.pref_manager.set_limit('arrays', arrays)

            channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
            self.pref_manager.set_limit('channels', channels)

        # Initialize the detection catalogs.
        catalogs = self.load_detection_catalogs()
        catalog_names = [x.name for x in catalogs]
        self.pref_manager.set_limit('detection_catalogs', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('detection_catalogs') not in catalog_names:
                self.pref_manager.set_value('detection_catalogs', catalog_names[0])


        # Initialize the event catalogs.
        catalogs = self.load_event_catalogs()
        catalog_names = [x.name for x in catalogs]
        self.pref_manager.set_limit('output_event_catalog', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('output_event_catalog') not in catalog_names:
                self.pref_manager.set_value('output_event_catalog', catalog_names[0])



        # Update the preference item gui elements based on the current
        # selections.
        self.on_window_mode_selected()

        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        ''' Execute the node.
        '''
        window_mode = self.pref_manager.get_value('window_mode')
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        if window_mode == 'free':
            window_length = self.pref_manager.get_value('window_length')
        elif window_mode == 'daily':
            start_time = utcdatetime.UTCDateTime(start_time.year, start_time.month, start_time.day)
            end_time = utcdatetime.UTCDateTime(end_time.year, end_time.month, end_time.day)
            window_length = 86400.
        elif window_mode == 'weekly':
            start_time = utcdatetime.UTCDateTime(start_time.year, start_time.month, start_time.day) - start_time.weekday * 86400
            end_time = utcdatetime.UTCDateTime(end_time.year, end_time.month, end_time.day) +  (7 - end_time.weekday) * 86400
            window_length = 86400. * 7


        array_binder = ArrayDetectionBinder(project = self.project,
                                            parent_rid = self.rid)

        array_binder.bind(start_time = start_time,
                          end_time = end_time,
                          array_names = self.pref_manager.get_value('arrays'),
                          channel_names = self.pref_manager.get_value('channels'),
                          window_length = window_length,
                          detection_catalog_names = self.pref_manager.get_value('detection_catalogs'),
                          event_catalog_name = self.pref_manager.get_value('output_event_catalog')
                         )



class ArrayDetectionBinder(object):

    def __init__(self, project, parent_rid = None):
        ''' Initialize the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.project = project

        self.parent_rid = parent_rid


    def bind(self, start_time, end_time, array_names, channel_names,
             window_length, detection_catalog_names, event_catalog_name):
        ''' Start the array detection binding.

        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan for which to detect the events.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan for which to detect the events.

        array_names : list of Strings
            The names of the arrays to process.

        channel_names : list of Strings
            The names of the channels to process.

        window_length : float
            The length of the sliding windwow in seconds.

        detection_catalog_names : list of Strings
            The names of the detection catalogs to use for the detection binding.

        event_catalog_name : String
            The name of the event catalog used to store the boung events.
        '''
        self.logger.info("Processing timespan %s to %s.", start_time.isoformat(), end_time.isoformat())

        window_length = float(window_length)

        # Check for correct argument values:
        if end_time <= start_time:
            raise ValueError("The end_time %s is smaller than the start_time %s." % (end_time.isoformat(), start_time.isoformat()))

        if not event_catalog_name:
            raise ValueError("An output event catalog name has to be specified.")

        # Compute the start times of the sliding windows.
        n_windows = np.floor((end_time - start_time) / window_length)
        if n_windows > 0:
            windowlist_start = [start_time + x * window_length for x in range(0, int(n_windows))]
        else:
            self.logger.warning("The window length of %f seconds doesn't fit into the given detection time span. Setting the detection window length to %f seconds starting from %s.", window_length, end_time - start_time, start_time.isoformat())
            windowlist_start = [start_time, ]
            window_length = end_time - start_time

        arrays = []
        for cur_name in array_names:
            arrays.extend(self.project.geometry_inventory.get_array(name = cur_name))

        # Get the target event catalog.
        event_library = event_core.Library(name = 'detection binder')
        event_library.load_catalog_from_db(project = self.project,
                                           name = event_catalog_name)
        event_catalog = event_library.catalogs[event_catalog_name]

        # Create the list of detection catalogs to use.
        detect_library = detect.Library(name = 'detection binder')
        detect_library.load_catalog_from_db(project = self.project,
                                            name = detection_catalog_names)
        detect_catalogs = detect_library.catalogs.values()

        if not event_catalog:
            raise RuntimeError("Couldn't load the event catalog %s from the database." % event_catalog_name)
        binder = bind.DetectionBinder(event_catalog = event_catalog)

        for cur_array in arrays:
            self.logger.info("Processing array %s.", cur_array.name)
            cur_array_stations = [x.item for x in cur_array.stations]
            binder.compute_search_windows(cur_array_stations)

            unbound_detections = None

            # Create the list of channels to process.
            channels = []
            for cur_name in channel_names:
                for cur_station in cur_array_stations:
                    channels.extend(cur_station.get_channel(name = cur_name))

            for cur_start_time in windowlist_start:
                cur_end_time = cur_start_time + window_length
                # Load the detections from the database and assign the inventory
                # channels to the detections.
                for cur_catalog in detect_catalogs:
                    cur_catalog.clear_detections()
                    cur_catalog.load_detections(project = self.project,
                                                start_time = cur_start_time,
                                                end_time = cur_end_time)
                    cur_catalog.assign_channel(self.project.geometry_inventory)

                unbound_detections = binder.bind(catalogs = detect_catalogs,
                                                 channel_scnl = [x.scnl for x in channels],
                                                 arrays = [cur_array,],
                                                 start_time = cur_start_time,
                                                 end_time = cur_end_time,
                                                 additional_detections = unbound_detections)

                # Write the events to the database.
                event_catalog.write_to_database(project = self.project)
                event_catalog.clear_events()



