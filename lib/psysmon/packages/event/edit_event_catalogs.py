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

from builtins import str
import os
import fnmatch
import logging
from psysmon.gui.context_menu import psyContextMenu
from psysmon.core.packageNodes import CollectionNode
from psysmon.core.preferences_manager import CustomPrefItem
import wx
import wx.aui
from obspy.core import read, Trace, Stream
import obspy.core.utcdatetime as op_utcdatetime
from operator import itemgetter

import psysmon.gui.validator as psy_val
import psysmon.gui.main.app as psy_app


## Documentation for class importWaveform
# 
# 
class EditEventCatalogs(CollectionNode):

    name = 'edit event catalogs'
    mode = 'execute only'
    category = 'Event'
    tags = ['stable',]

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

    def edit(self):
        pass

    def execute(self, prevNodeOutput={}):
        ''' Execute the node.
        '''
        app = psy_app.PsysmonApp()()
        dlg = EditEventCatalogsDlg(collection_node = self,
                                   project = self.project)
        dlg.Show()
        app.MainLoop()



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

        self.db_session = self.project.getDbSession()

        self.dialog_fields = (("name:", "name", wx.TE_RIGHT),
                             ("description:", "description", wx.TE_RIGHT))

        self.catalogs = []

        self.load_catalogs()

        self.init_ui()
        self.SetMinSize(self.GetBestSize())

        self.update_list_ctrl()


    def __del__(self):
        self.db_session.close()


    def init_ui(self):
        # Use standard button IDs.
        close_button = wx.Button(self, wx.ID_CLOSE)
        close_button.SetDefault()

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)
        grid_button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the grid editing buttons.
        add_catalog_button = wx.Button(self, wx.ID_ANY, 'add catalog')
        edit_catalog_button = wx.Button(self, wx.ID_ANY, 'edit catalog')
        delete_catalog_button = wx.Button(self, wx.ID_ANY, 'delete catalog')

        # Fill the grid button sizer.
        grid_button_sizer.Add(add_catalog_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(edit_catalog_button, 0, wx.EXPAND|wx.ALL)
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

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_catalog_selected, self.list_ctrl)

        self.Bind(wx.EVT_BUTTON, self.on_close, close_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_catalog, add_catalog_button)
        self.Bind(wx.EVT_BUTTON, self.on_edit_catalog, edit_catalog_button)
        self.Bind(wx.EVT_BUTTON, self.on_delete_catalog, delete_catalog_button)

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
        cat_table = self.project.dbTables['event_catalog'];
        query = self.db_session.query(cat_table.id,
                                 cat_table.name,
                                 cat_table.description,
                                 cat_table.agency_uri,
                                 cat_table.author_uri,
                                 cat_table.creation_time)
        self.catalogs = query.all()



    def on_catalog_selected(self, event):
        pass


    def on_close(self, event):
        self.db_session.close()
        self.Destroy()


    def on_add_catalog(self, event):
        dlg = EditDlg(parent = self,
                      dialog_fields = self.dialog_fields)
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.add_catalog(**dlg.data)
        dlg.Destroy()


    def on_edit_catalog(self, event):
        ''' Handle the edit catalog button click.
        '''
        if self.list_ctrl.GetSelectedItemCount() > 0:
            selected_row = self.list_ctrl.GetFirstSelected()
            selected_id = int(self.list_ctrl.GetItem(selected_row,0).GetText())
            selected_catalog = [x for x in self.catalogs if x.id == selected_id]
            if selected_catalog:
                selected_catalog = selected_catalog[0]
                data = {}
                data['name'] = selected_catalog.name
                data['description'] = selected_catalog.description
                dlg = EditDlg(parent = self,
                              dialog_fields = self.dialog_fields,
                              data = data)
                val = dlg.ShowModal()
                if val == wx.ID_OK:
                    self.change_catalog(catalog = selected_catalog, **dlg.data)

                dlg.Destroy()


    def on_delete_catalog(self, event):
        ''' Handle the delete catalog button click.
        '''
        if self.list_ctrl.GetSelectedItemCount() > 0:
            selected_row = self.list_ctrl.GetFirstSelected()
            selected_id = int(self.list_ctrl.GetItem(selected_row,0).GetText())
            selected_catalog = [x for x in self.catalogs if x.id == selected_id]
            if selected_catalog:
                selected_catalog = selected_catalog[0]
                dlg = wx.MessageDialog(self,
                                       "Do you really wan't to delete the catalog %s from the database?" % selected_catalog.name,
                                        'Confirm delete',
                                        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                val = dlg.ShowModal()
                if val == wx.ID_YES:
                    self.delete_catalog(selected_catalog)
                    self.update_list_ctrl()
                dlg.Destroy()


    def add_catalog(self, name, description):
        ''' Add a catalog to the database.

        '''
        cat_table = self.project.dbTables['event_catalog'];
        cat_orm = cat_table(name = name,
                            description = description,
                            agency_uri = self.project.activeUser.agency_uri,
                            author_uri = self.project.activeUser.author_uri,
                            creation_time = op_utcdatetime.UTCDateTime().isoformat())
        self.db_session.add(cat_orm)
        self.db_session.commit()
        self.catalogs.append(cat_orm)
        self.update_list_ctrl()


    def change_catalog(self, catalog, name, description):
        ''' Change the values of a catalog.
        '''
        catalog.name = name
        catalog.description = description
        self.db_session.commit()
        self.update_list_ctrl()


    def delete_catalog(self, catalog):
        ''' Delete a catalog.
        '''
        self.db_session.delete(catalog)
        self.db_session.commit()
        self.catalogs.remove(catalog)




class EditDlg(wx.Dialog):

    def __init__(self, dialog_fields, data = None, parent=None, size=(300, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new event catalog.", size=size)


        # Use standard button IDs.
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        self.dialog_fields = dialog_fields

        if data is None:
            self.data = {}
        else:
            self.data = data

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
        self.edit['name'].SetValidator(psy_val.NotEmptyValidator())         # Not empty.

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

            if curKey in iter(self.data.keys()):
                if not isinstance(self.data[curKey], (str, str)):
                    value_string = str(self.data[curKey], encoding = 'utf8')
                elif isinstance(self.data[curKey], str):
                    value_string = self.data[curKey].decode('utf8')
                else:
                    value_string = self.data[curKey]

                self.edit[curKey].SetValue(value_string)

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer
