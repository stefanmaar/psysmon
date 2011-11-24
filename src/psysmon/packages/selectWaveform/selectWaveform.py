## @file psysmon.packages.obspyImportWaveform.importWaveform.py
# 

## @package psysmon.packages.obspyImportWaveform.importWaveform
#
#
#
# @author: Stefan Mertl
# Created on Apr 25, 2011

## @page psysmon.packages.obspyImportWaveform.importWaveform_page  Page for module psysmon.packages.obspyImportWaveform.importWaveform
#
# @section sec_intro Introduction
#
#
# @section sec_license License
#     This file is part of Seismon.
#
#     If you use Seismon in any program or publication, please inform and
#     acknowledge its author Stefan Mertl (info@stefanmertl.com).
#
#     Seismon is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.

import psysmon.core.base
from psysmon.core.util import PsysmonError 
import wx
import wx.aui
import wx.calendar
import wx.lib.masked as masked
import wx.grid
import wx.lib.scrolledpanel as scrolled
import os
import datetime
from obspy.core.utcdatetime import UTCDateTime

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import date2num




def _wxdate2pydate(date):
     assert isinstance(date, wx.DateTime)
     if date.IsValid():
         ymd = map(int, date.FormatISODate().split('-'))
         return datetime.date(*ymd)
     else:
         return None 

def _pydate2wxdate(date):
     assert isinstance(date, (datetime.datetime, datetime.date))
     tt = date.timetuple()
     dmy = (tt[2], tt[1]-1, tt[0])
     return wx.DateTimeFromDMY(*dmy) 

## Documentation for class importWaveform
#
#
class SelectWaveform(psysmon.core.base.CollectionNode):
    
    def edit(self):
        dlg = SelectWaveformEditDlg(self, self.project, None)
        dlg.Show()
        
    def execute(self, prevNodeOutput={}):
        print "Executing the node %s." % self.name
         
        
    
    ## Return a tuple of values to be inserted into the traceheader database.
    def getDbData(self, psyProject, filename, format, Trace):
        
        wfDirId = ""
        for curWfDir in psyProject.waveformDirList:
            if filename.startswith(curWfDir['dirAlias']):
                wfDirId = curWfDir['id']
                break
        
        if wfDirId:
            return (format, wfDirId, filename, filename, Trace.stats.network,
                    Trace.stats.station, Trace.stats.channel, Trace.stats.location, 
                    Trace.stats.sampling_rate, Trace.stats.npts, Trace.stats.starttime.isoformat(' '), 
                    Trace.stats.starttime.getTimeStamp(), -1, -1, -1)
        else:
            print "File %s is not inside a waveform directory. Skipping this trace." % filename
            return ()
        
            
        
        
        
