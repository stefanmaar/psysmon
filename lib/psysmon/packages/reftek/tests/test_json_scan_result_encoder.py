'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest

import psysmon.packages.reftek.archive as rt_archive

class JsonScanResultEncoderTestCase(unittest.TestCase):
    """
    """

    @classmethod
    def setUpClass(cls):
        #cls.packages_path = os.path.dirname(os.path.abspath(__file__))
        #cls.packages_path = os.path.join(cls.packages_path, 'packages')
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_default(self):
        '''
        '''
        ac = rt_archive.ArchiveController('/home/stefan/Desktop/rt_archive')
        ac.scan()



def suite():
    return unittest.makeSuite(JsonScanResultEncoderTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')




