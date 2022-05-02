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

from builtins import str
import logging

import psysmon
import psysmon.core.plugins
import psysmon.artwork.icons
import psysmon.packages.pick.core
import psysmon.core.preferences_manager
import psysmon.gui.bricks
import psysmon.artwork.icons as icons

import obspy.core.utcdatetime as utcdatetime

class SelectPicks(psysmon.core.plugins.OptionPlugin):
    '''

    '''
    nodeClass = 'GraphicLocalizationNode'

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
        select_page = self.pref_manager.add_page('select')
        cat_group = select_page.add_group('catalog')
        ap_group = select_page.add_group('available picks')

        # Add the plugin preferences.
        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'catalog_mode',
                                          label = 'mode',
                                          value = 'time',
                                          limit = ['time',],
                                          tool_tip = 'Select a pick catalog to work on.')
        cat_group.add_item(item)

        item = psysmon.core.preferences_manager.SingleChoicePrefItem(name = 'pick_catalog',
                                          label = 'pick catalog',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select a pick catalog to work on.',
                                          hooks = {'on_value_change': self.on_select_catalog})
        cat_group.add_item(item)


        column_labels = ['db_id', 'scnl', 'label', 'time',
                         'agency_uri', 'author_uri']
        item = psysmon.core.preferences_manager.ListCtrlEditPrefItem(name = 'picks',
                                                                     label = 'picks',
                                                                     value = [],
                                                                     column_labels = column_labels,
                                                                     limit = [],
                                                                     hooks = {'on_value_change': self.on_pick_selected},
                                                                     tool_tip = 'The available picks for the selected event.')
        ap_group.add_item(item)



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        # Set the limits of the event_catalog field.
        catalog_names = self.library.get_catalogs_in_db(project = self.parent.project)
        self.pref_manager.set_limit('pick_catalog', catalog_names)
        #if catalog_names:
        #    self.pref_manager.set_value('pick_catalog', catalog_names[0])

        fold_panel = psysmon.gui.bricks.PrefEditPanel(pref = self.pref_manager,
                                                          parent = panelBar)

        # Customize the catalog field.
        #pref_item = self.pref_manager.get_item('pick_catalog')[0]
        #field = pref_item.gui_element[0]
        #fold_panel.Bind(wx.EVT_CHOICE, self.on_catalog_selected, field.controlElement)

        return fold_panel


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}

        hooks['shared_information_added'] = self.on_shared_information_added
        return hooks


    def on_shared_information_added(self, origin_rid, name):
        ''' Hook that is called when a shared information was added by a plugin.
        '''
        rid = '/plugin/select_event'
        if origin_rid.endswith(rid) and name == 'selected_event':
            self.load_picks()


    def on_select_catalog(self):
        ''' Handle the catalog selection.
        '''
        self.selected_catalog_name = self.pref_manager.get_value('pick_catalog')

        self.logger.info("Selected a catalog.")

        # Load the catalog from the database.
        self.library.clear()
        self.library.load_catalog_from_db(project = self.parent.project,
                                          name = self.selected_catalog_name)

        # Load the picks.
        self.load_picks()

        # Share the selected catalog.
        selected_catalog = self.library.catalogs[self.selected_catalog_name]
        self.parent.add_shared_info(origin_rid = self.rid,
                                    name = 'selected_pick_catalog',
                                    value = {'catalog': selected_catalog})


    def on_pick_selected(self):
        ''' Handle a value change in the picks list control.

        '''
        cur_catalog = self.library.catalogs[self.selected_catalog_name]
        pick_ids = [int(x[0]) for x in self.pref_manager.get_value('picks')]
        selected_picks = []
        for cur_id in pick_ids:
            selected_picks.extend(cur_catalog.get_pick(db_id = cur_id))
        self.parent.add_shared_info(origin_rid = self.rid,
                                    name = 'selected_picks',
                                    value = {'picks': selected_picks})


    def load_picks(self):
        ''' Load the picks for the selected event.
        '''
        cur_catalog = self.library.catalogs[self.selected_catalog_name]
        cur_catalog.clear_picks()

        # Check if an event is selected. If one is selected, use the event
        # limits to load the picks.
        selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/select_event',
                                                                           name = 'selected_event')
        if selected_event_info:
            if len(selected_event_info) > 1:
                raise RuntimeError("More than one event info was returned. This shouldn't happen.")
            selected_event_info = selected_event_info[0]
            cur_catalog.load_picks(project = self.parent.project,
                                   event_id = [selected_event_info.value['id'], ])
            pick_list = self.convert_picks_to_list(cur_catalog.picks)
            self.pref_manager.set_limit('picks', pick_list)

        # Update the shared information.
        self.parent.add_shared_info(origin_rid = self.rid,
                                    name = 'selected_pick_catalog',
                                    value = {'catalog': cur_catalog})



    def convert_picks_to_list(self, picks):
        ''' Convert a list of pick objects to a list suitable for the GUI element.
        '''
        list_fields = []
        list_fields.append(('db_id', 'id', int))
        list_fields.append(('scnl_string', 'scnl', str))
        list_fields.append(('label', 'label', str))
        list_fields.append(('time', 'time', str))
        list_fields.append(('agency_uri', 'agency_uri', str))
        list_fields.append(('author_uri', 'author_uri', str))

        pick_list = []
        for cur_pick in picks:
            cur_row = []
            for cur_field in list_fields:
                cur_name = cur_field[0]
                if cur_name == 'scnl_string':
                    cur_row.append(str(cur_pick.channel.scnl_string))
                else:
                    cur_row.append(str(getattr(cur_pick, cur_name)))
            pick_list.append(cur_row)

        return pick_list

