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
        ac = rt.archive.ArchiveController('/home/stefan/Desktop/rt_archive')
        ac.scan()
        raw_stream = ac.units['9DC8'].streams[1]
        raw_stream.sort_raw_files()
        for cur_file in raw_stream.raw_files:
            print cur_file.filename
            st = raw_stream.parse(cur_file)

def suite():
    return unittest.makeSuite(RtArchiveControllerCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

