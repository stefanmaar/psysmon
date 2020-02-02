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
Test the event library.

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

import obspy.core.utcdatetime as utcdatetime

import psysmon

from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_empty_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import clear_project_database_tables
from psysmon.core.test_util import remove_project_filestructure

import psysmon.packages.event.core as ev_core
import psysmon.packages.event.bulletin as ev_bulletin


class EventLibraryTestCase(unittest.TestCase):
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
        cls.project = create_empty_project(cls.psybase)
        cls.project.dbEngine.echo = False

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
        clear_project_database_tables(self.project)

    def test_library_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Create an event with valid time limits.
        library = ev_core.Library(name = 'test_name')
        self.assertIsInstance(library, ev_core.Library)
        self.assertEqual(library.name, 'test_name')
        self.assertIsInstance(library.catalogs, dict)
        self.assertEqual(library.catalogs, {})


    def test_load_catalog_from_db(self):
        ''' Test the loading of catalogs from the database.
        '''
        # Write event data to the database.
        bulletin_file = os.path.join(self.data_path, 'bulletin_ims1.0_1.txt')
        parser = ev_bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(name = 'REB', agency_uri = 'REB')
        catalog.write_to_database(self.project)

        bulletin_file = os.path.join(self.data_path, 'bulletin_zamg_ims1.0_1.txt')
        parser = ev_bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(name = 'ZAMG_AUTODRM', agency_uri = 'ZAMG')
        catalog.write_to_database(self.project)

        # Create the library and test the loading of one catalog.
        library = ev_core.Library(name = 'test_name')
        library.load_catalog_from_db(project = self.project, name = 'REB')

        self.assertEqual(len(library.catalogs), 1)
        self.assertEqual(iter(library.catalogs.keys()), ['REB'])
        self.assertIsInstance(library.catalogs['REB'], ev_core.Catalog)

        cur_catalog = library.catalogs['REB']
        self.assertEqual(len(cur_catalog.events), 1)
        cur_event = cur_catalog.events[0]
        self.assertIsInstance(cur_event, ev_core.Event)
        self.assertEqual(cur_event.public_id, '112460')

        # Create the library and test the loading of multiple catalogs.
        library = ev_core.Library(name = 'test_name')
        library.load_catalog_from_db(project = self.project, name = ['REB', 'ZAMG_AUTODRM'])
        self.assertEqual(len(library.catalogs), 2)
        self.assertListEqual(sorted(library.catalogs.keys()), ['REB', 'ZAMG_AUTODRM'])


    def test_get_catalogs_in_db(self):
        ''' Test the query of catalog names from the database.
        '''
        # Write event data to the database.
        bulletin_file = os.path.join(self.data_path, 'bulletin_zamg_ims1.0_1.txt')
        parser = ev_bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(name = 'ZAMG_AUTODRM', agency_uri = 'ZAMG')
        catalog.write_to_database(self.project)

        bulletin_file = os.path.join(self.data_path, 'bulletin_ims1.0_1.txt')
        parser = ev_bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(name = 'REB', agency_uri = 'REB')
        catalog.write_to_database(self.project)


        # Create the library.
        library = ev_core.Library(name = 'test_name')
        catalog_names = library.get_catalogs_in_db(project = self.project)

        self.assertIsInstance(catalog_names, list)
        self.assertEqual(len(catalog_names), 2)
        self.assertListEqual(catalog_names, ['REB', 'ZAMG_AUTODRM'])









def suite():
    return unittest.makeSuite(EventLibraryTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

