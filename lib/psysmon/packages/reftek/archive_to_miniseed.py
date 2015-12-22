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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The convert reftek archive to miniseed module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog


class ConvertArchiveToMiniseed(psysmon.core.packageNodes.CollectionNode):
    '''
    '''
    name = 'reftek archive to miniseed'
    mode = 'editable'
    category = 'Reftek utilities'
    tags = ['development', ]


    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        self.create_archive_prefs()


    def create_archive_prefs(self):
        ''' Create the archive input preference items.
        '''
        pagename = '1 input'
        self.pref_manager.add_page(pagename)

        # The archive directory
        pref_item = psy_pm.DirBrowsePrefItem(name = 'archive_dir',
                                             label = 'archive directory',
                                             group = 'archive',
                                             value = '',
                                             tool_tip = 'The root directory of the Reftek raw data archive.'
                                            )
        self.pref_manager.add_item(pagename = pagename, item = pref_item)


    def edit(self):
        ''' Create the edit dialog.
        '''
        dlg = psysmon.core.gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()

