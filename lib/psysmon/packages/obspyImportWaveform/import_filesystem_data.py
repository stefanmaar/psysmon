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
import logging

import psysmon
import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.gui.dialog.pref_listbook as psy_lb


class ImportFilesystemData(psysmon.core.packageNodes.CollectionNode):
    ''' Import data from the filesystem using the DB Waveclient.
    '''
    name = 'import filesystem data'
    mode = 'editable'
    category = 'Data Import'
    tags = ['stable']

    def __init__(self, **args):
        # Initialize the instance.
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)
        
        select_page = self.pref_manager.add_page('Select')
        wfdir_group = select_page.add_group('waveform directory')
        import_group = select_page.add_group('import options')


        item = psy_pm.SingleChoicePrefItem(name = 'waveclient',
                                           label = 'waveclient',
                                           limit = (),
                                           value = '',
                                           tool_tip = 'The available database waveclients.',
                                           hooks = {'on_value_change': self.on_waveclient_selected})
        wfdir_group.add_item(item)


        column_labels = ['db_id', 'waveclient', 'waveform dir', 'alias', 'description',
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

        # Get all database clients.
        db_clients = sorted([x for x in list(self.project.waveclient.values()) if x.mode == 'PsysmonDbWaveClient'])
        db_client_names = [x.name for x in db_clients]
        self.pref_manager.set_limit('waveclient', db_client_names)
        sel_client = self.pref_manager.get_value('waveclient')
        if not sel_client:
            sel_client = db_client_names[0]
            self.pref_manager.set_value('waveclient', sel_client)

        self.on_waveclient_selected()

        dlg = psy_lb.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prefNodeOutput = {}):

        selected_waveclient = self.pref_manager.get_value('waveclient')
        selected_wf_dir = self.pref_manager.get_value('wf_dir')

        client = self.project.waveclient[selected_waveclient]

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
        item.start_directory = selected_wf_dir[3]
        control_element.startDirectory = selected_wf_dir[3]


    def on_waveclient_selected(self):
        ''' Handle selections of the waveclient.
        '''
        selected_waveclient = self.pref_manager.get_value('waveclient')
        if not selected_waveclient:
            return

        client = self.project.waveclient[selected_waveclient]
        client.loadWaveformDirList()
        waveform_dir_list = client.waveformDirDict

        # Convert the dictionaries to lists.
        waveform_dir_list = [[x['id'],
                              x['waveclient'],
                              x['directory'],
                              x['alias'],
                              x['description'],
                              x['file_ext'],
                              x['first_import'],
                              x['last_scan']] for x in waveform_dir_list]

        self.pref_manager.set_limit('wf_dir', waveform_dir_list)

        # Select existing values based on the waveform dir id.
        try:
            values = self.pref_manager.get_value('wf_dir')
            # Ignore None values which might be caused
            # by bad preference value settings.
            values = [x for x in values if x is not None]
            value_ids = [x[0] for x in values]
            value_ids = list(set(value_ids))
            values = [x for x in waveform_dir_list if x[0] in value_ids]
            self.pref_manager.set_value('wf_dir', values)
        except Exception:
            self.logger.exception("Couldn't set the selected waveform directories.")
