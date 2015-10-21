# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
Test case for the waveclient module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import unittest
import logging

from obspy.core.utcdatetime import UTCDateTime

import psysmon
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_empty_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import clear_project_database_tables
from psysmon.core.test_util import remove_project_filestructure
import tempfile
import os

class WaveclientTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')

        cls.psybase = create_psybase()
        cls.project = create_empty_project(cls.psybase)
        cls.project.dbEngine.echo = True


    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print "dropping database tables...\n"
        drop_project_database_tables(cls.project)
        print "removing temporary file structure....\n"
        remove_project_filestructure(cls.project)
        print "removing temporary base directory....\n"
        os.removedirs(cls.project.base_dir)
        print "....finished cleaning up.\n"


    def setUp(self):
        pass

    def tearDown(self):
        clear_project_database_tables(self.project)



    def test_earthworm_waveclient(self):
        ''' Test the earthworm waveclient.
        '''
        from psysmon.core.waveclient import EarthwormWaveclient
        client = EarthwormWaveclient('test client', 'pubavo1.wr.usgs.gov', 16022)
        # Request the available stations.
        av_stat = client.client.availability('AV', channel = 'BHZ')
        cur_stat = av_stat[0]

        request_interval = 30
        start_time = cur_stat[5] - 120
        end_time = start_time + request_interval

        # Test the request of a data stream.
        cur_scnl = (cur_stat[1], cur_stat[3], cur_stat[0], cur_stat[2])
        stream = client.getWaveform(start_time, end_time, [cur_scnl,])
        self.assertEqual(len(stream), 1)
        delta = stream[0].stats.delta
        trace = stream[0]
        self.assertTrue(request_interval - delta <= (trace.stats.endtime - trace.stats.starttime) <= request_interval + delta)
        self.assertTrue(trace.stats.starttime >= start_time - delta)
        self.assertTrue(trace.stats.starttime <= start_time + delta)
        self.assertTrue(trace.stats.endtime >= end_time - delta)
        self.assertTrue(trace.stats.endtime <= end_time + delta)
        self.assertEqual(trace.stats.station, cur_scnl[0])
        self.assertEqual(trace.stats.channel, cur_scnl[1])
        self.assertEqual(trace.stats.network, cur_scnl[2])
        if cur_scnl[3] == '--':
            check_location = ''
        self.assertEqual(trace.stats.location, check_location)

        # Get the same data from the client stock.
        stock_stream = client.get_from_stock(station = cur_scnl[0],
                                             channel = cur_scnl[1],
                                             network = cur_scnl[2],
                                             location = cur_scnl[3],
                                             start_time = start_time,
                                             end_time = end_time)

        self.assertTrue(stock_stream == stream)

        # Preload data
        start_time = start_time - request_interval
        end_time = start_time + request_interval
        t = client.preload(start_time = start_time,
                           end_time = end_time,
                           scnl = [cur_scnl,])
        # Wait for the thread to join.
        t.join()
        # Get the preloaded data from the client stock.
        stock_stream = client.get_from_stock(station = cur_scnl[0],
                                             channel = cur_scnl[1],
                                             network = cur_scnl[2],
                                             location = cur_scnl[3],
                                             start_time = start_time,
                                             end_time = end_time)
        self.assertEqual(len(stock_stream), 1)
        trace = stock_stream[0]
        self.assertTrue(request_interval - delta <= (trace.stats.endtime - trace.stats.starttime) <= request_interval + delta)
        self.assertTrue(trace.stats.starttime >= start_time - delta)
        self.assertTrue(trace.stats.starttime <= start_time + delta)
        self.assertTrue(trace.stats.endtime >= end_time - delta)
        self.assertTrue(trace.stats.endtime <= end_time + delta)
        self.assertEqual(trace.stats.station, cur_scnl[0])
        self.assertEqual(trace.stats.channel, cur_scnl[1])
        self.assertEqual(trace.stats.network, cur_scnl[2])
        if cur_scnl[3] == '--':
            check_location = ''
        self.assertEqual(trace.stats.location, check_location)





def suite():
    return unittest.makeSuite(WaveclientTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

