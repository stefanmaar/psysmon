# -*- coding: utf-8 -*-
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
''' Import Bulletins into the pSysmon database.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import psysmon
from psysmon.core.packageNodes import CollectionNode
from psysmon.core.preferences_manager import CustomPrefItem
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.guiBricks as psy_guibricks

import os
import wx
import operator
import logging
import fnmatch
import bulletin

class ImportBulletin(CollectionNode):
    ''' Import earthquake bulletin files into the database.

    '''
    name = 'import earthquake bulletin'
    mode = 'editable'
    category = 'Event'
    tags = ['stable', 'event', 'autodrm', 'bulletin']

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)
        pref_item = psy_pm.SingleChoicePrefItem(name = 'bulletin_format',
                                                label = 'bulletin format',
                                                limit = ['IMS1.0', 'QuakeML'],
                                                value = 'IMS1.0')
        self.pref_manager.add_item(item = pref_item)
        pref_item = CustomPrefItem(name = 'input_files', value = [])
        self.pref_manager.add_item(item = pref_item)
        pref_item = CustomPrefItem(name = 'last_dir', value = [])
        self.pref_manager.add_item(item = pref_item)
        pref_item = CustomPrefItem(name = 'filter_pattern', value = ['*.txt',])
        self.pref_manager.add_item(item = pref_item)

    def edit(self):
        dlg = ImportBulletinEditDlg(self, self.project, None)
        dlg.Show()

    def execute(self, prevModuleOutput={}):
        ''' Import the selected bulletin files into the database.
        '''

        for cur_format, cur_file, cur_size in self.pref_manager.get_value('input_files'):
            self.logger.info('Importing file %s with format %s.', cur_file, cur_format)

            if cur_format == 'IMS1.0':
                parser = bulletin.ImsParser()
            else:
                parser = None

            if parser is not None:
                parser.parse(cur_file)
                catalog = parser.get_catalog()
                catalog.write_to_database(self.project)





class ImportBulletinEditDlg(wx.Frame):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collection_node, project,  parent, id=-1, title='import earthquake bulletin',
                 size=(640,480)):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY,
                           title=title,
                           size=size,
                           style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)

        # Create the logger.
        logger_prefix = psysmon.logConfig['package_prefix']
        logger_name = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

        self.collectionNode = collection_node
        self.project = project

        self.initUI()
        self.SetMinSize(self.GetBestSize())
        self.init_user_selections()



    def init_user_selections(self):
        filter_pattern = self.collectionNode.pref_manager.get_value('filter_pattern')
        self.filter_pattern_text.SetValue(','.join(filter_pattern))

        if self.collectionNode.pref_manager.get_value('input_files'):
            self.file_grid.GetTable().data = self.collectionNode.pref_manager.get_value('input_files')
            self.file_grid.GetTable().ResetView()

        self.bulletin_format_choice.SetStringSelection(self.collectionNode.pref_manager.get_value('bulletin_format'))


    def initUI(self):
        # Use standard button IDs.
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)
        grid_button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the grid editing buttons.
        add_files_button = wx.Button(self, wx.ID_ANY, 'add files')
        add_dir_button = wx.Button(self, wx.ID_ANY, 'add directory')
        self.filter_pattern_text =wx.TextCtrl(self, wx.ID_ANY, '*')
        #file_format_checkbox = wx.CheckBox(self, -1, "check file format")#, (65, 40), (150, 20), wx.NO_BORDER)
        #file_format_checkbox.SetValue(self.check_file_format)
        remove_selected_button = wx.Button(self, wx.ID_ANY, 'remove selected')
        clear_button = wx.Button(self, wx.ID_ANY, 'clear list')

        # Fill the grid button sizer.
        self.bulletin_format_choice = wx.Choice(self,
                                           wx.ID_ANY,
                                           choices = self.collectionNode.pref_manager.get_limit('bulletin_format'))
        grid_button_sizer.Add(self.bulletin_format_choice, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(add_files_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(add_dir_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(self.filter_pattern_text, 0, wx.EXPAND|wx.ALL)
        #grid_button_sizer.Add(file_format_checkbox, 0, wx.EXPAND|wx.BOTTOM, border = 20)
        grid_button_sizer.Add(remove_selected_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(clear_button, 0, wx.EXPAND|wx.ALL)

        self.file_grid = FileGrid(self, data = [])
        sizer.Add(self.file_grid, pos =(0,0), flag=wx.EXPAND|wx.ALL, border = 5)
        sizer.Add(grid_button_sizer, pos=(0,1), flag = wx.EXPAND|wx.ALL, border = 5)

        btn_sizer = wx.StdDialogButtonSizer()
        btn_sizer.AddButton(ok_button)
        btn_sizer.AddButton(cancel_button)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, pos=(1,0), span = (1,2), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_files, add_files_button)
        self.Bind(wx.EVT_BUTTON, self.on_add_directory, add_dir_button)
        self.Bind(wx.EVT_BUTTON, self.on_remove_selected, remove_selected_button)
        self.Bind(wx.EVT_BUTTON, self.on_clear_list, clear_button)
        #self.Bind(wx.EVT_CHECKBOX, self.onFileFormatCheck, file_format_checkbox)
        self.Bind(wx.EVT_TEXT, self.on_filter_pattern_text, self.filter_pattern_text)
        self.Bind(wx.EVT_CHOICE, self.on_bulletin_format_change, self.bulletin_format_choice)
        self.Bind(wx.EVT_SIZE, self.on_resize)



    def on_ok(self, event):
        self.collectionNode.pref_manager.set_value('input_files', self.file_grid.GetTable().data)
        self.Destroy()


    def on_cancel(self, event):
        self.Destroy()



    def on_add_files(self, event):

        wildcard_list = self.get_wildcard_data()

        wildcard = ""
        for curKey in sorted(wildcard_list.iterkeys()):
            wildcard = wildcard + wildcard_list[curKey] + '|'

        wildcard = wildcard + 'All files (*)|*'


        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=wildcard,
            style=wx.OPEN | wx.MULTIPLE
            )

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            # This returns a Python list of files that were selected.
            paths = dlg.GetPaths()
            matches = []

            for filename in paths:
                self.logger.info('Adding file %s', filename)
                fsize = os.path.getsize(filename);
                fsize = fsize/(1024.0*1024.0)           # Convert to MB
                bulletin_format = self.collectionNode.pref_manager.get_value('bulletin_format')
                matches.append((bulletin_format, filename, '%.2f' % fsize))

            matches = [x for x in matches if x not in self.file_grid.GetTable().data]
            self.file_grid.GetTable().data.extend(matches)
            self.file_grid.GetTable().ResetView()

        #self.file_grid.do_resize()

        dlg.Destroy()


    def on_add_directory(self, event):

        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE
                           | wx.DD_DIR_MUST_EXIST
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            matches = []
            k = 0
            filter_pattern = self.collectionNode.pref_manager.get_value('filter_pattern')
            for root, dirnames, filenames in os.walk(dlg.GetPath(), topdown = True):
                dirnames.sort()
                self.logger.info('Scanning directory: %s.', root)
                for cur_pattern in filter_pattern:
                    for filename in fnmatch.filter(filenames, cur_pattern):
                        self.logger.info('Adding file %s', os.path.join(root, filename))
                        fsize = os.path.getsize(os.path.join(root, filename));
                        fsize = fsize/(1024.0 * 1024.0)
                        bulletin_format = self.collectionNode.pref_manager.get_value('bulletin_format')
                        matches.append(bulletin_format, (os.path.join(root, filename), '%.2f' % fsize))
                        k += 1



            matches = [x for x in matches if x not in self.file_grid.GetTable().data]
            self.file_grid.GetTable().data.extend(matches)
            self.file_grid.GetTable().ResetView()

        #self.file_grid.do_resize()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()


    def on_remove_selected(self, event):
        self.logger.debug('Selected rows: %s', self.file_grid.GetSelectedRows())
        self.file_grid.removeRows(self.file_grid.GetSelectedRows())


    def on_clear_list(self, event):
        self.file_grid.clear()


    def on_filter_pattern_text(self, event):
        text = event.GetString()
        self.collectionNode.pref_manager.set_value('filter_pattern', text.split(','))


    def on_bulletin_format_change(self, event):
        self.collectionNode.pref_manager.set_value(name = 'bulletin_format',
                                                    value = self.bulletin_format_choice.GetStringSelection())

    def on_resize(self, event):
        self.file_grid.do_resize()


    def get_wildcard_data(self):
        return {'txt': 'text (*.txt)|*.txt',
                'gse2': 'gse2 (*.gse; *.gse2)|*.gse; *.gse2'
                }



class GridDataTable(wx.grid.PyGridTableBase):
    def __init__(self, data):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.col_labels = ['format', 'filename', 'size']

        self.currentRows = self.GetNumberRows()
        self.currentColumns = self.GetNumberCols()

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        if len(self.data) == 0:
            n_rows = 1
        else:
            n_rows = len(self.data)

        return n_rows

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.col_labels)

    def IsEmptyCell(self, row, col):
        """Return True if the cell is empty"""
        return False

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        if len(self.data) == 0:
            return ''
        elif len(self.data) < row:
            return ''
        else:
            return str(self.data[row][col])

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass


    def GetColLabelValue(self, col):
        ''' Get the column label.
        '''
        return self.col_labels[col]


    def sortColumn(self, col, reverse = False):
        """
        col -> sort the data based on the column indexed by col
        """
        self.data = sorted(self.data, key = operator.itemgetter(col), reverse = reverse)
        self.UpdateValues()


    def ResetView(self):
        """Trim/extend the control's rows and update all values"""
        self.GetView().BeginBatch()
        for current, new, delmsg, addmsg in [
                (self.currentRows, self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
                (self.currentColumns, self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:
                if new < current:
                        msg = wx.grid.GridTableMessage(
                                self,
                                delmsg,
                                new,    # position
                                current-new,
                        )
                        self.GetView().ProcessTableMessage(msg)
                elif new > current:
                        msg = wx.grid.GridTableMessage(
                                self,
                                addmsg,
                                new-current
                        )
                        self.GetView().ProcessTableMessage(msg)


        self.UpdateValues()
        self.currentRows = self.GetNumberRows()
        self.currentColumns = self.GetNumberCols()
        self.GetView().EndBatch()

        # The scroll bars aren't resized (at least on windows)
        # Jiggling the size of the window rescales the scrollbars
        h,w = self.GetView().GetSize()
        self.GetView().SetSize((h+1, w))
        self.GetView().SetSize((h, w))
        self.GetView().ForceRefresh()


    def UpdateValues( self ):
            """Update all displayed values"""
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            self.GetView().ProcessTableMessage(msg)



class FileGrid(wx.grid.Grid):
    def __init__(self, parent, data):
        wx.grid.Grid.__init__(self, parent, wx.ID_ANY)

        table = GridDataTable(data)

        self.SetTable(table, True)

        self.AutoSizeColumns(setAsMin = True)
        #self.SetMinSize((600, 100))
        #self.SetMaxSize((-1, 600))

        self.last_selected_row = None

        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onLabelRightClicked)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onCellLeftClicked)

    def Reset(self):
        """reset the view based on the data in the table.  Call
        this when rows are added or destroyed"""
        self.GetTable().ResetView()

    def removeRows(self, rows):
        ''' Remove the rows specified by the indexes in rows.
        '''
        for k in rows:
            self.GetTable().data.pop(k)

        self.Reset()


    def clear(self):
        ''' Clear the data from the table.
        '''
        self.GetTable().data = []
        self.Reset()


    def do_resize(self, event=None):
            self.GetParent().Freeze()
            self.AutoSizeColumns(setAsMin = True)
            self.GetParent().Layout()

            #the column which will be expanded
            expandCol = 1

            #calculate the total width of the other columns
            otherWidths = 0
            for i in [i for i in range(self.GetNumberCols()) if i != expandCol]:
                colWidth = self.GetColSize(i)
                otherWidths += colWidth

            #add the width of the row label column
            otherWidths += self.RowLabelSize

            descWidth = self.Size[0] - otherWidths

            self.SetColSize(expandCol, descWidth)

            self.GetParent().Layout()

            if event:
                event.Skip()
            self.GetParent().Thaw()


    def onLabelRightClicked(self, evt):
        # Did we click on a row or a column?
        row, col = evt.GetRow(), evt.GetCol()
        if row == -1: self.colPopup(col, evt)
        elif col == -1: self.rowPopup(row, evt)


    def onCellLeftClicked(self, evt):
        if evt.ShiftDown() == True:
            if evt.ControlDown() == False:
                self.ClearSelection()

            selected_row = evt.GetRow()
            if selected_row >= self.last_selected_row:
                for k in range(self.last_selected_row, selected_row + 1):
                    self.SelectRow(k, addToSelected = True)
            else:
                for k in range(selected_row, self.last_selected_row + 1):
                    self.SelectRow(k, addToSelected = True)

        else:
            if evt.ControlDown() == True:
                add_to_selection = True
            else:
                add_to_selection = False
            self.SelectRow(evt.GetRow(), addToSelected = add_to_selection)
            self.last_selected_row = evt.GetRow()


    def colPopup(self, col, evt):
        """(col, evt) -> display a popup menu when a column label is
        right clicked"""
        x = self.GetColSize(col)/2
        menu = wx.Menu()

        xo, yo = evt.GetPosition()
        self.SelectCol(col)
        cols = self.GetSelectedCols()
        self.Refresh()
        sort_asc_menu = menu.Append(wx.ID_ANY, "sort column asc.")
        sort_desc_menu = menu.Append(wx.ID_ANY, "sort column desc.")

        def sort(event, reverse, self=self, col=col):
            self.GetTable().sortColumn(col, reverse = reverse)
            self.Reset()

        self.Bind(wx.EVT_MENU, lambda event: sort(event, reverse=False), sort_asc_menu)
        self.Bind(wx.EVT_MENU, lambda event: sort(event, reverse=True), sort_desc_menu)

        self.PopupMenu(menu)
        menu.Destroy()



