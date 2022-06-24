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

import psysmon
import psysmon.gui.bricks as gui_bricks
import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons
import psysmon.core.preferences_manager as preferences_manager



class SortMode(plugins.OptionPlugin):
    ''' Publish the visible (processed) data to the project server.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.OptionPlugin.__init__(self,
                                      name = 'sort mode',
                                      category = 'display',
                                      tags = ['sort'])
        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.iconsBlack16.list_num_icon_16

        # The sort mode map.
        self.mode_map = {'nsl code': 'name',
                         'relative distance': 'rel_distance',
                         'custom epicenter': 'custom_epicenter'}

        # The plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        sort_group = pref_page.add_group('sort')

        limit = ['nsl code',
                 'relative distance',
                 'custom epicenter']
        tool_tip = 'The sort order used for the station display.'
        hooks = {'on_value_change': self.on_change_sort_mode}
        item = preferences_manager.SingleChoicePrefItem(name = 'sort_mode',
                                                        label = 'mode',
                                                        limit = limit,
                                                        value = 'nsl code',
                                                        tool_tip = tool_tip,
                                                        hooks = hooks)
        sort_group.add_item(item)

        limit = []
        tool_tip = 'The reference station used to compute the distance in relative distance sort mode.'
        hooks = {'on_value_change': self.on_change_sort_mode}
        item = preferences_manager.SingleChoicePrefItem(name = 'ref_station',
                                                        label = 'ref. station',
                                                        limit = limit,
                                                        value = None,
                                                        tool_tip = tool_tip,
                                                        hooks = hooks)
        sort_group.add_item(item)

        item = preferences_manager.FloatSpinPrefItem(name = 'ref_longitude',
                                                     label = 'longitude [°]',
                                                     value = 0,
                                                     limit = (-180, 180),
                                                     tool_tip = 'The longitude of the reference epicenter [°].')
        sort_group.add_item(item)

        item = preferences_manager.FloatSpinPrefItem(name = 'ref_latitude',
                                                     label = 'latitude [°]',
                                                     value = 0,
                                                     limit = (-90, 90),
                                                     tool_tip = 'The latitude of the reference epicenter [°].')
        sort_group.add_item(item)


    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        pref_man = self.pref_manager
        
        # The the limits of context sensitive items.
        self.set_context_limits()

        # Build the panel.
        fold_panel = gui_bricks.PrefEditPanel(pref = pref_man,
                                              parent = panelBar)

        # Call the change_sort_mode function to initialize all settings.
        self.on_change_sort_mode()

        return fold_panel
    
    
    def set_context_limits(self):
        ''' Set limits of context sensitive items.
        '''
        pref_man = self.pref_manager
        disp_man = self.parent.displayManager

        # Set the limits of the reference station field.
        cur_value = pref_man.get_value('ref_station')
        show_stations = disp_man.showStations
        limit = [x.label for x in show_stations]
        pref_man.set_limit('ref_station',
                           limit)
        if not cur_value:
            pref_man.set_value('ref_station',
                               limit[0])
        

    def disable_context_items(self):
        ''' Disable all context sensitive GUI items.
        '''
        pref_man = self.pref_manager
        item_names = ['ref_station',
                      'ref_longitude',
                      'ref_latitude']
        
        for cur_name in item_names:
            cur_item = pref_man.get_item(cur_name)[0]
            cur_item.disable_gui_element()

            
    def enable_gui_items(self, names):
        ''' Enable selected GUI items.
        '''
        pref_man = self.pref_manager
        for cur_name in names:
            cur_item = pref_man.get_item(cur_name)[0]
            cur_item.enable_gui_element()
        
    
    def on_change_sort_mode(self):
        ''' Hook called when the sort mode preference has been changed.
        '''
        pref_man = self.pref_manager
        disp_man = self.parent.displayManager
        selected_mode = pref_man.get_value('sort_mode')
        sort_mode = self.mode_map[selected_mode]
        sort_order = 'ascending'
        kwargs = {}

        # Refresh the limits of the context sensitive items.
        self.set_context_limits()

        # Disable all context sensitive items.
        self.disable_context_items()

        if sort_mode == 'rel_distance':
            ref_station = pref_man.get_value('ref_station')
            ref_station = ref_station.split(':')
            kwargs = {'ref_station': ref_station}

            # Enable the reference station item.
            self.enable_gui_items(names = ['ref_station'])

        elif sort_mode == 'custom_epicenter':
            # Enable the custom epicenter items.
            self.enable_gui_items(names = ['ref_longitude',
                                           'ref_latitude'])
            ref_longitude = pref_man.get_value('ref_longitude')
            ref_latitude = pref_man.get_value('ref_latitude')
            kwargs = {'ref_longitude': ref_longitude,
                      'ref_latitude': ref_latitude}

        if kwargs:
            disp_man.set_station_sort_mode(mode = sort_mode,
                                           order = sort_order,
                                           **kwargs)
        else:
            disp_man.set_station_sort_mode(mode = sort_mode,
                                           order = sort_order)
