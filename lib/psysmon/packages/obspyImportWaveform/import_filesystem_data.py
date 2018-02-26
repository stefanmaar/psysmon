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
The import filesystem data module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html


'''

import psysmon.core.gui_preference_dialog as psy_guiprefdlg
import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm

class ImportFilesystemData(psysmon.core.packageNodes.CollectionNode):
    ''' Import data from the filesystem using the DB Waveclient.
    '''
    name = 'import filesystem data'
    mode = 'editable'
    category = 'Data Import'
    tags = ['stable']

    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        select_page = self.pref_manager.add_page('Select')
        wfdir_group = select_page.add_group('waveform directory')
        import_group = select_page.add_group('import options')

        column_labels = ['db_id', 'waveform dir', 'alias', 'description',
                         'data file extension', 'first import', 'last scan']
        item = psy_pm.ListCtrlEditPrefItem(name = 'wf_dir',
                                           label = 'waveform directory',
                                           value = [],
                                           column_labels = column_labels,
                                           limit = [],
                                           tool_tip = 'The available waveform directories.',
                                           hooks = {'on_value_change': self.on_wf_dir_selected})
        wfdir_group.add_item(item)


        item = psy_pm.CheckBoxPrefItem(name = 'import_new_only',
                                       label = 'import new files only',
                                       value = True,
                                       tool_tip = 'Import only files not yet imported to the database. New files are detected based on the file name and file size. If unchecked all existing data associated with the selected waveform directory is deleted from the database before importing the new files in the waveform directory.')
        import_group.add_item(item)

        item = psy_pm.CheckBoxPrefItem(name = 'restrict_search_path',
                                       label = 'restrict search path',
                                       value = False,
                                       tool_tip = 'Restrict the search within the waveform directory to the directory specified below.')
        import_group.add_item(item)

        item = psy_pm.DirBrowsePrefItem(name = 'search_path',
                                        label = 'search path',
                                        value = '',
                                        tool_tip = 'The search path used to restrict the search.')
        import_group.add_item(item)


    def edit(self):
        # TODO: List the number of potential files in the grid.
        # TODO: List the number of imported files in the grid.
        # TODO: List the number of files in the data directory in the grid.
        client = self.project.waveclient['db client']
        client.loadWaveformDirList()
        waveform_dir_list = client.waveformDirList
        self.pref_manager.set_limit('wf_dir', waveform_dir_list)
        # Select existing values based on the waveform dir id.
        values = self.pref_manager.get_value('wf_dir')
        value_ids = [x[0] for x in values]
        values = [x for x in waveform_dir_list if x[0] in value_ids]
        values = list(set(values))
        self.pref_manager.set_value('wf_dir', values)

        dlg = psy_guiprefdlg.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prefNodeOutput = {}):
        client = self.project.waveclient['db client']
        selected_wf_dir = self.pref_manager.get_value('wf_dir')

        for cur_wf_dir in selected_wf_dir:
            self.logger.info('Importing data from waveformdirectory %d - %s.', cur_wf_dir[0], cur_wf_dir[1])
            if self.pref_manager.get_value('restrict_search_path'):
                search_path = self.pref_manager.get_value('search_path')
            else:
                search_path = None
            client.import_waveform(cur_wf_dir[0],
                                   import_new_only = self.pref_manager.get_value('import_new_only'),
                                   search_path = search_path)


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


