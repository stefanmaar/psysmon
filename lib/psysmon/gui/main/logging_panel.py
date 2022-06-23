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

import datetime
import logging
import os
import signal
import webbrowser

import wx
import wx.lib.mixins.listctrl as listmix
from pubsub import pub

import psysmon
import psysmon.core.util as psy_util
import psysmon.gui.context_menu as psy_cm


class LoggingPanel(wx.aui.AuiNotebook):
    def __init__(self, parent=None, style=None):
        wx.aui.AuiNotebook.__init__(self, parent=parent, style=style)
        self.SetMinSize((200, 120))

        # The logger.
        self.logger = psysmon.get_logger(self)

        ## The threadId map.
        #
        # A dictionary holding the row number of the processes in the
        # processes logging area. The key is the process name.
        self.processMap = {}

        # The general logging area.
        #self.status = wx.TextCtrl(self, -1, '',
        #                            wx.DefaultPosition, wx.Size(200,100),
        #                            wx.NO_BORDER 
        #                            | wx.TE_MULTILINE
        #                            | wx.HSCROLL
        #                            | wx.TE_RICH2)

        self.status = wx.ListCtrl(self, id = wx.ID_ANY,
                                      style=wx.LC_REPORT
                                      | wx.BORDER_NONE
                                      | wx.LC_SINGLE_SEL
                                      | wx.LC_SORT_ASCENDING)
        columns = {1: 'level', 2: 'message'}
        for colNum, name in columns.items():
            self.status.InsertColumn(colNum, name)
        self.status.SetColumnWidth(0, 100)
        self.status.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        # The collection thread logging area.
        self.processes = LogProcessStatusListCtrl(self, id = wx.ID_ANY,
                                                  style = wx.LC_REPORT |
                                                  wx.BORDER_NONE |
                                                  wx.LC_SINGLE_SEL |
                                                  wx.LC_SORT_ASCENDING)
        
        columns = {1: 'start', 2: 'pid', 3: 'name', 4: 'status', 5: 'duration'}

        for colNum, name in columns.items():
            self.processes.InsertColumn(colNum, name)

        # Create the context menu of the thread logging area.
        cmData = (("view log file", self.onViewLogFile),
                  ("kill process", self.onKillProcess),
                  ("remove from display", self.onRemoveProcess))
        self.contextMenu = psy_cm.psyContextMenu(cmData)
        self.processes.Bind(wx.EVT_RIGHT_UP, self.onShowContextMenu)

        # Add the elements to the notebook.
        self.AddPage(self.status, "status")
        self.AddPage(self.processes, "processes")

        # Subscribe to the state messages of the project.
        pub.subscribe(self.onCollectionExecutionMessage, "state.collection.execution")



    def log(self, msg, levelname = None):
        item = self.status.InsertItem(0, levelname)
        self.status.SetItem(0, 1, msg)
        if levelname.lower() == 'warning':
            self.status.SetItemBackgroundColour(item, wx.Colour('orange1'))
        elif levelname.lower() == 'error' or levelname.lower() == 'critical':
            self.status.SetItemBackgroundColour(item, wx.Colour('orangered1'))

        self.status.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        n_rows = self.status.GetItemCount()
        row_limit = self.GetParent().psyBase.pref_manager.get_value('n_status_messages')
        if n_rows > row_limit:
            for k in range(row_limit, n_rows):
                self.status.DeleteItem(k)


    def onCollectionExecutionMessage(self, msg):
        #self.logger.debug('Received pubsub message: %s', msg)

        if 'started' in msg['state']:
            wx.CallAfter(self.addThread, msg)
        elif 'running' in msg['state']:
            wx.CallAfter(self.updateThread, msg)
        elif 'stopped' in msg['state']:
            wx.CallAfter(self.updateThread, msg)



    def addThread(self, data):
        # index = self.threads.GetItemCount()
        index = 0
        date_str = datetime.datetime.strftime(data['startTime'],
                                              '%Y-%m-%d %H:%M:%S')
        self.processes.InsertItem(index,
                                  date_str)
        self.processes.SetItem(index, 1, str(data['pid']))
        self.processes.SetItem(index, 2, data['procName'])
        self.processes.SetItem(index, 3, data['state'])
        self.processes.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.processes.SetColumnWidth(4, wx.LIST_AUTOSIZE)

        # The new process is added on top of the list. Add 1 to all
        # index values of the process map.
        for curKey in self.processMap.keys():
            self.processMap[curKey] += 1

        self.processMap[data['procName']] = index
        

    def updateThread(self, data):
        #self.logger.debug('updating process: %s', data['procName'])
        error_code = {1: 'general error', 2: 'collection execution error', 3: 'collection preparation error', 4: 'finalization error', 5: 'looper child error'}
        if data['procName'] in iter(self.processMap.keys()):
            curIndex = self.processMap[data['procName']]
            #self.logger.debug('process has index: %d', curIndex)
            self.processes.SetItem(curIndex, 3, data['state'])
            duration = data['curTime'] - data['startTime']
            duration -= datetime.timedelta(microseconds = duration.microseconds)
            self.processes.SetItem(curIndex, 4, str(duration))
            if data['state'].lower() == 'stopped' and data['returncode'] > 0:
                self.processes.SetItem(curIndex, 3, 'error')
                self.processes.SetItemTextColour(curIndex, wx.NamedColour('orangered1'))
                self.logger.error("Error while executing process %s: %s.\nSee the log file of the process for more details.", data['procName'], error_code[data['returncode']].upper())
            elif data['state'].lower() == 'stopped':
                self.processes.SetItemTextColour(curIndex,
                                                 wx.Colour('grey70'))

    def onShowContextMenu(self, event):
        self.PopupMenu(self.contextMenu)

    def onViewLogFile(self, event):
        selectedRow = self.processes.GetFirstSelected()
        procName = self.processes.GetItem(selectedRow, 2).GetText()
        logFile = os.path.join(self.GetParent().psyBase.project.tmpDir,
                               procName + ".log")
        self.logger.info("Showing the log file %s.", logFile)
        try:
            psy_util.display_file(logFile)
        except Exception:
            webbrowser.open(logFile)


    def onKillProcess(self, event):
        selectedRow = self.processes.GetFirstSelected()
        pid = self.processes.GetItem(selectedRow, 1).GetText()
        pid = int(pid)
        self.logger.debug('Killing process with pid %d.', pid)
        os.kill(pid, signal.SIGTERM)

    def onRemoveProcess(self, event):
        pass


class LogProcessStatusListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id, pos = wx.DefaultPosition,
                 size = wx.DefaultSize, style = 0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(3)
