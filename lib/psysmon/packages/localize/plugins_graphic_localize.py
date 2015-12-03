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
import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons
import psysmon.core.preferences_manager as preferences_manager


class PluginGraphicLocalizer(plugins.CommandPlugin):
    ''' Localize an event origin using graphical methods.
    '''
    nodeClass = 'common'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'graphical localization',
                                       category = 'localize',
                                       tags = ['localize', 'circle', 'hyperble', 'tdoa', 'time difference of arrival'])

        # Create the logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.localize_graphical_icon_16

        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio', 
                                                       value = 20,
                                                       limit = (1, 99)
                                                      )
        self.pref_manager.add_item(item = item)


    def run(self):
        ''' Initialize the graphical localizer dialog and show it.
        '''
        # TODO: Add the localization method to the dialog attributes.
        # Or even better create a GraphicLocalizer class which does all the
        # computation and pass an instance to the dialog.

        # Get the selected event.
        selected_event_info = self.parent.get_shared_info(name = 'selected_event')
        if selected_event_info:
            selected_event_id = selected_event_info[0].value['id']
            selected_event_catalog_name = selected_event_info[0].value['catalog_name']
        else:
            selected_event_id = None
            selected_event_catalog_name = None

        # Get the selected pick catalog name.
        selected_pick_catalog_info = self.parent.get_shared_info(name = 'selected_pick_catalog')
        if selected_pick_catalog_info:
            selected_pick_catalog_name = selected_pick_catalog_info[0].value['catalog_name']
        else:
            selected_pick_catalog_name = None

        dlg = GraphicLocalizerDialog(project = self.parent.project,
                                     parent = self.parent,
                                     event_id = selected_event_id,
                                     event_catalog_name = selected_event_catalog_name,
                                     pick_catalog_name = selected_pick_catalog_name,
                                     id = wx.ID_ANY)

        dlg.Show()

