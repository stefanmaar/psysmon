import unittest
from unittest.mock import MagicMock
import numpy as np
from matplotlib.figure import Figure
from obspy.core.trace import Trace
from obspy.core.stream import Stream

import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from psysmon.packages.tracedisplay.plugins_views import SpectrogramPlotter, SpectrogramView


class SpectrogramViewTestCase(unittest.TestCase):
    def setUp(self):
        # Create SpectrogramPlotter plugin
        self.plotter = SpectrogramPlotter()

        # Create dummy parent with mock displayManager and dataManager
        self.parent = MagicMock()
        self.data_manager = MagicMock()
        self.display_manager = MagicMock()

        self.parent.dataManager = self.data_manager
        self.parent.displayManager = self.display_manager
        self.plotter.parent = self.parent

        # Setup sample stream with 100 Hz sampling rate (Nyquist = 50 Hz)
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX'})
        self.stream = Stream(traces=[tr])
        self.data_manager.procStream = self.stream
        self.data_manager.origStream = self.stream

    def test_preferences_initialization(self):
        ''' Verify fmin and fmax preferences exist with correct defaults and limits.
        '''
        self.assertIsNotNone(self.plotter.pref_manager.get_item('fmin'))
        self.assertIsNotNone(self.plotter.pref_manager.get_item('fmax'))

        fmin_item = self.plotter.pref_manager.get_item('fmin')[0]
        fmax_item = self.plotter.pref_manager.get_item('fmax')[0]

        self.assertEqual(fmin_item.label, 'fmin [Hz]')
        self.assertEqual(fmax_item.label, 'fmax [Hz]')
        self.assertEqual(fmin_item.value, 0.0)
        self.assertEqual(fmax_item.value, 0.0)
        self.assertEqual(fmin_item.limit, (0.0, None))
        self.assertEqual(fmax_item.limit, (0.0, None))
        self.assertIn('on_value_change', fmin_item.hooks)
        self.assertIn('on_value_change', fmax_item.hooks)

    def test_get_nyquist_frequency(self):
        ''' Verify Nyquist calculation from stream or parent dataManager.
        '''
        # From stream directly
        self.assertEqual(self.plotter.get_nyquist_frequency(self.stream), 50.0)

        # From parent dataManager
        self.assertEqual(self.plotter.get_nyquist_frequency(), 50.0)

        # Multiple streams with different sampling rates -> takes max
        tr2 = Trace(data=np.zeros(100), header={'sampling_rate': 250.0})
        multi_stream = Stream(traces=[self.stream[0], tr2])
        self.assertEqual(self.plotter.get_nyquist_frequency(multi_stream), 125.0)

        # Empty stream
        self.assertIsNone(self.plotter.get_nyquist_frequency(Stream()))

    def test_update_nyquist_fmax_on_plot(self):
        ''' Verify fmax automatically populates with Nyquist frequency when data is available.
        '''
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 0.0)
        self.assertFalse(self.plotter._user_fmax_set)

        self.plotter.update_nyquist_fmax(self.stream)
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

    def test_auto_reset_to_nyquist_when_zero_or_empty(self):
        ''' Verify that setting fmax to 0.0 or None automatically resets to Nyquist frequency.
        '''
        # First set a custom fmax
        self.plotter.pref_manager.set_value('fmax', 20.0)
        self.plotter.on_pref_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 20.0)
        self.assertTrue(self.plotter._user_fmax_set)

        # Reset fmax to 0.0
        self.plotter.pref_manager.set_value('fmax', 0.0)
        self.plotter.on_pref_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

        # Setting None should also reset to Nyquist
        self.plotter.pref_manager.set_value('fmax', None)
        self.plotter.on_pref_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

    def test_auto_clamping_fmax_above_nyquist(self):
        ''' Verify setting fmax > Nyquist clamps fmax to Nyquist.
        '''
        self.plotter.pref_manager.set_value('fmax', 80.0)
        self.plotter.on_pref_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

    def test_auto_clamping_negative_fmin(self):
        ''' Verify setting negative fmin clamps fmin to 0.0.
        '''
        self.plotter.pref_manager.set_value('fmin', -10.0)
        self.plotter.on_pref_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmin'), 0.0)

    def test_on_pref_changed_triggers_update_display(self):
        ''' Verify on_pref_changed calls parent.update_display().
        '''
        self.parent.update_display.reset_mock()
        self.plotter.pref_manager.set_value('fmin', 5.0)
        self.plotter.on_pref_changed()
        self.parent.update_display.assert_called_once()

    def _create_test_view(self):
        ''' Helper to construct a headless SpectrogramView with a matplotlib figure and axes.
        '''
        view = SpectrogramView.__new__(SpectrogramView)
        view.logger = psysmon.get_logger(view)
        view.plot_panel = MagicMock()
        fig = Figure()
        view.plot_panel.axes = fig.add_subplot(111)
        return view

    def test_spectrogram_full_range_rendering(self):
        ''' Test full frequency range rendering when fmin=0.0 and fmax=0.0.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=0.0, fmax=0.0)

        # Lowest non-DC frequency bin
        self.assertAlmostEqual(view.freq[0], 0.78125, places=3)
        # Nyquist frequency bin
        self.assertAlmostEqual(view.freq[-1], 50.0, places=3)

        ylim = view.axes.get_ylim()
        self.assertLess(ylim[0], 1.0)
        self.assertGreaterEqual(ylim[1], 50.0)

    def test_spectrogram_band_slicing_and_y_zoom(self):
        ''' Test slicing frequency bins and zooming y-axis to [fmin, fmax].
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=5.0, fmax=20.0)

        # Frequencies are sliced
        self.assertGreaterEqual(view.freq[0], 4.5)
        self.assertLessEqual(view.freq[0], 5.5)
        self.assertGreaterEqual(view.freq[-1], 19.5)
        self.assertLessEqual(view.freq[-1], 20.5)

        # Axes y-limits are zoomed exactly to [5.0, 20.0]
        ylim = view.axes.get_ylim()
        self.assertAlmostEqual(ylim[0], 5.0, places=4)
        self.assertAlmostEqual(ylim[1], 20.0, places=4)

    def test_spectrogram_fmin_only(self):
        ''' Test lower frequency limit only.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=10.0, fmax=0.0)

        ylim = view.axes.get_ylim()
        self.assertAlmostEqual(ylim[0], 10.0, places=4)
        self.assertGreaterEqual(ylim[1], 50.0)

    def test_spectrogram_fmax_only(self):
        ''' Test upper frequency limit only.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=0.0, fmax=15.0)

        ylim = view.axes.get_ylim()
        self.assertLess(ylim[0], 1.0)
        self.assertAlmostEqual(ylim[1], 15.0, places=4)

    def test_spectrogram_invalid_band_fallback(self):
        ''' Test fallback to full band when fmin >= fmax.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        # fmin > fmax
        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=30.0, fmax=10.0)

        # Safe fallback to full range up to 50 Hz
        self.assertAlmostEqual(view.freq[-1], 50.0, places=3)
        ylim = view.axes.get_ylim()
        self.assertGreaterEqual(ylim[1], 50.0)

    def test_measure_in_sliced_band(self):
        ''' Test that measure snaps accurately within the sliced frequency band.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=10.0, fmax=25.0)

        event = MagicMock()
        event.inaxes = view.axes
        event.xdata = view.time[len(view.time) // 2]
        event.ydata = 18.0

        measurement = view.measure(event)
        self.assertIsNotNone(measurement)
        self.assertEqual(measurement['label'], 'frequency')
        self.assertEqual(measurement['units'], 'Hz')

        # Snapped frequency must be in the [10.0, 25.0] range
        snap_f = measurement['xy'][1]
        self.assertGreaterEqual(snap_f, 10.0 - 0.5)
        self.assertLessEqual(snap_f, 25.0 + 0.5)
        self.assertAlmostEqual(snap_f, 18.0, delta=1.0)


if __name__ == '__main__':
    unittest.main()
