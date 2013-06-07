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
from operator import itemgetter



## Documentation for class importWaveform
# 
# 
class ImportWaveform(CollectionNode):

    name = 'import waveform'
    mode = 'editable'
    category = 'Data Import'
    tags = ['stable']

    def __init__(self):
        CollectionNode.__init__(self)
        pref_item = CustomPrefItem(name = 'input_files', value = [])
        self.pref_manager.add_item(item = pref_item)
        pref_item = CustomPrefItem(name = 'last_dir', value = [])
        self.pref_manager.add_item(item = pref_item)
        pref_item = CustomPrefItem(name = 'filter_pattern', value = ['*.msd', '*.mseed', '*.MSEED'])
        self.pref_manager.add_item(item = pref_item)

        #self.options = {}
        #self.options['inputFiles'] = []                     # The files to import.
        #self.options['lastDir'] = ""                        # The last used directory.

    def edit(self):
        dlg = ImportWaveformEditDlg(self, self.project, None)
        dlg.Show()

    def execute(self, prevNodeOutput={}):
        print "Executing the node %s." % self.name
        dbData = []
        for curFile in self.pref_manager.get_value('input_files'):
            print("Processing file " + curFile['filename'])
            stream = read(pathname_or_url=curFile['filename'],
                             format = curFile['format'],
                             headonly=True)

            print stream

            for curTrace in stream.traces:
                print "Importing trace " + curTrace.getId()
                cur_data = self.getDbData(curFile['filename'], curFile['format'], curTrace)
                if cur_data is not None:
                    dbData.append(cur_data)

        self.logger.debug('dbData: %s', dbData)   

        if len(dbData) > 0:
            dbSession = self.project.getDbSession()
            dbSession.add_all(dbData)
            dbSession.commit()
            dbSession.close()


    ## Return a tuple of values to be inserted into the traceheader database.
    def getDbData(self, filename, format, Trace):
        # Get the database traceheader table mapper class.
        Header = self.project.dbTables['traceheader']

        wfDirId = ""
        for curWfDir in self.project.waveclient['main client'].waveformDirList:
            if filename.startswith(curWfDir.alias):
                wfDirId = curWfDir.id
                break

        print wfDirId

        if wfDirId:
            # Remove the waveform directory from the file path.
            relativeFilename = filename.replace(curWfDir.alias, '')
            relativeFilename = relativeFilename[1:]
            labels = ['id', 'file_type', 'wf_id', 'filename', 'orig_path', 
                      'network', 'recorder_serial', 'channel', 'location', 
                      'sps', 'numsamp', 'begin_date', 'begin_time', 
                      'station_id', 'recorder_id', 'sensor_id']
            header2Insert = dict(zip(labels, (None, format, wfDirId, 
                            relativeFilename, os.path.dirname(filename), 
                            Trace.stats.network, Trace.stats.station, 
                            Trace.stats.channel, Trace.stats.location, 
                            Trace.stats.sampling_rate, Trace.stats.npts, 
                            Trace.stats.starttime.isoformat(' '), 
                            Trace.stats.starttime.timestamp,
                            None, None, None)))

            print header2Insert

            return Header(**header2Insert)
        else:
            print "File %s is not inside a waveform directory. Skipping this trace." % filename
            return None


class GridDataTable(wx.grid.PyGridTableBase):
    def __init__(self, data):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.col_labels = ['type', 'filename', 'size']

        self.currentRows = self.GetNumberRows()
        self.currentColumns = self.GetNumberCols()

        self.format_default = wx.grid.GridCellAttr()
        self.format_not_known = wx.grid.GridCellAttr()
        self.format_not_known.SetBackgroundColour("firebrick1")
        self.format_known = wx.grid.GridCellAttr()
        self.format_known.SetBackgroundColour("springgreen1")
        self.format_not_checked = wx.grid.GridCellAttr()
        self.format_not_checked.SetBackgroundColour("grey85")

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        if len(self.data) == 0:
            n_rows = 1
        else:
            n_rows = len(self.data)

        return n_rows

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return 3

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

    def GetAttr(self, row, col, kind):
        if len(self.data) == 0 or len(self.data) < row:
            self.format_default.SetBackgroundColour(self.GetView().GetDefaultCellBackgroundColour())
            attr = self.format_default
        elif self.data[row][0] == 'unknown':
            attr = self.format_not_known
        elif self.data[row][0] == 'not checked':
            attr =  self.format_not_checked
        else:
            attr =  self.format_known

        attr.SetReadOnly(True)
        attr.IncRef()
        return attr


    def sortColumn(self, col, reverse = False):
        """
        col -> sort the data based on the column indexed by col
        """
        self.data = sorted(self.data, key = itemgetter(col), reverse = reverse)
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
        self.SetMinSize((100, 100))
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


    def doResize(self, event=None):
            self.GetParent().Freeze()
            self.AutoSize()
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


