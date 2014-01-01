'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import os
import logging
import psysmon
import psysmon.core.packageSystem

class PackageManagerTestCase(unittest.TestCase):
    """
    Test suite for psysmon.core.packageSystem.PackageManager.
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        cls.packages_path = os.path.dirname(os.path.abspath(__file__))
        cls.packages_path = os.path.join(cls.packages_path, 'packages')


    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"


    def setUp(self):
        pass

    def tearDown(self):
        pass



    def test_package_manager_creation(self):
        pkg_manager = psysmon.core.packageSystem.PackageManager()


    def test_scan_4_packages(self):
        package_directories = [self.packages_path, ]
        pkg_manager = psysmon.core.packageSystem.PackageManager(packageDirectories = package_directories)
        pkg_manager.scan4Package()


def suite():
    return unittest.makeSuite(PackageManagerTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

