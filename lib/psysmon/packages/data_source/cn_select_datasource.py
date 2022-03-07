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
Handling data sources.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html


'''

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.core.gui_preference_dialog as psy_guiprefdlg


class SelectDataSource(psysmon.core.packageNodes.CollectionNode):
    ''' Select the data source for the execution of a collection.
    '''
    name = 'select data source'
    mode = 'editable'
    category = 'data handling'
    tags = []

    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        select_page = self.pref_manager.add_page('Select')
        source_group = select_page.add_group('source')

        # The waveclient to work with.
        item = psy_pm.SingleChoicePrefItem(name = 'waveclient',
                                           label = 'waveclient',
                                           limit = (),
                                           value = '',
                                           tool_tip = 'The available database waveclients.',
                                           hooks = {'on_value_change': self.on_waveclient_selected})
        source_group.add_item(item)

        # The waveform directories of the waveclient.
        column_labels = ['db_id', 'waveclient', 'waveform dir', 'alias', 'description',
                         'data file extension', 'first import', 'last scan']
        item = psy_pm.ListCtrlEditPrefItem(name = 'wf_dir',
                                           label = 'waveform directory',
                                           value = [],
                                           column_labels = column_labels,
                                           limit = [],
                                           tool_tip = 'The available waveform directories.',
                                           hooks = {'on_value_change': self.on_wf_dir_selected})

        source_group.add_item(item)

    def edit(self):
        ''' Call the edit dialog of the collection node.
        '''
        # Get all database clients.
        #db_clients = sorted([x for x in self.project.waveclient.values() if x.mode == 'PsysmonDbWaveClient'])
        waveclients = sorted([x for x in list(self.project.waveclient.values())])
        waveclient_names = [x.name for x in waveclients]
        self.pref_manager.set_limit('waveclient', waveclient_names)
        sel_client = self.pref_manager.get_value('waveclient')
        if not sel_client:
            sel_client = waveclient_names[0]
            self.pref_manager.set_value('waveclient', sel_client)

        self.on_waveclient_selected()

        dlg = psy_guiprefdlg.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prefNodeOutput = {}):
        ''' Execute the collection node.
        '''
        selected_waveclient = self.pref_manager.get_value('waveclient')
        selected_wf_dir = self.pref_manager.get_value('wf_dir')

        # Build the data source dictionary.
        # TODO: Implement the scnl specific data sources for a collection.
        scnl = [x.scnl for x in self.project.geometry_inventory.get_channel()]
        default_source = selected_waveclient
        self.parentCollection.data_sources = dict([(x, default_source) for x in scnl])


        # TODO: Implement a restriction to one or more waveform directories.
        # TODO: Implement a collection node to select the data source for
        # individual SCNL.


    def on_wf_dir_selected(self):
        ''' Handle selections of the waveform directory.
        '''
        selected_wf_dir = self.pref_manager.get_value('wf_dir')
        if selected_wf_dir:
            selected_wf_dir = selected_wf_dir[0]
        else:
            return

        item = self.pref_manager.get_item('search_path')[0]
        control_element = item.gui_element[0].controlElement
        item.start_directory = selected_wf_dir.alias
        control_element.startDirectory = selected_wf_dir.alias


    def on_waveclient_selected(self):
        ''' Handle selections of the waveclient.
        '''
        selected_waveclient = self.pref_manager.get_value('waveclient')
        if not selected_waveclient:
            return

        client = self.project.waveclient[selected_waveclient]

        if client.mode is not 'PsysmonDbWaveClient':
            waveform_dir_list = []
        else:
            client.loadWaveformDirList()
            waveform_dir_list = client.waveformDirList

        self.pref_manager.set_limit('wf_dir', waveform_dir_list)

        # Select existing values based on the waveform dir id.
        values = self.pref_manager.get_value('wf_dir')
        value_ids = [x[0] for x in values]
        values = [x for x in waveform_dir_list if x[0] in value_ids]
        values = list(set(values))
        self.pref_manager.set_value('wf_dir', values)
