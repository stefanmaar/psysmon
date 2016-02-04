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
import psysmon.core.plugins
import psysmon.artwork.icons
import psysmon.packages.pick.core
import psysmon.core.preferences_manager
import psysmon.core.guiBricks
import psysmon.artwork.icons as icons

class SelectPicks(psysmon.core.plugins.OptionPlugin):
    '''

    '''
    nodeClass = 'common'

    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.OptionPlugin.__init__(self,
                                                   name = 'select picks',
                                                   category = 'select',
                                                   tags = ['pick', 'select']
                                                  )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.hand_2_icon_16

        # The pick catalog library used to manage the catalogs.
        self.library = psysmon.packages.pick.core.Library(name = self.rid)

        # The name of the selected catalog.
        self.selected_catalog_name = None

        # Setup the pages of the preference manager.
        self.pref_manager.add_page('select')
        # Add the plugin preferences.
        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'catalog_mode',
                                          label = 'mode',
                                          group = 'catalog',
                                          value = 'time',
                                          limit = ['time',],
                                          tool_tip = 'Select a pick catalog to work on.')
        self.pref_manager.add_item(pagename = 'select',
                                   item = item)

        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'pick_catalog',
                                          label = 'pick catalog',
                                          group = 'catalog',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select a pick catalog to work on.',
                                          hooks = {'on_value_change': self.on_select_catalog})
        self.pref_manager.add_item(pagename = 'select',
                                   item = item)


    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        # Set the limits of the event_catalog field.
        catalog_names = self.library.get_catalogs_in_db(project = self.parent.project)
        self.pref_manager.set_limit('pick_catalog', catalog_names)
        #if catalog_names:
        #    self.pref_manager.set_value('pick_catalog', catalog_names[0])

        fold_panel = psysmon.core.guiBricks.PrefEditPanel(pref = self.pref_manager,
                                                          parent = panelBar)

        # Customize the catalog field.
        #pref_item = self.pref_manager.get_item('pick_catalog')[0]
        #field = pref_item.gui_element[0]
        #fold_panel.Bind(wx.EVT_CHOICE, self.on_catalog_selected, field.controlElement)

        return fold_panel


    def on_select_catalog(self):
        ''' Handle the catalog selection.
        '''
        self.selected_catalog_name = self.pref_manager.get_value('pick_catalog')
        self.parent.add_shared_info(origin_rid = self.rid,
                                    name = 'selected_pick_catalog',
                                    value = {'catalog_name': self.selected_catalog_name})

        # Load the catalog from the database.
        self.library.clear()
        self.library.load_catalog_from_db(project = self.parent.project,
                                          name = self.selected_catalog_name)

        # Load the picks.
        #self.load_picks()


