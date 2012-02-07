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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
The pSysmon GUI module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the graphical user interface (GUI) of the pSysmon 
main program.
'''


import wx
import wx.aui
import wx.html
import wx.grid
import wx.lib.mixins.listctrl as listmix
from wx.lib.pubsub import Publisher as pub
import MySQLdb as mysql
import os
from psysmon.core.util import PsysmonError
from psysmon.core.util import ActionHistory, Action
from psysmon.core.waveserver import WaveServer
from datetime import datetime
import webbrowser
from wx.lib.mixins.inspection import InspectionMixin 


## The pSysmon main application.
class PSysmonApp(wx.App, InspectionMixin):
    ''' The pSysmon wxPython App class.
    '''
    ## The constructor
    #
    def __init__(self, redirect=False, filename=None,
                 useBestVisual=False, clearSigInt=True):
        wx.App.__init__(self, redirect, filename, useBestVisual,
                        clearSigInt)

    def onInit(self):
        self.Init()         # The widget inspection tool can be called using CTRL+ALT+i
        return True

## The pSysmon main GUI
#
#
class PSysmonGui(wx.Frame):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, psyBase,  parent, id=-1, title='pSysmon', pos=wx.DefaultPosition, 
                 size=(800,600), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # The pSysmon base object.
        self.psyBase = psyBase

        #self.CreateStatusBar()  # A statusbar at the bottom of the window.
        #self.buildMenu()
        self.initUI()

        self.logger = Logger(self.loggingPanel, psyBase)

        self.collectionNodeInventoryPanel.initNodeInventoryList()



    ## Define the PSysmonGui menus.  
    #
    # The pSysmon menus are created depending on the list returned.
    #
    # @param self The Object pointer.
    def menuData(self):
        return (("File",
                 ("&New project", "Create a new project.", self.onCreateNewProject),
                 ("&Open project", "Open an existing project.", self.onOpenProject),
                 ("&Close project", "Close the current project.", self.onCloseProject),
                 ("&Save project", "Save the current project.", self.onSaveProject),
                 ("", "", ""),
                 ("&Exit", "Exit pSysmon.", self.onClose)),
                ("Edit",
                 ("Create DB user", "Create a new pSysmon database user.", self.onCreateNewDbUser),
                 ("Edit waveform directories", "Edit the waveform directories.", self.onEditWaveformDir)),
                ("Help",
                 ("&About", "About pSysmon", self.onAbout))
               )

    ## Create the PSysmonGui menubar.
    #
    # This method takes the menus defined in menuData and creates the according 
    # menubar and the menus.  
    #
    # @param self The Object pointer.
    def createMenuBar(self):
        menuBar = wx.MenuBar()

        for curMenuData in self.menuData():
            menuLabel = curMenuData[0]
            menuItems = curMenuData[1:]
            menuBar.Append(self.createMenu(menuItems), menuLabel)

        self.SetMenuBar(menuBar)


    ## Create a menu.
    #
    # Create a menu base on the menuData argument.
    #
    # @param self The Object pointer.
    def createMenu(self, menuData):
        menu = wx.Menu()

        for curLabel, curStatus, curHandler in menuData:
            if not curLabel:
                menu.AppendSeparator()
                continue

            menuItem = menu.Append(wx.ID_ANY, curLabel, curStatus)
            self.Bind(wx.EVT_MENU, curHandler, menuItem)

        return menu    


    ## Build the user interface.
    #
    # @param self The object pointer.    
    def initUI(self):
        self.mgr = wx.aui.AuiManager(self)

        self.createMenuBar()

        self.collectionPanel = CollectionPanel(self, self.psyBase, size=(300, -1))
        self.collectionNodeInventoryPanel = CollectionNodeInventoryPanel(self, self.psyBase)

        self.loggingPanel = LoggingPanel(self, 
                                         style=wx.aui.AUI_NB_BOTTOM)

        # Add the collection panel.
        self.mgr.AddPane(self.collectionPanel, wx.aui.AuiPaneInfo().Name("collection").
                          Caption("collection").Left().CloseButton(False).
                          BestSize(wx.Size(300,-1)).MinSize(wx.Size(200,-1)))

        # Add the module inventory panel.
        self.mgr.AddPane(self.collectionNodeInventoryPanel, wx.aui.AuiPaneInfo().Name("module inventory").
                          Caption("collection node inventory").CenterPane())

        # Add the logging panel.
        self.mgr.AddPane(self.loggingPanel, wx.aui.AuiPaneInfo().Name("log area").
                          Caption("log area").Bottom().CloseButton(False).
                          BestSize(wx.Size(300, 200)))

        # Disable the panels Disable the panels..
        self.enableGuiElements(False)

        # Create the status bar.
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -3])
        self.statusbar.SetStatusText("Ready", 0)
        self.statusbar.SetStatusText("pSysmon is there for you!", 1)

        # tell the manager to 'commit' all the changes just made
        self.mgr.Update()

        # Event Bindings
        self.Bind(wx.EVT_CLOSE, self.onClose)

        # Message subscriptions
        pub.subscribe(self.onCollectionNodeListCtrlMsg, 'collectionNodeListCtrl')
        #pub.subscribe(self.onCreateNewDbUserDlgMsg, 'createNewDbUserDlg')



    # DEFINE THE EVENT HANDLER METHODS.   

    ## Open project menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onOpenProject(self, event):
        '''
        Open project menu callback.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.gui.PSysmonGui`
        :param event: The menu event.
        :type event: :class:`wx.EVT_MENU`
        '''
        # If a project is open, close it.
        if self.psyBase.project:
            print "closing project"
            self.closeProject()

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard="pSysmon project (*.ppr)|*.ppr|"\
                     "All files (*.*)|*.*",
            style=wx.OPEN | wx.CHANGE_DIR
            )

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            path = dlg.GetPath()
            self.psyBase.loadPsysmonProject(path)

            # Quest for the user and the database password.
            dlg = ProjectLoginDlg()
            dlg.ShowModal()
            userData = dlg.userData
            userSet = self.psyBase.project.setActiveUser(userData['user'], userData['pwd'])

            if not userSet:
                self.psyBase.project = ""
                msg = "No valid user found. Project not loaded."
                dlg = wx.MessageDialog(None, msg, 
                                       "pSysmon runtime error.",
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()

            else:
                # Load the current database structure.
                self.psyBase.project.loadDatabaseStructure(self.psyBase.packageMgr.packages)

                # Load the waveform directories.
                self.psyBase.project.loadWaveformDirList()

                # The project waveserver.
                self.psyBase.project.waveserver = WaveServer('sqlDB', self.psyBase.project)

                # Check if the database tables have to be updated.
                self.psyBase.project.checkDbVersions(self.psyBase.packageMgr.packages)

                # Update the collection panel display.
                self.collectionPanel.refreshCollection()

                # Activate the user interfaces.
                self.enableGuiElements()

                # Set the loaded project name as the title.
                self.SetTitle(self.psyBase.project.name)

                # Set the status message.
                statusString = "Loaded project %s successfully." % self.psyBase.project.name
                self.psyBase.project.log('status', statusString)

        # Destroy the dialog. 
        dlg.Destroy()


    ## Save project menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onSaveProject(self, event):
        if not self.psyBase.project:
            msg = "No project found. Create or load a project first."
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
        else:
            self.psyBase.project.save()


    def onCloseProject(self, event):
        '''
        Close the current project.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.gui.PSysmon.Gui`
        :param event: The wxPython event.
        :type event: :class:`wx.EVT_MENU`
        '''
        if not self.psyBase.project:
            msg = "No project found. Create or load a project first."
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
        else:
            self.closeProject()

    ## Close menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onClose(self, event):
        # deinitialize the frame manager
        self.mgr.UnInit()
        # delete the frame
        self.Destroy()


    ## About menu button callback.
    #
    # @param self The Object pointer.
    # @param event The event object.       
    def onAbout(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "I love pSysmon so damn much!", "About pSysmon", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()



    def closeProject(self):
        '''
        Close the currently active project.

        :param self: The object pointer.
        :type self: :class:`psysmon.core.gui.PSysmonGui`
        '''
        self.SetTitle('pSysmon - no project loaded')
        self.enableGuiElements(False)
        msgString = "Closed project %s." % self.psyBase.project.name
        self.psyBase.closePsysmonProject()
        self.collectionPanel.refreshCollection()
        self.log('status', msgString)


    ## Enable of disable the main GUI elements.
    #
    #
    def enableGuiElements(self, state=True):
        if(state):
            self.collectionPanel.Enable()
            self.collectionNodeInventoryPanel.Enable()
            self.loggingPanel.Enable()
        else:
            self.collectionPanel.Disable()
            self.collectionNodeInventoryPanel.Disable()
            self.loggingPanel.Disable()

    ## Create new db user menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.  
    def onCreateNewDbUser(self, event):
        dlg = CreateNewDbUserDlg(parent=self, psyBase=self.psyBase)
        dlg.ShowModal()
        dlg.Destroy()


    def onEditWaveformDir(self, event):
        ''' The edit waveform directories callback.

        Parameters
        ----------
        event : 
            The event passed to the callback.
        '''
        if self.psyBase.project:
            dlg = EditWaveformDirDlg(parent=self, psyBase=self.psyBase)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.log('warning', 'You have to open a project to edit the waveform directories.')


    ## Create new project menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onCreateNewProject(self, event):
        dlg = CreateNewProjectDlg(psyBase=self.psyBase)
        dlg.ShowModal()
        #dlg.Destroy()

    def log(self, msgType, msg):
        '''
        Send a log message.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.gui.PSysmonGui`
        :param msgType: The type of the message (status, warning, error).
        :type msgType: String
        '''
        msgTopic = "log.general." + msgType
        pub.sendMessage(msgTopic, msg)


    # DEFINE THE MESSAGE LISTENERS

    ## Listen to messages from the collectionNodeListCtrl.
    #
    # @param self The object pointer.
    # @param msg The message object.     
    def onCollectionNodeListCtrlMsg(self, msg):
        print("msg.topic: ", msg.topic)
        if msg.topic == ('collectionNodeListCtrl', 'addSelectedNode'):
            print "Got message - Adding node ", self.selectedCollectionNodeTemplate.name, " to the collection."
        else:
            print "Unknown topic."



class Logger:

    def __init__(self, loggingArea, psyBase):
        self.loggingArea = loggingArea
        self.psyBase = psyBase

        # Subscribe to logging messages.
        pub.subscribe(self.logGeneral, "log.general")
        pub.subscribe(self.logCollectionNode, "log.collectionNode")

        # Subscribe to project state messages.
        pub.subscribe(self.onCollectionExecutionMessage, "state.collection.execution")



    def logGeneral(self, msg):
        curTime = datetime.now()
        timeStampString = datetime.strftime(curTime, '%Y-%m-%d %H:%M:%S')

        if 'error' in msg.topic:
            modeString = '[ERR] '
        elif 'warning' in msg.topic:
            modeString = '[WRN] '
        else:
            modeString = ' '

        msgString = msg.data.rstrip()
        msgString = timeStampString + ">>" + modeString + msgString + "\n"

        self.loggingArea.status.AppendText(msgString)


    def logCollectionNode(self, msg):
        curTime = datetime.now()
        timeStampString = datetime.strftime(curTime, '%Y-%m-%d %H:%M:%S')

        if 'error' in msg.topic:
            modeString = '[ERR] '
        elif 'warning' in msg.topic:
            modeString = '[WRN] '
        else:
            modeString = ' '

        msgString = msg.data.rstrip()
        msgString = timeStampString + "NODE>>" + modeString + msgString + "\n"

        with self.psyBase.project.threadMutex:
            self.loggingArea.status.AppendText(msgString)


    def onCollectionExecutionMessage(self, msg):
        data = msg.data

        if 'starting' in data['state']:
            self.loggingArea.addThread(data)
        elif 'running' in data['state']:
            self.loggingArea.updateThread(data)
        elif 'finished' in data['state']:
            self.loggingArea.updateThread(data)



## The collection listbox.
#       
class CollectionListBox(wx.SimpleHtmlListBox):

    ## The constructor
    #
    # @param self The object pointer. 
    def __init__(self, parent, id=wx.ID_ANY):
        wx.SimpleHtmlListBox.__init__(self, parent=parent, id=id)
        cmData = (("edit node", parent.onEditNode),
                  ("remove node", parent.onRemoveNode),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)
        self.Bind(wx.html.EVT_HTML_CELL_CLICKED, self.onItemRightClicked)


    ## Show the context menu.
    #    
    def onShowContextMenu(self, event):
        if not self.Parent.psyBase.project:
            return

        try:
            selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.GetSelection())
            if(selectedNode.mode == 'standalone'):
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'execute node')
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            elif(selectedNode.mode == 'uneditable'):
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'uneditable')
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            else:
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'edit node')
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
        except PsysmonError as e:
            pass


        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)

    def onItemRightClicked(self, event):
        print "Item right clicked."


class CollectionListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        cmData = (("edit node", parent.onEditNode),
                  ("remove node", parent.onRemoveNode),
                  ("separator", None),
                  ("load collection", parent.onCollectionLoad),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)




## The collection panel.
#        
class CollectionPanel(wx.Panel):

    ## The constructor.
    #
    # @param self The object pointer.
    # @param parent The parent object holding the panel.
    def __init__(self, parent, psyBase, size):
        wx.Panel.__init__(self, parent=parent, size=size, id=wx.ID_ANY)
        self.psyBase = psyBase

        self.SetBackgroundColour((255, 255, 255))

        self.collectionListCtrl = CollectionListCtrl(self, id=wx.ID_ANY,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_SORT_ASCENDING
                                 | wx.LC_SINGLE_SEL
                                 | wx.LC_NO_HEADER
                                 )

        columns = {1: 'node'}

        for colNum, name in columns.iteritems():
            self.collectionListCtrl.InsertColumn(colNum, name)

        sizer = wx.GridBagSizer(5, 5)
        sizer.Add(self.collectionListCtrl, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=0)

        self.executeButton = wx.Button(self, 10, "execute", (20, 20))
        sizer.Add(self.executeButton, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=2)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(1)
        self.SetSizerAndFit(sizer)


        # Bind the events
        self.Bind(wx.EVT_BUTTON, self.onExecuteCollection)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCollectionNodeItemSelected)

        self.selectedCollectionNodeIndex = -1


    # DEFINE THE CONTEXT MENU EVENT HANDLER.

    # Execute collection button callback.
    #
    # @param self The object pointer.
    # @param event The event object.  
    def onExecuteCollection(self, event): 
        self.psyBase.project.executeCollection()

    # Remove node context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onRemoveNode(self, event):
        try:
            print "Removing node at index %d." % self.selectedCollectionNodeIndex
            self.psyBase.project.removeNodeFromCollection(self.selectedCollectionNodeIndex)
            self.refreshCollection()
        except PsysmonError as e:
            msg = "Cannot remove the collection node:\n %s" % e
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal() 


    ## Edit node context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onEditNode(self, event):
        try:
            selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            if(selectedNode.mode == 'standalone'):
                print "in standalone"
                self.psyBase.project.executeNode(self.selectedCollectionNodeIndex)
            else:
                self.psyBase.project.editNode(self.selectedCollectionNodeIndex)
        except PsysmonError as e:
            msg = "Cannot edit the node:\n %s" % e
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal() 


    ## Select node item callback.
    #
    # This method responds to events raised by selecting a collection node in 
    # the collectionPanel.collectionListCtrl.
    #
    # @param self The object pointer.
    # @param event The event object.    
    def onCollectionNodeItemSelected(self, evt):
        print "Selected node in collection."
        self.selectedCollectionNodeIndex = evt.GetIndex()


    # Load a collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onCollectionLoad(self, event):
        collections = self.psyBase.project.getCollection()
        choices = [x.name for x in collections.itervalues()]
        dlg = wx.SingleChoiceDialog(None, "Select a collection", 
                                    "Load collection", 
                                    choices)
        if dlg.ShowModal() == wx.ID_OK:
            self.psyBase.project.setActiveCollection(dlg.GetStringSelection())
            self.refreshCollection()   
        dlg.Destroy()


    # Add new collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onCollectionNew(self, event):
        colName = wx.GetTextFromUser('collection name', caption='New collection', 
                                     default_value="", parent=None)

        if not colName:
            return
        else:
            self.psyBase.project.addCollection(colName)
            self.refreshCollection()


    # Delete a collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onCollectionDelete(self, event):
        print("Delete a collection")



    def refreshCollection(self):
        '''
        Refresh the collection nodes displayed in the collection listbox.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.gui.CollectionPanel`
        '''
        if not self.psyBase.project:
            self.collectionListCtrl.DeleteAllItems()
            return 

        activeCollection = self.psyBase.project.getActiveCollection()
        if activeCollection:
            auiPane = self.GetParent().mgr.GetPane('collection')
            auiPane.Caption(activeCollection.name)
            self.GetParent().mgr.Update()

            self.collectionListCtrl.DeleteAllItems()
            for k, curNode in enumerate(activeCollection.nodes):
                self.collectionListCtrl.InsertStringItem(k, curNode.name)


class NodeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        cmData = (("add", parent.onCollectionNodeAdd),
                  ("help", parent.onCollectionNodeHelp))

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)



class LoggingPanel(wx.aui.AuiNotebook):
    def __init__(self, parent=None, style=None):
        wx.aui.AuiNotebook.__init__(self, parent=parent, style=style)
        self.SetMinSize((200, 120))

        ## The threadId map.
        #
        # A dictionary holding the row number of the threads in the threads logging
        # area. The key is the thread ID.
        self.threadMap = {}

        # The general logging area.
        self.status = wx.TextCtrl(self, -1, '',
                                    wx.DefaultPosition, wx.Size(200,100),
                                    wx.NO_BORDER 
                                    | wx.TE_MULTILINE
                                    | wx.HSCROLL)

        # The collection thread logging area.
        self.threads = wx.ListCtrl(self, id=wx.ID_ANY,
                                      style=wx.LC_REPORT 
                                      | wx.BORDER_NONE
                                      | wx.LC_SINGLE_SEL
                                      | wx.LC_SORT_ASCENDING
                                      )

        columns = {1: 'start', 2: 'id', 3: 'status', 4: 'duration'}

        for colNum, name in columns.iteritems():
            self.threads.InsertColumn(colNum, name)

        # Create the context menu of the thread logging area.
        cmData = (("view log file", self.onViewLogFile),
                  ("remove", self.onRemoveThread))
        self.contextMenu = psyContextMenu(cmData)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

        # Add the elements to the notebook.
        self.AddPage(self.status, "status")
        self.AddPage(self.threads, "threads")


    def addThread(self, data):
        print data
        #index = self.threads.GetItemCount()
        index = 0
        self.threads.InsertStringItem(index, datetime.strftime(data['startTime'], '%Y-%m-%d %H:%M:%S'))
        self.threads.SetStringItem(index, 1, data['procId'])
        self.threads.SetStringItem(index, 2, data['state'])
        self.threadMap[data['procId']] = index

    def updateThread(self, data):
        if data['procId'] in self.threadMap.keys():
            curIndex = self.threadMap[data['procId']]
            self.threads.SetStringItem(curIndex, 1, data['procId'])
            self.threads.SetStringItem(curIndex, 2, data['state'])

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)

    def onViewLogFile(self, event):
        selectedRow = self.threads.GetFirstSelected()
        threadId = self.threads.GetItem(selectedRow, 1).GetText()
        logFile = os.path.join(self.GetParent().psyBase.project.tmpDir, threadId + ".log")
        webbrowser.open(logFile)
        print "Showing the log file %s." % logFile

    def onRemoveThread(self, event):
        pass


class CollectionNodeInventoryPanel(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent, psyBase):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.itemDataMap = {}

        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        self.psyBase = psyBase
        self.collectionPanel = parent.collectionPanel

        self.SetBackgroundColour((255, 255, 255))

        sizer = wx.GridBagSizer(5, 5)

        self.searchButton = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        self.searchButton.SetDescriptiveText('Search collection nodes')
        self.searchButton.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancelSearch, self.searchButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onDoSearch, self.searchButton)
        sizer.Add(self.searchButton, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)

        self.nodeListCtrl = NodeListCtrl(self, id=wx.ID_ANY,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_SINGLE_SEL
                                 | wx.LC_SORT_ASCENDING
                                 )

        self.nodeListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


        columns = {1: 'name', 2: 'mode', 3: 'category', 4: 'tags'}

        for colNum, name in columns.iteritems():
            self.nodeListCtrl.InsertColumn(colNum, name)

        sizer.Add(self.nodeListCtrl, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=0)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(1)

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCollectionNodeItemSelected)



    ## Select node item callback.
    #
    # This method responds to events raised by selecting a collection node in 
    # the collectionNodeInventoryPanel.nodeListCtrl .
    #
    # @param self The object pointer.
    # @param event The event object.    
    def onCollectionNodeItemSelected(self, evt):
        item = evt.GetItem()
        print "Selected item: ", item.GetText()
        self.selectedCollectionNodeTemplate = self.psyBase.packageMgr.getCollectionNodeTemplate(item.GetText())


    def onDoSearch(self, evt):
        foundNodes = self.psyBase.packageMgr.searchCollectionNodeTemplates(self.searchButton.GetValue())
        self.updateNodeInvenotryList(foundNodes)
        print foundNodes

    def onCancelSearch(self, evt):
        self.initNodeInventoryList()
        self.searchButton.SetValue(self.searchButton.GetDescriptiveText())



    def onCollectionNodeAdd(self, event):
        msg =  "Adding node template to collection: " + self.selectedCollectionNodeTemplate.name
        pub.sendMessage("log.general.status", msg)

        try:
            pos = self.collectionPanel.selectedCollectionNodeIndex
            if pos != -1:
                pos += 1    # Add after the selected node in the collection.
            print pos
            self.psyBase.project.addNode2Collection(self.selectedCollectionNodeTemplate, pos)
            self.collectionPanel.refreshCollection()
        except PsysmonError:
            msg = "No collection found. Create one first."
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()    

    ## Show the node's online help file.
    # 
    # Each collection node should provide a html formatted help file. This 
    # file can be shown using the collection node inventory context menu.
    def onCollectionNodeHelp(self, event):
        docFile = self.selectedCollectionNodeTemplate.docEntryPoint
        docDir = self.selectedCollectionNodeTemplate.parentPackage.docDir

        if docFile and docDir:
            docFile = os.path.join(docDir, docFile)

            if os.path.isfile(docFile):
                webbrowser.open(docFile)
            else:
                msg =  "No documentation found for node %s " % self.selectedCollectionNodeTemplate.name
                pub.sendMessage("log.general.status", msg)
        else:
            msg =  "No documentation found for node %s " % self.selectedCollectionNodeTemplate.name
            pub.sendMessage("log.general.status", msg)



    def initNodeInventoryList(self):
        nodeTemplates = {}
        for curPkg in self.psyBase.packageMgr.packages.itervalues():
            nodeTemplates.update(curPkg.collectionNodeTemplates)

        self.updateNodeInvenotryList(nodeTemplates)
        listmix.ColumnSorterMixin.__init__(self, 4)


    def updateNodeInvenotryList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates.itervalues():
            self.nodeListCtrl.InsertStringItem(index, curNode.name)
            self.nodeListCtrl.SetStringItem(index, 1, curNode.mode)
            self.nodeListCtrl.SetStringItem(index, 2, curNode.category)
            self.nodeListCtrl.SetStringItem(index, 3, ', '.join(curNode.tags))
            self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
            self.nodeListCtrl.SetItemData(index, index)
            index += 1

    def GetListCtrl(self):
        return self.nodeListCtrl

    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)


class psyContextMenu(wx.Menu):

        def __init__(self, cmData):
            wx.Menu.__init__(self)

            for cmLabel, cmHandler in cmData:
                if cmLabel.lower() == "separator":
                    self.AppendSeparator()
                else:
                    item = self.Append(-1, cmLabel)
                    self.Bind(wx.EVT_MENU, cmHandler, item)



## The create new db user dialog window.
#
# This window is used to get the parameters needed to create a new pSysmon 
# database user.
class CreateNewDbUserDlg(wx.Dialog):

    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, psyBase, parent=None, size=(300, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new DB user", size=size)

        self.psyBase = psyBase

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {};
        self.edit = {};

        sizer.Add(self.createDialogFields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Add the validators.
        self.edit['rootUser'].SetValidator(NotEmptyValidator())         # Not empty.
        self.edit['mysqlHost'].SetValidator(NotEmptyValidator())        # Not empty.
        self.edit['userName'].SetValidator(NotEmptyValidator())         # Not empty.
        self.edit['retypeUserPwd'].SetValidator(IsEqualValidator(self.edit['userPwd']))     # Equal to userPwd.


        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def onOk(self, event):
        isValid = self.Validate()

        if(isValid):
            userData = {};
            for _, curKey, _ in self.dialogData():
                userData[curKey] = self.edit[curKey].GetValue()

            userCreated = self.createUser(userData)
            #pub.sendMessage("createNewDbUserDlg.createUser", userData)
            if(userCreated):
                # Set the status message.
                statusString = "Created the user %s successfully." % userData['userName']
                self.GetParent().log('status', statusString)

                # Close the dialog.
                self.Destroy()

            else:
                # Set the status message.
                statusString = "Error while creating the user %s." % userData['userName']
                if not self.GetParent():
                    print "NO PARENT"
                else:
                    self.GetParent().log('status', statusString)



    def dialogData(self):
        return(("root user:", "rootUser", wx.TE_RIGHT),
               ("root pwd:", "rootPwd", wx.TE_PASSWORD|wx.TE_RIGHT),
               ("mysql host:", "mysqlHost", wx.TE_RIGHT),
               ("username:", "userName", wx.TE_RIGHT),
               ("user pwd:", "userPwd", wx.TE_PASSWORD|wx.TE_RIGHT),
               ("retype user pwd:", "retypeUserPwd", wx.TE_PASSWORD|wx.TE_RIGHT)
               )

    def createDialogFields(self):
        dialogData = self.dialogData()
        fgSizer = wx.FlexGridSizer(len(dialogData), 2, 5, 5)

        for curLabel, curKey, curStyle in dialogData:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(200, -1), 
                                            style=curStyle)

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer



    def createUser(self, userData):

        try:
            self.psyBase.createPsysmonDbUser(userData['rootUser'],
                                             userData['rootPwd'], 
                                             userData['mysqlHost'],
                                             userData['userName'],
                                             userData['userPwd'])
            return True
        except mysql.Error, e:
            msg = "An error occured when trying to create the pSysmon database user:\n%s" % e
            dlg = wx.MessageDialog(None, msg, 
                                   "MySQL database error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return False


class EditWaveformDirDlg(wx.Dialog):
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
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Edit the waveform directories", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=size)

        self.psyBase = psyBase

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Create the grid editing buttons.
        addDirButton = wx.Button(self, wx.ID_ANY, "add")
        removeDirButton = wx.Button(self, wx.ID_ANY, "remove")
        undoButton = wx.Button(self, wx.ID_ANY, "undo")

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)
        gridButtonSizer = wx.BoxSizer(wx.VERTICAL)

        # Fill the grid button sizer
        gridButtonSizer.Add(addDirButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(removeDirButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(undoButton, 0, wx.EXPAND|wx.ALL)

        fields = self.getGridColumns()
        self.wfGrid = wx.grid.Grid(self)
        self.wfGrid.CreateGrid(1, len(fields))

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)
        for k, (name, label, attr) in enumerate(fields):
            self.wfGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.wfGrid.SetColAttr(k, roAttr)

        self.wfGrid.AutoSizeColumns()
        self.initWfTable()
        sizer.Add(self.wfGrid, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)

        sizer.Add(gridButtonSizer, pos=(0,1), flag=wx.EXPAND|wx.ALL, border=5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onAddDirectory, addDirButton)
        self.Bind(wx.EVT_BUTTON, self.onRemoveDirectory, removeDirButton)
        self.Bind(wx.EVT_BUTTON, self.onUndo, undoButton)
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)

        self.wfDir = self.psyBase.project.dbTables['waveformDir']
        self.wfDirAlias = self.psyBase.project.dbTables['waveformDirAlias']

        # A list of available waveform directories. It consits of tuples of
        # wfDirTable and wfDirAliasTable instances.
        self.wfDirList = []

        self.dbSession = self.psyBase.project.getDbSession()

        self.history = ActionHistory(attrMap = {}, 
                                     actionTypes = []
                                     ) 

    def onUndo(self, event):
        ''' Undo the last recorded action.

        '''
        self.history.undo()


    def onAddDirectory(self, event):
        ''' The add directory callback.

        Show a directory browse dialog.
        If a directory has been selected, call to insert the directory 
        into the database.
        '''
        # In this case we include a "New directory" button. 
        dlg = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            self.psyBase.project.log('status', 'You selected: %s\n' % dlg.GetPath())

            newWfDir = self.wfDir(dlg.GetPath(), '')
            newAlias = self.wfDirAlias(self.psyBase.project.activeUser.name,
                                            dlg.GetPath())
            newWfDir.aliases.append(newAlias)

            self.dbSession.add(newWfDir)
            #self.dbSession.add(newWfDirAlias)

            self.wfDirList.append(newWfDir)

            rowNumber = 1
            action = Action(style='METHOD',
                            affectedObject=None,
                            dataBefore=None,
                            dataAfter=None,
                            undoMethod=self.removeDirectory,
                            undoParameters=rowNumber
                            )
            self.history.do(action)

        # Only destroy a dialog after you're done with it.
        dlg.Destroy() 



    def onRemoveDirectory(self, event):
        ''' The remove directory callback.
        '''
        pass


    def removeDirectory(self, rowNumber):
        ''' Remove the directory at row *rowNumber*

        '''
        self.psyBase.project.log('status', 'Removing row number %d' % rowNumber)



    def initWfTable(self):
        ''' Initialize the waveformDir table with values.

        '''
        for k, curDir in enumerate(self.psyBase.project.waveformDirList):
            self.wfGrid.SetCellValue(k, 0, str(curDir['id']))
            self.wfGrid.SetCellValue(k, 1, curDir['dir'])
            self.wfGrid.SetCellValue(k, 2, curDir['dirAlias'])
            self.wfGrid.SetCellValue(k, 3, curDir['description'])


    def getGridColumns(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('origDir', 'original directory', 'readonly'))
        tableField.append(('alias', 'alias', 'editable'))
        tableField.append(('description', 'description', 'editable'))
        return tableField


    def onOk(self, event):
        print("Commiting the session:")
        self.dbSession.commit()
        self.Destroy()




## The create a new project dialog window.
#
# This window is used to get the parameters needed to create a new pSysmon 
# project.
class CreateNewProjectDlg(wx.Dialog):

    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, psyBase, parent=None, size=(500, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new project", 
                           size=size, 
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.psyBase = psyBase

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {};
        self.edit = {};

        sizer.Add(self.createDialogFields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Add some default values.
        self.edit['dbHost'].SetValue('localhost')

        # Add the validators.
        self.edit['name'].SetValidator(NotEmptyValidator())         # Not empty.
        self.edit['baseDir'].SetValidator(NotEmptyValidator())         # Not empty.
        self.edit['dbHost'].SetValidator(NotEmptyValidator())        # Not empty.
        self.edit['user'].SetValidator(NotEmptyValidator())        # Not empty.
        #self.edit['userPwd'].SetValidator(NotEmptyValidator())        # Not empty.

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)

    def onBaseDirBrowse(self, event):

        # Create the directory dialog.
        dlg = wx.DirDialog(self, message="Choose a directory:",
                           defaultPath=self.edit['baseDir'].GetValue(),
                           style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # Get the selected directory
        if dlg.ShowModal() == wx.ID_OK:
            self.edit['baseDir'].SetValue(dlg.GetPath())

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

    def onOk(self, event):  
        isValid = self.Validate()

        if(isValid):
            projectData = {};
            for _, curKey, _, _, _ in self.dialogData():
                projectData[curKey] = self.edit[curKey].GetValue()

            projectCreated = self.createProject(projectData)
            #pub.sendMessage("createNewDbUserDlg.createUser", userData)
            if(projectCreated):
                self.GetParent().enableGuiElements()
                self.Destroy()



    def dialogData(self):
        return(("name:", "name", wx.TE_RIGHT, False, ""),
               ("base directory:", "baseDir", wx.TE_LEFT, True, self.onBaseDirBrowse),
               ("database host:", "dbHost", wx.TE_RIGHT, False, ""),
               ("user:", "user", wx.TE_RIGHT, False, ""),
               ("user pwd:", "userPwd", wx.TE_PASSWORD|wx.TE_RIGHT, False, "")
               )

    def createDialogFields(self):
        dialogData = self.dialogData()
        gbSizer = wx.GridBagSizer(5, 5)
        rowCount = 0

        for curLabel, curKey, curStyle, hasBrowseBtn, curBtnHandler in dialogData:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(300, -1), 
                                            style=curStyle)

            if(hasBrowseBtn):
                browseButton = wx.Button(self, wx.ID_ANY, "browse", (50,-1))
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0), 
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1), 
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL)
                gbSizer.Add(browseButton, pos=(rowCount, 2), 
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL)

                self.Bind(wx.EVT_BUTTON, curBtnHandler, browseButton)
            else:
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

            rowCount += 1

        return gbSizer


    ## Create a new pSysmon project.
    def createProject(self, projectData):

        try:
            self.psyBase.createPsysmonProject(**projectData)
            return True
        except Exception as e:
            print "Error while creating the project: %s" % e
            raise
            return False  



## A dialog field validator which doesn't allow empty field values.
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



## A dialog field validator which checks for field entry equality.
#
# This validator can be used to check if the value entered in the field is 
# equal to another one. It's useful when checking for the correct typing of new
# passwords.    
class IsEqualValidator(wx.PyValidator):

    ## The constructor.
    #
    # @param self The object pointer.
    # @param ctrl2Compare A wx control to which the value of the validated field should be compared.
    def __init__(self, ctrl2Compare):
        wx.PyValidator.__init__(self)

        ## The control to which the field to be validated should be compared to.
        self.ctrl2Compare = ctrl2Compare

    ## The default clone method.    
    def Clone(self):
        return IsEqualValidator(self.ctrl2Compare)

    ## The method run when validating the field.
    #
    # This method checks whether the values entered in the two controls are equal
    # or not. 
    # @param self The object pointer.
    def Validate(self, win):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()
        value2Compare = self.ctrl2Compare.GetValue()

        if value != value2Compare:
            wx.MessageBox("The two passwords don't match!", "Error")
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



class ProjectLoginDlg(wx.Dialog):

    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, size=(300, 200)):
        wx.Dialog.__init__(self, None, wx.ID_ANY, "Project login", size=size)

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {};
        self.edit = {};

        sizer.Add(self.createDialogFields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.edit['user'].SetFocus()

        # Add the validators.
        self.edit['user'].SetValidator(NotEmptyValidator())         # Not empty.        

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def onOk(self, event):  
        isValid = self.Validate()

        if(isValid):
            self.userData = {};
            for _, curKey, _ in self.dialogData():
                self.userData[curKey] = self.edit[curKey].GetValue()
                self.Destroy()


    def dialogData(self):
        return(
               ("user:", "user", wx.TE_RIGHT),
               ("password:", "pwd", wx.TE_PASSWORD|wx.TE_RIGHT),
              )

    def createDialogFields(self):
        dialogData = self.dialogData()
        fgSizer = wx.FlexGridSizer(len(dialogData), 2, 5, 5)

        for curLabel, curKey, curStyle in dialogData:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(200, -1), 
                                            style=curStyle)

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer




