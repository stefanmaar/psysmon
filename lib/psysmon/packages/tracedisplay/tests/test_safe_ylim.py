import unittest
from unittest.mock import MagicMock
import numpy as np
from matplotlib.figure import Figure
from obspy.core.trace import Trace
from obspy.core.stream import Stream

import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from psysmon.packages.tracedisplay.plugins_views import (
    get_safe_trace_max,
    SeismogramPlotter,
    SeismogramView,
)


class SafeYLimTestCase(unittest.TestCase):
    ''' Unit tests for safe y_lim extraction and seismogram view rendering.
    '''

    def test_get_safe_trace_max_finite(self):
        ''' Verify get_safe_trace_max on standard finite arrays.
        '''
        self.assertEqual(get_safe_trace_max([1.0, -5.5, 3.2]), 5.5)
        self.assertEqual(get_safe_trace_max(np.array([-10.0, 2.0, 8.0])), 10.0)

    def test_get_safe_trace_max_with_nans_and_infs(self):
        ''' Verify get_safe_trace_max filters out NaNs and Infs.
        '''
        data = np.array([1.0, np.nan, -12.5, np.inf, -np.inf, 4.0])
        self.assertEqual(get_safe_trace_max(data), 12.5)

    def test_get_safe_trace_max_all_nans_or_infs(self):
        ''' Verify get_safe_trace_max returns None when no finite values exist.
        '''
        self.assertIsNone(get_safe_trace_max([np.nan, np.nan]))
        self.assertIsNone(get_safe_trace_max([np.inf, -np.inf]))
        self.assertIsNone(get_safe_trace_max([np.nan, np.inf, -np.inf]))

    def test_get_safe_trace_max_zeros_or_empty(self):
        ''' Verify get_safe_trace_max returns None for zeros, empty sequences, or None.
        '''
        self.assertIsNone(get_safe_trace_max([0.0, 0.0, 0.0]))
        self.assertIsNone(get_safe_trace_max([]))
        self.assertIsNone(get_safe_trace_max(np.array([])))
        self.assertIsNone(get_safe_trace_max(None))

    def test_get_safe_trace_max_masked_array(self):
        ''' Verify get_safe_trace_max unmasks and handles MaskedArray properly.
        '''
        # Partially masked
        ma = np.ma.array([10.0, 50.0, -30.0], mask=[False, True, False])
        self.assertEqual(get_safe_trace_max(ma), 30.0)

        # Partially masked with NaN in unmasked portion
        ma_nan = np.ma.array([np.nan, 25.0, -15.0], mask=[False, False, True])
        self.assertEqual(get_safe_trace_max(ma_nan), 25.0)

        # All masked
        ma_all = np.ma.masked_all(10)
        self.assertIsNone(get_safe_trace_max(ma_all))

    def _create_test_view(self):
        ''' Helper to construct a headless SeismogramView with a matplotlib figure and axes.
        '''
        view = SeismogramView.__new__(SeismogramView)
        view.logger = psysmon.get_logger(view)
        view.plot_panel = MagicMock()
        fig = Figure()
        view.plot_panel.axes = fig.add_subplot(111)
        view.t0 = None
        view.scaleBar = None
        view.scale_bar_text = None
        view.scale_bar_amp = None
        view.scale_bar_amp_text = []
        view.line = None
        view.envelope_line_top = None
        view.envelope_line_bottom = None
        view.envelope_collection_filled = None
        return view

    def test_seismogram_view_plot_normal(self):
        ''' Verify standard plotting sets y_limits to [-max, max].
        '''
        view = self._create_test_view()
        data = np.array([-5.0, 0.0, 10.0], dtype=np.float32)
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX', 'unit': 'counts'})
        stream = Stream(traces=[tr])

        view.plot(stream, color=[0, 0, 0], duration=1.0, end_time=tr.stats.endtime)
        ylim = view.axes.get_ylim()
        self.assertAlmostEqual(ylim[0], -10.0)
        self.assertAlmostEqual(ylim[1], 10.0)

    def test_seismogram_view_plot_with_nans(self):
        ''' Verify plotting a trace containing NaNs does not crash and uses the finite max.
        '''
        view = self._create_test_view()
        data = np.array([1.0, np.nan, -8.0, 2.0], dtype=np.float32)
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX', 'unit': 'counts'})
        stream = Stream(traces=[tr])

        view.plot(stream, color=[0, 0, 0], duration=1.0, end_time=tr.stats.endtime)
        ylim = view.axes.get_ylim()
        self.assertTrue(np.all(np.isfinite(ylim)))
        self.assertAlmostEqual(ylim[0], -8.0)
        self.assertAlmostEqual(ylim[1], 8.0)

    def test_seismogram_view_plot_all_nans_fallback(self):
        ''' Verify plotting an all-NaN trace safely falls back to y_lim = 1.0 without crashing.
        '''
        view = self._create_test_view()
        data = np.array([np.nan, np.nan, np.nan], dtype=np.float32)
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX', 'unit': 'counts'})
        stream = Stream(traces=[tr])

        view.plot(stream, color=[0, 0, 0], duration=1.0, end_time=tr.stats.endtime)
        ylim = view.axes.get_ylim()
        self.assertTrue(np.all(np.isfinite(ylim)))
        self.assertAlmostEqual(ylim[0], -1.0)
        self.assertAlmostEqual(ylim[1], 1.0)

    def test_seismogram_view_plot_all_masked_fallback(self):
        ''' Verify plotting an all-masked trace safely falls back to y_lim = 1.0 without crashing.
        '''
        view = self._create_test_view()
        data = np.ma.masked_all(10, dtype=np.float32)
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX', 'unit': 'counts'})
        stream = Stream(traces=[tr])

        view.plot(stream, color=[0, 0, 0], duration=1.0, end_time=tr.stats.endtime)
        ylim = view.axes.get_ylim()
        self.assertTrue(np.all(np.isfinite(ylim)))
        self.assertAlmostEqual(ylim[0], -1.0)
        self.assertAlmostEqual(ylim[1], 1.0)

    def test_seismogram_view_plot_envelope_with_nans(self):
        ''' Verify show_envelope=True on NaN-contaminated data does not crash.
        '''
        view = self._create_test_view()
        data = np.array([1.0, np.nan, -6.0, 3.0], dtype=np.float32)
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX', 'unit': 'counts'})
        stream = Stream(traces=[tr])

        view.plot(stream, color=[0, 0, 0], duration=1.0, end_time=tr.stats.endtime, show_envelope=True)
        ylim = view.axes.get_ylim()
        self.assertTrue(np.all(np.isfinite(ylim)))
        self.assertAlmostEqual(ylim[0], -6.0)
        self.assertAlmostEqual(ylim[1], 6.0)

    def test_seismogram_plotter_scaling_modes_with_gaps(self):
        ''' Verify SeismogramPlotter.plotChannel handles window and station scaling with gap traces.
        '''
        plotter = SeismogramPlotter()
        plotter.parent = MagicMock()
        data_manager = MagicMock()
        display_manager = MagicMock()

        # Stream with one valid trace and one all-NaN trace
        tr1 = Trace(data=np.array([1.0, -15.0, 2.0]), header={'sampling_rate': 100.0, 'station': 'STA1', 'channel': 'HHZ', 'network': 'XX'})
        tr2 = Trace(data=np.array([np.nan, np.nan]), header={'sampling_rate': 100.0, 'station': 'STA2', 'channel': 'HHZ', 'network': 'XX'})
        stream = Stream(traces=[tr1, tr2])
        data_manager.procStream = stream

        mock_channel = MagicMock()
        mock_channel.name = 'HHZ'
        mock_channel.parent.name = 'STA1'
        mock_channel.parent.network = 'XX'
        mock_channel.parent.location = ''

        mock_view = MagicMock()
        display_manager.getViewContainer.return_value = [mock_view]
        display_manager.startTime.timestamp = 0.0
        display_manager.endTime.timestamp = 10.0

        # Test window scaling mode
        plotter.pref_manager.set_value('scaling_mode', 'window')
        plotter.plotChannel(display_manager, data_manager, [mock_channel])
        mock_view.plot.assert_called_once()
        _, kwargs = mock_view.plot.call_args
        self.assertEqual(kwargs.get('y_lim'), 15.0)

        # Test station scaling mode with STA2 (all NaN)
        mock_view.plot.reset_mock()
        mock_channel.parent.name = 'STA2'
        plotter.pref_manager.set_value('scaling_mode', 'station')
        plotter.plotChannel(display_manager, data_manager, [mock_channel])
        mock_view.plot.assert_called_once()
        _, kwargs = mock_view.plot.call_args
        self.assertIsNone(kwargs.get('y_lim'))


if __name__ == '__main__':
    unittest.main()
