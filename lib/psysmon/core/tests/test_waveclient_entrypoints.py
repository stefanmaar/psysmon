# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
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

import os
import unittest
from obspy.core.util.base import ENTRY_POINTS
import psysmon.core.util as psy_util


class WaveclientEntryPointsTestCase(unittest.TestCase):
    """
    Test suite for ObsPy format checker loading and compatibility.
    """

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.msd_file = os.path.join(
            self.test_data_dir,
            'ZAMG-seis_event00017_GUWA_HHE_20100831_075759.740.msd'
        )

    def test_load_format_checker_all_waveform_plugins(self):
        """ Test that format checkers load for all waveform plugins.
        """
        EPS = ENTRY_POINTS['waveform']
        self.assertGreater(len(EPS), 0)

        for key, format_ep in EPS.items():
            checker = psy_util.load_format_checker(format_ep, 'waveform')
            self.assertIsNotNone(checker, f"Failed to load format checker for {key}")
            self.assertTrue(callable(checker), f"Checker for {key} is not callable")

    def test_format_detection_msd_file(self):
        """ Test format detection on an actual MiniSEED (.msd) file.
        """
        self.assertTrue(os.path.exists(self.msd_file), f"Test file {self.msd_file} missing")

        EPS = ENTRY_POINTS['waveform']
        detected_format = None

        for format_ep in EPS.values():
            isFormat = psy_util.load_format_checker(format_ep, 'waveform')
            if isFormat is None:
                continue
            if isFormat(self.msd_file):
                detected_format = format_ep.name
                break

        self.assertEqual(detected_format, 'MSEED')

    def test_path_distribution_compatibility(self):
        """ Test mock entry point with PathDistribution style dist (only .name, no .key).
        """
        class MockPathDistribution(object):
            def __init__(self, name):
                self.name = name

        class MockEntryPoint(object):
            def __init__(self, name, dist_name):
                self.name = name
                self.dist = MockPathDistribution(dist_name)

        mock_ep = MockEntryPoint(name='MSEED', dist_name='obspy')
        checker = psy_util.load_format_checker(mock_ep, 'waveform')
        self.assertIsNotNone(checker)
        self.assertTrue(callable(checker))
        self.assertTrue(checker(self.msd_file))

    def test_legacy_pkg_resources_dist_compatibility(self):
        """ Test mock entry point with legacy pkg_resources style dist (only .key, no .name).
        """
        class MockLegacyDistribution(object):
            def __init__(self, key):
                self.key = key

        class MockEntryPoint(object):
            def __init__(self, name, dist_key):
                self.name = name
                self.dist = MockLegacyDistribution(dist_key)

        mock_ep = MockEntryPoint(name='MSEED', dist_key='obspy')
        checker = psy_util.load_format_checker(mock_ep, 'waveform')
        self.assertIsNotNone(checker)
        self.assertTrue(callable(checker))
        self.assertTrue(checker(self.msd_file))

    def test_invalid_or_missing_entry_point(self):
        """ Test that non-existent entry point returns None gracefully without crashing.
        """
        class MockDist(object):
            name = 'obspy'

        class MockInvalidEntryPoint(object):
            name = 'NON_EXISTENT_FORMAT_XYZ'
            dist = MockDist()

        mock_ep = MockInvalidEntryPoint()
        checker = psy_util.load_format_checker(mock_ep, 'waveform')
        self.assertIsNone(checker)


if __name__ == '__main__':
    unittest.main()
