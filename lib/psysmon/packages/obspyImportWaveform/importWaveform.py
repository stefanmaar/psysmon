

from psysmon.core.util import PsysmonError 
from psysmon.core.packageNodes import CollectionNode
import wx
import wx.aui
from obspy.core import read, Trace, Stream
import os


## Documentation for class importWaveform
# 
# 
class ImportWaveform(CollectionNode):

    def edit(self):
        dlg = ImportWaveformEditDlg(self, self.project, None)
        dlg.Show()

    def execute(self, prevNodeOutput={}):
        print "Executing the node %s." % self.name
        dbData = []
        for curFile in self.options['inputFiles']:
            print("Processing file " + curFile['filename'])
            stream = read(pathname_or_url=curFile['filename'],
                             format = curFile['format'],
                             headonly=True)

            print stream

            for curTrace in stream.traces:
                print "Importing trace " + curTrace.getId()
                dbData.append(self.getDbData(curFile['filename'], curFile['format'], curTrace))

        print dbData   

        headerTable = self.project.dbTableNames['traceheader']
        query =  ("INSERT INTO %s "
                  "(file_type, wf_id, filename, orig_path, network, recorder_serial, channel, location, sps, numsamp, begin_date, begin_time, station_id, recorder_id, sensor_id) "
                  "VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)") % headerTable  
        res = self.project.executeManyQuery(query, dbData)

        if not res['isError']:
            self.waveformDirList = res['data']
            print self.waveformDirList
        else:
            print res['msg']  


    ## Return a tuple of values to be inserted into the traceheader database.
    def getDbData(self, filename, format, Trace):

        wfDirId = ""
        for curWfDir in self.project.waveformDirList:
            if filename.startswith(curWfDir['dirAlias']):
                wfDirId = curWfDir['id']
                break

        print wfDirId

        if wfDirId:
            # Remove the waveform directory from the file path.
            relativeFilename = filename.replace(curWfDir['dirAlias'], '')
            relativeFilename = relativeFilename[1:]
            return (format, wfDirId, relativeFilename, os.path.dirname(filename), Trace.stats.network,
                    Trace.stats.station, Trace.stats.channel, Trace.stats.location, 
                    Trace.stats.sampling_rate, Trace.stats.npts, Trace.stats.starttime.isoformat(' '), 
                    Trace.stats.starttime.getTimeStamp(), -1, -1, -1)
        else:
            print "File %s is not inside a waveform directory. Skipping this trace." % filename
            return ()





## The pSysmon main GUI
# 
# 
class ImportWaveformEditDlg(wx.Dialog):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collectionNode, psyProject,  parent, id=-1, title='import waveform', 
                 size=(300,200)):
        wx.Dialog.__init__(self, parent=None, id=wx.ID_ANY, 
                           title=title, 
                           size=size,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        self.collectionNode = collectionNode
        self.psyProject = psyProject

        self.initUI()

        self.initUserSelections()


    def initUserSelections(self):
        if self.collectionNode.options['inputFiles']:
            print "Set the list to the previously selected files."

            index = 0
            for curFile in self.collectionNode.options['inputFiles']:
                fSize = os.path.getsize(curFile['filename']);
                fSize = fSize/1024.0
                self.fileListCtrl.InsertStringItem(index, curFile['format'])
                self.fileListCtrl.SetStringItem(index, 1, curFile['filename'])
                self.fileListCtrl.SetStringItem(index, 2, "%.2f" % fSize)
                index += 1


    def initUI(self):
        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.GridBagSizer(5, 5)

        self.fileListCtrl = FileListCtrl(self, id=wx.ID_ANY,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 )
        sizer.Add(self.fileListCtrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def onOk(self, event):
        inputFiles = []
        for idx in range(self.fileListCtrl.GetItemCount()):
            format = self.fileListCtrl.GetItem(idx, 0).GetText()
            name = self.fileListCtrl.GetItem(idx, 1).GetText()
            inputFiles.append({'format':format, 'filename':name})

        self.collectionNode.options['inputFiles'] = inputFiles
        self.Destroy()


    def onAddFiles(self, event):
        print "Adding files"
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
        if dlg.ShowModal() == wx.ID_OK:
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


    def onAddDirectory(self, event):
        print "Adding directory"

    def getWildCardData(self):
        return {'mseed': 'miniSeed (*.msd; *.mseed)|*.msd;*.mseed| ', 
                'gse2': 'gse2 (*.gse; *.gse2)|*.gse; *.gse2| ',
                }



class FileListCtrl(wx.ListCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        #listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.SetMinSize((500, 300))

        cmData = (("add files", parent.onAddFiles),
                 ("add directory", parent.onAddDirectory))

        # create the context menu.
        self.contextMenu = ContextMenu(cmData)

        columns = {1: 'type', 2: 'name', 3: 'size'}

        for colNum, name in columns.iteritems():
            self.InsertColumn(colNum, name)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)




class ContextMenu(wx.Menu):

        def __init__(self, cmData):
            wx.Menu.__init__(self)

            for cmLabel, cmHandler in cmData:
                item = self.Append(-1, cmLabel)
                self.Bind(wx.EVT_MENU, cmHandler, item)