## The pSysmon main GUI
# 
# 
class SelectWaveformEditDlg(wx.Frame):
        
    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collectionNode, psyProject,  parent=None, id=wx.ID_ANY, title='select waveform', 
                 size=(800,600)):
        wx.Frame.__init__(self,
                          parent=parent, 
                          id=id, 
                          title=title, 
                          pos=wx.DefaultPosition, 
                          size=size, 
                          style=wx.DEFAULT_FRAME_STYLE)
        
        self.collectionNode = collectionNode
        self.psyProject = psyProject
        self.SetSize(size)
        
        self.initUI()
        
        #self.initUserSelections()
        
    
    def initUserSelections(self):
        if self.collectionNode.property['inputFiles']:
            print "Set the list to the previously selected files."
            
            index = 0
            for curFile in self.collectionNode.property['inputFiles']:
                fSize = os.path.getsize(curFile['filename']);
                fSize = fSize/1024.0
                self.fileListCtrl.InsertStringItem(index, curFile['format'])
                self.fileListCtrl.SetStringItem(index, 1, curFile['filename'])
                self.fileListCtrl.SetStringItem(index, 2, "%.2f" % fSize)
                index += 1
    
    
    def initUI(self):
        # Use the AUI docking library.
        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow(self)
         
        self.selectionPanel = SelectionPanel(self, self.psyProject)
        self.displayPanel = DisplayPanel(self, self.psyProject )
        
        # Add the selection panel as the center pane.
        self.mgr.AddPane(self.selectionPanel, wx.aui.AuiPaneInfo().Name("selectionPanel").
                          Caption("select parameters").Center().Layer(1).Position(1).Row(2).CloseButton(False)
                          )
        
        # Add the display panel.
        self.mgr.AddPane(self.displayPanel, wx.aui.AuiPaneInfo().Name("display").
                          Caption("available waveform").Left().Layer(1).Position(1).Row(1).CloseButton(False).
                          MinSize(wx.Size(200, -1)).MaxSize(wx.Size(200, -1)))
        
        self.mgr.Update()
        
         
        # Use standard button IDs.
        #okButton = wx.Button(self, wx.ID_OK)
        #okButton.SetDefault()
        #cancelButton = wx.Button(self, wx.ID_CANCEL)
        
        # Layout using sizers.
        #sizer = wx.GridBagSizer(5, 5)
        

        #sizer.Add(self.fileListCtrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        
        #btnSizer = wx.StdDialogButtonSizer()
        #btnSizer.AddButton(okButton)
        #btnSizer.AddButton(cancelButton)
        #btnSizer.Realize()
        #sizer.Add(btnSizer, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)
        #sizer.AddGrowableCol(0)
        #sizer.AddGrowableRow(0)
        
        #self.SetSizerAndFit(sizer)
        
        #self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        
        
    def onOk(self, event):
        inputFiles = []
        for idx in range(self.fileListCtrl.GetItemCount()):
            format = self.fileListCtrl.GetItem(idx, 0).GetText()
            name = self.fileListCtrl.GetItem(idx, 1).GetText()
            inputFiles.append({'format':format, 'filename':name})

        self.collectionNode.property['inputFiles'] = inputFiles
        self.Destroy()
        
        
    
## The selection panel.
#        
class SelectionPanel(scrolled.ScrolledPanel):
    
    ## The constructor.
    #
    # @param self The object pointer.
    # @param parent The parent object holding the panel.
    def __init__(self, parent, psyProject):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.SetMaxSize((600, -1))
        
        ## The pSysmon project.
        self.psyProject = psyProject
                
        ## The selected start time.
        #self.startTime = UTCDateTime.today()
        #self.startTime = self.startTime.replace(hour=0, minute=0, second=0, microsecond=0)
        self.startTime = UTCDateTime(2009, 11, 30, 1, 0, 0)

        ## The selected duration.
        self.selDuration = 3600


        sizer = wx.GridBagSizer(5, 5)
        
        
        # Create the labels.
        dateLabel = wx.StaticText(self, wx.ID_ANY, "Date")
        timeLabel = wx.StaticText(self, wx.ID_ANY, "Time")
        durationLabel = wx.StaticText(self, wx.ID_ANY, "Duration")
        sizer.Add(dateLabel, pos=(0,0), flag=wx.ALIGN_CENTER|wx.TOP|wx.LEFT|wx.RIGHT, border=4)
        sizer.Add(timeLabel, pos=(0,1), flag=wx.ALIGN_CENTER|wx.TOP|wx.LEFT|wx.RIGHT, border=4)
        sizer.Add(durationLabel, pos=(0,2), flag=wx.ALIGN_CENTER|wx.TOP|wx.LEFT|wx.RIGHT, border=4)
        
        # Create the calendar control.
        self.calendarCtrl = wx.calendar.CalendarCtrl(self, -1, _pydate2wxdate(self.startTime))
        sizer.Add(self.calendarCtrl, pos=(1, 0), flag=wx.ALL, border=4)
        
        # Create the time control.
        self.timeCtrl = masked.TimeCtrl(
                        self, -1, name="24 hour control", fmt24hr=True)
        #h = self.timeCtrl.GetSize().height
        sizer.Add(self.timeCtrl, pos=(1, 1), flag=wx.ALL, border=4)
        
        # Create the duration spin control.
        sc = wx.SpinCtrl(self, -1, "")
        sc.SetRange(1,86400)
        sc.SetValue(self.selDuration)
        self.durationCtrl = sc
        sizer.Add(self.durationCtrl, pos=(1, 2), flag=wx.ALIGN_LEFT|wx.ALL, border=4)
        
        # Create the station selection grid.
        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True) 
        
        fields = self.getTableFields()
        data = self.getTableData()
        self.stationGrid = wx.grid.Grid(self, size=(-1, -1))
        self.stationGrid.CreateGrid(len(data), len(fields))
        
        # Bind the sensorGrid events.
        #self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onSensorCellChange)

        for k, (name, label, attr)  in enumerate(fields):
            self.stationGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.stationGrid.SetColAttr(k, roAttr)
            
            if k > 0:
                attr = wx.grid.GridCellAttr()
                attr.SetEditor(wx.grid.GridCellBoolEditor())
                self.stationGrid.SetColAttr(k, attr)
                self.stationGrid.SetColFormatBool(k)
                
        for k, (netName, statName, location) in enumerate(sorted(data)):
            self.stationGrid.SetCellValue(k, 0, netName+":"+statName+":"+location)
        
        sizer.Add(self.stationGrid, pos=(2, 0), span=(1,4), flag=wx.EXPAND|wx.ALL, border=4)

