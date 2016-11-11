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
        self.cid = None


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


    def on_button_press(self, event, dataManager=None, displayManager=None):
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
            if cur_view.name.endswith('plot_seismogram'):
                self.measure_seismogram(event, dataManager, displayManager)
                cid = cur_view.plotCanvas.canvas.mpl_connect('motion_notify_event', lambda evt, dataManager=dataManager, displayManager=displayManager, callback=self.measure_seismogram : callback(evt, dataManager, displayManager))
                self.cid = cid
            else:
                self.logger.error('Measuring a %s view is not supported.', cur_view.name)


    def on_button_release(self, event, dataManager=None, displayManager=None):
        ''' Handle the mouse button release event.
        '''
        # Clear the motion notify callbacks.
        if self.cid is not None:
            self.view.clearEventCallbacks(cid_list = [self.cid,])

        self.desaturate_crosshair()


    def measure_seismogram(self, event, data_manager, display_manager):
        ''' Measure the seismogram line in the seismogram view.
        '''
        if event.inaxes is None:
            return

        cur_axes = self.view.axes

        seismo_line = [x for x in cur_axes.lines if x.get_label() == 'seismogram']
        if len(seismo_line) > 0:
            seismo_line = seismo_line[0]
        else:
            raise RuntimeError('No seismogram line found.')
        xdata = seismo_line.get_xdata()
        ydata = seismo_line.get_ydata()
        ind_x = np.searchsorted(xdata, [event.xdata])[0]
        snap_x = xdata[ind_x]
        snap_y = ydata[ind_x]

        if self.view not in self.crosshair.keys():
            ml_x = cur_axes.axvline(x = snap_x,
                                     color = 'k')
            ml_y = cur_axes.axhline(y = snap_y,
                                     color = 'k')
            self.crosshair[self.view] = (ml_x, ml_y)

        cur_crosshair = self.crosshair[self.view]

        for cur_line in cur_crosshair:
            cur_line.set_color('k')

        cur_crosshair[0].set_xdata(snap_x)
        cur_crosshair[1].set_ydata(snap_y)

        date_string = utcdatetime.UTCDateTime(snap_x)
        if isinstance(snap_y, np.ma.MaskedArray):
            snap_y = snap_y[0]
        measure_string = 'time: {0:s}\nampl.: {1:g}\n'.format(date_string.isoformat(),
                                                              snap_y)
        self.view.setAnnotation(measure_string)

        self.view.draw()


    def desaturate_crosshair(self, view = None):
        ''' Desaturate the current crosshair.
        '''
        if view is None:
            view = self.view

        if view not in self.crosshair.keys():
            return

        for cur_line in self.crosshair[view]:
            cur_line.set_color('0.75')

        view.draw()





