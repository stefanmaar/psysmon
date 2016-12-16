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

import psysmon.packages.event.detect as detect


class DetectionCatalogTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
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
        self.psybase.project_server.unregister_data()
        clear_project_database_tables(self.project)

    def test_catalog_creation(self):
        ''' Test the pSysmon Event class.
        '''
        # Create an event with valid time limits.
        catalog = detect.Catalog(name = 'test_name')
        self.assertIsInstance(catalog, detect.Catalog)
        self.assertEqual(catalog.name, 'test_name')
        self.assertIsNone(catalog.db_id)
        self.assertIsNone(catalog.description)
        self.assertIsNone(catalog.agency_uri)
        self.assertIsNone(catalog.author_uri)
        self.assertIsNotNone(catalog.creation_time)
        self.assertListEqual(catalog.detections, [])


    def test_add_detections(self):
        ''' Test the add_events method.
        '''
        catalog = detect.Catalog(name = 'test')

        # Create a detection.
        start_time = '2000-01-01T00:00:00'
        end_time = '2000-01-01T01:00:00'
        creation_time = UTCDateTime()
        det = detect.Detection(start_time = start_time,
                                 end_time = end_time,
                                 creation_time = creation_time)

        catalog.add_detections([det,])

        self.assertEqual(len(catalog.detections), 1)
        self.assertEqual(catalog.detections[0], det)
        self.assertEqual(det.parent, catalog)


    def test_write_to_database(self):
        ''' Test the write_to_database method.
        '''
        creation_time = UTCDateTime()
        catalog = detect.Catalog(name = 'test',
                          description = 'A test description.',
                          agency_uri = 'uot',
                          author_uri = 'tester',
                          creation_time = creation_time)
        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['detection_catalog']
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


    def test_write_to_database_with_detections(self):
        ''' Test the writing to the database of a catalog with detections.
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
                                 creation_time = creation_time)

        catalog.add_detections([det,])


        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['detection_catalog']
        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(len(tmp.detections), 1)
        self.assertEqual(tmp.detections[0].catalog_id, catalog.db_id)

        # Add a second event.
        start_time = '2000-01-02T00:00:00'
        end_time = '2000-01-02T01:00:00'
        creation_time = UTCDateTime()
        det = detect.Detection(start_time = start_time,
                      end_time = end_time,
                      creation_time = creation_time)
        catalog.add_detections([det,])
        catalog.write_to_database(self.project)

        db_session = self.project.getDbSession()
        result = db_session.query(db_catalog_orm).all()
        db_session.close()
        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertEqual(len(tmp.detections), 2)
        self.assertEqual(tmp.detections[0].catalog_id, catalog.db_id)
        self.assertEqual(tmp.detections[1].catalog_id, catalog.db_id)


    def test_load_detections(self):
        ''' Test the loading of detections from the database.
        '''
        creation_time = UTCDateTime()
        catalog = detect.Catalog(name = 'test',
                          description = 'A test description.',
                          agency_uri = 'uot',
                          author_uri = 'tester',
                          creation_time = creation_time)

        # Create detections and add it to the catalog.
        det_start_times = ['2000-01-01T00:00:00',
                           '2000-01-01T01:00:00',
                           '2000-01-01T02:00:00']

        for cur_start_time in det_start_times:
            start_time = UTCDateTime(cur_start_time)
            end_time = start_time + 10
            creation_time = UTCDateTime()
            det = detect.Detection(start_time = start_time,
                                     end_time = end_time,
                                     creation_time = creation_time)
            catalog.add_detections([det,])
        catalog.write_to_database(self.project)

        db_catalog_orm = self.project.dbTables['detection_catalog']
        db_session = self.project.getDbSession()
        query = db_session.query(db_catalog_orm).filter(db_catalog_orm.name.in_(['test',]))
        if db_session.query(query.exists()):
            cur_db_catalog = query.first()
            loaded_catalog = detect.Catalog.from_db_catalog(cur_db_catalog, load_detections = False)
        db_session.close()

        self.assertEqual(loaded_catalog.detections, [])
        loaded_catalog.load_detections(self.project)
        self.assertEqual(len(loaded_catalog.detections), len(det_start_times))




def suite():
    return unittest.makeSuite(DetectionCatalogTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

