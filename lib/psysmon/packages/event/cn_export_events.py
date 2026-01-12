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
The export events module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
from __future__ import division

from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import logging
import os

import obspy.core.utcdatetime as utcdatetime
import sqlalchemy

import psysmon
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.result as result
import psysmon.packages.event.core as event_core
import psysmon.packages.event.detect as detect

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.gui.dialog.pref_listbook as psy_lb
    import psysmon.packages.event.plugins_event_selector as plugins_event_selector



class ExportEvents(package_nodes.CollectionNode):
    ''' Export events from the database to a file.
    '''
    name = 'export events'
    mode = 'editable'
    category = 'Event'
    tags = ['export', 'event', 'csv']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.CollectionNode.__init__(self, **args)

        # The event catalog library
        self.event_library = event_core.Library('binder')

        self.create_selector_preferences()
        self.create_filter_preferences()
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
        dlg = psy_lb.ListbookPrefDialog(preferences = self.pref_manager)

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
        ''' Execute the collection node.
        '''
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')

        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        exporter = EventExporter(project = self.project,
                                 output_dir = output_dir,
                                 parent_name = self.name,
                                 parent_rid = self.rid)

        if self.pref_manager.get_value('select_individual') is True:
            events = self.pref_manager.get_value('events')
            event_ids = [x.id for x in events]
        else:
            event_ids = None

        event_tags = self.pref_manager.get_value('event_tag')
        if event_tags:
            event_tags = [event_tags]
        else:
            event_tags = None

        now = utcdatetime.UTCDateTime()
        self.save_settings(output_dir = exporter.output_dir,
                           execution_time = now)

        exporter.export(start_time = start_time,
                        end_time = end_time,
                        output_interval = self.pref_manager.get_value('output_interval'),
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
                                           value = utcdatetime.UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        time_group.add_item(item)

        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           value = utcdatetime.UTCDateTime('2015-01-01T00:00:00'),
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
                                     gui_class = plugins_event_selector.EventListField,
                                     tool_tip = 'The available events. Selected events will be used for processing.')
        event_group.add_item(item)

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
                                          limit = ('hour', 'day', 'week', 'month', 'whole'),
                                          value = 'day',
                                          tool_tip = 'The interval for which the output should be grouped.')
        output_group.add_item(item)

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



