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

from psysmon.core.packageNodes import CollectionNode
import psysmon.core.preferences_manager as pref_manager


class JsonPlainTestNode(CollectionNode):
    ''' Plain test node.

    This node has no function and no preferences.
    '''
    name = 'json plain testnode'
    mode = 'editable'
    category = 'Test'
    tags = ['stable', 'test']
    docEntryPoint = None

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

    def edit(self):
        pass

    def execute(self, prevModuleOutput={}):
        pass



class JsonPreferencesTestNode(CollectionNode):
    ''' Plain test node.

    This node has no function and no preferences.
    '''
    name = 'json preferences testnode'
    mode = 'editable'
    category = 'Test'
    tags = ['stable', 'test']
    docEntryPoint = None

    def __init__(self):
        CollectionNode.__init__(self)
        pref_item = pref_manager.TextEditPrefItem(name = 'filter_name',
                                                  label = 'filter name',
                                                  value = 'test filter')
        self.pref_manager.add_item(item = pref_item)

        pref_item = pref_manager.DirBrowsePrefItem(name = 'directory_browse',
                                                   label = 'browse',
                                                   value = '',
                                                   start_directory = '/home')
        self.pref_manager.add_item(item = pref_item)

        pref_item = pref_manager.FloatSpinPrefItem(name = 'filter_cutoff',
                                                   label = 'filter cutoff',
                                                   value = '4.5')
        self.pref_manager.add_item(item = pref_item)

    def edit(self):
        pass

    def execute(self, prevModuleOutput={}):
        pass
