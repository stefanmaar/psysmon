'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import logging
import os

from obspy.core.utcdatetime import UTCDateTime

import psysmon

from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_empty_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import clear_project_database_tables
from psysmon.core.test_util import remove_project_filestructure

from psysmon.packages.event.core import Event
import psysmon.packages.event.core as core
import psysmon.packages.event.detect as detect



class EventTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('INFO')
        logger.addHandler(psysmon.getLoggerHandler())

        # Create an empty project.
        cls.psybase = create_psybase()
        cls.project = create_empty_project(cls.psybase)
        cls.project.dbEngine.echo = False

    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print "dropping database tables...\n"
        drop_project_database_tables(cls.project)
        print "removing temporary file structure....\n"
        remove_project_filestructure(cls.project)
        print "removing temporary base directory....\n"
        os.removedirs(cls.project.base_dir)
        print "....finished cleaning up.\n"

    def setUp(self):
        pass

    def tearDown(self):
        clear_project_database_tables(self.project)

    def test_event_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Test the control of None values of the time limits.
        self.assertRaises(ValueError, Event, start_time = None, end_time = None)
        self.assertRaises(ValueError, Event, start_time = '2000-01-01', end_time = None)
        self.assertRaises(ValueError, Event, start_time = None, end_time = '2000-01-01')

        # Test the control of the time limits.
        self.assertRaises(ValueError, Event, start_time = '2000-01-01', end_time = '1999-01-01')
        self.assertRaises(ValueError, Event, start_time = '2000-01-01', end_time = '2000-01-01')

        # Create an event with valid time limits.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        event = Event(start_time = start_time, end_time = end_time)
        self.assertIsInstance(event, Event)
        self.assertEqual(event.start_time, UTCDateTime(start_time))
        self.assertEqual(event.end_time, UTCDateTime(end_time))
        self.assertTrue(event.changed)



    def test_write_event_to_database(self):
        ''' Test the writing of an event to the database.
        '''
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)
        self.project.dbEngine.echo = True
        event.write_to_database(self.project)

        db_event_orm = self.project.dbTables['event']
        db_session = self.project.getDbSession()
        result = db_session.query(db_event_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.start_time, event.start_time.timestamp)
        self.assertEqual(tmp.end_time, event.end_time.timestamp)
        self.assertEqual(tmp.creation_time, event.creation_time.isoformat())


    def test_update_event_in_database(self):
        ''' Test the update of an event to the database.
        '''
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)
        self.project.dbEngine.echo = True
        event.write_to_database(self.project)
        db_id = event.db_id


        start_time = UTCDateTime('2000-01-02T00:00:00')
        end_time = UTCDateTime('2000-01-02T01:00:00')
        event.start_time = start_time
        event.end_time = end_time
        event.write_to_database(self.project)

        db_event_orm = self.project.dbTables['event']
        db_session = self.project.getDbSession()
        result = db_session.query(db_event_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.id, db_id)
        self.assertEqual(tmp.id, event.db_id)
        self.assertEqual(tmp.start_time, event.start_time.timestamp)
        self.assertEqual(tmp.end_time, event.end_time.timestamp)
        self.assertEqual(tmp.creation_time, event.creation_time.isoformat())


    def test_add_detection_to_event(self):
        ''' Test the adding of detections.
        '''
        # Create a detection.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        det = detect.Detection(start_time = start_time,
                                 end_time = end_time,
                                 creation_time = creation_time)
        # Write the detection to the database. Only detections in a database
        # can be associated with the event in the database.
        det.write_to_database(self.project)

        # Create an event.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time,
                      detections = [det, ])

        # Write the event to the database.
        event.write_to_database(self.project)

        # Now reload the event and check if the detections were linked
        # correctly with the event.
        db_event_orm = self.project.dbTables['event']
        try:
            db_session = self.project.getDbSession()
            result = db_session.query(db_event_orm).all()
            cur_event = Event.from_db_event(result[0])
            self.assertEqual(len(cur_event.detections), 1)
            self.assertEqual(cur_event.detections[0].start_time, det.start_time)
            self.assertEqual(cur_event.detections[0].end_time, det.end_time)
        finally:
            db_session.close()


    def test_event_type(self):
        ''' Test the event type creation.
        '''
        event_type = core.EventType(name = 'type 1',
                                    description = 'type 1 description')

        # Write the event type to the database.
        event_type.write_to_database(self.project)

        db_event_type_orm_class = self.project.dbTables['event_type']
        try:
            db_session = self.project.getDbSession()
            result = db_session.query(db_event_type_orm_class).all()
            cur_event_type = core.EventType.from_db_event_type(result[0])

            self.assertIsInstance(cur_event_type, core.EventType)
            self.assertEqual(cur_event_type.name, 'type 1')
            self.assertEqual(cur_event_type.description, 'type 1 description')
        finally:
            db_session.close()


    def test_assign_type_to_event(self):
        ''' Test the assignment of events to event types.
        '''
        # Create an event.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)

        event_type = core.EventType(name = 'type 1',
                                    description = 'type 1 description')

        # Write the event type to the database. The event type has to exist in
        # the database before it can be linked by an event in the database.
        event_type.write_to_database(self.project)

        event.event_type = event_type
        event.write_to_database(self.project)



def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(EventTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

