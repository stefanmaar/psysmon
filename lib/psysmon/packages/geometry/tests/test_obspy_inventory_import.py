import unittest
import obspy.core.inventory as obs_inv
import psysmon.packages.geometry.inventory as psy_inv


class ObsPyInventoryImportTestCase(unittest.TestCase):
    ''' Test suite for importing ObsPy inventories into pSysmon inventories,
    specifically focusing on location codes, empty strings, and extended networks.
    '''

    def _create_mock_channel(self, code, location_code='', lat=70.0, lon=-21.0, elev=0.0):
        chan = obs_inv.Channel(
            code=code,
            location_code=location_code,
            latitude=lat,
            longitude=lon,
            elevation=elev,
            depth=0.0
        )
        chan.sensor = obs_inv.Equipment(
            type='sensor',
            serial_number=f'sens_{code}_{location_code}',
            manufacturer='TestSensProducer',
            model='TestSensModel'
        )
        chan.data_logger = obs_inv.Equipment(
            type='recorder',
            serial_number=f'rec_{code}_{location_code}',
            manufacturer='TestRecProducer',
            model='TestRecModel'
        )
        return chan

    def test_import_station_with_empty_location_code(self):
        ''' Test converting an ObsPy station with multiple channels having empty location code "".
        In pSysmon, empty location codes should normalize to '--' without creating duplicate
        stations or raising RuntimeError when adding streams.
        '''
        net = obs_inv.Network(code='DK')
        stat = obs_inv.Station(
            code='SCO',
            latitude=70.48,
            longitude=-21.95,
            elevation=69.0,
            site=obs_inv.Site(name='Scoresbysund, Greenland')
        )
        c_z = self._create_mock_channel('HHZ', location_code='')
        c_n = self._create_mock_channel('HHN', location_code='')
        c_e = self._create_mock_channel('HHE', location_code='')
        stat.channels = [c_z, c_n, c_e]
        net.stations = [stat]
        raw_inv = obs_inv.Inventory(networks=[net])

        inv = psy_inv.Inventory.from_obspy_inventory(raw_inv)

        self.assertEqual(len(inv.networks), 1)
        psy_net = inv.networks[0]
        self.assertEqual(psy_net.name, 'DK')
        self.assertEqual(len(psy_net.stations), 1)

        psy_stat = psy_net.stations[0]
        self.assertEqual(psy_stat.name, 'SCO')
        self.assertEqual(psy_stat.location, '--')
        self.assertEqual(len(psy_stat.channels), 3)

        for chan in psy_stat.channels:
            self.assertIsNotNone(chan.parent_station)
            self.assertIsNotNone(chan.parent_inventory)
            self.assertEqual(len(chan.streams), 1)

    def test_import_multiple_stations_mixed_locations_and_extended_inventory(self):
        ''' Test importing multiple stations from separate inventory fetches joined with extend().
        DAG has location '00', SCO has '', and DBG has ''.
        '''
        # First inventory: DK.DAG ('00') and DK.SCO ('')
        net1 = obs_inv.Network(code='DK')
        stat_dag = obs_inv.Station(
            code='DAG',
            latitude=76.77,
            longitude=-18.66,
            elevation=20.0,
            site=obs_inv.Site(name='Danmarkshavn, Greenland')
        )
        stat_dag.channels = [
            self._create_mock_channel('HHZ', location_code='00'),
            self._create_mock_channel('HHN', location_code='00'),
            self._create_mock_channel('HHE', location_code='00'),
        ]

        stat_sco = obs_inv.Station(
            code='SCO',
            latitude=70.48,
            longitude=-21.95,
            elevation=69.0,
            site=obs_inv.Site(name='Scoresbysund, Greenland')
        )
        stat_sco.channels = [
            self._create_mock_channel('HHZ', location_code=''),
            self._create_mock_channel('HHN', location_code=''),
            self._create_mock_channel('HHE', location_code=''),
        ]
        net1.stations = [stat_dag, stat_sco]
        inv1 = obs_inv.Inventory(networks=[net1])

        # Second inventory from another data center: DK.DBG ('')
        net2 = obs_inv.Network(code='DK')
        stat_dbg = obs_inv.Station(
            code='DBG',
            latitude=65.61,
            longitude=-37.63,
            elevation=90.0,
            site=obs_inv.Site(name='Danmarks Bro, Greenland')
        )
        stat_dbg.channels = [
            self._create_mock_channel('HHZ', location_code=''),
            self._create_mock_channel('HHN', location_code=''),
        ]
        net2.stations = [stat_dbg]
        inv2 = obs_inv.Inventory(networks=[net2])

        inv1.extend(inv2)

        # Convert
        psy_inv_res = psy_inv.Inventory.from_obspy_inventory(inv1)

        self.assertEqual(len(psy_inv_res.networks), 1)
        net = psy_inv_res.networks[0]
        self.assertEqual(net.name, 'DK')
        self.assertEqual(len(net.stations), 3)

        # Look up each station
        dag_stations = net.get_station(name='DAG', location='00')
        self.assertEqual(len(dag_stations), 1)
        self.assertEqual(len(dag_stations[0].channels), 3)

        sco_stations = net.get_station(name='SCO', location='--')
        self.assertEqual(len(sco_stations), 1)
        self.assertEqual(len(sco_stations[0].channels), 3)

        dbg_stations = net.get_station(name='DBG', location='--')
        self.assertEqual(len(dbg_stations), 1)
        self.assertEqual(len(dbg_stations[0].channels), 2)

    def test_get_station_with_empty_and_none_location(self):
        ''' Test that get_station() queries with location='', location=None, or location='--'
        all match stations stored with the default '--' location code.
        '''
        net = psy_inv.Network(name='DK')
        stat = psy_inv.Station(name='SCO', location='', x=0.0, y=0.0, z=0.0)
        net.add_station(stat)

        # Test Network.get_station
        self.assertEqual(len(net.get_station(name='SCO', location='')), 1)
        self.assertEqual(len(net.get_station(name='SCO', location=None)), 1)
        self.assertEqual(len(net.get_station(name='SCO', location='--')), 1)

        # Test Inventory.get_station
        inv = psy_inv.Inventory(name='test_inv')
        inv.add_network(net)
        self.assertEqual(len(inv.get_station(name='SCO', location='')), 1)
        self.assertEqual(len(inv.get_station(name='SCO', location=None)), 1)
        self.assertEqual(len(inv.get_station(name='SCO', location='--')), 1)

    def test_remove_station_with_empty_location(self):
        ''' Test that Network.remove_station() with location='' or location=None
        properly removes the station.
        '''
        net = psy_inv.Network(name='DK')
        stat = psy_inv.Station(name='SCO', location='', x=0.0, y=0.0, z=0.0)
        net.add_station(stat)
        self.assertEqual(len(net.stations), 1)

        removed = net.remove_station(name='SCO', location='')
        self.assertIsNotNone(removed)
        self.assertEqual(len(net.stations), 0)

    def test_import_with_missing_sensor_and_site_metadata(self):
        ''' Test converting when obs_chan.sensor is None or obs_stat.site is None.
        '''
        net = obs_inv.Network(code='DK')
        stat = obs_inv.Station(code='SCO', latitude=70.0, longitude=-20.0, elevation=0.0, site=None)
        c1 = obs_inv.Channel(code='HHZ', location_code='', latitude=70.0, longitude=-20.0, elevation=0.0, depth=0.0)
        c2 = obs_inv.Channel(code='HHN', location_code='', latitude=70.0, longitude=-20.0, elevation=0.0, depth=0.0)
        c1.sensor = None
        c2.sensor = None
        c1.data_logger = None
        c2.data_logger = None
        stat.channels = [c1, c2]
        net.stations = [stat]
        raw_inv = obs_inv.Inventory(networks=[net])

        inv = psy_inv.Inventory.from_obspy_inventory(raw_inv)
        self.assertEqual(len(inv.networks), 1)
        self.assertEqual(len(inv.networks[0].stations), 1)
        self.assertEqual(len(inv.networks[0].stations[0].channels), 2)

    def test_export_xml_after_obspy_import(self):
        ''' Test exporting an inventory converted from ObsPy to an XML file.
        Verifies that etree is properly imported and export_xml does not fail.
        '''
        import tempfile
        import os
        import psysmon.packages.geometry.inventory_parser as psy_invparser

        net = obs_inv.Network(code='DK')
        stat = obs_inv.Station(code='SCO', latitude=70.48, longitude=-21.95, elevation=69.0)
        chan = self._create_mock_channel('HHZ', location_code='')
        stat.channels = [chan]
        net.stations = [stat]
        raw_inv = obs_inv.Inventory(networks=[net])

        inv = psy_inv.Inventory.from_obspy_inventory(raw_inv)
        parser = psy_invparser.InventoryXmlParser()

        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            parser.export_xml(inv, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()
