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

import sqlalchemy
import wx

import psysmon
import psysmon.core.preferences_manager as psy_pm
import psysmon.gui.dialog.pref_listbook as psy_lb


class PsysmonDbWaveClientOptions(wx.Panel):

    def __init__(self, parent=None, client=None, project=None, size=(-1, -1)):
        ''' Initialize the instance.

        '''
        wx.Panel.__init__(self, parent, wx.ID_ANY, size = size)

        # The logger.
        self.logger = psysmon.get_logger(self)

        # The waveclient holding the options.
        self.client = client

        # The currently selected directory index.
        self.selected_waveform_dir = None

        # Create the grid editing buttons.
        addDirButton = wx.Button(self, wx.ID_ANY, "add")
        removeDirButton = wx.Button(self, wx.ID_ANY, "remove")
        editDirButton = wx.Button(self, wx.ID_ANY, "edit")

        gridButtonSizer = wx.BoxSizer(wx.VERTICAL)

        # Fill the grid button sizer
        gridButtonSizer.Add(addDirButton, 0, wx.EXPAND | wx.ALL)
        gridButtonSizer.Add(editDirButton, 0, wx.EXPAND | wx.ALL)
        gridButtonSizer.Add(removeDirButton, 0, wx.EXPAND | wx.ALL)

        fields = self.getGridColumns()
        self.wfListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)

        for k, (name, label, attr) in enumerate(fields):
            self.wfListCtrl.InsertColumn(k, label)


        # Add the editing elements.
        self.name_label = wx.StaticText(self, -1, "name:")
        self.name_edit = wx.TextCtrl(self, -1,
                                     self.client.name, size=(100, -1))
        self.description_label = wx.StaticText(self, -1, "description:")
        self.description_edit = wx.TextCtrl(self, -1,
                                            self.client.description,
                                            size=(100, -1))

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)


        sizer.Add(self.name_label, pos=(0, 0),
                  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border = 5)
        sizer.Add(self.name_edit, pos=(0, 1),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)
        sizer.Add(self.description_label, pos=(1, 0),
                  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border=5)
        sizer.Add(self.description_edit, pos=(1, 1),
                  flag=wx.EXPAND | wx.ALL,
                  border = 5)

        sizer.Add(self.wfListCtrl, pos=(2, 1),
                  flag = wx.EXPAND | wx.ALL,
                  border=5)
        sizer.Add(gridButtonSizer, pos=(2, 2),
                  flag = wx.EXPAND | wx.ALL,
                  border=5)

        sizer.AddGrowableRow(2)
        sizer.AddGrowableCol(1)

        self.SetSizer(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onAddDirectory, addDirButton)
        self.Bind(wx.EVT_BUTTON, self.onRemoveDirectory, removeDirButton)
        self.Bind(wx.EVT_BUTTON, self.onEditDirectory, editDirButton)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.onDirectorySelected,
                  self.wfListCtrl)

        self.SetSizerAndFit(sizer)

        self.project = project
        self.wfDir = self.project.dbTables['waveform_dir']
        self.wfDirAlias = self.project.dbTables['waveform_dir_alias']
        self.dbSession = self.project.getDbSession()

        # The preferences of the selected waveform directory.
        self.wfd_pref_manager = psy_pm.PreferencesManager()
        self.create_wfd_preferences()

        # A list of available waveform directories. It consits of tuples of
        self.wfDirList = self.dbSession.query(self.wfDir).join(self.wfDirAlias,
                                                               self.wfDir.id==self.wfDirAlias.wf_id).\
                                                          filter(self.wfDirAlias.user==self.project.activeUser.name).\
                                                          filter(self.wfDir.waveclient == self.client.name).all()
        self.updateWfListCtrl()
        sizer.Fit(self)



    def getGridColumns(self):
        ''' Create the column fields used by the list control.

        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('origDir', 'original directory', 'readonly'))
        tableField.append(('alias', 'alias', 'editable'))
        tableField.append(('description', 'description', 'editable'))
        tableField.append(('file_ext', 'data file extension', 'editable'))
        tableField.append(('first_import', 'first import', 'readonly'))
        tableField.append(('last_scan', 'last scan', 'readonly'))
        return tableField


    def onDirectorySelected(self, evt):
        ''' The item selected callback of the directory list.
        '''
        self.selected_waveform_dir = self.wfDirList[evt.GetIndex()]


    def initPreferenceValues(self):
        ''' Set the preference values to default values.
        '''
        self.wfd_pref_manager.set_value('waveform_dir',
                                        '')
        self.wfd_pref_manager.set_value('waveform_dir_alias',
                                        '')
        self.wfd_pref_manager.set_value('description',
                                        '')
        self.wfd_pref_manager.set_value('file_ext',
                                        '*.msd, *.mseed')


    def setPreferenceValues(self):
        ''' Set the preference values using the selected waveform directory.
        '''
        self.wfd_pref_manager.set_value('waveform_dir',
                                        self.selected_waveform_dir.directory)
        self.wfd_pref_manager.set_value('waveform_dir_alias',
                                        self.selected_waveform_dir.aliases[0].alias)
        self.wfd_pref_manager.set_value('description',
                                        self.selected_waveform_dir.description)
        self.wfd_pref_manager.set_value('file_ext',
                                        self.selected_waveform_dir.file_ext)


    def onEditDirectory(self, event):
        ''' Edit the waveform directory values.
        '''
        self.setPreferenceValues()
        self.wfd_pref_manager.get_item('waveform_dir')[0].visible = False
        self.wfd_pref_manager.get_item('waveform_dir_alias')[0].visible = True

        dlg = psy_lb.ListbookPrefDialog(preferences = self.wfd_pref_manager,
                                         title = 'edit waveform directory')
        if dlg.ShowModal() == wx.ID_OK:
            self.selected_waveform_dir.description = self.wfd_pref_manager.get_value('description')
            self.selected_waveform_dir.file_ext = self.wfd_pref_manager.get_value('file_ext')
            self.selected_waveform_dir.aliases[0].alias = self.wfd_pref_manager.get_value('waveform_dir_alias')
            self.updateWfListCtrl()

        dlg.Destroy()



    def onAddDirectory(self, event):
        ''' The add directory callback.

        Show a directory browse dialog.
        If a directory has been selected, call to insert the directory
        into the database.
        '''
        self.initPreferenceValues()
        self.wfd_pref_manager.get_item('waveform_dir')[0].visible = True
        self.wfd_pref_manager.get_item('waveform_dir_alias')[0].visible = False
        dlg = psy_lb.ListbookPrefDialog(preferences = self.wfd_pref_manager,
                                         title = 'edit waveform directory')
        if dlg.ShowModal() == wx.ID_OK:
            newWfDir = self.wfDir(self.client.name,
                                  self.wfd_pref_manager.get_value('waveform_dir'),
                                  self.wfd_pref_manager.get_value('description'),
                                  self.wfd_pref_manager.get_value('file_ext'),
                                  '',
                                  '')
            newAlias = self.wfDirAlias(self.project.activeUser.name,
                                       self.wfd_pref_manager.get_value('waveform_dir'))
            newWfDir.aliases.append(newAlias)

            self.dbSession.add(newWfDir)

            self.wfDirList.append(newWfDir)
            self.updateWfListCtrl()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()


    def create_wfd_preferences(self):
        ''' Create the preference items used to edit a waveform directory.
        '''
        page = self.wfd_pref_manager.add_page('preferences')
        group = page.add_group('preferences')

        item = psy_pm.DirBrowsePrefItem(name = 'waveform_dir',
                                        label = 'waveform directory',
                                        value = '',
                                        tool_tip = 'The waveform directory.')
        group.add_item(item)

        item = psy_pm.DirBrowsePrefItem(name = 'waveform_dir_alias',
                                        label = 'waveform directory alias',
                                        value = '',
                                        tool_tip = 'The waveform directory alias.')
        group.add_item(item)

        item = psy_pm.TextEditPrefItem(name = 'description',
                                       label = 'description',
                                       value = '',
                                       tool_tip = 'The description of the waveform directory.')
        group.add_item(item)

        item = psy_pm.TextEditPrefItem(name = 'file_ext',
                                       label = 'file extension',
                                       value = '',
                                       tool_tip = 'The file extension search pattern used to scan the directory for data files. A comma separated string (e.g. *.msd, *.mseed).')
        group.add_item(item)



    def updateWfListCtrl(self):
        ''' Initialize the waveformDir table with values.

        '''
        self.wfListCtrl.DeleteAllItems()
        for k, curDir in enumerate(self.wfDirList):
            if not curDir.first_import:
                first_import = 'not yet imported'
            else:
                first_import = curDir.first_import

            if not curDir.last_scan:
                last_scan = 'not yet imported'
            else:
                last_scan = curDir.last_scan

            self.wfListCtrl.InsertItem(k, str(curDir.id))
            self.wfListCtrl.SetStringItem(k, 1, curDir.directory)
            self.wfListCtrl.SetStringItem(k, 2, curDir.aliases[0].alias)
            self.wfListCtrl.SetStringItem(k, 3, curDir.description)
            self.wfListCtrl.SetStringItem(k, 4, curDir.file_ext)
            self.wfListCtrl.SetStringItem(k, 5, first_import)
            self.wfListCtrl.SetStringItem(k, 6, last_scan)

        self.wfListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        #self.wfListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        #self.wfListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        #self.wfListCtrl.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        self.wfListCtrl.SetColumnWidth(4, wx.LIST_AUTOSIZE)


    def onRemoveDirectory(self, event):
        ''' The remove directory callback.
        '''
        selectedRow = self.wfListCtrl.GetFocusedItem()
        #item2Delete =  self.wfListCtrl.GetItem(selectedRow, 0)
        obj2Delete = self.wfDirList.pop(selectedRow)
        try:
            self.dbSession.delete(obj2Delete)
        except sqlalchemy.exc.InvalidRequestError:
            self.dbSession.expunge(obj2Delete)

        self.wfListCtrl.DeleteItem(selectedRow)

    def onOk(self):
        ''' Apply the changes.

        This method should be called by the dialog holding the options when the user clicks 
        the ok button.
        '''
        self.client.name = self.name_edit.GetValue()
        self.client.description = self.description_edit.GetValue()
        self.logger.debug(self.client.name)

        try:
            self.dbSession.commit()
        finally:
            self.dbSession.close()
        # Reload the project's waveform directory list to make sure, that it's 
        # consistent with the database.
        self.client.loadWaveformDirList()

        return self.client


    def onCancel(self):
        ''' Called when the dialog cancel button is clicked.
        '''
        self.dbSession.close()


class SeedlinkWaveClientOptions(wx.Panel):

    def __init__(self, parent=None, client=None, project=None, size=(-1, -1)):
        ''' Initialize the instance.
        '''
        wx.Panel.__init__(self, parent, wx.ID_ANY, size = size)

        # The logger.
        self.logger = psysmon.get_logger(self)

        # The waveclient holding the options.
        self.client = client


        self.nameLabel = wx.StaticText(self, -1, "name:")
        self.nameEdit = wx.TextCtrl(self, -1, self.client.name, size=(100, -1))
        self.hostLabel = wx.StaticText(self, -1, "host:")
        self.hostEdit = wx.TextCtrl(self, -1, self.client.host, size=(100, -1))
        self.portLabel = wx.StaticText(self, -1, "port:")
        self.portEdit = wx.TextCtrl(self, -1, str(self.client.port),
                                    size=(100, -1))

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)


        sizer.Add(self.nameLabel, pos=(0, 0),
                  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border=5)
        sizer.Add(self.nameEdit, pos=(0, 1), flag=wx.EXPAND | wx.ALL,
                  border=5)
        sizer.Add(self.hostLabel, pos=(1, 0),
                  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border=5)
        sizer.Add(self.hostEdit, pos=(1, 1),
                  flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(self.portLabel, pos=(2, 0),
                  flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border=5)
        sizer.Add(self.portEdit, pos=(2, 1),
                  flag=wx.EXPAND | wx.ALL,
                  border=5)

        sizer.AddGrowableCol(1)

        self.SetSizerAndFit(sizer)

        self.project = project


    def onOk(self):
        ''' Apply the changes.

        This method should be called by the dialog holding the options when the user clicks 
        the ok button.
        '''
        self.client.name = self.nameEdit.GetValue()
        self.client.host = self.hostEdit.GetValue()
        self.client.port = int(self.portEdit.GetValue())
        self.logger.debug(self.client.name)
        return self.client


    def onCancel(self):
        ''' Called when the dialog cancel button is clicked.
        '''
        pass


class EarthwormWaveClientOptions(wx.Panel):

    def __init__(self, parent=None, client=None, project=None, size=(-1, -1)):
        ''' Initialize the instance.
        '''
        wx.Panel.__init__(self, parent, wx.ID_ANY, size = size)

        # The logger.
        self.logger = psysmon.get_logger(self)

        # The waveclient holding the options.
        self.client = client


        self.nameLabel = wx.StaticText(self, -1, "name:")
        self.nameEdit = wx.TextCtrl(self, -1, self.client.name, size=(100, -1))
        self.hostLabel = wx.StaticText(self, -1, "host:")
        self.hostEdit = wx.TextCtrl(self, -1, self.client.host, size=(100, -1))
        self.portLabel = wx.StaticText(self, -1, "port:")
        self.portEdit = wx.TextCtrl(self, -1, str(self.client.port),
                                    size=(100, -1))

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)


        sizer.Add(self.nameLabel, pos=(0, 0),
                  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border = 5)
        sizer.Add(self.nameEdit, pos=(0, 1),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)
        sizer.Add(self.hostLabel, pos=(1, 0),
                  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border = 5)
        sizer.Add(self.hostEdit, pos=(1, 1),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)
        sizer.Add(self.portLabel, pos=(2, 0),
                  flag = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL,
                  border = 5)
        sizer.Add(self.portEdit, pos=(2, 1),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)

        sizer.AddGrowableCol(1)

        self.SetSizerAndFit(sizer)

        self.project = project


    def onOk(self):
        ''' Apply the changes.

        This method should be called by the dialog holding the options when the user clicks 
        the ok button.
        '''
        self.client.name = self.nameEdit.GetValue()
        self.client.host = self.hostEdit.GetValue()
        self.client.port = int(self.portEdit.GetValue())
        self.logger.debug(self.client.name)
        return self.client


    def onCancel(self):
        ''' Called when the dialog cancel button is clicked.
        '''
        pass
