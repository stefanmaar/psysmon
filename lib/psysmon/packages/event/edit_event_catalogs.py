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
The importWaveform module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classes of the importWaveform dialog window.
'''

import os
import fnmatch
import logging
from psysmon.core.gui import psyContextMenu
from psysmon.core.packageNodes import CollectionNode
from psysmon.core.preferences_manager import CustomPrefItem
import wx
import wx.aui
from obspy.core import read, Trace, Stream
import obspy.core.utcdatetime as op_utcdatetime
from operator import itemgetter



## Documentation for class importWaveform
# 
# 
class EditEventCatalogs(CollectionNode):

    name = 'edit event catalogs'
    mode = 'standalone'
    category = 'Event'
    tags = ['stable',]

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

    def edit(self):
        pass

    def execute(self, prevNodeOutput={}):

        dlg = EditEventCatalogsDlg(collection_node = self,
                                   project = self.project)
        dlg.Show()
#        dbData = []
#        for curFile in self.pref_manager.get_value('input_files'):
#            print("Processing file " + curFile[1])
#            if curFile[0] == 'not checked':
#                format = None
#            else:
#                format = curFile[0]
#            stream = read(pathname_or_url=curFile[1],
#                             format = format,
#                             headonly=True)
#
#            print stream
#
#            for curTrace in stream.traces:
#                print "Importing trace " + curTrace.getId()
#                cur_data = self.getDbData(curFile[1], format, curTrace)
#                if cur_data is not None:
#                    dbData.append(cur_data)
#
#        self.logger.debug('dbData: %s', dbData)
#
#        if len(dbData) > 0:
#            dbSession = self.project.getDbSession()
#            dbSession.add_all(dbData)
#            dbSession.commit()
#            dbSession.close()



class EditEventCatalogsDlg(wx.Frame):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collection_node, project, parent = None, id = wx.ID_ANY, title='edit event catalogs',
                 size=(640,480)):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY,
                           title=title,
                           size=size,
                           style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)

        # Create the logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.collection_node = collection_node

        self.project = project

        self.dialog_fields = (("name:", "name", wx.TE_RIGHT),
                             ("description:", "description", wx.TE_RIGHT))

        self.catalogs = []

        self.load_catalogs()

        self.init_ui()
        self.SetMinSize(self.GetBestSize())

        self.update_list_ctrl()


    def init_ui(self):
        # Use standard button IDs.
        close_button = wx.Button(self, wx.ID_CLOSE)
        close_button.SetDefault()

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)
        grid_button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the grid editing buttons.
        add_catalog_button = wx.Button(self, wx.ID_ANY, 'add catalog')
        delete_catalog_button = wx.Button(self, wx.ID_ANY, 'delete catalog')

        # Fill the grid button sizer.
        grid_button_sizer.Add(add_catalog_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(delete_catalog_button, 0, wx.EXPAND|wx.ALL)


        # Create the icons for column sorting.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))
        # Create the list control.
        self.list_ctrl = wx.ListCtrl(parent = self,
                                     id = wx.ID_ANY,
                                     style=wx.LC_REPORT
                                     | wx.BORDER_NONE
                                     | wx.LC_SINGLE_SEL
                                     | wx.LC_SORT_ASCENDING
                                    )
        self.list_ctrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        # Set the column labels of the list control.
        column_labels = ['id', 'name', 'description', 'agency_uri', 'author_uri', 'creation_time']
        for k, cur_label in enumerate(column_labels):
            self.list_ctrl.InsertColumn(k, cur_label)

        # Add the elements to the sizer.
        sizer.Add(self.list_ctrl, pos =(0,0), flag=wx.EXPAND|wx.ALL, border = 5)
        sizer.Add(grid_button_sizer, pos=(0,1), flag = wx.EXPAND|wx.ALL, border = 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(close_button)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), span = (1,2), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.on_close, close_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_catalog, add_catalog_button)

        #self.file_grid.doResize()


    def update_list_ctrl(self):
        ''' Rebuild the entries of the list control.
        '''
        index = 0
        self.list_ctrl.DeleteAllItems()

        for cur_catalog in self.catalogs:
            self.list_ctrl.InsertStringItem(index, str(cur_catalog.id))
            self.list_ctrl.SetStringItem(index, 1, cur_catalog.name)
            self.list_ctrl.SetStringItem(index, 2, cur_catalog.description)
            self.list_ctrl.SetStringItem(index, 3, cur_catalog.agency_uri)
            self.list_ctrl.SetStringItem(index, 4, cur_catalog.author_uri)
            self.list_ctrl.SetStringItem(index, 5, cur_catalog.creation_time)

            index += 1



    def load_catalogs(self):
        ''' Load the event catalogs from the database.

        '''
        db_session = self.project.getDbSession()
        try:
            cat_table = self.project.dbTables['event_catalog'];
            query = db_session.query(cat_table.id,
                                     cat_table.name,
                                     cat_table.description,
                                     cat_table.agency_uri,
                                     cat_table.author_uri,
                                     cat_table.creation_time)
            self.catalogs = query.all()

        finally:
            db_session.close()


    def on_close(self, event):
        self.Destroy()


    def on_add_catalog(self, event):
        dlg = EditDlg(parent = self,
                      dialog_fields = self.dialog_fields)
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.add_catalog(**dlg.data)
        dlg.Destroy()


    def add_catalog(self, name, description):
        ''' Add a catalog to the database.

        '''
        db_session = self.project.getDbSession()
        try:
            cat_table = self.project.dbTables['event_catalog'];
            cat_orm = cat_table(name = name,
                                description = description,
                                agency_uri = self.project.activeUser.agency_uri,
                                author_uri = self.project.activeUser.author_uri,
                                creation_time = op_utcdatetime.UTCDateTime().isoformat())
            db_session.add(cat_orm)
            db_session.commit()
            self.catalogs.append(cat_orm)
            self.update_list_ctrl()
        finally:
            db_session.close()


class EditDlg(wx.Dialog):

    def __init__(self, dialog_fields, parent=None, size=(300, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new event catalog.", size=size)


        # Use standard button IDs.
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)


        self.dialog_fields = dialog_fields

        self.data = {}

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {};
        self.edit = {};

        sizer.Add(self.create_dialog_fields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(ok_button)
        btnSizer.AddButton(cancel_button)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Add the validators.
        self.edit['name'].SetValidator(NotEmptyValidator())         # Not empty.

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)


    def on_ok(self, event):
        is_valid = self.Validate()

        if(is_valid):
            for _, cur_key, _ in self.dialog_fields:
                self.data[cur_key] = self.edit[cur_key].GetValue()

            self.EndModal(wx.ID_OK)


    def create_dialog_fields(self):
        fgSizer = wx.FlexGridSizer(len(self.dialog_fields), 2, 5, 5)

        for curLabel, curKey, curStyle in self.dialog_fields:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(200, -1), 
                                            style=curStyle)

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer


class NotEmptyValidator(wx.PyValidator):
    ## The constructor
    #
    # @param self The object pointer.
    def __init__(self):
        wx.PyValidator.__init__(self)


    ## The default clone method.    
    def Clone(self):
        return NotEmptyValidator()


    ## The method run when validating the field.
    #
    # This method checks if the control has a value. If not, it returns False.
    # @param self The object pointer.
    def Validate(self, win):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()

        if len(value) == 0:
            wx.MessageBox("This field must contain some text!", "Error")
            ctrl.SetBackgroundColour("pink")
            ctrl.SetFocus()
            ctrl.Refresh()
            return False
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
            return True

    ## The method called when entering the dialog.      
    def TransferToWindow(self):
        return True

    ## The method called when leaving the dialog.  
    def TransferFromWindow(self):
        return True
