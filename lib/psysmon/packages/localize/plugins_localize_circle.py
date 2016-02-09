import ipdb
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

import psysmon
import psysmon.core.preferences_manager as preferences_manager


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

        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'p_velocity',
                                                       label = 'P velocity [m/s]',
                                                       value = 5000,
                                                       limit = (1, 100000),
                                                       tool_tip = 'The P-wave velocity in m/s.'
                                                      )
        self.pref_manager.add_item(item = item)


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
                return

            # Check for the shared pick catalog.
            pick_info = self.parent.get_shared_info(name = 'selected_pick_catalog')
            if pick_info:
                if len(pick_info) > 1:
                    raise RuntimeError("More than one pick catalog info was returned. This shouldn't happen.")
                pick_info = pick_info[0]
                pick_catalog = pick_info.value['catalog']
            else:
                return


            # TODO: Split the selected phases into P- and S- phases.
            # Check for the shared phases.
            phase_info = self.parent.get_shared_info(name = 'selected_phases')
            if phase_info:
                if len(phase_info) > 1:
                    raise RuntimeError("More than one phase info was returned. This shouldn't happen.")
                phase_info = phase_info[0]
                phases = phase_info.value['phases']
            else:
                return


            # Compute the epidistances.
            self.compute_epidist(event_id, pick_catalog, p_phases, s_phases)

            # Plot the circles into the map view axes.
            self.plot_circles()


    def compute_epidist(self, event_id, pick_catalog, p_phases, s_phases, stations = None):
        ''' Compute the epidistances.
        '''
        # Get the stations for which to compute the epidistances.
        ipdb.set_trace() ############################## Breakpoint ##############################
        if not stations:
            stations = self.parent.project.geometry_inventory.get_station()

        epidist = {}
        for cur_station in stations:
            # TODO: Compute all combinations of P and S phases.
            cur_p = pick_catalog.get_pick(event_id = event_id,
                                          station = cur_station.name)



    def plot_circles(self):
        ''' Plot the circles in the map view.
        '''
        pass
