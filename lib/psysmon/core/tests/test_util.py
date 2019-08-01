'''
Created on May 17, 2011

@author: Stefan Mertl
'''
from __future__ import print_function

import logging
import unittest

import psysmon
import psysmon.core.util as util

class UtilTestCase(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler(log_level = 'DEBUG'))


    @classmethod
    def tearDownClass(cls):
        print("....in tearDownClass.\n")


    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_version(self):
        ''' Test the version class.
        '''
        version = util.Version()
        self.assertEqual(version.version, (0,0,1))

        version = util.Version('1.0.0')
        self.assertEqual(version.version, (1,0,0))

        # Test compare equal.
        version_1 = util.Version('1.0.0')
        version_2 = util.Version('1.0.0')
        self.assertTrue(version_1 == version_2)
        version_2 = util.Version('1.0.1')
        self.assertFalse(version_1 == version_2)
        version_2 = util.Version('1.1.1')
        self.assertFalse(version_1 == version_2)
        version_2 = util.Version('0.0.1')
        self.assertFalse(version_1 == version_2)

        # Test greater than.
        version_1 = util.Version('1.0.0')
        version_2 = util.Version('1.0.0')
        self.assertFalse(version_1 > version_2)
        version_2 = util.Version('1.0.1')
        self.assertTrue(version_2 > version_1)
        version_2 = util.Version('0.10.1')
        self.assertFalse(version_2 > version_1)
        version_2 = util.Version('2.0.0')
        self.assertTrue(version_2 > version_1)

        # Test less than.
        version_1 = util.Version('1.0.0')
        version_2 = util.Version('1.0.0')
        self.assertFalse(version_1 < version_2)
        version_2 = util.Version('0.0.1')
        self.assertFalse(version_1 < version_2)
        version_2 = util.Version('0.10.3')
        self.assertFalse(version_1 < version_2)
        version_1 = util.Version('10.9.4')
        version_2 = util.Version('10.10.3')
        self.assertTrue(version_1 < version_2)

        # Test for greater or equal.
        version_1 = util.Version('1.0.0')
        version_2 = util.Version('1.0.0')
        self.assertTrue(version_1 >= version_2)
        version_2 = util.Version('0.0.1')
        self.assertTrue(version_1 >= version_2)
        version_2 = util.Version('2.0.1')
        self.assertFalse(version_1 >= version_2)

        # Test for less or equal.
        version_1 = util.Version('1.0.0')
        version_2 = util.Version('1.0.0')
        self.assertTrue(version_1 <= version_2)
        version_2 = util.Version('0.0.1')
        self.assertFalse(version_1 <= version_2)
        version_2 = util.Version('2.0.1')
        self.assertTrue(version_1 <= version_2)



def suite():
    return unittest.makeSuite(UtilTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

