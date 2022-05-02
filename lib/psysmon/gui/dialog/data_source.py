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
import operator as op

import wx

import psysmon.artwork.icons as psy_icon
import psysmon.core.waveclient as psy_wc
import psysmon.gui.dialog.waveclient_options as psy_wcopt


class DataSourceDlg(wx.Dialog):
    ''' The EditWaveformDirDlg class.

    This class creates a dialog used to edit the pSysmon data sources.

    Attributes
    ----------
    psyBase : :class:`~psysmon.core.Base`
        The pSysmon base instance.
    '''
    def __init__(self, psyBase, parent=None, size=(300, 100)):
        ''' Initialize the instance.

        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Edit the waveclients",
                           style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           size = size)

        self.psyBase = psyBase

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Create the grid editing buttons.
        addButton = wx.Button(self, wx.ID_ANY, "add")
        editButton = wx.Button(self, wx.ID_ANY, "edit")
        removeButton = wx.Button(self, wx.ID_ANY, "remove")
        defaultButton = wx.Button(self, wx.ID_ANY, "as default")

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)
        gridButtonSizer = wx.BoxSizer(wx.VERTICAL)

        # Fill the grid button sizer
        gridButtonSizer.Add(addButton, 0, wx.EXPAND | wx.ALL)
        gridButtonSizer.Add(editButton, 0, wx.EXPAND | wx.ALL)
        gridButtonSizer.Add(removeButton, 0, wx.EXPAND | wx.ALL)
        gridButtonSizer.Add(defaultButton, 0, wx.EXPAND | wx.ALL)

        # Create the image list for the list control.
        self.il = wx.ImageList(16, 16)
        icon_bmp = psy_icon.iconsBlack16.star_icon_16.GetBitmap()
        self.iconDefault = self.il.Add(icon_bmp)

        # Create the list control
        fields = self.getGridColumns()
        self.wcListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.wcListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        for k, (name, label, attr) in enumerate(fields):
            self.wcListCtrl.InsertColumn(k, label)

        sizer.Add(self.wcListCtrl, pos = (0, 0),
                  flag=wx.EXPAND | wx.ALL,
                  border=5)
        sizer.Add(gridButtonSizer, pos = (0, 1),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos = (1, 0), span = (1, 2),
                  flag = wx.ALIGN_RIGHT | wx.ALL,
                  border = 5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizer(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onAdd, addButton)
        self.Bind(wx.EVT_BUTTON, self.onEdit, editButton)
        self.Bind(wx.EVT_BUTTON, self.onRemove, removeButton)
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onSetAsDefault, defaultButton)

        self.updateWcListCtrl()
        sizer.Fit(self)
        self.SetMinSize(self.GetBestSize())


    def onEdit(self, event):
        ''' The edit button callback.

        '''
        selectedRow = self.wcListCtrl.GetFocusedItem()
        selectedItem = self.wcListCtrl.GetItemText(selectedRow)
        client2Edit = self.psyBase.project.waveclient[selectedItem]
        dlg = EditWaveclientDlg(psyBase = self.psyBase,
                                client = client2Edit)
        dlg.ShowModal()
        dlg.Destroy()

        # Check if the name of the waveclient has changed.
        if client2Edit.name != selectedItem:
            self.psyBase.project.handleWaveclientNameChange(selectedItem,
                                                            client2Edit)

        self.updateWcListCtrl()



    def onAdd(self, event):
        ''' The add directory callback.

        Show a directory browse dialog.
        If a directory has been selected, call to insert the directory 
        into the database.
        '''
        dlg = AddDataSourceDlg(psyBase=self.psyBase)
        dlg.ShowModal()
        #dlg.Destroy()
        self.updateWcListCtrl()


    def onSetAsDefault(self, event):
        ''' The remove directory callback.
        '''
        selectedRow = self.wcListCtrl.GetFocusedItem()
        selectedItem = self.wcListCtrl.GetItemText(selectedRow)
        self.psyBase.project.defaultWaveclient = selectedItem
        self.updateWcListCtrl()



    def onRemove(self, event):
        ''' The remove directory callback.
        '''
        selectedRow = self.wcListCtrl.GetFocusedItem()
        selectedItem = self.wcListCtrl.GetItemText(selectedRow)

        if selectedItem != 'db client':
            self.psyBase.project.removeWaveClient(selectedItem)
            self.updateWcListCtrl()
        else:
            msg = "The db client can't be deleted."
            self.logger.error(msg)


    def updateWcListCtrl(self):
        ''' Initialize the waveformDir table with values.

        '''
        self.wcListCtrl.DeleteAllItems()
        client_names = sorted(self.psyBase.project.waveclient.keys())
        for k, name in enumerate(client_names):
            client = self.psyBase.project.waveclient[name]
            if name == self.psyBase.project.defaultWaveclient:
                self.wcListCtrl.InsertImageStringItem(k, client.name, self.iconDefault)
            else:
                self.wcListCtrl.InsertStringItem(k, client.name)
            self.wcListCtrl.SetStringItem(k, 1, client.mode)
            self.wcListCtrl.SetStringItem(k, 2, client.description)
            #self.wcListCtrl.SetStringItem(k, 2, curDir.aliases[0].alias)

        self.wcListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.wcListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.wcListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)


    def addItem2WfListCtrl(self, item):
        ''' Add a waveform directory to the list control.

        Parameters
        ----------
        item : Object
            The waveformDir mapper instance to be added to the list control.
        '''
        k = self.wfListCtrl.GetItemCount()
        self.wfListCtrl.InsertStringItem(k, str(item.id))
        self.wfListCtrl.SetStringItem(k, 1, item.directory)
        self.wfListCtrl.SetStringItem(k, 2, item.aliases[0].alias)
        self.wfListCtrl.SetStringItem(k, 3, item.description)
        self.wfListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.wfListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.wfListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)



    def getGridColumns(self):
        ''' Create the column fields used by the list control.

        '''
        tableField = []
        tableField.append(('name', 'name', 'readonly'))
        tableField.append(('type', 'type', 'readonly'))
        tableField.append(('description', 'description', 'readonly'))
        return tableField



    def onOk(self, event):
        ''' The ok button callback.

        Parameters
        ----------
        event :
            The wxPython event passed to the callback.

        Commit the database changes and update the project's waveform directory 
        list.
        '''
        self.Destroy()


class EditWaveclientDlg(wx.Dialog):

    def __init__(self, parent=None, size=(-1, -1),
                 psyBase = None, client = None):
        ''' Initialize the instance.

        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY,
                           "Edit the waveclient options",
                           style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.psyBase = psyBase

        self.clientOptionPanels = self.getClientOptionsPanels()

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        okButton.SetDefault()

        # Create the client's options panel.
        (curLabel, curPanel) = self.clientOptionPanels[client.mode]
        self.optionsPanel = curPanel(parent = self, client=client,
                                     project = self.psyBase.project)

        # The main dialog sizer.
        sizer = wx.GridBagSizer(5, 5)

        sizer.Add(self.optionsPanel, pos = (0, 0),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)

        # The button sizer.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos = (1, 0),
                  flag = wx.ALIGN_RIGHT | wx.ALL,
                  border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelButton)

        sizer.Fit(self)


    def getClientOptionsPanels(self):
        clientModes = {}
        clientModes['EarthwormWaveClient'] = ('Earthworm Waveserver',
                                              psy_wcopt.EarthwormWaveClientOptions)
        clientModes['PsysmonDbWaveClient'] = ('pSysmon database',
                                              psy_wcopt.PsysmonDbWaveClientOptions)
        clientModes['SeedlinkWaveClient'] = ('Seedlink Server',
                                             psy_wcopt.SeedlinkWaveClientOptions)
        return clientModes


    def onOk(self, event):
        ''' The ok button callback.

        Parameters
        ----------
        event :
            The wxPython event passed to the callback.

        Commit the database changes and update the project's waveform directory 
        list.
        '''
        # Call the onOk method of the options class.
        self.optionsPanel.onOk()
        self.EndModal(wx.ID_OK)


    def onCancel(self, event):
        ''' The cancel button callback.

        Parameters
        ----------
        event :
            The wxPython event passed to the callback.

        Commit the database changes and update the project's waveform directory 
        list.
        '''
        # Call the onOk method of the options class.
        self.optionsPanel.onCancel()
        self.EndModal(wx.ID_CANCEL)


