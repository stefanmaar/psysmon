# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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
        pref_item = CustomPrefItem(name = 'filter_pattern', value = ['*.msd', '.mseed', '*.MSEED'])
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

        self.currentRows = self.GetNumberRows()
        self.currentColumns = self.GetNumberCols()

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.data)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return 1

    def IsEmptyCell(self, row, col):
        """Return True if the cell is empty"""
        return False

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        return repr(self.data[row])

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass

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
        self.GetView().EndBatch()

        # The scroll bars aren't resized (at least on windows)
        # Jiggling the size of the window rescales the scrollbars
        #h,w = grid.GetSize()
        #grid.SetSize((h+1, w))
        #grid.SetSize((h, w))
        #grid.ForceRefresh()

    def UpdateValues( self ):
            """Update all displayed values"""
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            self.GetView().ProcessTableMessage(msg)



class FileGrid(wx.grid.Grid):
    def __init__(self, parent, data):
        wx.grid.Grid.__init__(self, parent, wx.ID_ANY)

        table = GridDataTable(data)

        self.SetTable(table, True)


## The pSysmon main GUI
# 
# 
class ImportWaveformEditDlg(wx.Frame):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collectionNode, psyProject,  parent, id=-1, title='import waveform', 
                 size=(300,200)):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY, 
                           title=title, 
                           size=size,
                           style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)

        # Create the logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.collectionNode = collectionNode
        self.psyProject = psyProject

        self.initUI()

        self.initUserSelections()


    def initUserSelections(self):
        if self.collectionNode.pref_manager.get_value('input_files'):
            print "Set the list to the previously selected files."

            for k, curFile in enumerate(self.collectionNode.pref_manager.get_value('input_files')):
                fSize = os.path.getsize(curFile['filename']);
                fSize = fSize/1024.0
                self.fileListCtrl.InsertStringItem(k, curFile['format'])
                self.fileListCtrl.SetStringItem(k, 1, curFile['filename'])
                self.fileListCtrl.SetStringItem(k, 2, "%.2f" % fSize)


    def initUI(self):
        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)

        cmData = (("add files", self.onAddFiles),
                 ("add directory", self.onAddDirectory))

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)

        self.fileListCtrl = FileListCtrl(self, id=wx.ID_ANY,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 )
        sizer.Add(self.fileListCtrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)


        fields = ('type', 'name', 'size')
        self.file_grid = FileGrid(self, data = [])
        sizer.Add(self.file_grid, pos =(1,0), flag=wx.EXPAND|wx.ALL, border = 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(2,0), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableRow(1)

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelButton)
        self.fileListCtrl.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)


    def onShowContextMenu(self, event):
        print "Showing context menu."
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)
        print "Popup closed"


    def onOk(self, event):
        inputFiles = []
        for idx in range(self.fileListCtrl.GetItemCount()):
            format = self.fileListCtrl.GetItem(idx, 0).GetText()
            name = self.fileListCtrl.GetItem(idx, 1).GetText()
            inputFiles.append({'format':format, 'filename':name})

        self.collectionNode.pref_manager.set_value('input_files', inputFiles)
        self.Destroy()


    def onCancel(self, event):
        self.Destroy()



    def onAddFiles(self, event):
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
            style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
            )

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            # This returns a Python list of files that were selected.
            paths = dlg.GetPaths()
            filterIndex= dlg.GetFilterIndex()

            keys = sorted(wildCards.keys())

            if(filterIndex < len(keys)):
                fileFormat = keys[filterIndex]
            else:
                fileFormat = '???'

            index = 0
            for curPath in paths:
                fSize = os.path.getsize(curPath);
                fSize = fSize/1024.0
                self.fileListCtrl.InsertStringItem(index, fileFormat)
                self.fileListCtrl.SetStringItem(index, 1, curPath)
                self.fileListCtrl.SetStringItem(index, 2, "%.2f" % fSize)
                index += 1

        dlg.Destroy()


    def onAddDirectory(self, event):
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
                        #fsize = os.path.getsize(os.path.join(root, filename));
                        fsize = 0
                        fsize = fsize/1024.0
                        #self.fileListCtrl.InsertStringItem(k, '???')
                        #self.fileListCtrl.SetStringItem(k, 1, os.path.join(root, filename))
                        #self.fileListCtrl.SetStringItem(k, 2, "%.2f" % fsize)
                        matches.append(os.path.join(root, filename))
                        k += 1
            self.file_grid.GetTable().data = matches
            self.file_grid.GetTable().ResetView()
            #bar.Destroy()
        # Only destroy a dialog after you're done with it.
        dlg.Destroy()


    def getWildCardData(self):
        return {'mseed': 'miniSeed (*.msd; *.mseed)|*.msd;*.mseed| ', 
                'gse2': 'gse2 (*.gse; *.gse2)|*.gse; *.gse2| ',
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

