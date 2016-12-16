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
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_database_tables

import psysmon.packages.event.detect as detect


class DetectionTestCase(unittest.TestCase):
    '''
    '''

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

    def test_detection_creation(self):
        ''' Test the pSysmon Detection class.
        '''
        # Test the control of None values of the time limits.
        self.assertRaises(ValueError, detect.Detection, start_time = None, end_time = None)
        self.assertRaises(ValueError, detect.Detection, start_time = '2000-01-01', end_time = None)
        self.assertRaises(ValueError, detect.Detection, start_time = None, end_time = '2000-01-01')

        # Test the control of the time limits.
        self.assertRaises(ValueError, detect.Detection, start_time = '2000-01-01', end_time = '1999-01-01')
        self.assertRaises(ValueError, detect.Detection, start_time = '2000-01-01', end_time = '2000-01-01')

        # Create an event with valid time limits.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        det = detect.Detection(start_time = start_time, end_time = end_time)
        self.assertIsInstance(det, detect.Detection)
        self.assertEqual(det.start_time, UTCDateTime(start_time))
        self.assertEqual(det.end_time, UTCDateTime(end_time))
        self.assertTrue(det.changed)


    def test_write_detection_to_database(self):
        ''' Test the writing of a detection to the database.
        '''
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        det = detect.Detection(start_time = start_time,
                                 end_time = end_time,
                                 creation_time = creation_time)
        self.project.dbEngine.echo = True
        det.write_to_database(self.project)

        db_detection_orm = self.project.dbTables['detection']
        db_session = self.project.getDbSession()
        result = db_session.query(db_detection_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.start_time, det.start_time.timestamp)
        self.assertEqual(tmp.end_time, det.end_time.timestamp)
        self.assertEqual(tmp.creation_time, det.creation_time.isoformat())


    def test_update_detection_in_database(self):
        ''' Test the update of a detection to the database.
        '''
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        det = detect.Detection(start_time = start_time,
                                 end_time = end_time,
                                 creation_time = creation_time)
        self.project.dbEngine.echo = True
        det.write_to_database(self.project)
        db_id = det.db_id


        start_time = UTCDateTime('2000-01-02T00:00:00')
        end_time = UTCDateTime('2000-01-02T01:00:00')
        det.start_time = start_time
        det.end_time = end_time
        det.write_to_database(self.project)

        db_detection_orm = self.project.dbTables['detection']
        db_session = self.project.getDbSession()
        result = db_session.query(db_detection_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.id, db_id)
        self.assertEqual(tmp.id, det.db_id)
        self.assertEqual(tmp.start_time, det.start_time.timestamp)
        self.assertEqual(tmp.end_time, det.end_time.timestamp)
        self.assertEqual(tmp.creation_time, det.creation_time.isoformat())



class GeometryDetectionCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('INFO')
        logger.addHandler(psysmon.getLoggerHandler(log_level = 'DEBUG'))

        drop_database_tables(db_dialect = 'mysql',
                              db_driver = None,
                              db_host = 'localhost',
                              db_name = 'psysmon_unit_test',
                              db_user = 'unit_test',
                              db_pwd = 'test',
                              project_name = 'unit_test')


        cls.psybase = create_psybase()
        create_full_project(cls.psybase)
        cls.project = cls.psybase.project
        cls.project.dbEngine.echo = False
        logger.setLevel('DEBUG')


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

    def test_detection(self):
        '''
        '''
        creation_time = UTCDateTime()
        catalog = detect.Catalog(name = 'test',
                          description = 'A test description.',
                          agency_uri = 'uot',
                          author_uri = 'tester',
                          creation_time = creation_time)

        # Create a detection and add it to the catalog.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        det = detect.Detection(start_time = start_time,
                                 end_time = end_time,
                                 creation_time = creation_time,
                                 rec_stream_id = 1)
        catalog.add_detections([det,])
        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['detection_catalog']
        db_session = self.project.getDbSession()
        try:
            query = db_session.query(db_catalog_orm).filter(db_catalog_orm.name.in_(['test',]))
            if db_session.query(query.exists()):
                cur_db_catalog = query.first()
                loaded_catalog = detect.Catalog.from_db_catalog(cur_db_catalog, load_detections = True)
        finally:
            db_session.close()

        det = loaded_catalog.detections[0]
        channel = self.project.geometry_inventory.get_channel_from_stream(id = det.rec_stream_id)


def suite():
#    tests = ['testXmlImport']
#    return unittest.TestSuite(map(InventoryTestCase, tests))
    return unittest.makeSuite([DetectionTestCase, GeometryDetectionCase], 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

