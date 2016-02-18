'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import logging
import os
import psysmon

import psysmon.packages.event.bulletin as bulletin

class BulletinTestCase(unittest.TestCase):
    """
    Test suite
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_ims_parser(self):
        ''' Test IMS1.0 bulletin file parser.
        '''
        # Create an event with valid time limits.
        bulletin_file = os.path.join(self.data_path, 'bulletin_ims1.0_1.txt')
        #bulletin_file = os.path.join(self.data_path, 'bulletin_zamg_ims1.0_1.txt')
        parser = bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog()

        cur_events = catalog.events
        self.assertEqual(len(cur_events), 1)
        self.assertEqual(cur_events[0].public_id, '112460')
        self.assertEqual(cur_events[0].description, 'Southeast of Honshu, Japan')

        bulletin_file = os.path.join(self.data_path, 'bulletin_zamg_ims1.0_1.txt')
        parser = bulletin.ImsParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog()

        cur_events = catalog.events
        self.assertEqual(len(cur_events), 13)


    def test_csv_parser(self):
        ''' Test the csv parser.
        '''
        bulletin_file = os.path.join(self.data_path, 'bulletin_csv_1.txt')
        parser = bulletin.CsvParser()
        parser.parse(bulletin_file)
        catalog = parser.get_catalog(author_uri = 'stest',
                                     agency_uri = 'at.uot')

        cur_events = catalog.events
        self.assertEqual(len(cur_events), 3)

        # Check the public id.
        self.assertEqual(cur_events[0].public_id, 'event_1')
        self.assertEqual(cur_events[1].public_id, 'event_2')
        self.assertEqual(cur_events[2].public_id, 'event_3')

        # Check the start time.
        self.assertEqual(cur_events[0].start_time.isoformat(), '2015-01-01T01:00:00')
        self.assertEqual(cur_events[1].start_time.isoformat(), '2015-01-02T01:00:00')
        self.assertEqual(cur_events[2].start_time.isoformat(), '2015-11-30T13:20:00')

        # Check the end time.
        self.assertEqual(cur_events[0].end_time.isoformat(), '2015-01-01T01:00:10')
        self.assertEqual(cur_events[1].end_time.isoformat(), '2015-01-02T01:00:10')
        self.assertEqual(cur_events[2].end_time.isoformat(), '2015-11-30T13:21:00')

        # Check the end time.
        self.assertEqual(cur_events[0].description, 'example event 1')
        self.assertEqual(cur_events[1].description, 'example event 2')
        self.assertEqual(cur_events[2].description, 'example event 3')

        # Check the author uri.
        self.assertEqual(cur_events[0].author_uri, 'sm')
        self.assertEqual(cur_events[1].author_uri, 'stest')
        self.assertEqual(cur_events[2].author_uri, 'stest')

        # Check the agency uri.
        self.assertEqual(cur_events[0].agency_uri, 'mr')
        self.assertEqual(cur_events[1].agency_uri, 'at.uot')
        self.assertEqual(cur_events[2].agency_uri, 'at.uot')

def suite():
    return unittest.makeSuite(BulletinTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

