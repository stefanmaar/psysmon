'''
Created on May 17, 2011

@author: Stefan Mertl
'''
from __future__ import print_function

import unittest
import psysmon.core.lib_signal as lib_signal
import numpy as np
import numpy.testing as np_test

class CLibSignalTestCase(unittest.TestCase):
    """

    """

    @classmethod
    def setUpClass(cls):
        print("In setUpClass...\n")


    @classmethod
    def tearDownClass(cls):
        print("Cleaning up....\n")
        print("done.\n")


    def setUp(self):
        print("Setting up test method...")

    def tearDown(self):
        print("Tearing down test method...")


    def test_moving_average(self):
        ''' Test the moving average function.
        '''
        clib_signal = lib_signal.clib_signal

        n_data = 10
        n_op = 3
        data = np.arange(n_data)
        data = np.ascontiguousarray(data, dtype = np.float64)
        avg = np.empty(n_data, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_data, n_op, data, avg)

        self.assertEqual(ret_val, 0)
        np_test.assert_equal(avg, [0, 1/3., 1, 2, 3, 4, 5, 6, 7, 8])

        n_data = 100
        n_op = 10
        data = np.ones(n_data) * 2
        data = np.ascontiguousarray(data, dtype = np.float64)
        avg = np.empty(n_data, dtype = np.float64)

        ret_val = clib_signal.moving_average(n_data, n_op, data, avg)
        self.assertEqual(len(avg), n_data)
        np_test.assert_almost_equal(np.max(avg[9:]), 2)
        np_test.assert_almost_equal(np.min(avg[9:]), 2)


def suite():
    return unittest.makeSuite(CLibSignalTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