class AddDataSourceDlg(wx.Dialog):

    def __init__(self, parent=None, size=(-1, -1), psyBase=None):
        ''' The constructor.

        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Add a new waveclient",
                           style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.psyBase = psyBase

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        okButton.SetDefault()

        # Create the choicebook.
        self.modeChoiceBook = wx.Choicebook(parent = self, id = wx.ID_ANY)

        for curLabel, curClass in self.clientModes().values():
            if curClass == psy_wc.PsysmonDbWaveClient:
                panel = psy_wcopt.PsysmonDbWaveClientOptions(parent = self.modeChoiceBook,
                                                             project = self.psyBase.project,
                                                             client = curClass(name = 'database client'))
            elif curClass == psy_wc.EarthwormWaveClient:
                panel = psy_wcopt.EarthwormWaveClientOptions(parent = self.modeChoiceBook,
                                                             project = self.psyBase.project,
                                                             client = curClass(name='earthworm client'))
            elif curClass == psy_wc.SeedlinkWaveClient:
                panel = psy_wcopt.SeedlinkWaveClientOptions(parent = self.modeChoiceBook,
                                                            project = self.psyBase.project,
                                                            client = curClass(name='seedlink client'))

            panel.SetMinSize((200, 200))
            self.modeChoiceBook.AddPage(panel, curLabel)


        # The main dialog sizer.
        sizer = wx.GridBagSizer(5, 5)

        # Add the choicebook.
        sizer.Add(self.modeChoiceBook, pos=(0, 0),
                  flag = wx.EXPAND | wx.ALL,
                  border = 5)

        # The button sizer.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1, 0),
                  flag = wx.ALIGN_RIGHT | wx.ALL,
                  border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def clientModes(self):
        clientModes = {}
        clientModes['earthworm'] = ('Earthworm Waveserver',
                                    psy_wc.EarthwormWaveClient)
        clientModes['psysmonDb'] = ('pSysmon database',
                                    psy_wc.PsysmonDbWaveClient)
        clientModes['seedlink'] = ('Seedlink Server',
                                   psy_wc.SeedlinkWaveClient)
        return clientModes


    def onOk(self, event):
        client = self.modeChoiceBook.GetCurrentPage().onOk()
        self.psyBase.project.addWaveClient(client)
        self.Destroy()





class EditScnlDataSourcesDlg(wx.Dialog):
    ''' The EditWaveformDirDlg class.

    This class creates a dialog used to edit the pSysmon waveform directories.

    Attributes
    ----------
    psyBase : :class:`~psysmon.core.Base`
        The pSysmon base instance.
    '''
    def __init__(self, psyBase, parent=None, size=(-1, -1)):
        ''' The constructor.

        '''
        wx.Dialog.__init__(self,
                           parent,
                           wx.ID_ANY,
                           "Edit the waveclients",
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,
                           size=size)

        self.psyBase = psyBase

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Get the inventory from the database.
        inventoryDbController = InventoryDatabaseController(self.psyBase.project)
        self.inventory = inventoryDbController.load()

        # Create the scnl-datasource list.
        self.scnl = []
        for curNetwork in self.inventory.networks.values():
            for curStation in curNetwork.stations.values():
                self.scnl.extend(curStation.getScnl())

        # Sort the scnl list.
        self.scnl = sorted(self.scnl, key = op.itemgetter(0, 1, 2, 3))

        for curScnl in self.scnl:
            if curScnl not in iter(self.psyBase.project.scnlDataSources.keys()):
                self.psyBase.project.scnlDataSources[curScnl] = self.psyBase.project.defaultWaveclient


        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)

        # Create the grid.
        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)
        columns = self.getGridColumns()
        self.dataSourceGrid = wx.grid.Grid(self, size=(-1, 100))
        self.dataSourceGrid.CreateGrid(len(self.scnl), len(columns))

        for k, (name, label, attr) in enumerate(columns):
            self.dataSourceGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.dataSourceGrid.SetColAttr(k, roAttr)

        self.dataSourceGrid.AutoSizeColumns()
        
        # Fill the table values
        for k, curScnl in enumerate(self.scnl):
            self.dataSourceGrid.SetCellValue(k, 0, "-".join(x for x in curScnl))
            self.dataSourceGrid.SetCellValue(k, 1, self.psyBase.project.scnlDataSources[curScnl])
        
        sizer.Add(self.dataSourceGrid, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)

        # Create a button sizer and add the ok and cancel buttons.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def getGridColumns(self):
        ''' Create the column fields used by the list control.

        '''
        tableField = []
        tableField.append(('scnl', 'SCNL', 'readonly'))
        tableField.append(('dataSource', 'data source', 'editable'))
        return tableField


    def onOk(self, event):
        ''' The ok button callback.

        Parameters
        ----------
        event :
            The wxPython event passed to the callback.

        Commit the database changes and update the project's waveform directory 
        list.
        '''
        self.Destroy()
