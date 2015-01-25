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
from psysmon.packages.event.core import Catalog



class EventCatalogTestCase(unittest.TestCase):
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

    def test_catalog_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Create an event with valid time limits.
        catalog = Catalog()
        self.assertIsInstance(catalog, Catalog)
        self.assertIsNone(catalog.db_id)
        self.assertIsNone(catalog.description)
        self.assertIsNone(catalog.agency_uri)
        self.assertIsNone(catalog.author_uri)
        self.assertIsNotNone(catalog.creation_time)
        self.assertListEqual(catalog.events, [])


    def test_add_events(self):
        ''' Test the add_events method.
        '''
        catalog = Catalog()

        # Create an event.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)

        catalog.add_events([event,])

        self.assertEqual(len(catalog.events), 1)
        self.assertEqual(catalog.events[0], event)



def suite():
    return unittest.makeSuite(EventCatalogTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

