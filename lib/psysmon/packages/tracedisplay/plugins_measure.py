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

import logging
import wx
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons
from obspy.core import UTCDateTime
import psysmon.core.preferences_manager as preferences_manager

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
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.measure_icon_16
        self.cursor = wx.CURSOR_CROSS
        #self.cursor = icons.zoom_icon_16
        #self.cursor_hotspot = (0.5, 0.5)

        self.start_time = None
        self.end_time = None
        self.ml_x = None
        self.ml_y = None


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


    def on_mouse_motion(self, event, dataManger=None, displayManager=None):
        if event.inaxes is None:
            return

        if self.ml_x is None:
            self.ml_x = event.inaxes.axvline(x = event.xdata,
                                             color = 'k')
        else:
            self.ml_x.set_xdata(event.xdata)

        if self.ml_y is None:
            self.ml_y = event.inaxes.axhline(y = event.ydata,
                                             color = 'k')
        else:
            self.ml_y.set_ydata(event.ydata)

        event.canvas.draw()


