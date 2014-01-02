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
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons
from obspy.core import UTCDateTime
import psysmon.core.preferences_manager as preferences_manager

class Zoom(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'zoom',
                                   category = 'view',
                                   tags = None
                                  )
        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.zoom_icon_16

        self.beginLine = {}
        self.endLine = {}
        self.bg = {}
        self.motionNotifyCid = []
        self.startTime = None
        self.endTime = None

        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio', 
                                                       value = 20,
                                                       limit = (1, 99)
                                                      )
        self.pref_manager.add_item(item = item)


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.onButtonPress
        hooks['button_release_event'] = self.onButtonRelease

        return hooks



    def onButtonPress(self, event, dataManager=None, displayManager=None):
        self.logger.debug('onButtonPress - button: %s', str(event.button))
        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # Use the right mouse button to zoom out.
            self.startTime = event.xdata
            ratio = self.pref_manager.get_value('zoom ratio')
            duration = displayManager.endTime - displayManager.startTime
            shrinkAmount = duration * ratio/100.0
            tmp = self.startTime
            self.startTime = tmp - shrinkAmount*2.0
            self.endTime = tmp + shrinkAmount*2.0
            displayManager.setTimeLimits(UTCDateTime(self.startTime),
                                         UTCDateTime(self.endTime))

            displayManager.parent.updateDisplay()
            return

        #self.logger.debug('dataManager: %s\ndisplayManager: %s', dataManager, displayManager)

        #print 'Clicked mouse:\nxdata=%f, ydata=%f' % (event.xdata, event.ydata)
        #print 'x=%f, y=%f' % (event.x, event.y)

        self.startTime = event.xdata
        self.endTime = event.xdata

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    #bg = curView.plotCanvas.canvas.copy_from_bbox(curView.dataAxes.bbox)
                    #curView.plotCanvas.canvas.restore_region(bg)

                    if curView in self.endLine.keys():
                        self.endLine[curView].set_visible(False)
                        curView.dataAxes.draw_artist(self.endLine[curView])


                    if curView in self.beginLine.keys():
                        self.beginLine[curView].set_xdata(event.xdata)
                    else:
                        self.beginLine[curView] = curView.dataAxes.axvline(x=event.xdata)

                    curView.plotCanvas.canvas.draw()

                    cid = curView.plotCanvas.canvas.mpl_connect('motion_notify_event', lambda evt, dataManager=dataManager, displayManager=displayManager, callback=self.onMouseMotion : callback(evt, dataManager, displayManager))
                    self.motionNotifyCid.append((curView.plotCanvas.canvas, cid))


    def onMouseMotion(self, event, dataManger=None, displayManager=None):
        self.logger.debug('mouse motion')
        self.logger.debug('x: %f', event.x)
        if event.inaxes is not None:
            self.logger.debug('xData: %f', event.xdata)
            self.endTime = event.xdata

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    if event.inaxes is None:
                        inv = curView.dataAxes.transData.inverted()
                        tmp = inv.transform((event.x, event.y))
                        self.logger.debug('xTrans: %f', tmp[0])
                        event.xdata = tmp[0]
                    canvas = curView.plotCanvas.canvas
                    if curView not in self.bg.keys():
                        self.bg[curView] = canvas.copy_from_bbox(curView.dataAxes.bbox)
                    canvas.restore_region(self.bg[curView])

                    if curView not in self.endLine.keys():
                        self.endLine[curView] = curView.dataAxes.axvline(x=event.xdata, animated=True)
                    else:
                        self.endLine[curView].set_xdata(event.xdata)
                        self.endLine[curView].set_visible(True)

                    curView.dataAxes.draw_artist(self.endLine[curView])
                    canvas.blit()



    def onButtonRelease(self, event, dataManager=None, displayManager=None):
        self.logger.debug('onButtonRelease')
        for canvas, cid in self.motionNotifyCid:
            canvas.mpl_disconnect(cid)

        self.motionNotifyCid = []
        self.bg = {}


        # Delete all begin- and end lines from the axes.
        for curView in self.beginLine.keys():
            if curView in self.beginLine.keys():
                curView.dataAxes.lines.remove(self.beginLine[curView])
            if curView in self.endLine.keys():
                curView.dataAxes.lines.remove(self.endLine[curView])

        self.beginLine = {}
        self.endLine = {}



        # Call the setTimeLimits of the displayManager.
        # The timebase of the plots is unixseconds.
        if self.startTime == self.endTime:
            # This was a single click with no drag.
            ratio = self.pref_manager.get_value('zoom ratio')
            duration = displayManager.endTime - displayManager.startTime
            shrinkAmount = duration * ratio/100.0
            tmp = self.startTime
            self.startTime = tmp - shrinkAmount/2.0
            self.endTime = tmp + shrinkAmount/2.0
        elif self.endTime < self.startTime:
            tmp = self.startTime
            self.startTime = self.endTime
            self.endTime = tmp

        displayManager.setTimeLimits(UTCDateTime(self.startTime),
                                     UTCDateTime(self.endTime))

        displayManager.parent.updateDisplay()

