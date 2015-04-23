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
Test the pick catalog.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

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

import psysmon.packages.pick.core as pick_core


class PickCatalogTestCase(unittest.TestCase):
    """
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('INFO')
        logger.addHandler(psysmon.getLoggerHandler())

        # Set the data path.
        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')

        # Create an empty project.
        cls.psybase = create_psybase()
        cls.project = create_full_project(cls.psybase)
        cls.project.dbEngine.echo = True

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
        self.psybase.project_server.unregister_data()

        # Clear the picks database tables.
        tables_to_clear = ['pick', 'pick_catalog']
        for cur_name in tables_to_clear:
            cur_table = self.project.dbTables[cur_name]
            self.project.dbEngine.execute(cur_table.__table__.delete())


    def test_catalog_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Create an event with valid time limits.
        catalog = pick_core.Catalog(name = 'test_name')
        self.assertIsInstance(catalog, pick_core.Catalog)
        self.assertEqual(catalog.name, 'test_name')
        self.assertEqual(catalog.mode, 'time')
        self.assertIsNone(catalog.db_id)
        self.assertIsNone(catalog.description)
        self.assertIsNone(catalog.agency_uri)
        self.assertIsNone(catalog.author_uri)
        self.assertIsNotNone(catalog.creation_time)
        self.assertListEqual(catalog.picks, [])


    def test_add_picks(self):
        ''' Test the add_picks method.
        '''
        catalog = pick_core.Catalog(name = 'test')

        # Create the pick
        pick_time = UTCDateTime('2011-01-01T00:00:00')
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'SITA')
        channel = channel[0]
        pick = pick_core.Pick(label = 'P',
                              time = pick_time,
                              amp1 = 10,
                              channel = channel)
        catalog.add_picks([pick,])

        self.assertEqual(len(catalog.picks), 1)
        self.assertEqual(catalog.picks[0], pick)
        self.assertEqual(pick.parent, catalog)


    def test_write_to_database(self):
        ''' Test the write_to_database method.
        '''
        catalog = pick_core.Catalog(name = 'test',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')
        catalog.write_to_database(self.project)

        catalog_orm_class = self.project.dbTables['pick_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(catalog_orm_class).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(tmp.name, 'test')
        self.assertEqual(tmp.description, 'A test description.')
        self.assertEqual(tmp.agency_uri, 'uot')
        self.assertEqual(tmp.author_uri, 'tester')


    def test_write_to_database_with_picks(self):
        ''' Test the writing to the database of a catalog with events.
        '''
        catalog = pick_core.Catalog(name = 'test',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')

        # Create a pick.
        pick_time = UTCDateTime('2011-01-01T00:00:00')
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'SITA')
        channel = channel[0]
        pick1 = pick_core.Pick(label = 'P',
                               time = pick_time,
                               amp1 = 10,
                               channel = channel)
        pick2 = pick_core.Pick(label = 'S',
                               time = pick_time + 10,
                               amp1 = 20,
                               channel = channel)
        catalog.add_picks([pick1, pick2])

        catalog.write_to_database(self.project)


        catalog_orm_class = self.project.dbTables['pick_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(catalog_orm_class).all()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(len(tmp.picks), 2)
        self.assertEqual(tmp.picks[0].catalog_id, catalog.db_id)
        db_session.close()

        # Add a third pick and update the catalog in the database.
        channel = self.project.geometry_inventory.get_channel(name = 'HHZ', station = 'GUWA')
        channel = channel[0]
        pick3 = pick_core.Pick(label = 'P',
                               time = pick_time,
                               amp1 = 30,
                               channel = channel)

        catalog.add_picks([pick3,])
        catalog.write_to_database(self.project)

        db_session = self.project.getDbSession()
        result = db_session.query(catalog_orm_class).all()

        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(len(tmp.picks), 3)
        self.assertEqual(tmp.picks[0].catalog_id, catalog.db_id)
        self.assertEqual(tmp.picks[1].catalog_id, catalog.db_id)
        self.assertEqual(tmp.picks[2].catalog_id, catalog.db_id)
        db_session.close()




def suite():
    return unittest.makeSuite(PickCatalogTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

