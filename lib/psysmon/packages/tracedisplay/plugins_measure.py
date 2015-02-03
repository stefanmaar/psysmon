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
import numpy as np

class Measure(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'measure',
                                   category = 'view',
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
        self.axes = None
        self.ml_x = None
        self.ml_y = None


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        self.active = False
        self.cleanup()


    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        if self.ml_x is not None:
            self.axes.lines.remove(self.ml_x)
            self.ml_x = None

        if self.ml_y is not None:
            self.axes.lines.remove(self.ml_y)
            self.ml_y = None

        if self.axes is not None:
            self.axes.figure.canvas.draw()

        self.start_time = None
        self.end_time = None


    def getHooks(self):
        hooks = {}

        hooks['motion_notify_event'] = self.on_mouse_motion
        #hooks['button_press_event'] = self.on_button_press
        #hooks['button_release_event'] = self.onButtonRelease

        return hooks


    def on_button_press(self, event, dataManger=None, displayManager=None):
        if event.inaxes is None:
            return

        if self.ml_x is None:
            self.ml_x = event.inaxes.axvline(x = event.xdata,
                                            color = 'k')
            event.canvas.draw()
        else:
            self.ml_x.set_xdata(event.xdata)
            event.canvas.draw()
            #event.inaxes.draw_artist(self.ml_x)


    def on_mouse_motion(self, event, data_manager=None, display_manager=None):
        ''' Handle the mouse motion.
        '''
        cur_view = event.canvas.GetGrandParent()
        if cur_view.name == 'plot seismogram':
            self.measure_seismogram(event, data_manager, display_manager)
        else:
            self.logger.debug('Measuring a %s view is not supported.', cur_view.name)


    def measure_seismogram(self, event, data_manager, display_manager):
        ''' Measure the seismogram line in the seismogram view.
        '''
        if event.inaxes is None:
            return
        elif self.axes != event.inaxes:
            # The cursor is in another axes.
            self.cleanup()

        self.axes = event.inaxes

        seismo_line = [x for x in self.axes.lines if x.get_label() == 'seismogram']
        if len(seismo_line) > 0:
            seismo_line = seismo_line[0]
        else:
            raise RuntimeError('No seismogram line found.')
        xdata = seismo_line.get_xdata()
        ydata = seismo_line.get_ydata()
        ind_x = np.searchsorted(xdata, [event.xdata])[0]
        snap_x = xdata[ind_x]
        snap_y = ydata[ind_x]

        if self.ml_x is None:
            self.ml_x = self.axes.axvline(x = snap_x,
                                          color = 'k')
        else:
            self.ml_x.set_xdata(snap_x)

        if self.ml_y is None:
            self.ml_y = self.axes.axhline(y = snap_y,
                                          color = 'k')
        else:
            self.ml_y.set_ydata(snap_y)

        event.canvas.draw()


