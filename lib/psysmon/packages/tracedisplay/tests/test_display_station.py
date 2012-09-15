'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import tempfile
import os
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.tracedisplay.tracedisplay import DisplayStation
from psysmon.packages.tracedisplay.tracedisplay import DisplayChannel

class DisplayStationTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"


    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"
        #os.removedir(cls.base_dir)


    def setUp(self):
        # Create the standart test station.
        station = Station(name = 'GUWA',
                          location = '00',
                          x = 15.346444,
                          y = 47.696306,
                          z = 880,
                          coordSystem = 'epsg:4326',
                          description = 'Gusswerk',
                          network = 'XX')
        
        self.station_loc_00 = DisplayStation(station = station)
        
        # Create a station with the '--' location.
        station = Station(name = 'GUWA',
                          location = '--',
                          x = 15.346444,
                          y = 47.696306,
                          z = 880,
                          coordSystem = 'epsg:4326',
                          description = 'Gusswerk',
                          network = 'XX')
        self.station_loc_none = DisplayStation(station = station)

    def tearDown(self):
        pass


    def test_obspy_location(self):  
        ''' Test the obspy_location attribute.
        ''' 
        self.assertEquals(self.station_loc_none.obspy_location, None)
        self.assertEquals(self.station_loc_none.location, '--')
        self.assertEquals(self.station_loc_00.obspy_location, '00')

    
    def test_add_channel(self):
        ''' Test the adding of channels.
        '''
        self.station_loc_00.addChannel('HHZ')
        self.assertEquals(len(self.station_loc_00.channels), 1)
        self.assertIsInstance(self.station_loc_00.channels[0], DisplayChannel)
        self.assertEquals(self.station_loc_00.channels[0].name, 'HHZ')

        self.station_loc_00.channels = []
        self.station_loc_00.addChannel(['HHZ', 'HHN', 'HHE'])
        self.assertEquals(len(self.station_loc_00.channels), 3)
        self.assertIsInstance(self.station_loc_00.channels[0], DisplayChannel)
        self.assertIsInstance(self.station_loc_00.channels[1], DisplayChannel)
        self.assertIsInstance(self.station_loc_00.channels[2], DisplayChannel)
        self.assertEquals(self.station_loc_00.channels[0].name, 'HHZ')
        self.assertEquals(self.station_loc_00.channels[1].name, 'HHN')
        self.assertEquals(self.station_loc_00.channels[2].name, 'HHE')

    
    def test_remove_channel(self):
        ''' Test the removeChannel method.
        '''
        # Test the removal of a single channel.
        self.station_loc_00.addChannel('HHZ')
        self.assertEquals(len(self.station_loc_00.channels), 1)
        self.station_loc_00.removeChannel('HHE')
        self.assertEquals(len(self.station_loc_00.channels), 1)
        self.station_loc_00.removeChannel('HHZ')
        self.assertEquals(len(self.station_loc_00.channels), 0)

        # Test the removal of a channel from a list of channels.
        self.station_loc_00.addChannel(['HHZ', 'HHN', 'HHE'])
        scnl = self.station_loc_00.removeChannel('HHZ')
        self.assertEquals(len(self.station_loc_00.channels), 2)
        self.assertIsInstance(scnl, list)
        self.assertIsInstance(scnl[0], tuple)
        self.assertEquals(scnl[0], ('GUWA', 'HHZ', 'XX', '00'))
        self.assertEquals(self.station_loc_00.channels[0].name, 'HHN')
        self.assertEquals(self.station_loc_00.channels[1].name, 'HHE')

        # Test the removal of multiple channels.
        scnl = self.station_loc_00.removeChannel(['HHE', 'HHN'])
        self.assertEquals(len(self.station_loc_00.channels), 0)
        self.assertEquals(len(scnl), 2)
        self.assertEquals(scnl[0], ('GUWA', 'HHN', 'XX', '00'))
        self.assertEquals(scnl[1], ('GUWA', 'HHE', 'XX', '00'))

        # Test the removal of multiple channels with one wrong channel name.
        self.station_loc_00.addChannel(['HHZ', 'HHN', 'HHE'])
        scnl = self.station_loc_00.removeChannel(['HHN', 'HHZ', 'wrong'])
        self.assertEquals(len(scnl), 2)
        self.assertEquals(scnl[0], ('GUWA', 'HHZ', 'XX', '00'))
        self.assertEquals(scnl[1], ('GUWA', 'HHN', 'XX', '00'))
        self.assertEquals(self.station_loc_00.channels[0].name, 'HHE')


    def test_get_channel_names(self):
        ''' Test the getChannelNames method.
        '''
        self.station_loc_00.addChannel(['HHZ', 'HHN', 'HHE'])
        names = self.station_loc_00.getChannelNames()
        self.assertIsInstance(names, list)
        self.assertEquals(len(names), 3)
        self.assertEquals(names, ['HHZ', 'HHN', 'HHE'])
        

    def test_get_scnl(self):
        ''' Test the getSCNL method.
        '''
        # A station with no channels returns an empty list.
        self.assertEquals(self.station_loc_00.getSCNL(), [])
        
        self.station_loc_00.addChannel('HHZ')
        scnl = self.station_loc_00.getSCNL()
        self.assertIsInstance(scnl, list)
        self.assertEquals(len(scnl), 1)
        self.assertIsInstance(scnl[0], tuple)
        self.assertEquals(scnl[0], ('GUWA', 'HHZ', 'XX', '00'))
        
        self.station_loc_none.addChannel('HHZ')
        scnl = self.station_loc_none.getSCNL()
        self.assertEquals(scnl[0], ('GUWA', 'HHZ', 'XX', '--'))


    def test_get_snl(self):
        ''' Test the getSNL method.
        '''
        snl = self.station_loc_00.getSNL()
        self.assertIsInstance(snl, tuple)
        self.assertEquals(snl, ('GUWA', 'XX', '00'))
        
        snl = self.station_loc_none.getSNL()
        self.assertIsInstance(snl, tuple)
        self.assertEquals(snl, ('GUWA', 'XX', '--'))









def suite():
    return unittest.makeSuite(DisplayStationTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