class EventExporter(object):

    def __init__(self, project, output_dir, parent_name = None, parent_rid = None):
        ''' Initialize the instance.

        '''
        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.project = project

        # The timespan for which waveform data is available.
        self.active_timespan = ()

        self.parent_name = parent_name
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
            int_start = utcdatetime.UTCDateTime(start_time.year, start_time.month, start_time.day) + length
            int_end = utcdatetime.UTCDateTime(end_time.year, end_time.month, end_time.day)
            n_intervals = old_div((int_end - int_start), length)
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        if interval == 'day':
            length = seconds_per_day
            int_start = utcdatetime.UTCDateTime(start_time.year, start_time.month, start_time.day) + length
            int_end = utcdatetime.UTCDateTime(end_time.year, end_time.month, end_time.day)
            n_intervals = old_div((int_end - int_start), length)
            interval_start.extend([int_start + x * length for x in range(0, int(n_intervals))])
        elif interval == 'week':
            length = seconds_per_day*7
            int_start = utcdatetime.UTCDateTime(start_time.year, start_time.month, start_time.day) + (6 - start_time.weekday) * seconds_per_day
            int_end = utcdatetime.UTCDateTime(end_time.year, end_time.month, end_time.day) - end_time.weekday * seconds_per_day
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
                    if len(year_list) == 1:
                        month_dict[cur_year] = list(range(start_month,
                                                          end_month + 1))
                    else:
                        month_dict[cur_year] = list(range(start_month, 13))
                elif k == len(year_list) - 1:
                    month_dict[cur_year] = list(range(1, end_month))
                else:
                    month_dict[cur_year] = list(range(1, 12))

            for cur_year, month_list in month_dict.items():
                for cur_month in month_list:
                    cur_time = utcdatetime.UTCDateTime(year = cur_year,
                                                       month = cur_month,
                                                       day = 1)
                    interval_start.append(cur_time)

        interval_start.append(end_time)
        self.logger.info(interval_start)
        return interval_start


    def load_event_types(self):
        ''' Load the available event types from the database.
        '''
        db_session = self.project.getDbSession()
        event_types = []
        try:
            event_type_table = self.project.dbTables['event_type']
            query = db_session.query(event_type_table)
            query = query.options(sqlalchemy.orm.immediateload(event_type_table.children))
            query = query.options(sqlalchemy.orm.immediateload(event_type_table.parent))
            event_types = query.all()
        finally:
            db_session.close()

        return event_types

    def create_public_id(self, utc_datetime, agency_id, author_id,
                         service_id, project_id, resource_id):
        template = "smi:{aid:s}.{auid:s}.{sid:s}/{pid:s}{rid:s}-{date:s}"
        date = utc_datetime.isoformat().replace(':', '')\
                                       .replace('.', '')\
                                       .replace('-', '')
        pub_id = template.format(aid = agency_id,
                                 auid = author_id,
                                 sid = service_id,
                                 pid = project_id,
                                 rid = resource_id,
                                 date = date)
        return pub_id

    
    def export(self, start_time, end_time, output_interval,
               event_catalog, event_ids = None,
               event_types = None, event_tags = None):
        ''' Export the events of a catalog.
        '''
        self.logger.info("Exporting events for timespan timespan %s to %s.",
                         start_time.isoformat(),
                         end_time.isoformat())

        if event_tags is None:
            event_tags = []

        if event_types is None:
            event_types = []


        interval_start = self.compute_intervals(start_time = start_time,
                                                end_time = end_time,
                                                interval = output_interval)
        event_lib = event_core.Library('events')
        event_lib.load_catalog_from_db(self.project, name = event_catalog)
        catalog = event_lib.catalogs[event_catalog]

        det_lib = detect.Library('detections')
        name_list = det_lib.get_catalogs_in_db(self.project)
        det_lib.load_catalog_from_db(project = self.project,
                                     name = name_list,
                                     load_detections = False)
        det_cat_map = [(x.db_id, x.name) for x in det_lib.catalogs.values()]
        det_cat_map = dict(det_cat_map)
        
        available_event_types = self.load_event_types()

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
                                    min_event_length = 0.1,
                                    event_tags = event_tags)
            else:
                # Load the events with the given ids from the database. Ignore the
                # time-span.
                catalog.load_events(project = self.project,
                                    event_id = event_ids)

            # Abort the execution if no events are available for the time span.
            if not catalog.events:
                if event_ids is None:
                    self.logger.info('No events found for the timespan %s to %s.', cur_start_time.isoformat(), cur_end_time.isoformat())
                else:
                    self.logger.info('No events found for the specified event IDs: %s.', event_ids)
                continue
            
            # Create the event result.
            res_columns = ['public_id', 'event_start_time', 'event_end_time',
                           'n_stations', 'detection_scnl', 'detection_start',
                           'detection_end', 'catalog_name', 'event_type_id',
                           'event_type']
            cur_res = result.TableResult(name = 'event',
                                         key_name = 'id',
                                         start_time = cur_start_time,
                                         end_time = cur_end_time,
                                         origin_name = self.parent_name,
                                         origin_resource = self.parent_rid,
                                         column_names = res_columns)

            # Create the detection result.
            det_columns = ['start_time', 'end_time', 'channel', 'catalog',
                           'event_id', 'event_start_time', 'event_end_time']
            cur_det_res = result.TableResult(name = 'detection',
                                             key_name = 'id',
                                             start_time = cur_start_time,
                                             end_time = cur_end_time,
                                             origin_name = self.parent_name,
                                             origin_resource = self.parent_rid,
                                             column_names = det_columns)

            # Loop through the events.
            n_events = len(catalog.events)
            for k, cur_event in enumerate(sorted(catalog.events, key = lambda x: x.start_time)):
                self.logger.info("Processing event %d (%d/%d).", cur_event.db_id, k, n_events)

                # Assign the channel instance to the detections.
                cur_event.assign_channel_to_detections(self.project.geometry_inventory)

                # TODO: Load the event type from the database when loading the event.
                # Get the related event_type name.
                cur_event_type = None
                if cur_event.event_type is not None:
                    cur_event_type = [x.name for x in available_event_types if x.id == cur_event.event_type]
                    if len(cur_event_type) == 1:
                        cur_event_type = cur_event_type[0]
                    else:
                        cur_event_type = None

                # Create the public ID if needed.
                pub_id = self.create_public_id(utc_datetime = cur_event.start_time,
                                               agency_id = cur_event.agency_uri,
                                               author_id = cur_event.author_uri,
                                               service_id = 'psysmon',
                                               project_id = self.project.name,
                                               resource_id = cur_event.rid)
                
                # Add the event to the result.
                detection_scnl = [str(x.channel.scnl_string) for x in cur_event.detections]
                detection_start = [str(x.start_time.timestamp) for x in cur_event.detections]
                detection_end = [str(x.end_time.timestamp) for x in cur_event.detections]
                event_start = cur_event.start_time.isoformat()
                event_end = cur_event.end_time.isoformat()
                cur_res.add_row(key = cur_event.db_id,
                                public_id = pub_id,
                                event_start_time = event_start,
                                event_end_time = event_end,
                                n_stations = len(cur_event.detections),
                                detection_scnl = ','.join(detection_scnl),
                                detection_start = ','.join(detection_start),
                                detection_end = ','.join(detection_end),
                                catalog_name = catalog.name,
                                event_type_id = cur_event.event_type,
                                event_type = cur_event_type)

                # Add the detections to the detection result.
                for cur_det in cur_event.detections:
                    det_start = cur_det.start_time.isoformat()
                    det_end = cur_det.end_time.isoformat()
                    det_cat = det_cat_map[cur_det.catalog_id]
                    cur_det_res.add_row(key = cur_det.db_id,
                                        start_time = det_start,
                                        end_time = det_end,
                                        channel = cur_det.channel.scnl_string,
                                        catalog = det_cat,
                                        event_id = cur_event.db_id,
                                        event_start_time = event_start,
                                        event_end_time = event_end)

            # Save the results.
            cur_res.base_output_dir = self.output_dir
            cur_res.save(with_timewindow = False)

            cur_det_res.base_output_dir = self.output_dir
            cur_det_res.save(with_timewindow = False)

