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

from psysmon.packages.pick.core import Pick
from psysmon.packages.geometry.db_inventory import DbChannel



class PickTestCase(unittest.TestCase):
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
        create_full_project(cls.psybase)
        cls.project = cls.psybase.project
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
        # Clear the picks database tables.
        tables_to_clear = ['pick', 'pick_catalog']
        for cur_name in tables_to_clear:
            cur_table = self.project.dbTables[cur_name]
            self.project.dbEngine.execute(cur_table.__table__.delete())


    def test_pick_creation(self):
        ''' Test the pSysmon Pick class.
        '''
        # Create an event with valid time limits.
        pick_time = UTCDateTime('2011-01-01T00:00:00')
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'SITA')
        channel = channel[0]
        pick = Pick(label = 'P',
                    time = pick_time,
                    amp1 = 10,
                    channel = channel)

        self.assertIsInstance(pick, Pick)
        self.assertEqual(pick.label, 'P')
        self.assertEqual(pick.time, pick_time)
        self.assertEqual(pick.amp1, 10)
        self.assertEqual(pick.channel, channel)
        self.assertIsNone(pick.db_id)
        self.assertIsNone(pick.parent)
        self.assertIsNone(pick.amp2)
        self.assertEqual(pick.first_motion, 0)
        self.assertIsNone(pick.error)
        self.assertIsNone(pick.agency_uri)
        self.assertIsNone(pick.author_uri)
        self.assertIsInstance(pick.creation_time, UTCDateTime)
        self.assertTrue(pick.changed)


    def test_write_pick_to_database(self):
        ''' Test the writing of an event to the database.
        '''
        pick_time = UTCDateTime('2011-01-01T00:00:00')
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'SITA')
        channel = channel[0]
        pick = Pick(label = 'P',
                    time = pick_time,
                    amp1 = 10,
                    channel = channel)
        self.project.dbEngine.echo = True
        pick.write_to_database(self.project)

        db_event_orm = self.project.dbTables['pick']
        db_session = self.project.getDbSession()
        result = db_session.query(db_event_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.id, pick.db_id)
        self.assertEqual(tmp.id, pick.db_id)
        self.assertEqual(tmp.label, 'P')
        self.assertEqual(tmp.amp1, 10)
        self.assertEqual(tmp.time, UTCDateTime('2011-01-01T00:00:00').timestamp)
        self.assertEqual(tmp.creation_time, pick.creation_time.isoformat())


    def test_update_pick_in_database(self):
        ''' Test the update of an event to the database.
        '''
        pick_time = UTCDateTime('2011-01-01T00:00:00')
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'SITA')
        channel = channel[0]
        pick = Pick(label = 'P',
                    time = pick_time,
                    amp1 = 10,
                    channel = channel)
        self.project.dbEngine.echo = True
        pick.write_to_database(self.project)
        db_id = pick.db_id

        pick.label = 'S'
        pick.amp1 = 20
        pick.time = UTCDateTime('2011-01-01T00:00:00')
        pick.write_to_database(self.project)

        db_event_orm = self.project.dbTables['pick']
        db_session = self.project.getDbSession()
        result = db_session.query(db_event_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.id, pick.db_id)
        self.assertEqual(tmp.label, 'S')
        self.assertEqual(tmp.amp1, 20)
        self.assertEqual(tmp.time, UTCDateTime('2011-01-01T00:00:00').timestamp)
        self.assertEqual(tmp.creation_time, pick.creation_time.isoformat())


    def test_create_pick_from_orm(self):
        ''' Test the conversion of an ORM instance.
        '''
        from sqlalchemy.orm import subqueryload

        pick_time = UTCDateTime('2011-01-01T00:00:00')
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'SITA')
        channel = channel[0]
        pick = Pick(label = 'P',
                    time = pick_time,
                    amp1 = 10,
                    channel = channel)
        self.project.dbEngine.echo = True
        pick.write_to_database(self.project)

        pick_orm_class = self.project.dbTables['pick']
        db_session = self.project.getDbSession()
        result = db_session.query(pick_orm_class).options(subqueryload(pick_orm_class.stream)).options(subqueryload('stream.parent')).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        pick_orm = result[0]

        pick = Pick.from_orm(pick_orm, inventory = self.project.geometry_inventory)

        self.assertIsInstance(pick, Pick)
        self.assertIsInstance(pick.channel, DbChannel)
        self.assertEqual(pick.channel.name, 'HHZ')
        self.assertEqual(pick.channel.parent_station.name, 'SITA')
        self.assertEqual(pick.label, 'P')
        self.assertEqual(pick.amp1, 10)
        self.assertEqual(pick.time, pick_time)



#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite(PickTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

