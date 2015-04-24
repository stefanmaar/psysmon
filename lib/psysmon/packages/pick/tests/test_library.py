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
Test the pick library.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/licenses/gpl-3.0.html)

'''

import unittest
import logging
import os

import psysmon

from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure

from obspy.core.utcdatetime import UTCDateTime

import psysmon.packages.pick.core as pick_core


class PickLibraryTestCase(unittest.TestCase):
    """
    Test suite
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

    def test_library_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Create an event with valid time limits.
        library = pick_core.Library(name = 'test_name')
        self.assertIsInstance(library, pick_core.Library)
        self.assertEqual(library.name, 'test_name')
        self.assertIsInstance(library.catalogs, dict)
        self.assertEqual(library.catalogs, {})


    def test_get_catalogs_in_db(self):
        ''' Test the query of catalog names from the database.
        '''
        catalog = pick_core.Catalog(name = 'catalog_name_1',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')
        catalog.write_to_database(self.project)

        catalog = pick_core.Catalog(name = 'catalog_name_2',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')
        catalog.write_to_database(self.project)

        catalog = pick_core.Catalog(name = 'catalog_name_3',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')
        catalog.write_to_database(self.project)

        # Create the library.
        library = pick_core.Library(name = 'test_name')
        catalog_names = library.get_catalogs_in_db(project = self.project)

        self.assertIsInstance(catalog_names, list)
        self.assertEqual(len(catalog_names), 3)
        self.assertListEqual(catalog_names, ['catalog_name_1', 'catalog_name_2', 'catalog_name_3'])


    def test_load_catalog_from_db(self):
        ''' Test the loading of catalogs from the database.
        '''
        catalog = pick_core.Catalog(name = 'catalog_name_1',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')

        # Create some picks.
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

        # Create a second catalog.
        catalog = pick_core.Catalog(name = 'catalog_name_2',
                                    description = 'A test description.',
                                    agency_uri = 'uot',
                                    author_uri = 'tester')
        catalog.write_to_database(self.project)

        # Create the library.
        library = pick_core.Library(name = 'test_name')

        # Test the loading of one catalog without picks.
        library.load_catalog_from_db(project = self.project,
                                     name = 'catalog_name_1')

        self.assertEqual(len(library.catalogs), 1)
        self.assertEqual(library.catalogs.keys(), ['catalog_name_1'])
        self.assertIsInstance(library.catalogs['catalog_name_1'], pick_core.Catalog)

        cur_catalog = library.catalogs['catalog_name_1']
        self.assertEqual(len(cur_catalog.picks), 0)

        # Test the loading of one catalog without picks.
        library.clear()
        library.load_catalog_from_db(project = self.project,
                                     name = 'catalog_name_1',
                                     load_picks = True)

        self.assertEqual(len(library.catalogs), 1)
        self.assertEqual(library.catalogs.keys(), ['catalog_name_1'])
        self.assertIsInstance(library.catalogs['catalog_name_1'], pick_core.Catalog)

        cur_catalog = library.catalogs['catalog_name_1']
        self.assertEqual(len(cur_catalog.picks), 2)


        # Test the loading of all catalogs.
        library.clear()
        catalog_names = library.get_catalogs_in_db(project = self.project)
        library.load_catalog_from_db(project = self.project, name = catalog_names)
        self.assertEqual(len(library.catalogs), 2)
        self.assertListEqual(sorted(library.catalogs.keys()), ['catalog_name_1', 'catalog_name_2'])











def suite():
    return unittest.makeSuite(PickLibraryTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

