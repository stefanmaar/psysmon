import unittest
import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from obspy.core.utcdatetime import UTCDateTime
from psysmon.packages.tracedisplay.plugins_reset_view import ResetView
from psysmon.packages.tracedisplay.plugins_views import SeismogramPlotter
from psysmon.packages.tracedisplay.tracedisplay import DisplayManager, TraceDisplayDlg


class DummyDisplayManager(object):
    def __init__(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    @property
    def duration(self):
        if self.startTime is not None and self.endTime is not None:
            return self.endTime - self.startTime
        return None

    def setTimeLimits(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    def setStartTime(self, startTime):
        duration = self.duration
        self.startTime = startTime
        if duration is not None:
            self.endTime = startTime + duration

    def setDuration(self, duration):
        if self.startTime is not None:
            self.endTime = self.startTime + duration


class DummyParent(object):
    def __init__(self, startTime, endTime):
        self.displayManager = DummyDisplayManager(startTime, endTime)
        self.orig_startTime = startTime
        self.orig_duration = self.displayManager.duration
        self.reset_called = False
        self.update_called = False

    def reset_view(self):
        self.reset_called = True
        self.displayManager.setTimeLimits(self.orig_startTime, self.orig_startTime + self.orig_duration)

    def update_display(self):
        self.update_called = True


class ResetViewTestCase(unittest.TestCase):

    def test_reset_view_plugin_attributes(self):
        plugin = ResetView()
        self.assertEqual(plugin.name, 'reset view')
        self.assertEqual(plugin.category, 'control')
        self.assertEqual(plugin.accelerator_string, 'Space')
        self.assertIn('view', plugin.tags)
        self.assertIn('reset', plugin.tags)

    def test_reset_view_plugin_run(self):
        plugin = ResetView()
        parent = DummyParent(UTCDateTime('2023-07-03T00:00:00'), UTCDateTime('2023-07-04T00:00:00'))
        plugin.parent = parent
        plugin.run()
        self.assertTrue(parent.reset_called)

    def test_seismogram_original_view_preferences(self):
        plotter = SeismogramPlotter()
        self.assertIsNotNone(plotter.pref_manager.get_item(name='original_duration'))
        self.assertIsNotNone(plotter.pref_manager.get_item(name='original_start_time'))
        self.assertIsNotNone(plotter.pref_manager.get_item(name='capture_current_view'))
        self.assertIsNotNone(plotter.pref_manager.get_item(name='reset_view_now'))

        dur_item = plotter.pref_manager.get_item(name='original_duration')[0]
        start_item = plotter.pref_manager.get_item(name='original_start_time')[0]
        self.assertEqual(dur_item.label, 'duration [s]')
        self.assertEqual(start_item.label, 'start time')

        # Default values
        self.assertEqual(plotter.pref_manager.get_value('original_duration'), 86400.0)
        self.assertIsNone(plotter.pref_manager.get_value('original_start_time'))

    def test_seismogram_capture_and_reset_callbacks(self):
        plotter = SeismogramPlotter()
        start = UTCDateTime('2023-07-03T12:00:00')
        end = start + 3600.0
        parent = DummyParent(start, end)
        plotter.parent = parent

        # Test capture
        plotter.on_capture_current_view()
        self.assertEqual(plotter.pref_manager.get_value('original_start_time'), start)
        self.assertEqual(plotter.pref_manager.get_value('original_duration'), 3600.0)
        self.assertEqual(parent.orig_startTime, start)
        self.assertEqual(parent.orig_duration, 3600.0)

        # Test reset callback
        parent.reset_called = False
        plotter.on_reset_view_now()
        self.assertTrue(parent.reset_called)

    def test_display_manager_duration_property(self):
        start = UTCDateTime('2023-07-03T00:00:00')
        dm = DummyDisplayManager(start, start + 86400.0)
        self.assertEqual(dm.duration, 86400.0)

        dm.setTimeLimits(start, start + 300.0)
        self.assertEqual(dm.duration, 300.0)

    def test_trace_display_dlg_reset_view_method(self):
        # Test TraceDisplayDlg reset_view method directly on an object with plugins and displayManager
        class MockDlg(object):
            pass

        dlg = MockDlg()
        dlg.logger = psysmon.get_logger(dlg)
        start = UTCDateTime('2023-07-03T00:00:00')
        dlg.displayManager = DummyDisplayManager(start + 1000.0, start + 2000.0) # zoomed in
        dlg.orig_startTime = start
        dlg.orig_duration = 86400.0

        plotter = SeismogramPlotter()
        plotter.parent = dlg
        plotter.pref_manager.set_value('original_start_time', start)
        plotter.pref_manager.set_value('original_duration', 86400.0)
        dlg.plugins = [plotter]

        dlg.update_called = False
        def mock_update():
            dlg.update_called = True
        dlg.update_display = mock_update

        # Bind reset_view
        TraceDisplayDlg.reset_view(dlg)

        # Verify displayManager was reset to original view
        self.assertEqual(dlg.displayManager.startTime, start)
        self.assertEqual(dlg.displayManager.endTime, start + 86400.0)
        self.assertEqual(dlg.displayManager.duration, 86400.0)
        self.assertTrue(dlg.update_called)

    def test_trace_display_dlg_set_start_and_duration_sync(self):
        class MockDlg(object):
            sync_original_view_to_preferences = TraceDisplayDlg.sync_original_view_to_preferences

        dlg = MockDlg()
        dlg.logger = psysmon.get_logger(dlg)
        start = UTCDateTime('2023-07-03T00:00:00')
        dlg.displayManager = DummyDisplayManager(start, start + 300.0)
        dlg.orig_startTime = start
        dlg.orig_duration = 300.0

        plotter = SeismogramPlotter()
        plotter.parent = dlg
        dlg.plugins = [plotter]
        dlg.update_display = lambda: None

        # Test setStartTime with sync
        new_start = UTCDateTime('2023-07-04T00:00:00')
        TraceDisplayDlg.setStartTime(dlg, new_start, is_original=True)
        self.assertEqual(dlg.orig_startTime, new_start)
        self.assertEqual(plotter.pref_manager.get_value('original_start_time'), new_start)

        # Test setDuration with sync
        new_duration = 86400.0
        TraceDisplayDlg.setDuration(dlg, new_duration, is_original=True)
        self.assertEqual(dlg.orig_duration, new_duration)
        self.assertEqual(plotter.pref_manager.get_value('original_duration'), new_duration)


if __name__ == '__main__':
    unittest.main()
