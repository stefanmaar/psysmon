import unittest
import logging
import os

from obspy.core.utcdatetime import UTCDateTime

import psysmon

import psysmon.packages.reftek as rt
import psysmon.packages.reftek.archive

class RtArchiveControllerCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('INFO')
        logger.addHandler(psysmon.getLoggerHandler())


    @classmethod
    def tearDownClass(cls):
        pass


    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_scan(self):
        ''' Test the scanning of a Reftek archive.
        '''
        ac = rt.archive.ArchiveController('/home/stefan/Desktop/rt_archive',
                                          output_directory = './converted')
        ac.scan()
        ac.archive_to_mseed(unit_id = '9DC8',
                            stream = 1,
                            start_time = UTCDateTime(2011,4,22,0,0,0),
                            end_time = UTCDateTime(2011,4,22,12,0,0))

def suite():
    return unittest.makeSuite(RtArchiveControllerCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

