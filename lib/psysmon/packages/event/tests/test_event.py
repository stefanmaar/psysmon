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



class EventTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        # Create an empty project.
        cls.psybase = create_psybase()
        cls.project = create_empty_project(cls.psybase)
        cls.project.dbEngine.echo = True

    @classmethod
    def tearDownClass(cls):
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

        # Test the access to obspy event parameters.
        event.event_type = 'landslide'
        self.assertEqual(event.event_type, 'landslide')


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
        self.assertEqual(tmp.creation_time, event.creation_time.timestamp)


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



#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(EventTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