## The pSysmon main GUI
# 
# 
class ImportWaveformEditDlg(wx.Frame):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collectionNode, psyProject,  parent, id=-1, title='import waveform', 
                 size=(640,480)):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY, 
                           title=title, 
                           size=size,
                           style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)

        # Create the logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.collectionNode = collectionNode
        self.psyProject = psyProject
        self.check_file_format = True

        self.initUI()
        self.SetMinSize(self.GetBestSize())
        self.initUserSelections()



    def initUserSelections(self):
        filter_pattern = self.collectionNode.pref_manager.get_value('filter_pattern')
        self.filter_pattern_text.SetValue(','.join(filter_pattern))

        if self.collectionNode.pref_manager.get_value('input_files'):
            self.file_grid.GetTable().data = self.collectionNode.pref_manager.get_value('input_files')
            self.file_grid.GetTable().ResetView()
            #for k, curFile in enumerate(self.collectionNode.pref_manager.get_value('input_files')):
            #    fSize = os.path.getsize(curFile['filename']);
            #    fSize = fSize/1024.0
            #    self.fileListCtrl.InsertStringItem(k, curFile['format'])
            #    self.fileListCtrl.SetStringItem(k, 1, curFile['filename'])
            #    self.fileListCtrl.SetStringItem(k, 2, "%.2f" % fSize)


    def initUI(self):
        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)
        grid_button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create the grid editing buttons.
        add_files_button = wx.Button(self, wx.ID_ANY, 'add files')
        add_dir_button = wx.Button(self, wx.ID_ANY, 'add directory')
        self.filter_pattern_text =wx.TextCtrl(self, wx.ID_ANY, '*')
        file_format_checkbox = wx.CheckBox(self, -1, "check file format")#, (65, 40), (150, 20), wx.NO_BORDER)
        file_format_checkbox.SetValue(self.check_file_format)
        remove_selected_button = wx.Button(self, wx.ID_ANY, 'remove selected')
        clear_button = wx.Button(self, wx.ID_ANY, 'clear list')

        # Fill the grid button sizer.
        grid_button_sizer.Add(add_files_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(add_dir_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(self.filter_pattern_text, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(file_format_checkbox, 0, wx.EXPAND|wx.BOTTOM, border = 20)
        grid_button_sizer.Add(remove_selected_button, 0, wx.EXPAND|wx.ALL)
        grid_button_sizer.Add(clear_button, 0, wx.EXPAND|wx.ALL)

        self.file_grid = FileGrid(self, data = [])
        sizer.Add(self.file_grid, pos =(0,0), flag=wx.EXPAND|wx.ALL, border = 5)

        sizer.Add(grid_button_sizer, pos=(0,1), flag = wx.EXPAND|wx.ALL, border = 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), span = (1,2), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.onAddFiles, add_files_button)
        self.Bind(wx.EVT_BUTTON, self.onAddDirectory, add_dir_button)
        self.Bind(wx.EVT_BUTTON, self.onRemoveSelected, remove_selected_button)
        self.Bind(wx.EVT_BUTTON, self.onClearList, clear_button)
        self.Bind(wx.EVT_CHECKBOX, self.onFileFormatCheck, file_format_checkbox)
        self.Bind(wx.EVT_TEXT, self.onFilterPatternText, self.filter_pattern_text)

        #self.file_grid.doResize()



    def onOk(self, event):
        self.collectionNode.pref_manager.set_value('input_files', self.file_grid.GetTable().data)
        self.Destroy()


    def onCancel(self, event):
        self.Destroy()



    def onAddFiles(self, event):
        from obspy.core.util.base import ENTRY_POINTS
        from pkg_resources import load_entry_point

        wildCards = self.getWildCardData()

        wildCard = ""
        for curKey in sorted(wildCards.iterkeys()):
            wildCard = wildCard + wildCards[curKey]

        wildCard = wildCard + 'All files (*)|*|'


        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard=wildCard,
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

                if self.check_file_format is True:
                    # Check the file formats.
                    EPS = ENTRY_POINTS['waveform']
                    for format_ep in [x for (key, x) in EPS.items() if key == 'MSEED']:
                        # search isFormat for given entry point
                        isFormat = load_entry_point(format_ep.dist.key,
                            'obspy.plugin.%s.%s' % ('waveform', format_ep.name),
                            'isFormat')
                        # check format
                        self.logger.debug('Checking format with %s.', isFormat)
                        if isFormat(filename):
                            file_format = format_ep.name
                            break;
                    else:
                        file_format = 'unknown'
                else:
                    file_format = 'not checked'

                self.logger.debug('adding to matches')
                matches.append((file_format, filename, '%.2f' % fsize))

            matches = [x for x in matches if x not in self.file_grid.GetTable().data]
            self.file_grid.GetTable().data.extend(matches)
            self.file_grid.GetTable().ResetView()

        dlg.Destroy()


    def onAddDirectory(self, event):
        from obspy.core.util.base import ENTRY_POINTS
        from pkg_resources import load_entry_point

        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE
                           | wx.DD_DIR_MUST_EXIST
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            #bar = wx.ProgressDialog("Progress dialog example",
            #                   "An informative message",
            #                   parent=self,
            #                   style = wx.PD_CAN_ABORT
            #                    | wx.PD_APP_MODAL
            #                    | wx.PD_ELAPSED_TIME
            #                    | wx.PD_ESTIMATED_TIME
            #                    | wx.PD_REMAINING_TIME
            #                    )
            matches = []
            #count = 0
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

                        if self.check_file_format is True:
                            # Check the file formats.
                            EPS = ENTRY_POINTS['waveform']
                            for format_ep in [x for (key, x) in EPS.items() if key == 'MSEED']:
                                # search isFormat for given entry point
                                isFormat = load_entry_point(format_ep.dist.key,
                                    'obspy.plugin.%s.%s' % ('waveform', format_ep.name),
                                    'isFormat')
                                # check format
                                self.logger.debug('Checking format with %s.', isFormat)
                                if isFormat(os.path.join(root,filename)):
                                    file_format = format_ep.name
                                    break;
                            else:
                                file_format = 'unknown'
                        else:
                            file_format = 'not checked'

                        self.logger.debug('adding to matches')
                        matches.append((file_format, os.path.join(root, filename), '%.2f' % fsize))
                        k += 1



            matches = [x for x in matches if x not in self.file_grid.GetTable().data]
            self.file_grid.GetTable().data.extend(matches)
            self.file_grid.GetTable().ResetView()
            #bar.Destroy()

        self.file_grid.doResize()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        self.logger.debug('Exiting the onAddDirectory.')

    def onRemoveSelected(self, event):
        self.logger.debug('Selected rows: %s', self.file_grid.GetSelectedRows())
        self.file_grid.removeRows(self.file_grid.GetSelectedRows())


    def onClearList(self, event):
        self.file_grid.clear()

    def onFileFormatCheck(self, event):
        cb = event.GetEventObject()
        self.check_file_format = cb.IsChecked()

    def onFilterPatternText(self, event):
        text = event.GetString()
        self.collectionNode.pref_manager.set_value('filter_pattern', text.split(','))


    def getWildCardData(self):
        return {'mseed': 'miniSeed (*.msd; *.mseed)|*.msd;*.mseed| ', 
                'gse2': 'gse2 (*.gse; *.gse2)|*.gse; *.gse2| '
                }



class FileListCtrl(wx.ListCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style = None):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        #listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.SetMinSize((500, 300))

        columns = {1: 'type', 2: 'name', 3: 'size'}

        for colNum, name in columns.iteritems():
            self.InsertColumn(colNum, name)

