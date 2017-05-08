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
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure

import psysmon.packages.event.core as core

class EventToArrayTestCase(unittest.TestCase):
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
        cls.project = create_full_project(cls.psybase)
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
        pass


    def test_assign_event_to_array(self):
        ''' Test the assignment of an event to an array.
        '''
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = core.Event(start_time = start_time,
                           end_time = end_time,
                           creation_time = creation_time)

        array = self.project.geometry_inventory.arrays[0]

        event.arrays.append(array)

        event.write_to_database(self.project)

        # Reload the event and check for the correct arrays.
        event_orm_class = self.project.dbTables['event']
        try:
            db_session = self.project.getDbSession()
            result = db_session.query(event_orm_class).filter(event_orm_class.id == event.db_id).scalar()
            cur_event = core.Event.from_db_event(result)
            self.assertIsInstance(cur_event, core.Event)
            self.assertEqual(len(cur_event.arrays), 1)
            self.assertEqual(cur_event.arrays[0], array.name)
        finally:
            db_session.close()





def suite():
    return unittest.makeSuite(EventToArrayTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
