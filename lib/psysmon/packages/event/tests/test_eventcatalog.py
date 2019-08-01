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
'''
Test the event catalog.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

'''
from __future__ import print_function

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

import psysmon.packages.event.core as ev_core
import psysmon.packages.event.bulletin as ev_bulletin



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

        # Set the data path.
        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')

        # Create an empty project.
        cls.psybase = create_psybase()
        cls.project = create_empty_project(cls.psybase)
        cls.project.dbEngine.echo = True

    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print("dropping database tables...\n")
        drop_project_database_tables(cls.project)
        print("removing temporary file structure....\n")
        remove_project_filestructure(cls.project)
        print("removing temporary base directory....\n")
        os.removedirs(cls.project.base_dir)
        print("....finished cleaning up.\n")

    def setUp(self):
        pass

    def tearDown(self):
        self.psybase.project_server.unregister_data()
        clear_project_database_tables(self.project)

    def test_catalog_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Create an event with valid time limits.
        catalog = ev_core.Catalog(name = 'test_name')
        self.assertIsInstance(catalog, ev_core.Catalog)
        self.assertEqual(catalog.name, 'test_name')
        self.assertIsNone(catalog.db_id)
        self.assertIsNone(catalog.description)
        self.assertIsNone(catalog.agency_uri)
        self.assertIsNone(catalog.author_uri)
        self.assertIsNotNone(catalog.creation_time)
        self.assertListEqual(catalog.events, [])


    def test_add_events(self):
        ''' Test the add_events method.
        '''
        catalog = ev_core.Catalog(name = 'test')

        # Create an event.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = ev_core.Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)

        catalog.add_events([event,])

        self.assertEqual(len(catalog.events), 1)
        self.assertEqual(catalog.events[0], event)
        self.assertEqual(event.parent, catalog)


    def test_write_to_database(self):
        ''' Test the write_to_database method.
        '''
        creation_time = UTCDateTime()
        catalog = ev_core.Catalog(name = 'test',
                          description = 'A test description.',
                          agency_uri = 'uot',
                          author_uri = 'tester',
                          creation_time = creation_time)
        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['event_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.name, 'test')
        self.assertEqual(tmp.description, 'A test description.')
        self.assertEqual(tmp.agency_uri, 'uot')
        self.assertEqual(tmp.author_uri, 'tester')
        self.assertEqual(tmp.creation_time, creation_time.isoformat())


    def test_write_to_database_with_events(self):
        ''' Test the writing to the database of a catalog with events.
        '''
        creation_time = UTCDateTime()
        catalog = ev_core.Catalog(name = 'test',
                          description = 'A test description.',
                          agency_uri = 'uot',
                          author_uri = 'tester',
                          creation_time = creation_time)

        # Create an event.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        event = ev_core.Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)

        catalog.add_events([event,])

        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['event_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(len(tmp.events), 1)
        self.assertEqual(tmp.events[0].ev_catalog_id, catalog.db_id)

        # Add a second event.
        start_time = '2000-01-02T00:00:00'
        end_time = '2000-01-02T01:00:00'
        creation_time = UTCDateTime()
        event = ev_core.Event(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)

        catalog.add_events([event,])
        catalog.write_to_database(self.project)

        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(len(tmp.events), 2)
        self.assertEqual(tmp.events[0].ev_catalog_id, catalog.db_id)
        self.assertEqual(tmp.events[1].ev_catalog_id, catalog.db_id)



    def test_write_bulletin_to_database(self):
        ''' Test the import of a bulletin into the database.
        '''
        bulletin_file = os.path.join(self.data_path, 'bulletin_ims1.0_1.txt')
        parser = ev_bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(name = 'REB', agency_uri = 'REB')

        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['event_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.name, 'REB')
        self.assertEqual(len(tmp.events), 1)
        cur_event = tmp.events[0]
        self.assertEqual(cur_event.public_id, '112460')
        self.assertEqual(cur_event.description, 'Southeast of Honshu, Japan')

        # Clear the database tables.
        clear_project_database_tables(self.project)

        bulletin_file = os.path.join(self.data_path, 'bulletin_zamg_ims1.0_1.txt')
        parser = ev_bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(name = 'ZAMG_AUTODRM', agency_uri = 'ZAMG')

        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['event_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)




def suite():
    return unittest.makeSuite(EventCatalogTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

