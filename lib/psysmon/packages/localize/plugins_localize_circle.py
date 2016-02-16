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
'''
The plugin for the localization using the circle method.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import logging

import numpy as np

import psysmon
import psysmon.core.preferences_manager as preferences_manager

import matplotlib as mpl
import matplotlib.patches
import mpl_toolkits.basemap as basemap


class LocalizeCircle(psysmon.core.plugins.CommandPlugin):
    ''' Run a localization using the circle method.

    '''
    nodeClass = 'GraphicLocalizationNode'


    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.CommandPlugin.__init__(self,
                                                    name = 'circle method',
                                                    category = 'localize',
                                                    tags = ['localize', 'circle']
                                                    )

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = psysmon.artwork.icons.iconsBlack16.localize_graphical_icon_16

        # Setup the order of the groups.
        self.pref_manager.group_order = ['phase selection', 'velocity model']
        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'p_velocity',
                                                       label = 'P velocity [m/s]',
                                                       group = 'velocity model',
                                                       value = 5000,
                                                       limit = (1, 100000),
                                                       tool_tip = 'The P-wave velocity in m/s.'
                                                      )
        self.pref_manager.add_item(item = item)


        item = psysmon.core.preferences_manager.MultiChoicePrefItem(name = 'p_phases',
                                          label = 'P phases',
                                          group = 'phase selection',
                                          value = [],
                                          limit = [],
                                          tool_tip = 'Select the P phases to use for the localization.')
        self.pref_manager.add_item(item = item)

        item = psysmon.core.preferences_manager.MultiChoicePrefItem(name = 's_phases',
                                          label = 'S phases',
                                          group = 'phase selection',
                                          value = [],
                                          limit = [],
                                          tool_tip = 'Select the S phases to use for the localization.')
        self.pref_manager.add_item(item = item)


        # The plotted circles.
        self.circles = []


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}

        hooks['shared_information_added'] = self.on_shared_information_added
        return hooks


    def on_shared_information_added(self, origin_rid, name):
        ''' Hook that is called when a shared information was added by a plugin.
        '''
        rid = '/plugin/select_picks'
        if origin_rid.endswith(rid) and name == 'selected_pick_catalog':
            self.update_phases()


    def update_phases(self):
        ''' Update the available P- and S-phases.
        '''
        # TODO: Get the selected pick catalog. The pick catalog should contain
        # only the picks of the selected event. This should be handled by the
        # select_picks plugin.
        # Check for the shared pick catalog.
        pick_info = self.parent.get_shared_info(name = 'selected_pick_catalog')
        if pick_info:
            if len(pick_info) > 1:
                raise RuntimeError("More than one pick catalog info was returned. This shouldn't happen.")
            pick_info = pick_info[0]
            catalog = pick_info.value['catalog']
        else:
            self.logger.error("No selected pick catalog available. Can't continue the localization.")
            return

        labels = list(set([x.label for x in catalog.picks]))
        p_phases = [x for x in labels if x.lower().startswith('p')]
        s_phases = [x for x in labels if x.lower().startswith('s')]
        self.pref_manager.set_limit('p_phases', p_phases)
        self.pref_manager.set_limit('s_phases', s_phases)
        # TODO: Check if the currently selected values are part of the
        # available limits. This should be done by the pref_manager fields.


    def run(self):
        ''' Run the circle method localization.
        '''
        self.logger.info("Localizing using the circle method.")

        # Check for an existing 2D map view.
        map_view_name = self.rid[:self.rid.rfind('/') + 1] + 'map_view'
        map_view = self.parent.viewport.get_node(name = map_view_name)
        if map_view:
            # Check for the shared selected event.
            selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/select_event',
                                                                               name = 'selected_event')
            if selected_event_info:
                if len(selected_event_info) > 1:
                    raise RuntimeError("More than one event info was returned. This shouldn't happen.")
                selected_event_info = selected_event_info[0]
                event_id = selected_event_info.value['id']
            else:
                self.logger.error("No selected event available. Can't continue the localization.")
                return

            # Check for the shared pick catalog.
            pick_info = self.parent.get_shared_info(name = 'selected_pick_catalog')
            if pick_info:
                if len(pick_info) > 1:
                    raise RuntimeError("More than one pick catalog info was returned. This shouldn't happen.")
                pick_info = pick_info[0]
                pick_catalog = pick_info.value['catalog']
            else:
                self.logger.error("No selected pick catalog available. Can't continue the localization.")
                return

            p_phases = self.pref_manager.get_value('p_phases')
            s_phases = self.pref_manager.get_value('s_phases')

            # Compute the epidistances.
            epidist = self.compute_epidist(event_id, pick_catalog, p_phases, s_phases)

            # Plot the circles into the map view axes.
            self.plot_circles(epidist)




    def compute_epidist(self, event_id, pick_catalog, p_phases, s_phases, stations = None):
        ''' Compute the epidistances.
        '''
        if not p_phases:
            self.logger.error("No P phases available. Can't continue with localization.")
            return

        if not s_phases:
            self.logger.error("No S phases available. Can't continue with localization.")
            return

        # Get the stations for which to compute the epidistances.
        if not stations:
            stations = self.parent.project.geometry_inventory.get_station()

        used_picks = []
        vp = self.pref_manager.get_value('p_velocity')
        epidist = {}
        for cur_station in stations:
            epidist[cur_station.name] = {}
            for cur_p_phase in p_phases:
                cur_p = pick_catalog.get_pick(event_id = event_id,
                                              label = cur_p_phase,
                                              station = cur_station.name)
                if not cur_p:
                    self.logger.info("No pick found for event_id %d, station %s and label %s. Can't compute the S-P difference.", event_id, cur_station.name, cur_p_phase)
                    continue

                if len(cur_p) > 1:
                    raise RuntimeError("More than one phase was returned for station %s, event_id %d and label %s. This shouldn't happen." % (cur_station.name, event_id, cur_p_phase))
                cur_p = cur_p[0]

                for cur_s_phase in s_phases:
                    cur_s = pick_catalog.get_pick(event_id = event_id,
                                                  label = cur_s_phase,
                                                  station = cur_station.name)
                    if not cur_s:
                        self.logger.info("No pick found for event_id %d, station %s and label %s. Can't compute the S-P difference.", event_id, cur_station.name, cur_s_phase)
                        continue
                    if len(cur_s) > 1:
                        raise RuntimeError("More than one phase was returned for station %s, event_id %d and label %s. This shouldn't happen." % (cur_station.name, event_id, cur_s_phase))
                    cur_s = cur_s[0]

                    sp_diff = cur_s.time - cur_p.time
                    cur_epidist = sp_diff * vp / (np.sqrt(3) - 1)
                    epidist[cur_station.name][(cur_p.label, cur_s.label)] = cur_epidist

                    used_picks.append(cur_p)
                    used_picks.append(cur_s)

        used_data = {}
        used_data['picks'] = used_picks
        used_data['event_id'] = event_id
        self.parent.add_shared_info(origin_rid = self.rid,
                                    name = 'used_data',
                                    value = used_data)

        return epidist


    def plot_circles(self, epidist):
        ''' Plot the circles in the map view.
        '''
        # Get all map views.
        map_view_name = self.rid[:self.rid.rfind('/') + 1] + 'map_view'
        map_view = self.parent.viewport.get_node(name = map_view_name)

        for cur_view in map_view:
            proj = basemap.pyproj.Proj(init = cur_view.map_config['epsg'])

            # Remove existing circles from the view.
            circles_to_delete = [x for x in cur_view.axes.patches if x.get_gid() == self.rid]
            for cur_circle in circles_to_delete:
                cur_view.axes.patches.remove(cur_circle)

            for cur_station_name in epidist.keys():
                station = self.parent.project.geometry_inventory.get_station(name = cur_station_name)

                if not station:
                    continue

                station = station[0]
                stat_lon, stat_lat = station.get_lon_lat()
                stat_x, stat_y = proj(stat_lon, stat_lat)
                for cur_key, cur_epidist in epidist[cur_station_name].iteritems():
                    label = cur_station_name + ':' + cur_key[0] + ':' + cur_key[1]
                    circle = mpl.patches.Circle((stat_x, stat_y), radius = cur_epidist,
                                                fill = False, gid = self.rid, label = label)
                    cur_view.axes.add_patch(circle)
                    self.circles.append(circle)

            # Remove existing text from the axes.
            text_2_delete = [x for x in cur_view.axes.texts if x.get_gid() == self.rid]
            for cur_text in text_2_delete:
                cur_view.axes.texts.remove(cur_text)
            # Add the used velocity to the map.
            cur_view.axes.text(0.98, 0.02, 'circle vp = ' + str(self.pref_manager.get_value('p_velocity')) + ' m/s',
                ha = 'right', transform = cur_view.axes.transAxes, gid = self.rid)

            #cur_view.axes.autoscale(True)
            cur_view.draw()

