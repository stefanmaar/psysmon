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

import psysmon
import logging
import wx
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import obspy.core.utcdatetime as utcdatetime
import numpy as np

class MeasurePoint(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'measure point',
                                   category = 'analyze',
                                   tags = None
                                  )
        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.measure_icon_16
        self.cursor = wx.CURSOR_CROSS
        #self.cursor = icons.zoom_icon_16
        #self.cursor_hotspot = (0.5, 0.5)

        self.start_time = None
        self.end_time = None
        self.view = None
        self.crosshair = {}


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        self.active = False
        self.cleanup()


    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        for cur_crosshair in self.crosshair.itervalues():
            cur_crosshair[0].axes.lines.remove(cur_crosshair[0])
            cur_crosshair[1].axes.lines.remove(cur_crosshair[1])
            cur_crosshair[0].axes.figure.canvas.draw()

        self.crosshair = {}

        self.start_time = None
        self.end_time = None


    def getHooks(self):
        hooks = {}

        #hooks['motion_notify_event'] = self.on_mouse_motion
        hooks['button_press_event'] = self.on_button_press
        hooks['button_release_event'] = self.on_button_release

        return hooks


    def on_button_press(self, event, parent = None):
        if event.inaxes is None:
            return

        cur_view = event.canvas.GetGrandParent()
        self.view = cur_view

        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # Skipt the right mouse button.
            return
        else:
            measurement = self.view.measure(event)
            if measurement is not None:
                self.measure_view(event, parent)
                hook = {}
                hook['motion_notify_event'] = self.measure_view
                cur_view.set_mpl_event_callbacks(hook, parent = parent)
            #if cur_view.name.endswith('plot_seismogram'):
            #    self.measure_seismogram(event, parent)
            #    hook = {}
            #    hook['motion_notify_event'] = self.measure_seismogram
            #    cur_view.set_mpl_event_callbacks(hook, parent = parent)
            else:
                self.logger.error('Measuring a %s view is not supported.', cur_view.name)


    def on_button_release(self, event, parent):
        ''' Handle the mouse button release event.
        '''
        # Clear the motion notify callbacks.
        self.view.clear_mpl_event_callbacks('motion_notify_event')
        self.desaturate_crosshair()


    def measure_view(self, event, parent):
        ''' Measure the seismogram line in the seismogram view.
        '''
        measurement = self.view.measure(event)
        if measurement is None:
            return

        if isinstance(measurement, dict):
            measurement = [measurement,]

        measure_string = ''
        for cur_measurement in measurement:
            cur_axes = cur_measurement['axes']

            xy = cur_measurement['xy']
            if (self.view, cur_axes) not in self.crosshair.keys():
                ml_x = cur_axes.axvline(x = xy[0])
                ml_y = cur_axes.axhline(y = xy[1])
                self.crosshair[(self.view, cur_axes)] = (ml_x, ml_y)

            cur_crosshair = self.crosshair[(self.view, cur_axes)]

            for cur_line in cur_crosshair:
                cur_line.set_color('r')

            cur_crosshair[0].set_xdata(xy[0])
            cur_crosshair[1].set_ydata(xy[1])

            date_string = utcdatetime.UTCDateTime(xy[0])
            measure_string += 'time: {0:s}\n{1:s}: {2:g}\n\n'.format(date_string.isoformat(),
                                                                  cur_measurement['label'],
                                                                  xy[1])
        self.view.set_annotation(measure_string)
        self.view.draw()


    def desaturate_crosshair(self, view = None):
        ''' Desaturate the current crosshair.
        '''
        if view is None:
            view = self.view

        view_crosshairs = [x for x in self.crosshair.keys() if x[0] == view]
        if len(view_crosshairs) == 0:
            return

        for cur_crosshair_keys in view_crosshairs:
            for cur_line in self.crosshair[cur_crosshair_keys]:
                cur_line.set_color('0.75')

        view.draw()





