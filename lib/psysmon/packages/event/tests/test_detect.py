'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import logging

import numpy as np
import numpy.testing as np_test

import psysmon
import psysmon.packages.event.detect as detect
import psysmon.core.test_util


class DetectTestCase(unittest.TestCase):
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

    def test_sta_lta_detector_creation(self):
        ''' Test the creation of the StaLtaDetector instance.
        '''
        detector = detect.StaLtaDetector()
        np_test.assert_array_equal(detector.cf, np.empty((0,0)))
        np_test.assert_array_equal(detector.thrf, np.empty((0,0)))
        np_test.assert_array_equal(detector.sta, np.empty((0,0)))
        np_test.assert_array_equal(detector.lta, np.empty((0,0)))

        np_test.assert_raises(ValueError, detect.StaLtaDetector, cf_type = 'not_valid')



    def test_set_data(self):
        ''' Test the setting of the data.
        '''
        data = np.arange(10)
        detector = detect.StaLtaDetector()
        detector.set_data(data)

        np_test.assert_array_equal(detector.data, data)
        np_test.assert_array_equal(detector.cf, np.empty((0,0)))
        np_test.assert_array_equal(detector.thrf, np.empty((0,0)))
        np_test.assert_array_equal(detector.sta, np.empty((0,0)))
        np_test.assert_array_equal(detector.lta, np.empty((0,0)))

    def test_compute_cf(self):
        ''' Test the computation of the characteristic function.
        '''
        data = np.arange(10)
        detector = detect.StaLtaDetector()
        detector.compute_cf()
        np_test.assert_array_equal(detector.data, np.empty((0,0)))
        np_test.assert_array_equal(detector.cf, np.empty((0,0)))

        detector.set_data(data = data)
        detector.cf_type = 'abs'
        detector.compute_cf()
        np_test.assert_array_equal(detector.data, data)
        np_test.assert_array_equal(detector.cf, np.abs(data))

        detector.cf_type = 'square'
        detector.compute_cf()
        np_test.assert_array_equal(detector.data, data)
        np_test.assert_array_equal(detector.cf, data**2)


    def test_compute_sta_lta(self):
        ''' Test the computation of the threshold function.
        '''
        seismo = psysmon.core.test_util.compute_synthetic_seismogram(length = 5,
                                                                     sps = 1000,
                                                                     wavelet_offset = 2)
        detector = detect.StaLtaDetector(data = seismo)
        detector.compute_cf()
        detector.compute_sta_lta()



def suite():
    return unittest.makeSuite(DetectTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

