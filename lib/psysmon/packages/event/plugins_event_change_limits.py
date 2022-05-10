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
from psysmon.gui.bricks import PrefEditPanel
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
                                   category = 'tools',
                                   tags = ['event', 'modify',
                                           'change', 'limit',
                                           'start', 'end'])

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.event_change_limits_16
        self.cursor = wx.CURSOR_CROSS

        self.bg = {}
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
        selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid +'/plugin/show_events',
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



    def on_button_press(self, event, parent = None):
        self.logger.debug('on_button_press')
        if event.button == 1:
            # Clicking the left mouse button changes the event start time.
            selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid +'/plugin/show_events',
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
            selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid +'/plugin/show_events',
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

        viewport = self.parent.viewport
        hooks = {'motion_notify_event': self.on_mouse_motion}
        viewport.register_mpl_event_callbacks(hooks)

        station_nodes = viewport.get_node(recursive = False)
        for cur_node in station_nodes:
            cur_node.plot_annotation_vline(x = event.xdata,
                                           parent_rid = self.rid,
                                           key = 'begin_line')
            cur_node.draw()



    def on_mouse_motion(self, event, dataManger=None, displayManager=None):
        if event.inaxes is not None:
            self.endTime = event.xdata

        viewport = self.parent.viewport
        station_nodes = viewport.get_node(recursive = False)
        for cur_node in station_nodes:
            view_nodes = cur_node.get_node(node_type = 'view')
            for cur_view in view_nodes:
                if event.inaxes is None:
                    inv = cur_view.axes.transData.inverted()
                    tmp = inv.transform((event.x, event.y))
                    event.xdata = tmp[0]
                if cur_view not in iter(self.bg.keys()):
                    self.bg[cur_view] = cur_view.plot_panel.canvas.copy_from_bbox(cur_view.axes.bbox)
                cur_view.plot_panel.canvas.restore_region(self.bg[cur_view])

                line_artist, label_artist = cur_view.plot_annotation_vline(x = event.xdata,
                                                                           parent_rid = self.rid,
                                                                           key = 'end_line',
                                                                           animated = True)

                cur_view.axes.draw_artist(line_artist)
                cur_view.plot_panel.canvas.blit()


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
        station_nodes = self.parent.viewport.get_node(recursive = False)
        for cur_node in station_nodes:
            cur_node.clear_annotation_artist(parent_rid = self.rid)
            cur_node.draw()

        # Clear the motion notify callbacks.
        self.parent.viewport.clear_mpl_event_callbacks(event_name = 'motion_notify_event')

        self.bg = {}

