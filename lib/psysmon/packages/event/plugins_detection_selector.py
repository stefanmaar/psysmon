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
from obspy.core.utcdatetime import UTCDateTime
import wx.lib.mixins.listctrl as listmix
from wx.lib.stattext import GenStaticText as StaticText

import psysmon
from psysmon.core.plugins import OptionPlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm
import psysmon.packages.event.detect as detect


class SelectDetection(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        OptionPlugin.__init__(self,
                              name = 'show detections',
                              category = 'view',
                              tags = ['show', 'detection']
                             )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.lighting_icon_16

        # The detection library.
        self.library = detect.Library(self.rid)

        # The selected catalog.
        self.selected_catalog = None

        # The plot colors used by the plugin.
        self.colors = {}
        self.colors['detection_vspan'] = '0.9'

        # Create the preferences.
        self.create_select_preferences()


    def create_select_preferences(self):
        ''' Create the select preferences.
        '''
        select_page = self.pref_manager.add_page('Select')
        ds_group = select_page.add_group('detection selection')

        item = psy_pm.SingleChoicePrefItem(name = 'detection_catalog',
                                          label = 'detection catalog',
                                          value = '',
                                          limit = [],
                                          hooks = {'on_value_change': self.on_catalog_selected},
                                          tool_tip = 'Select the detection catalog to show.')
        ds_group.add_item(item)


    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                  parent = panelBar)
        return fold_panel


    def activate(self):
        ''' Extend the plugin activate method.
        '''
        OptionPlugin.activate(self)

        # Initialize the catalog names.
        catalog_names = self.library.get_catalogs_in_db(self.parent.project)
        self.pref_manager.set_limit('detection_catalog', catalog_names)
        if catalog_names:
            self.pref_manager.set_value('detection_catalog', catalog_names[0])
            self.on_catalog_selected()


    def deactivate(self):
        ''' Extend the plugin deactivate method.
        '''
        OptionPlugin.deactivate(self)
        self.clear_annotation()
        # TODO: Think about not deleting the shared information if the plugin
        # is deactivated. Otherwise not many plugins can be opened at a time.
        self.parent.plugins_information_bag.remove_info(origin_rid = self.rid)


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}

        #hooks['time_limit_changed'] = self.load_detections
        hooks['after_plot'] = self.on_after_plot
        hooks['after_plot_station'] = self.on_after_plot_station

        return hooks


    def on_catalog_selected(self):
        ''' Load the selected detection catalog.
        '''
        catalog_name = self.pref_manager.get_value('detection_catalog')
        start_time = self.parent.displayManager.startTime
        end_time = self.parent.displayManager.endTime

        if catalog_name not in self.library.catalogs.keys():
            self.library.load_catalog_from_db(project = self.parent.project,
                                              name = catalog_name)

        cur_catalog = self.library.catalogs[catalog_name]
        cur_catalog.clear_detections()
        cur_catalog.load_detections(project = self.parent.project,
                                    start_time = start_time,
                                    end_time = end_time)

        self.selected_catalog = cur_catalog


    def load_detections(self):
        ''' Load the detections for the displayed timespan.
        '''
        start_time = self.parent.displayManager.startTime
        end_time = self.parent.displayManager.endTime
        self.logger.debug('Loading the detections from %s to %s....',
                          start_time,
                          end_time)
        self.selected_catalog.clear_detections()
        self.selected_catalog.load_detections(project = self.parent.project,
                                              start_time = start_time,
                                              end_time = end_time)
        self.selected_catalog.assign_channel(self.parent.project.geometry_inventory)
        self.logger.debug('....done.')


    def on_after_plot(self):
        ''' The hook called after the plotting in tracedisplay.
        '''
        self.logger.debug('on_after_plot')
        self.add_detection_marker_to_station(station = self.parent.displayManager.showStations)


    def on_after_plot_station(self, station):
        ''' The hook called after the plotting of a station in tracedisplay.
        '''
        self.logger.debug('on_after_plot_station')
        self.add_detection_marker_to_station(station = station)


    def add_detection_marker_to_station(self, station = None):
        ''' Add the detection markers to station plots.
        '''
        if station:
            # Load the detections from the database.
            # TODO: Limit the request to the selected stations.
            self.load_detections()
            for cur_station in station:
                self.add_detection_marker_to_channel(cur_station.channels)


    def add_detection_marker_to_channel(self, channel = None):
        ''' Add the detection markers to channel plots.
        '''
        for cur_channel in channel:
            scnl = cur_channel.getSCNL()
            channel_nodes = self.parent.viewport.get_node(station = scnl[0],
                                                          channel = scnl[1],
                                                          network = scnl[2],
                                                          location = scnl[3],
                                                          node_type = 'container')
            for cur_node in channel_nodes:
                cur_detection_list = self.selected_catalog.get_detections(scnl = cur_channel.scnl)

                for cur_detection in cur_detection_list:
                    cur_node.plot_annotation_vspan(x_start = cur_detection.start_time,
                                                   x_end = cur_detection.end_time,
                                                   label = cur_detection.db_id,
                                                   parent_rid = self.rid,
                                                   key = cur_detection.db_id,
                                                   color = self.colors['detection_vspan'])


    def clear_annotation(self):
        ''' Clear the annotation elements in the tracedisplay views.
        '''
        node_list = self.parent.viewport.get_node(node_type = 'container')
        for cur_node in node_list:
            cur_node.clear_annotation_artist(mode = 'vspan',
                                             parent_rid = self.rid)
            cur_node.draw()

