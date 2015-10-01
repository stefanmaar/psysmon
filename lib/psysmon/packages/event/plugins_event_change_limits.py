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

import psysmon
from psysmon.core.plugins import InteractivePlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm
from obspy.core.utcdatetime import UTCDateTime
import psysmon.packages.event.core as event_core


class CreateEvent(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        InteractivePlugin.__init__(self,
                              name = 'change event limits',
                              category = 'edit',
                              tags = ['event', 'modify', 'change', 'limit', 'start', 'end']
                             )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.event_change_limits_16
        self.cursor = wx.CURSOR_CROSS

        self.begin_line = {}
        self.end_line = {}
        self.bg = {}
        self.motion_notify_cid = []
        self.startTime = None
        self.endTime = None


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.on_button_press
        hooks['button_release_event'] = self.on_button_release

        return hooks


    def activate(self):
        ''' Activate the plugin.
        '''
        selected_event_info = self.parent.get_shared_info(origin_rid = '/plugin/tracedisplay/show_events',
                                                          name = 'selected_event')
        if selected_event_info:
            if len(selected_event_info) > 1:
                raise RuntimeError("More than one selected event returned. Don't know which one to use.")
            InteractivePlugin.activate(self)
        else:
            self.logger.info("No selected event found. Can't activate the plugin.")


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        InteractivePlugin.deactivate(self)
        self.cleanup()



    def on_button_press(self, event, dataManager=None, displayManager=None):
        self.logger.debug('on_button_press')
        if event.button == 1:
            # Clicking the left mouse button changes the event start time.
            selected_event_info = self.parent.get_shared_info(origin_rid = '/plugin/tracedisplay/show_events',
                                                       name = 'selected_event')
            if selected_event_info:
                if len(selected_event_info) > 1:
                    raise RuntimeError("More than one selected event returned. Don't know which one to use.")

                selected_event_info = selected_event_info[0]
                # Update the event data in the database.
                catalog_name = selected_event_info.value['catalog_name']
                # TODO: Add a get_event method in the event catalog class to get events based on
                # search critea.
                cur_event = [x for x in self.parent.event_library.catalogs[catalog_name].events if x.db_id == selected_event_info.value['id']]

                if cur_event:
                    cur_event = cur_event[0]

                    # Check for a valid time value.
                    if UTCDateTime(event.xdata) >= cur_event.end_time:
                        self.logger.error("The start time has to be smaller than the end time.")
                        return

                    self.event_start = event.xdata

                    cur_event.start_time = UTCDateTime(self.event_start)
                    cur_event.write_to_database(self.parent.project)
                    selected_event_info.value['start_time'] = cur_event.start_time
                    selected_event_info.change_rid = self.rid
                    self.parent.notify_shared_info_change(selected_event_info)

        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # Clicking the right mouse button changes the event end time.
            selected_event_info = self.parent.get_shared_info(origin_rid = '/plugin/tracedisplay/show_events',
                                                       name = 'selected_event')
            if selected_event_info:
                if len(selected_event_info) > 1:
                    raise RuntimeError("More than one selected event returned. Don't know which one to use.")

                selected_event_info = selected_event_info[0]
                # Update the event data in the database.
                catalog_name = selected_event_info.value['catalog_name']
                # TODO: Add a get_event method in the event catalog class to get events based on
                # search critea.
                cur_event = [x for x in self.parent.event_library.catalogs[catalog_name].events if x.db_id == selected_event_info.value['id']]

                if cur_event:
                    cur_event = cur_event[0]

                    # Check for a valid time value.
                    if UTCDateTime(event.xdata) <= cur_event.start_time:
                        self.logger.error("The start time has to be larger than the start time.")
                        return

                    self.event_end = event.xdata

                    cur_event.end_time = UTCDateTime(self.event_end)
                    cur_event.write_to_database(self.parent.project)
                    selected_event_info.value['end_time'] = cur_event.end_time
                    selected_event_info.change_rid = self.rid
                    self.parent.notify_shared_info_change(selected_event_info)

        return

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    #bg = curView.plotCanvas.canvas.copy_from_bbox(curView.dataAxes.bbox)
                    #curView.plotCanvas.canvas.restore_region(bg)

                    if curView in self.end_line.keys():
                        self.end_line[curView].set_visible(False)
                        curView.dataAxes.draw_artist(self.end_line[curView])


                    if curView in self.begin_line.keys():
                        self.begin_line[curView].set_xdata(event.xdata)
                    else:
                        self.begin_line[curView] = curView.dataAxes.axvline(x=event.xdata)

                    curView.plotCanvas.canvas.draw()

                    cid = curView.plotCanvas.canvas.mpl_connect('motion_notify_event', lambda evt, dataManager=dataManager, displayManager=displayManager, callback=self.on_mouse_motion : callback(evt, dataManager, displayManager))
                    self.motion_notify_cid.append((curView.plotCanvas.canvas, cid))


    def on_mouse_motion(self, event, dataManger=None, displayManager=None):
        if event.inaxes is not None:
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

                    if curView not in self.end_line.keys():
                        self.end_line[curView] = curView.dataAxes.axvline(x=event.xdata, animated=True)
                    else:
                        self.end_line[curView].set_xdata(event.xdata)
                        self.end_line[curView].set_visible(True)

                    curView.dataAxes.draw_artist(self.end_line[curView])
                    canvas.blit()


    def on_button_release(self, event, dataManager=None, displayManager=None):
        self.logger.debug('on_button_release')

        return
        self.cleanup()

        # Call the setTimeLimits of the displayManager.
        # The timebase of the plots is unixseconds.
        if self.startTime == self.endTime:
            return
        elif self.endTime < self.startTime:
            self.create_event(start_time = self.endTime, end_time = self.endTime)
        else:
            self.create_event(start_time = self.startTime, end_time = self.endTime)



    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        # Clear the zoom lines.
        for curView in self.begin_line.keys():
            if curView in self.begin_line.keys():
                curView.dataAxes.lines.remove(self.begin_line[curView])
            if curView in self.end_line.keys():
                curView.dataAxes.lines.remove(self.end_line[curView])
            curView.draw()

        self.begin_line = {}
        self.end_line = {}


        # Clear the motion notify callbacks.
        for canvas, cid in self.motion_notify_cid:
            canvas.mpl_disconnect(cid)

        self.motion_notify_cid = []
        self.bg = {}

