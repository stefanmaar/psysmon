'''
Created on May 17, 2011

@author: Stefan Mertl
'''
from __future__ import print_function

import unittest
import logging
import os
import operator as op

import numpy as np
import numpy.testing as np_test

import obspy.core.utcdatetime as utcdatetime

import psysmon
import psysmon.packages.event.detect as detect
import psysmon.packages.event.event_binding as binding
import psysmon.packages.event.core as ev_core
import psysmon.core.test_util as test_util


class EventBindTestCase(unittest.TestCase):
    """
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('INFO')
        logger.addHandler(psysmon.getLoggerHandler())

        test_util.drop_database_tables(db_dialect = 'mysql',
                              db_driver = None,
                              db_host = 'localhost',
                              db_name = 'psysmon_unit_test',
                              db_user = 'unit_test',
                              db_pwd = 'test',
                              project_name = 'unit_test')


        cls.psybase = test_util.create_psybase()
        test_util.create_full_project(cls.psybase)
        cls.project = cls.psybase.project
        cls.project.dbEngine.echo = False
        logger.setLevel('DEBUG')

    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print("dropping database tables...\n")
        test_util.drop_project_database_tables(cls.project)
        print("removing temporary file structure....\n")
        test_util.remove_project_filestructure(cls.project)
        print("removing temporary base directory....\n")
        os.removedirs(cls.project.base_dir)
        print("....finished cleaning up.\n")

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_bind(self):
        ''' Test the binding of the detections.
        '''
        # Create the test detections.
        catalog = detect.Catalog(name = 'test',
                          description = 'A test description.',
                          agency_uri = 'uot',
                          author_uri = 'tester',
                          creation_time = utcdatetime.UTCDateTime())

        channels = [('GILA', 'HHZ', 'ALPAACT', '00'),
                    ('GUWA', 'HHZ', 'ALPAACT', '00'),
                    ('G_NAWA', 'HHZ', 'ALPAACT', '00'),
                    ('SITA', 'HHZ', 'ALPAACT', '00')]
        events = {}
        events['2016-01-01T00:00:00'] = [0, 1, 2, 3]
        events['2016-01-01T01:00:00'] = [1, 0, 1, 2]
        events['2016-01-01T03:00:00'] = [2, 1, 0, 1]
        events['2016-01-01T04:00:00'] = [3, 2, 1, 0]

        for cur_start, cur_delay_list in events.iteritems():
            for k, cur_delay in enumerate(cur_delay_list):
                cur_scnl = channels[k]
                cur_channel = self.project.geometry_inventory.get_channel(station = cur_scnl[0],
                                                                          name = cur_scnl[1],
                                                                          network = cur_scnl[2],
                                                                          location = cur_scnl[3])
                cur_channel = cur_channel[0]


                # Create a detection and add it to the catalog.
                start_time = utcdatetime.UTCDateTime(cur_start) + cur_delay
                end_time = start_time + 3
                cur_rec_stream = cur_channel.get_stream(start_time = start_time,
                                                        end_time = end_time)
                cur_rec_stream = cur_rec_stream[0]
                det = detect.Detection(start_time = start_time,
                                         end_time = end_time,
                                         creation_time = utcdatetime.UTCDateTime(),
                                         rec_stream_id = cur_rec_stream.id)
                catalog.add_detections([det,])
        catalog.write_to_database(self.project)

        # Get the channels for the detections.
        catalog.assign_channel(self.project.geometry_inventory)

        # Create an event catalog where to store the events.
        event_catalog = ev_core.Catalog(name = 'event_bind_test',
                                        description = 'A test description.',
                                        agency_uri = 'uot',
                                        author_uri = 'tester',
                                        creation_time = utcdatetime.UTCDateTime())


        # Bind the detections to events.
        binder = binding.EventBinder(event_catalog = event_catalog,
                                    author_uri = 'tester',
                                    agency_uri = 'uot')
        binder.compute_search_windows(self.project.geometry_inventory.get_station())
        binder.bind(catalog, channels)

        # Save the event catalog to the database.
        event_catalog.write_to_database(self.project)

        # Load the events from the database and check for the correctly
        # associated detections.
        db_catalog_orm = self.project.dbTables['event_catalog']
        db_session = self.project.getDbSession()
        try:
            result = db_session.query(db_catalog_orm).filter(db_catalog_orm.name == 'event_bind_test').all()
            loaded_catalog = ev_core.Catalog.from_db_catalog(result[0], load_events = True)
            for cur_event_start, cur_delay in events.iteritems():
                cur_event_start = utcdatetime.UTCDateTime(cur_event_start)
                selected_event = loaded_catalog.get_events(start_time = cur_event_start,
                                                           end_time = cur_event_start + 10)
                self.assertEqual(len(selected_event), 1)
                selected_event = selected_event[0]
                self.assertEqual(len(selected_event.detections), 4)
                detections = sorted(selected_event.detections, key = op.attrgetter('start_time'))
                cur_det_starts = [cur_event_start + x for x in sorted(cur_delay)]
                self.assertEqual(detections[0].start_time, cur_det_starts[0])
                self.assertEqual(detections[1].start_time, cur_det_starts[1])
                self.assertEqual(detections[2].start_time, cur_det_starts[2])
                self.assertEqual(detections[3].start_time, cur_det_starts[3])

        finally:
            db_session.close()





def suite():
    return unittest.makeSuite(EventBindTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

