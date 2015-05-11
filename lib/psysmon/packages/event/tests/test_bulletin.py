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





def suite():
    return unittest.makeSuite(BulletinTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