#        self.executeButton = wx.Button(self, 10, "execute", (20, 20))
#        sizer.Add(self.executeButton, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=2)
#        
        #sizer.AddGrowableCol(0)
        #sizer.AddGrowableRow(2)
        sizer.AddGrowableCol(3)
        self.SetSizerAndFit(sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
#        
#
        # Bind the events
        self.Bind(wx.calendar.EVT_CALENDAR_SEL_CHANGED,
                  self.onCalSelChanged, self.calendarCtrl)
        self.Bind(masked.EVT_TIMEUPDATE, self.onTimeChange, self.timeCtrl)
        self.Bind(wx.EVT_SPINCTRL, self.onDurationSpinChanged, self.durationCtrl)
#        self.Bind(wx.EVT_BUTTON, self.onExecuteCollection)
        #self.Bind(wx.EVT_SIZE, self.OnSize)
#        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCollectionNodeItemSelected)
#
#        self.selectedCollectionNodeIndex = -1

    def OnSize(self, event):
        #print "Resizing"
        #print self.GetSize()
        #print self.GetBestSize()
        #print self.GetMinSize()
        self.Refresh()
        event.Skip()

    def onDurationSpinChanged(self, event):
        self.selDuration = self.durationCtrl.GetValue()
        print "Duration changed: %f" % self.selDuration
        self.GetParent().displayPanel.updateDisplay((self.startTime, self.startTime + self.selDuration))

    def onCalSelChanged(self, event):
        cal = event.GetEventObject()
        curDate = wx.calendar._wxdate2pydate(cal.GetDate())
        self.startTime= self.startTime.replace(year=curDate.year,
                                            month=curDate.month,
                                            day=curDate.day)
        print "Date changes: %s" % self.startTime.isoformat()
        self.GetParent().displayPanel.updateDisplay((self.startTime, self.startTime + self.selDuration))

    def onTimeChange(self, event):
        curTime = self.timeCtrl.GetMxDateTime()
        self.startTime = self.startTime.replace(hour=curTime.hour,
                                            minute=curTime.minute,
                                            second=curTime.second)
        print "Time changed: %s" % self.startTime.isoformat()
        self.GetParent().displayPanel.updateDisplay((self.startTime, self.startTime + self.selDuration))



    def getTableFields(self):
        tableField = []
        tableField.append(('station', 'station', 'readonly'))

        # Get all available channel names from the database and create the
        # accoding table column fields.
        tableName = self.psyProject.dbTableNames['geom_sensor']
        query =  ("SELECT DISTINCT channel_name FROM  %s") % tableName

        res = self.psyProject.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                tableField.append((curData['channel_name'], curData['channel_name'], 'editable'))

        return tableField



    def getTableData(self):
        tableData = []

        # Get all available channel names from the database and create the
        # accoding table column fields.
        tableName = self.psyProject.dbTableNames['geom_station']
        query =  ("SELECT net_name, name, location FROM  %s order by net_name, name") % tableName

        res = self.psyProject.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                tableData.append((curData['net_name'], curData['name'], curData['location']))

        return tableData


## The station-channel selection grid.
#
class StationSelectionGrid(wx.grid.Grid):
    def __init__(self, parent, id=wx.ID_ANY):
        wx.grid.Grid.__init__(self, parent=parent, id=id)
        
## The selection panel.
#        
class DisplayPanel(wx.Panel):
    
    ## The constructor.
    #
    # @param self The object pointer.
    # @param parent The parent object holding the panel.
    def __init__(self, parent, psyProject):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.psyProject = psyProject
        self.SetMinSize((200, -1))
        #self.SetMaxSize((300, -1))
        
        self.sizer = wx.GridBagSizer(0, 0)
        
        self.displayFigure = Figure(figsize=(1, 1), facecolor='white')
        self.displayAxes = self.displayFigure.add_subplot(111, xscale='linear', axis_bgcolor='w')
        self.displayCanvas = FigureCanvas(self, -1, self.displayFigure)
        
        self.sizer.Add(self.displayCanvas, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=0)
        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(0)
        self.SetSizerAndFit(self.sizer)

        #self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        print "Resizing"
        print self.GetSize()
        self.SetMinSize((200, -1))
        #self.SetMaxSize((300, -1))
        print self.GetMinSize()
        print self.GetMaxSize()
        self.GetParent().mgr.GetPane("selectionPanel").MaxSize((300, -1))
        print self.GetParent().mgr.GetPane("selectionPanel").max_size 
        self.Refresh()
        event.Skip()

    def updateDisplay(self, timespan):
        print "Updating display axes."
        traceheaderTable = self.psyProject.dbTableNames['traceheader']
        stationTable = self.psyProject.dbTableNames['geom_station']
        sensorTable = self.psyProject.dbTableNames['geom_sensor']

        #orderString = getOrderString(handles);

        startTime = timespan[0].getTimeStamp()
        endTime = timespan[1].getTimeStamp()  

        query = ("SELECT stat.name as statName, "
                "sens.channel_name as chanName, "
                "concat(stat.name, '-', sens.channel_name) as label, "
                "th.begin_time as beginTime, "
                "th.begin_time + th.numsamp/th.sps as endTime "
                "FROM %s as th, %s as stat, %s as sens "
                "WHERE "
                "th.station_id = stat.id "
                "AND th.sensor_id = sens.id "
                "AND  ( (th.begin_time>=%f AND th.begin_time<%f) OR ( (th.begin_time+(th.numsamp/th.sps)) >%f AND (th.begin_time+(th.numsamp/th.sps)) <=%f)  OR ( th.begin_time<=%f AND (th.begin_time+(th.numsamp/th.sps)) >=%f) ) "
                "ORDER BY stat.name, sens.channel_name"
                ) % (traceheaderTable, stationTable, sensorTable, startTime, endTime, startTime, endTime, startTime, endTime)

        res = self.psyProject.executeQuery(query)
        #print query
        #print res
         
        self.displayAxes.clear()
        
        if(not res['isError'] and res['data']): 
            labels = [x['label'] for x in res['data']]
            set = {}
            labels = [set.setdefault(e,e) for e in labels if e not in set]
            labels.sort()
            del(set)
            
            for curData in res['data']:
                pos = labels.index(curData['label'])
                self.displayAxes.plot_date(date2num([UTCDateTime(curData['beginTime']), UTCDateTime(curData['endTime'])]), [pos, pos], linestyle='-', color='black')
            
            self.displayAxes.set_yticks(range(0,len(res['data'])+1))
            self.displayAxes.set_yticklabels([x['label'] for x in res['data']])
            self.displayAxes.set_xlim(date2num(timespan))
            self.displayAxes.figure.autofmt_xdate()
        
        self.displayAxes.figure.canvas.draw()
