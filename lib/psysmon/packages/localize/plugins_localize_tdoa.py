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


class LocalizeTdoa(psysmon.core.plugins.CommandPlugin):
    ''' Run a localization using the time-difference of arrival method.

    '''
    nodeClass = 'GraphicLocalizationNode'


    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.CommandPlugin.__init__(self,
                                                    name = 'tdoa method',
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


        item = psysmon.core.preferences_manager.MultiChoicePrefItem(name = 'phases',
                                          label = 'phases',
                                          group = 'phase selection',
                                          value = [],
                                          limit = [],
                                          tool_tip = 'Select the phases to use for the localization.')
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
        self.pref_manager.set_limit('phases', labels)
        # TODO: Check if the currently selected values are part of the
        # available limits. This should be done by the pref_manager fields.


    def run(self):
        ''' Run the tdoa method localization.
        '''
        self.logger.info("Localizing using the TDOA method.")

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

            phases = self.pref_manager.get_value('phases')

            # Compute the epidistances.
            self.run_tdoa(event_id, pick_catalog, phases)
        else:
            self.logger.error("No map view found. Please activate the map view plugin.")



    def run_tdoa(self, event_id, pick_catalog, phases, stations = None):
        ''' Run the time-difference of arrival localization.
        '''
        if not phases:
            self.logger.error("No phases available. Can't continue with localization.")
            return

        # Get the stations for which to compute the epidistances.
        if not stations:
            stations = self.parent.project.geometry_inventory.get_station()

        used_picks = []
        epidist = {}
        for k, cur_master in enumerate(stations):
            for m in range(k+1, len(stations)):
                cur_slave = stations[m]
                for cur_phase in phases:
                    cur_master_pick = pick_catalog.get_pick(event_id = event_id,
                                                            label = cur_phase,
                                                            station = cur_master.name)
                    cur_slave_pick = pick_catalog.get_pick(event_id = event_id,
                                                            label = cur_phase,
                                                            station = cur_slave.name)
                    if not cur_master_pick:
                        self.logger.info("No pick found for event_id %d, station %s and label %s. Can't compute the S-P difference.", event_id, cur_master.name, cur_phase)
                        continue

                    if not cur_slave_pick:
                        self.logger.info("No pick found for event_id %d, station %s and label %s. Can't compute the S-P difference.", event_id, cur_slave.name, cur_phase)
                        continue

                    if len(cur_master_pick) > 1:
                        raise RuntimeError("More than one phase was returned for station %s, event_id %d and label %s. This shouldn't happen." % (cur_master.name, event_id, cur_phase))
                    cur_master_pick = cur_master_pick[0]

                    if len(cur_slave_pick) > 1:
                        raise RuntimeError("More than one phase was returned for station %s, event_id %d and label %s. This shouldn't happen." % (cur_slave.name, event_id, cur_phase))
                    cur_slave_pick = cur_slave_pick[0]

                    self.plot_hyperbola(cur_master, cur_slave, cur_master_pick, cur_slave_pick)

                    #sp_diff = cur_s.time - cur_p.time
                    #cur_epidist = sp_diff * vp / (np.sqrt(3) - 1)
                    #epidist[cur_station.name][(cur_p.label, cur_s.label)] = cur_epidist

                    used_picks.append(cur_master_pick)
                    used_picks.append(cur_slave_pick)

        # Get all map views.
        map_view_name = self.rid[:self.rid.rfind('/') + 1] + 'map_view'
        map_view = self.parent.viewport.get_node(name = map_view_name)

        # Update the map view axes.
        for cur_view in map_view:
            cur_view.draw()

        used_data = {}
        used_data['picks'] = used_picks
        used_data['event_id'] = event_id
        self.parent.add_shared_info(origin_rid = self.rid,
                                    name = 'used_data',
                                    value = used_data)

        return epidist


    def compute_hyperbola(self, r1, r2, t1, t2, x_max):
        ''' Compute a TDOA hyperbola in the first Hauptlage.

        '''
        v = self.pref_manager.get_value('p_velocity')
        dd = v * (t1 - t2)
        D = np.sqrt(np.sum((r1 - r2)**2))
        alpha = np.arctan2(r2[1] - r1[1], r2[0] - r1[0])
        M = (r1 + r2) / 2.


        a = dd/2.
        b = np.sqrt((D/2.)**2 - (dd/2.)**2)

        x = np.arange(0, x_max, x_max/100.)

        if a < 0:
            x = a - x
        else:
            x = a + x

        xa = x**2 / a**2
        mask = xa >= 1
        xa = xa[mask]
        x = x[mask]
        x = np.hstack([np.flipud(x), x])

        b1 = b * np.sqrt(xa -1)
        y = np.hstack([np.flipud(b1), -b1])
        x_hyp = np.cos(alpha) * x - np.sin(alpha) * y + M[0]
        y_hyp = np.sin(alpha) * x + np.cos(alpha) * y + M[1]

        return np.vstack([x_hyp, y_hyp]).transpose()




    def plot_hyperbola(self, master, slave, master_pick, slave_pick):
        ''' Plot the hyperbola in the map view.
        '''
        # Get all map views.
        map_view_name = self.rid[:self.rid.rfind('/') + 1] + 'map_view'
        map_view = self.parent.viewport.get_node(name = map_view_name)

        for cur_view in map_view:
            proj = basemap.pyproj.Proj(init = cur_view.map_config['epsg'])

            # Remove existing circles from the view.
            #hyp_to_delete = [x for x in cur_view.axes.lines if x.get_gid() == self.rid]
            #for cur_hyp in hyp_to_delete:
            #    cur_view.axes.lines.remove(cur_hyp)

            master_lon, master_lat = master.get_lon_lat()
            master_x, master_y = proj(master_lon, master_lat)
            slave_lon, slave_lat = slave.get_lon_lat()
            slave_x, slave_y = proj(slave_lon, slave_lat)

            r1 = np.array([master_x, master_y])
            r2 = np.array([slave_x, slave_y])
            hyp = self.compute_hyperbola(r1, r2, master_pick.time, slave_pick.time, 1000)

            label = master.name + ':' + slave.name + ':' + master_pick.label
            cur_view.axes.autoscale(False)
            cur_view.axes.plot(hyp[:,0], hyp[:,1], gid = self.rid, label = label)




