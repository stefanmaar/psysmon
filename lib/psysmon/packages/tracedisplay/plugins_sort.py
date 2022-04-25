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

import psysmon.core.guiBricks as gui_bricks
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
                                      category = 'view',
                                      tags = ['sort']
                                      )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.list_num_icon_16

        # The plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        sort_group = pref_page.add_group('sort')

        limit = ('station name',
                 'relative_distance')
        tool_tip = 'The sort order used for the station display.'
        hooks = {'on_value_change': self.on_change_sort_mode}
        item = preferences_manager.SingleChoicePrefItem(name = 'mode',
                                                        label = 'mode',
                                                        limit = limit,
                                                        value = 'station',
                                                        tool_tip = tool_tip,
                                                        hooks = hooks)
        sort_group.add_item(item)


    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        fold_panel = gui_bricks.PrefEditPanel(pref = self.pref_manager,
                                              parent = panelBar)

        return fold_panel

    
    def on_change_sort_mode(self):
        ''' Hook called when the sort mode preference has been changed.
        '''
        sort_mode = 'rel_distance'
        sort_order = 'ascending'
        self.parent.displayManager.set_station_sort_mode(mode = sort_mode,
                                                         order = sort_order)
