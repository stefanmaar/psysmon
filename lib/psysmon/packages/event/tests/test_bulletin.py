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
        parser = bulletin.ImsParser()
        catalogs = parser.parse(bulletin_file)



def suite():
    return unittest.makeSuite(BulletinTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

