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


import logging
from operator import attrgetter

import wx
import wx.aui
import wx.html
import wx.grid
from wx import Choicebook
from operator import itemgetter
import wx.lib.mixins.listctrl as listmix
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub
import wx.lib.colourdb
try:
    from agw import ribbon as ribbon
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.ribbon as ribbon
import os
import signal
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy
import psysmon
import psysmon.core.gui_view
from psysmon.core.error import PsysmonError
from psysmon.core.waveclient import PsysmonDbWaveClient, EarthwormWaveclient
from psysmon.artwork.icons import iconsBlack10, iconsBlack16
import datetime
import webbrowser
#from wx.lib.mixins.inspection import InspectionMixin
import wx.lib.mixins.inspection as wit
import wx.lib.scrolledpanel as scrolled
from wx.lib.splitter import MultiSplitterWindow
import wx.lib.platebtn as platebtn

from psysmon.core.gui_preference_dialog import ListbookPrefDialog

try:
    from agw import advancedsplash as splash
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.advancedsplash as splash


## The pSysmon main application.
class PSysmonApp(wx.App, wit.InspectionMixin):
    ''' The pSysmon wxPython App class.
    '''
    ## The constructor
    #
    #def __init__(self, redirect=False, filename=None,
    #             useBestVisual=False, clearSigInt=True):
    #    wx.App.__init__(self, redirect, filename, useBestVisual,
    #                    clearSigInt)

    def OnInit(self):
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

        wx.lib.colourdb.updateColourDB()

        bitmapDir = os.path.join(psyBase.baseDirectory, 'artwork', 'splash')
        pn = os.path.normpath(os.path.join(bitmapDir, "psysmon.png"))
        bitmap = wx.Bitmap(pn, wx.BITMAP_TYPE_PNG)

        frame = splash.AdvancedSplash(self, bitmap=bitmap, timeout=1000,
                                      agwStyle=splash.AS_TIMEOUT |
                                      splash.AS_CENTER_ON_SCREEN)


        # The pSysmon base object.
        self.psyBase = psyBase

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        #self.CreateStatusBar()  # A statusbar at the bottom of the window.
        #self.buildMenu()
        self.initUI()

        self.collectionNodeInventoryPanel.initNodeInventoryList()

        # Load new colour names into the colour database.
        wx.lib.colourdb.updateColourDB()


    def save_config(self):
        ''' Save the configuration data to the config file.
        '''
        import json
        import platform
        if platform.system() == 'Linux':
            config_dir = os.path.join(os.path.expanduser('~'), '.config', 'psysmon')
            if not os.path.exists(config_dir):
                os.mkdir(config_dir)
            config_file = os.path.join(config_dir, 'psysmon.cfg')
            config = {}
            config['recent_files'] = [self.filehistory.GetHistoryFile(x) for x in range(self.filehistory.GetCount())]
            config['pref_manager'] = self.psyBase.pref_manager
            try:
                fp = open(config_file, mode = 'w')
                json.dump(config, fp = fp, cls = psysmon.core.json_util.ConfigFileEncoder)
                fp.close()
            except:
                pass




    ## Define the PSysmonGui menus.  
    #
    # The pSysmon menus are created depending on the list returned.
    #
    # @param self The Object pointer.
    def menuData(self):
        return (("File",
                 ("&New project", "Create a new project.", self.onCreateNewProject, True, False, None),
                 ("&Open project", "Open an existing project.", self.onOpenProject, True, False, None),
                 ("Open recent", "Open a recent project.", None, True, True, ()),
                 ("&Close project", "Close the current project.", self.onCloseProject, False, False, None),
                 ("&Save project", "Save the current project.", self.onSaveProject, False, False, None),
                 ("", "", "", True, False, None),
                 ("&Exit", "Exit pSysmon.", self.onClose, True, False, None)),
                ("Edit",
                 ("Create DB user", "Create a new pSysmon database user.", self.onCreateNewDbUser, True, False, None),
                 ("psysmon preferences", "The preferences of the psysmon program.", self.onPsysmonPreferences, True, False, None)),
                ("Project",
                 ("Data sources", "Edit the data sources of the project.", self.onEditDataSources, False, False, None),
                 ("SCNL data sources", "Edit the data sources of the SCNLs in the inventory.", self.onEditScnlDataSources, False, False, None),
                 ("", "", "", True, False, None),
                 ("Project preferences","Edit the project preferences", self.onEditProjectPreferences, False, False, None)),
                ("Help",
                 ("&Help", "psysmon help", self.onHelp, True, False, None),
                 ("&About", "About pSysmon", self.onAbout, True, False, None))
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

        for curLabel, curStatus, curHandler, editable, is_submenu, submenu_data in menuData:
            if not curLabel:
                menu.AppendSeparator()
                continue
            elif is_submenu:
                cur_sub_menu = self.createMenu(submenu_data)
                menuItem = menu.AppendMenu(wx.ID_ANY, curLabel, cur_sub_menu)
                # Add the filehistory to the menu.
                if curLabel.lower() == 'open recent':
                    self.filehistory = wx.FileHistory()
                    self.filehistory.UseMenu(cur_sub_menu)
                    self.Bind(wx.EVT_MENU_RANGE, self.onOpenRecentProject, id=wx.ID_FILE1, id2=wx.ID_FILE9)

            else:
                menuItem = menu.Append(wx.ID_ANY, curLabel, curStatus)
            menuItem.Enable(editable)
            self.Bind(wx.EVT_MENU, curHandler, menuItem)

        return menu


    ## Build the user interface.
    #
    # @param self The object pointer.    
    def initUI(self):
        self.mgr = wx.aui.AuiManager(self)

        self.createMenuBar()

        # Add the file history to the File menu.
        if False:
            self.filehistory = wx.FileHistory()
            menubar = self.GetMenuBar()
            menus = menubar.GetMenus()
            tmp = [x[0] for x in menus if x[1] == 'File']
            if len(tmp) == 1:
                tmp = tmp[0]
                recent_menu = [x for x in tmp.GetMenuItems() if x.GetLabel().lower() == "open recent"]
                if len(recent_menu) == 1:
                    recent_menu = recent_menu[0]
                    self.filehistory.UseMenu(recent_menu.GetMenu())
                else:
                    self.logger.error("No open recent menu found. Couldn't add the filehistory.")

            else:
                self.logger.error("No File menu found. Couldn't add the filehistory.")

        self.collectionPanel = CollectionPanel(self, self.psyBase, size=(300, -1))
        self.collectionNodeInventoryPanel = CollectionNodeInventoryPanel(self, self.psyBase)

        self.loggingPanel = LoggingPanel(self, 
                                         style=wx.aui.AUI_NB_BOTTOM)

        # Add the collection panel.
        self.mgr.AddPane(self.collectionPanel, wx.aui.AuiPaneInfo().Name("collection").
                          Caption("collection").Left().CloseButton(False).
                          BestSize(wx.Size(200,-1)).MinSize(wx.Size(50,-1)))

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
            self.logger.info("closing project")
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


            self.loadProject(path)



    def onOpenRecentProject(self, event):
        fileNum = event.GetId() - wx.ID_FILE1
        path = self.filehistory.GetHistoryFile(fileNum)
        self.filehistory.AddFileToHistory(path)  # move up the list
        self.loadProject(path)


    def loadProject(self, path):
        ''' Load a psysmon project.
        '''
        # Quest for the user and the database password.
        self.logger.info("Loading the project file %s.", path)
        dlg = ProjectLoginDlg()
        dlg.ShowModal()
        userData = dlg.userData
        projectLoaded = self.psyBase.load_json_project(path,
                                                       user_name = userData['user'],
                                                       user_pwd = userData['pwd'])

        if not projectLoaded:
            self.psyBase.project = ""
            #msg = "No valid user found. Project not loaded."
            #dlg = wx.MessageDialog(None, msg,
            #                       "pSysmon runtime error.",
            #                       wx.OK | wx.ICON_ERROR)
            #dlg.ShowModal()
            self.logger.error("No valid user found. Project not loaded.")

        else:
            # Load the current database structure.
            #self.psyBase.project.loadDatabaseStructure(self.psyBase.packageMgr.packages)

            # Load the waveform directories.
            #self.psyBase.project.loadWaveformDirList()

            # By default, the project has a database waveclient.
            #waveclient = PsysmonDbWaveClient('main client', self.psyBase.project)
            #self.psyBase.project.addWaveClient(waveclient)

            # Add the default localhost earthworm waveclient.
            #waveclient = EarthwormWaveClient('earthworm localhost')
            #self.psyBase.project.addWaveClient(waveclient)

            # Check if the database tables have to be updated.
            #self.psyBase.project.checkDbVersions(self.psyBase.packageMgr.packages)

            # Update the collection panel display.
            self.collectionPanel.refreshCollection()

            # Activate the user interfaces.
            self.enableGuiElements(mode = 'project')

            # Set the loaded project name as the title.
            self.SetTitle(self.psyBase.project.name)

            # Save the project path in the filehistory.
            self.filehistory.AddFileToHistory(path)

            # Set the status message.
            self.logger.info("Loaded project %s successfully.", self.psyBase.project.name)
            #self.psyBase.project.log('status', statusString)

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
            #self.psyBase.project.save()
            self.psyBase.project.save_json()


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
        # Save the gui configuration to a JSON file
        # Remove the wx-redirect logging handler from the logger.
        handler_list = self.logger.parent.handlers
        for cur_handler in handler_list:
            if isinstance(cur_handler, psysmon.LoggingRedirectHandler):
                self.logger.parent.removeHandler(cur_handler)

        # Save the configuration.
        self.save_config()

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
        dlg = wx.MessageDialog(self, "psysmon is a seismological prototyping and processing software!", "About pSysmon", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()


    def onHelp(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        doc_dir = psysmon.doc_entry_point
        doc_file = 'index.html'

        filename = os.path.join(doc_dir, doc_file)

        if os.path.isfile(filename):
            webbrowser.open_new(filename)
        else:
            msg =  "Couldn't find the documentation file %s." % filename
            self.logger.warning(msg)


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

        self.logger.info(msgString)


    ## Enable of disable the main GUI elements.
    #
    #
    def enableGuiElements(self, state=True, mode = None):
        if(state):
            self.collectionPanel.Enable()
            self.collectionNodeInventoryPanel.Enable()
            #self.loggingPanel.Enable()
        else:
            self.collectionPanel.Disable()
            self.collectionNodeInventoryPanel.Disable()
            #self.loggingPanel.Disable()

        if mode == 'project':
            # Enable the project menu.
            labels_to_enable = ('Close project', 'Save project', 
                                'Data sources', 'SCNL data sources', 'Project preferences')
            mb = self.GetMenuBar()
            for cur_menu, cur_label in mb.GetMenus():
                m_items = cur_menu.GetMenuItems()
                items_to_enable = [x for x in m_items if x.GetItemLabelText() in labels_to_enable]
                for cur_item in items_to_enable:
                    cur_item.Enable(True)

    ## Create new db user menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.  
    def onCreateNewDbUser(self, event):
        dlg = CreateNewDbUserDlg(parent=self, psyBase=self.psyBase)
        dlg.ShowModal()
        dlg.Destroy()


    def onPsysmonPreferences(self, event):
        ''' The psysmon preferences callback.

        Parameters
        ----------
        event :
            The event passed to the callback.
        '''
        dlg = ListbookPrefDialog(preferences = self.psyBase.pref_manager)
        if dlg.ShowModal() == wx.ID_OK:
            # Set the log levels of the loggers.
            root_logger = logging.getLogger('psysmon')
            handlers = root_logger.handlers

            root_logger.setLevel(self.psyBase.pref_manager.get_value('main_loglevel'))

            status_handler = [x for x in handlers if x.get_name() == 'gui_status']
            for cur_handler in status_handler:
                cur_handler.setLevel(self.psyBase.pref_manager.get_value('gui_status_loglevel'))

            shell_handler = [x for x in handlers if x.get_name() == 'shell']
            for cur_handler in shell_handler:
                cur_handler.setLevel(self.psyBase.pref_manager.get_value('shell_loglevel'))

        dlg.Destroy()


    def onEditDataSources(self, event):
        ''' The edit wave clients callback.

        Parameters
        ----------
        event :
            The event passed to the callback.
        '''
        if self.psyBase.project:
            dlg = DataSourceDlg(parent=self, psyBase=self.psyBase)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.logger.warning('You have to open a project first to edit the wave clients.')


    def onEditScnlDataSources(self, event):
        ''' The edit scnl data sources callback.

        Parameters
        ----------
        event :
            The event passed to the callback.
        '''
        if self.psyBase.project:
            dlg = EditScnlDataSourcesDlg(parent=self, psyBase=self.psyBase)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.logger.warning('You have to open a project first to edit the scnl data sources.')


    def onEditProjectPreferences(self, event):
        ''' The edit project preferences callback.

        Parameters
        ----------
        event :
            The event passed to the callback.
        '''
        if self.psyBase.project:
            dlg = ListbookPrefDialog(preferences = self.psyBase.project.pref)
            dlg.ShowModal()
        else:
            self.logger.warning('You have to open a project first to edit the preferences.')


    ## Create new project menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onCreateNewProject(self, event):
        dlg = CreateNewProjectDlg(psyBase=self.psyBase, parent = self)
        retval = dlg.ShowModal()


    # DEFINE THE MESSAGE LISTENERS

    ## Listen to messages from the collectionNodeListCtrl.
    #
    # @param self The object pointer.
    # @param msg The message object.     
    def onCollectionNodeListCtrlMsg(self, msg):
        if msg.topic == ('collectionNodeListCtrl', 'addSelectedNode'):
            self.logger.debug("Got message - Adding node %s  to the collection.", self.selectedCollectionNodeTemplate.name)
        else:
            self.logger.debug("Unknown topic: %s", msg.topic)



class Logger:

    def __init__(self, loggingArea, psyBase):
        self.loggingArea = loggingArea
        self.psyBase = psyBase

        # Subscribe to logging messages.
        #pub.subscribe(self.logGeneral, "log.general")
        #pub.subscribe(self.logCollectionNode, "log.collectionNode")

        # Subscribe to project state messages.
        pub.subscribe(self.onCollectionExecutionMessage, "state.collection.execution")



    def logGeneral(self, msg):
        curTime = datetime.datetime.now()
        timeStampString = datetime.datetime.strftime(curTime, '%Y-%m-%d %H:%M:%S')

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
        curTime = datetime.datetime.now()
        timeStampString = datetime.datetime.strftime(curTime, '%Y-%m-%d %H:%M:%S')

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
        if 'starting' in msg['state']:
            self.loggingArea.addThread(msg)
        elif 'running' in msg['state']:
            self.loggingArea.updateThread(msg)
        elif 'finished' in msg['state']:
            self.loggingArea.updateThread(msg)



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
            if(selectedNode.mode == 'execute only'):
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'edit node')
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            elif(selectedNode.mode == 'uneditable'):
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'uneditable')
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            else:
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'edit node')
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
        except PsysmonError as e:
            pass

        self.PopupMenu(self.contextMenu)


    def onItemRightClicked(self, event):
        self.logger.debug("Item right clicked.")


class CollectionListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        # create the context menu.
        cmData = (("edit node", parent.onEditNode),
                  ("disable node", parent.onDisableNode),
                  ("enable node", parent.onEnableNode),
                  ("remove node", parent.onRemoveNode),
                  ("separator", None),
                  ("load collection", parent.onCollectionLoad),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)


    def onShowContextMenu(self, event):
        try:
            selectedNode = self.Parent.Parent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
            if(selectedNode.mode == 'standalone'):
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            elif(selectedNode.mode == 'uneditable'):
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            else:
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
        except Exception:
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)

        self.PopupMenu(self.contextMenu)


class CollectionTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)

        il = wx.ImageList(16, 16)
        self.icons = {}
        self.icons['node'] = il.Add(iconsBlack16.arrow_r_icon_16.GetBitmap())
        self.icons['looper_node'] = il.Add(iconsBlack16.playback_reload_icon_16.GetBitmap())
        self.icons['looper_node_child'] = il.Add(iconsBlack16.arrow_l_icon_16.GetBitmap())

        self.AssignImageList(il)

        self.root = self.AddRoot("collection")

        self.SetMinSize(size)

        # create the context menu.
        cmData = (("edit node", parent.onEditNode),
                  ("enable node", parent.onToggleNodeEnable),
                  ("remove node", parent.onRemoveNode),
                  ("separator", None),
                  ("load collection", parent.onCollectionLoad),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onShowContextMenu)


    def onShowContextMenu(self, event):
        try:
            if self.Parent.selectedNodeType in ['node', 'looper']:
                selectedNode = self.GrandParent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
            elif self.Parent.selectedNodeType == 'looper_child':
                selectedLooper = self.GrandParent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
                selectedNode = selectedLooper.children[self.Parent.selectedLooperChildNodeIndex]

            #selectedNode = self.Parent.Parent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
            if(selectedNode.mode == 'execute only'):
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            else:
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)

            if selectedNode.enabled:
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'disable node')
            else:
                self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'enable node')
        except Exception as e:
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
            print e

        self.PopupMenu(self.contextMenu)


## The collection panel.
#        
class CollectionPanel(wx.Panel):

    ## The constructor.
    #
    # @param self The object pointer.
    # @param parent The parent object holding the panel.
    def __init__(self, parent, psyBase, size):
        wx.Panel.__init__(self, parent=parent, size=size, id=wx.ID_ANY)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.psyBase = psyBase

        self.SetBackgroundColour((255, 255, 255))

        if False:
            self.collectionListCtrl = CollectionListCtrl(self, id=wx.ID_ANY,
                                     size=(200, -1),
                                     style=wx.LC_REPORT 
                                     | wx.BORDER_NONE
                                     | wx.LC_SORT_ASCENDING
                                     | wx.LC_SINGLE_SEL
                                     | wx.LC_NO_HEADER
                                     )
            self.collectionListCtrl.SetMinSize((200, -1))

            columns = {1: 'node'}

            for colNum, name in columns.iteritems():
                self.collectionListCtrl.InsertColumn(colNum, name)

            sizer = wx.GridBagSizer(5, 5)
            sizer.Add(self.collectionListCtrl, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=0)
        else:
            self.collectionTreeCtrl = CollectionTreeCtrl(self, id = wx.ID_ANY,
                                                         pos = wx.DefaultPosition,
                                                         size = (200, -1),
                                                         style = wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
            sizer = wx.GridBagSizer(5, 5)
            sizer.Add(self.collectionTreeCtrl, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=0)

        self.executeButton = wx.Button(self, 10, "execute", (20, 20))
        sizer.Add(self.executeButton, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=2)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        #sizer.AddGrowableCol(1)
        self.SetSizerAndFit(sizer)

        # create the context menu.
        cmData = (("load collection", self.onCollectionLoad),
                  ("new collection", self.onCollectionNew),
                  ("delete collection", self.onCollectionDelete))
        self.contextMenu = psyContextMenu(cmData)

        # Bind the events
        self.Bind(wx.EVT_BUTTON, self.onExecuteCollection)
        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCollectionNodeItemSelected)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onCollectionNodeItemSelected)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

        self.selectedCollectionNodeIndex = -1
        self.selectedLooperChildNodeIndex = -1
        self.selectedNodeType = None




    def onShowContextMenu(self, event):
        self.PopupMenu(self.contextMenu)


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
            if self.selectedNodeType in ['node', 'looper']:
                self.logger.debug("Removing node at index %d.", self.selectedCollectionNodeIndex)
                self.psyBase.project.removeNodeFromCollection(self.selectedCollectionNodeIndex)
                self.selectedCollectionNodeIndex -= 1
                if self.selectedCollectionNodeIndex < 0 and len(self.psyBase.project.activeUser.activeCollection) > 0:
                    self.selectedCollectionNodeIndex = 0
                if self.selectedNodeType == 'looper':
                    self.selectedLooperChildNodeIndex = -1
            elif self.selectedNodeType == 'looper_child':
                selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
                selectedNode.children.pop(self.selectedLooperChildNodeIndex)
                self.selectedLooperChildNodeIndex -= 1
                if self.selectedLooperChildNodeIndex < 0 and len(selectedNode.children) > 0:
                    self.selectedLooperChildNodeIndex = 0
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
            if self.selectedNodeType in ['node', 'looper']:
                selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            elif self.selectedNodeType == 'looper_child':
                selectedLooper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
                selectedNode = selectedLooper.children[self.selectedLooperChildNodeIndex]

            if(selectedNode.mode == 'standalone'):
                self.logger.debug("in standalone")
                selectedNode.execute()
            else:
                selectedNode.edit()
        except PsysmonError as e:
            msg = "Cannot edit the node:\n %s" % e
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal() 


    def onToggleNodeEnable(self, event):
        if self.selectedNodeType in ['node', 'looper']:
            selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
        elif self.selectedNodeType == 'looper_child':
            selectedLooper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            selectedNode = selectedLooper.children[self.selectedLooperChildNodeIndex]

        if selectedNode.mode != 'standalone':
            selectedNode.enabled = not selectedNode.enabled
            if selectedNode.enabled:
                self.collectionTreeCtrl.SetItemTextColour(self.collectionTreeCtrl.GetSelection(), wx.BLACK)
            else:
                self.collectionTreeCtrl.SetItemTextColour(self.collectionTreeCtrl.GetSelection(), wx.TheColourDatabase.Find('GREY70'))

    ## Select node item callback.
    #
    # This method responds to events raised by selecting a collection node in 
    # the collectionPanel.collectionListCtrl.
    #
    # @param self The object pointer.
    # @param event The event object.    
    def onCollectionNodeItemSelected(self, evt):
        collection_pos, node_type = self.collectionTreeCtrl.GetItemPyData(evt.GetItem())
        self.logger.debug("Selected node %s at position %d in collection.", node_type, collection_pos)
        self.selectedNodeType = node_type
        if node_type in ['node', 'looper']:
            self.selectedCollectionNodeIndex = collection_pos
        elif node_type == 'looper_child':
            self.selectedLooperChildNodeIndex = collection_pos


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
        self.logger.debug("Delete a collection.")


    def refreshCollection(self):
        '''
        Refresh the collection nodes displayed in the collection listbox.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.gui.CollectionPanel`
        '''
        if not self.psyBase.project:
            self.collectionTreeCtrl.DeleteChildren(self.collectionTreeCtrl.root)
            return

        activeCollection = self.psyBase.project.getActiveCollection()
        if activeCollection is not None:
            auiPane = self.GetParent().mgr.GetPane('collection')
            auiPane.Caption(activeCollection.name)
            self.GetParent().mgr.Update()

            self.collectionTreeCtrl.DeleteChildren(self.collectionTreeCtrl.root)
            for k, curNode in enumerate(activeCollection.nodes):
                if isinstance(curNode, psysmon.core.packageNodes.LooperCollectionNode):
                    node_string = curNode.name + ' (looper)'
                    looper_node_item = self.collectionTreeCtrl.AppendItem(self.collectionTreeCtrl.root, node_string)
                    self.collectionTreeCtrl.SetItemPyData(looper_node_item, (k, 'looper'))
                    self.collectionTreeCtrl.SetItemImage(looper_node_item, self.collectionTreeCtrl.icons['looper_node'], wx.TreeItemIcon_Normal)
                    if k == self.selectedCollectionNodeIndex:
                        self.collectionTreeCtrl.SelectItem(looper_node_item)
                    if not curNode.enabled:
                        self.collectionTreeCtrl.SetItemTextColour(looper_node_item, wx.TheColourDatabase.Find('GREY70'))

                    for child_pos, cur_child in enumerate(curNode.children):
                        node_string = cur_child.name + '(child)'
                        node_item = self.collectionTreeCtrl.AppendItem(looper_node_item, node_string)
                        self.collectionTreeCtrl.SetItemPyData(node_item, (child_pos, 'looper_child'))
                        self.collectionTreeCtrl.SetItemImage(node_item, self.collectionTreeCtrl.icons['looper_node_child'], wx.TreeItemIcon_Normal)
                        if not curNode.enabled:
                            self.collectionTreeCtrl.SetItemTextColour(node_item, wx.TheColourDatabase.Find('GREY70'))
                else:
                    node_string = curNode.name
                    node_item = self.collectionTreeCtrl.AppendItem(self.collectionTreeCtrl.root, node_string)
                    self.collectionTreeCtrl.SetItemPyData(node_item, (k, 'node'))
                    self.collectionTreeCtrl.SetItemImage(node_item, self.collectionTreeCtrl.icons['node'], wx.TreeItemIcon_Normal)
                    if k == self.selectedCollectionNodeIndex:
                        self.collectionTreeCtrl.SelectItem(node_item)
                    if not curNode.enabled:
                        self.collectionTreeCtrl.SetItemTextColour(node_item, wx.TheColourDatabase.Find('GREY70'))

        self.collectionTreeCtrl.ExpandAll()


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
        self.PopupMenu(self.contextMenu)



class LoggingPanel(wx.aui.AuiNotebook):
    def __init__(self, parent=None, style=None):
        wx.aui.AuiNotebook.__init__(self, parent=parent, style=style)
        self.SetMinSize((200, 120))

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

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
        for colNum, name in columns.iteritems():
            self.status.InsertColumn(colNum, name)
        self.status.SetColumnWidth(0, 100)
        self.status.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        # The collection thread logging area.
        self.processes = LogProcessStatusListCtrl(self, id=wx.ID_ANY,
                                      style=wx.LC_REPORT
                                      | wx.BORDER_NONE
                                      | wx.LC_SINGLE_SEL
                                      | wx.LC_SORT_ASCENDING)

        columns = {1: 'start', 2: 'pid', 3: 'name', 4: 'status', 5: 'duration'}

        for colNum, name in columns.iteritems():
            self.processes.InsertColumn(colNum, name)

        # Create the context menu of the thread logging area.
        cmData = (("view log file", self.onViewLogFile),
                  ("kill process", self.onKillProcess),
                  ("remove from display", self.onRemoveProcess))
        self.contextMenu = psyContextMenu(cmData)
        self.processes.Bind(wx.EVT_RIGHT_UP, self.onShowContextMenu)

        # Add the elements to the notebook.
        self.AddPage(self.status, "status")
        self.AddPage(self.processes, "processes")

        # Subscribe to the state messages of the project.
        pub.subscribe(self.onCollectionExecutionMessage, "state.collection.execution")



    def log(self, msg, levelname = None):
        item = self.status.InsertStringItem(0, levelname)
        self.status.SetStringItem(0, 1, msg)
        if levelname.lower() == 'warning':
            self.status.SetItemBackgroundColour(item, wx.NamedColour('orange1'))
        elif levelname.lower() == 'error' or levelname.lower() == 'critical':
            self.status.SetItemBackgroundColour(item, wx.NamedColour('orangered1'))

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
        #index = self.threads.GetItemCount()
        index = 0
        self.processes.InsertStringItem(index, datetime.datetime.strftime(data['startTime'], '%Y-%m-%d %H:%M:%S'))
        self.processes.SetStringItem(index, 1, str(data['pid']))
        self.processes.SetStringItem(index, 2, data['procName'])
        self.processes.SetStringItem(index, 3, data['state'])
        self.processes.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.processes.SetColumnWidth(4, wx.LIST_AUTOSIZE)

        # The new process is added on top of the list. Add 1 to all
        # index values of the process map.
        for curKey in self.processMap.keys():
            self.processMap[curKey] += 1

        self.processMap[data['procName']] = index

    def updateThread(self, data):
        #self.logger.debug('updating process: %s', data['procName'])
        error_code = {1: 'general error', 2: 'collection execution error', 3: 'collection preparation error', 4: 'finalization error'}
        if data['procName'] in self.processMap.keys():
            curIndex = self.processMap[data['procName']]
            #self.logger.debug('process has index: %d', curIndex)
            self.processes.SetStringItem(curIndex, 3, data['state'])
            duration = data['curTime'] - data['startTime']
            duration -= datetime.timedelta(microseconds = duration.microseconds)
            self.processes.SetStringItem(curIndex, 4, str(duration))
            if data['state'].lower() == 'stopped' and data['returncode'] > 0:
                self.processes.SetStringItem(curIndex, 3, 'error')
                self.processes.SetItemTextColour(curIndex, wx.NamedColour('orangered1'))
                self.logger.error("Error while executing process %s: %s.\nSee the log file of the process for more details.", data['procName'], error_code[data['returncode']].upper())
            elif data['state'].lower() == 'stopped':
                self.processes.SetItemTextColour(curIndex, wx.NamedColour('grey70'))

    def onShowContextMenu(self, event):
        self.PopupMenu(self.contextMenu)

    def onViewLogFile(self, event):
        selectedRow = self.processes.GetFirstSelected()
        procName = self.processes.GetItem(selectedRow, 2).GetText()
        logFile = os.path.join(self.GetParent().psyBase.project.tmpDir, procName + ".log")
        webbrowser.open(logFile)
        self.logger.info("Showing the log file %s.", logFile)


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


class CollectionNodeInventoryPanel(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent, psyBase):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.itemDataMap = {}

        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        self.psyBase = psyBase
        self.collectionPanel = parent.collectionPanel

        self.SetBackgroundColour((255, 255, 255))

        sizer = wx.GridBagSizer(5, 5)

        self.searchButton = wx.SearchCtrl(self, size=(200,30), style=wx.TE_PROCESS_ENTER)
        self.searchButton.SetMinSize((-1, 30))
        #self.searchButton.SetDescriptiveText('Search collection nodes')
        self.searchButton.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancelSearch, self.searchButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onDoSearch, self.searchButton)
        sizer.Add(self.searchButton, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)

        self.nodeListCtrl = NodeListCtrl(self, id=wx.ID_ANY,
                                 size = (400, -1),
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_SINGLE_SEL
                                 | wx.LC_SORT_ASCENDING
                                 )
        self.nodeListCtrl.SetMinSize((400, 100))

        self.nodeListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


        columns = {1: 'name', 2: 'mode', 3: 'category', 4: 'tags'}

        for colNum, name in columns.iteritems():
            self.nodeListCtrl.InsertColumn(colNum, name)

        sizer.Add(self.nodeListCtrl, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=0)

        sizer.AddGrowableCol(0)
        #sizer.AddGrowableCol(1)
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
        self.logger.debug("Selected item: %s", item.GetText())
        self.selectedCollectionNodeTemplate = self.psyBase.packageMgr.getCollectionNodeTemplate(item.GetText())


    def onDoSearch(self, evt):
        foundNodes = self.psyBase.packageMgr.searchCollectionNodeTemplates(self.searchButton.GetValue())
        self.updateNodeInvenotryList(foundNodes)
        self.logger.debug('%s', foundNodes)

    def onCancelSearch(self, evt):
        self.initNodeInventoryList()
        self.searchButton.SetValue(self.searchButton.GetDescriptiveText())



    def onCollectionNodeAdd(self, event):
        msg =  "Adding node template to collection: " + self.selectedCollectionNodeTemplate.name
        #pub.sendMessage("log.general.status", msg = msg)
        self.logger.info(msg)

        if psysmon.core.packageNodes.LooperCollectionChildNode in self.selectedCollectionNodeTemplate.__bases__:
            # Check if a collection exists.

            # Check if the selected node is a looper node.
            #selected_node = self.Parent.psyBase.project.getNodeFromCollection(self.collectionPanel.selectedCollectionNodeIndex)
            #if psysmon.core.packageNodes.LooperCollectionNode in selected_node:

            # Add the currend looper child node to the looper node.
            pos = self.collectionPanel.selectedCollectionNodeIndex
            self.psyBase.project.addNode2Looper(self.selectedCollectionNodeTemplate, pos)
            self.collectionPanel.refreshCollection()
        else:
            try:
                pos = self.collectionPanel.selectedCollectionNodeIndex
                if pos != -1:
                    pos += 1    # Add after the selected node in the collection.
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
        doc_dir = psysmon.doc_entry_point

        package_name = self.selectedCollectionNodeTemplate.parentPackage.name
        node_name = self.selectedCollectionNodeTemplate.name.replace(' ', '_')

        filename = os.path.join(doc_dir, 'packages', package_name, node_name + '.html')

        if os.path.isfile(filename):
            webbrowser.open_new(filename)
        else:
            msg =  "Couldn't find the documentation file %s." % filename
            self.logger.warning(msg)



    def initNodeInventoryList(self):
        nodeTemplates = {}
        for curPkg in self.psyBase.packageMgr.packages.itervalues():
            nodeTemplates.update(curPkg.collectionNodeTemplates)

        self.updateNodeInvenotryList(nodeTemplates)
        listmix.ColumnSorterMixin.__init__(self, 4)
        self.nodeListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.nodeListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.nodeListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)


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

            # The logger.
            loggerName = __name__ + "." + self.__class__.__name__
            self.logger = logging.getLogger(loggerName)

            for cmLabel, cmHandler in cmData:
                if cmLabel.lower() == "separator":
                    self.AppendSeparator()
                else:
                    if isinstance(cmHandler, list) or isinstance(cmHandler, tuple):
                        # This is a submenu.
                        submenu = wx.Menu()
                        for subLabel, subHandler in cmHandler:
                            item = submenu.Append(-1, subLabel)
                            submenu.Bind(wx.EVT_MENU, subHandler, item)
                        self.AppendMenu(-1, cmLabel, submenu)
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
                self.GetParent().logger.info(statusString)

                # Close the dialog.
                self.Destroy()

            else:
                # Set the status message.
                statusString = "Error while creating the user %s." % userData['userName']
                if not self.GetParent():
                    self.GetParent().logger.debug("NO PARENT")
                else:
                    self.GetParent().logger.error(statusString)



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
        except SQLAlchemyError as e:
            msg = "An error occured when trying to create the pSysmon database user:\n%s" % str(e)
            dlg = wx.MessageDialog(None, msg,
                                   "MySQL database error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return False



class DataSourceDlg(wx.Dialog):
    ''' The EditWaveformDirDlg class.

    This class creates a dialog used to edit the pSysmon data sources.

    Attributes
    ----------
    psyBase : :class:`~psysmon.core.Base`
        The pSysmon base instance.
    '''
    def __init__(self, psyBase, parent=None, size=(300, 100)):
        ''' The constructor.

        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Edit the waveclients", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=size)

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
        sizer = wx.GridBagSizer(5,5)
        gridButtonSizer = wx.BoxSizer(wx.VERTICAL)

        # Fill the grid button sizer
        gridButtonSizer.Add(addButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(editButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(removeButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(defaultButton, 0, wx.EXPAND|wx.ALL)

        # Create the image list for the list control.
        self.il = wx.ImageList(16, 16)
        self.iconDefault = self.il.Add(iconsBlack16.star_icon_16.GetBitmap())

        # Create the list control
        fields = self.getGridColumns()
        self.wcListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.wcListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        for k, (name, label, attr) in enumerate(fields):
            self.wcListCtrl.InsertColumn(k, label)

        sizer.Add(self.wcListCtrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add(gridButtonSizer, pos=(0,1), flag=wx.EXPAND|wx.ALL, border=5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)

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
            self.psyBase.project.handleWaveclientNameChange(selectedItem, client2Edit)

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
        for k, (name, client) in enumerate(self.psyBase.project.waveclient.iteritems()):
            if name == self.psyBase.project.defaultWaveclient:
                self.wcListCtrl.InsertImageStringItem(k, client.name, self.iconDefault)
            else:
                self.wcListCtrl.InsertStringItem(k, client.name)
            self.wcListCtrl.SetStringItem(k, 1, client.mode)
            #self.wcListCtrl.SetStringItem(k, 2, curDir.aliases[0].alias)
            #self.wcListCtrl.SetStringItem(k, 3, curDir.description)

        self.wcListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.wcListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        #self.wcListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)


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
        #tableField.append(('alias', 'alias', 'editable'))
        #tableField.append(('description', 'description', 'editable'))
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


class PsysmonDbWaveclientOptions(wx.Panel):

    def __init__(self, parent=None, client=None, project=None, size=(-1, -1)):
        ''' The constructor.

        '''
        wx.Panel.__init__(self, parent, wx.ID_ANY, size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The waveclient holding the options.
        self.client = client

        # The currently selected directory index.
        self.selected_waveform_dir = None

        # Create the grid editing buttons.
        addDirButton = wx.Button(self, wx.ID_ANY, "add")
        removeDirButton = wx.Button(self, wx.ID_ANY, "remove")
        changeAliasButton = wx.Button(self, wx.ID_ANY, "change alias")

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)
        gridButtonSizer = wx.BoxSizer(wx.VERTICAL)

        # Fill the grid button sizer
        gridButtonSizer.Add(addDirButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(removeDirButton, 0, wx.EXPAND|wx.ALL)
        gridButtonSizer.Add(changeAliasButton, 0, wx.EXPAND|wx.ALL)

        fields = self.getGridColumns()
        self.wfListCtrl = wx.ListCtrl(self, style=wx.LC_REPORT)

        for k, (name, label, attr) in enumerate(fields):
            self.wfListCtrl.InsertColumn(k, label)

        sizer.Add(self.wfListCtrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add(gridButtonSizer, pos=(0,1), flag=wx.EXPAND|wx.ALL, border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizer(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onAddDirectory, addDirButton)
        self.Bind(wx.EVT_BUTTON, self.onRemoveDirectory, removeDirButton)
        self.Bind(wx.EVT_BUTTON, self.onChangeAlias, changeAliasButton)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onDirectorySelected, self.wfListCtrl)

        self.project = project
        self.wfDir = self.project.dbTables['waveform_dir']
        self.wfDirAlias = self.project.dbTables['waveform_dir_alias']
        self.dbSession = self.project.getDbSession()

        # A list of available waveform directories. It consits of tuples of
        self.wfDirList = self.dbSession.query(self.wfDir).join(self.wfDirAlias,
                                                               self.wfDir.id==self.wfDirAlias.wf_id
                                                              ).filter(self.wfDirAlias.user==self.project.activeUser.name).all()
        self.updateWfListCtrl()
        sizer.Fit(self)



    def getGridColumns(self):
        ''' Create the column fields used by the list control.

        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('origDir', 'original directory', 'readonly'))
        tableField.append(('alias', 'alias', 'editable'))
        tableField.append(('description', 'description', 'editable'))
        return tableField


    def onDirectorySelected(self, evt):
        ''' The item selected callback of the directory list.
        '''
        self.selected_waveform_dir = self.wfDirList[evt.GetIndex()]


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
            self.logger.info('You selected: %s', dlg.GetPath())

            newWfDir = self.wfDir(dlg.GetPath(), '')
            newAlias = self.wfDirAlias(self.project.activeUser.name,
                                            dlg.GetPath())
            newWfDir.aliases.append(newAlias)

            self.dbSession.add(newWfDir)
            #self.dbSession.add(newWfDirAlias)

            self.wfDirList.append(newWfDir)
            self.updateWfListCtrl()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()


    def updateWfListCtrl(self):
        ''' Initialize the waveformDir table with values.

        '''
        self.wfListCtrl.DeleteAllItems()
        for k, curDir in enumerate(self.wfDirList):
            self.wfListCtrl.InsertStringItem(k, str(curDir.id))
            self.wfListCtrl.SetStringItem(k, 1, curDir.directory)
            self.wfListCtrl.SetStringItem(k, 2, curDir.aliases[0].alias)
            self.wfListCtrl.SetStringItem(k, 3, curDir.description)

        self.wfListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.wfListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.wfListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)


    def onRemoveDirectory(self, event):
        ''' The remove directory callback.
        '''
        selectedRow =  self.wfListCtrl.GetFocusedItem()
        #item2Delete =  self.wfListCtrl.GetItem(selectedRow, 0)
        obj2Delete = self.wfDirList.pop(selectedRow)
        try:
            self.dbSession.delete(obj2Delete)
        except sqlalchemy.exc.InvalidRequestError:
            self.dbSession.expunge(obj2Delete)

        self.wfListCtrl.DeleteItem(selectedRow)


    def onChangeAlias(self, event):
        ''' The change alias button callback.

        Select a new directory to use a the waveform directory alias.

        Parameters
        ----------
        event :
            The wxPython event passed to the callback.
        '''
        if not self.selected_waveform_dir:
            return

        # In this case we include a "New directory" button.
        dlg = wx.DirDialog(self, "Choose a new alias directory:",
                          style=wx.DD_DEFAULT_STYLE
                           | wx.DD_DIR_MUST_EXIST,
                           defaultPath = self.selected_waveform_dir.aliases[0].alias
                           )

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            self.logger.info('New alias directory: %s', dlg.GetPath())
            self.selected_waveform_dir.aliases[0].alias = dlg.GetPath()
            self.updateWfListCtrl()

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()


    def onOk(self):
        ''' Apply the changes.

        This method should be called by the dialog holding the options when the user clicks 
        the ok button.
        '''
        try:
            self.dbSession.commit()
        finally:
            self.dbSession.close()
        # Reload the project's waveform directory list to make sure, that it's 
        # consistent with the database.
        self.client.loadWaveformDirList()


    def onCancel(self):
        ''' Called when the dialog cancel button is clicked.
        '''
        self.dbSession.close()



class EarthwormWaveclientOptions(wx.Panel):

    def __init__(self, parent=None, client=None, project=None, size=(-1, -1)):
        ''' The constructor.

        '''
        wx.Panel.__init__(self, parent, wx.ID_ANY, size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The waveclient holding the options.
        self.client = client


        self.nameLabel = wx.StaticText(self, -1, "name:")
        self.nameEdit = wx.TextCtrl(self, -1, self.client.name, size=(100, -1))
        self.hostLabel = wx.StaticText(self, -1, "host:")
        self.hostEdit = wx.TextCtrl(self, -1, self.client.host, size=(100, -1))
        self.portLabel = wx.StaticText(self, -1, "port:")
        self.portEdit = wx.TextCtrl(self, -1, str(self.client.port), size=(100, -1))

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)


        sizer.Add(self.nameLabel, pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        sizer.Add(self.nameEdit, pos=(0,1), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add(self.hostLabel, pos=(1,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        sizer.Add(self.hostEdit, pos=(1,1), flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add(self.portLabel, pos=(2,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, border=5)
        sizer.Add(self.portEdit, pos=(2,1), flag=wx.EXPAND|wx.ALL, border=5)

        sizer.AddGrowableCol(1)

        self.SetSizerAndFit(sizer)

        self.project = project


    
    def onOk(self):
        ''' Apply the changes.

        This method should be called by the dialog holding the options when the user clicks 
        the ok button.
        '''
        self.client.name = self.nameEdit.GetValue()
        self.client.host = self.hostEdit.GetValue()
        self.client.port = int(self.portEdit.GetValue())
        self.logger.debug(self.client.name)
        return self.client


    def onCancel(self):
        ''' Called when the dialog cancel button is clicked.
        '''
        pass




class EditWaveclientDlg(wx.Dialog):

    def __init__(self, parent=None, size=(-1, -1), psyBase = None, client = None):
        ''' The constructor.

        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Edit the waveclient options", style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.psyBase = psyBase

        self.clientOptionPanels = self.getClientOptionsPanels()

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        okButton.SetDefault()

        # Create the client's options pane.
        (curLabel, curPanel) = self.clientOptionPanels[client.mode]
        self.optionsPanel = curPanel(parent=self, client=client, project=self.psyBase.project)

        # The main dialog sizer.
        sizer = wx.GridBagSizer(5,5)

        sizer.Add(self.optionsPanel, pos=(0,0), flag=wx.EXPAND|wx.ALL, border = 5)

        # The button sizer.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelButton)

        sizer.Fit(self)


    def getClientOptionsPanels(self):
        clientModes = {}
        clientModes['EarthwormWaveclient'] =  ('Earthworm', EarthwormWaveclientOptions)
        clientModes['PsysmonDbWaveClient'] =  ('pSysmon database', PsysmonDbWaveclientOptions)
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

    def __init__(self, parent=None, size=(-1,-1), psyBase=None):
        ''' The constructor.

        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Add a new waveclient", style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.psyBase = psyBase

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        okButton.SetDefault()

        # Create the choicebook.
        self.modeChoiceBook = Choicebook(parent = self, id = wx.ID_ANY)

        for curLabel, curClass in self.clientModes().itervalues():
            if curClass == PsysmonDbWaveClient:
                panel = PsysmonDbWaveclientOptions(parent = self.modeChoiceBook, project=self.psyBase.project)
                #panel.SetBackgroundColour('red')
            elif curClass == EarthwormWaveclient:
                panel = EarthwormWaveclientOptions(parent=self.modeChoiceBook, 
                                                   project=self.psyBase.project,
                                                   client=curClass(name='earthworm client'))
                #panel.SetBackgroundColour('green')

            panel.SetMinSize((200, 200))
            self.modeChoiceBook.AddPage(panel, curLabel)


        # The main dialog sizer.
        sizer = wx.GridBagSizer(5,5)

        # Add the choicebook.
        sizer.Add(self.modeChoiceBook, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)

        # The button sizer.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)
        
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)
        
        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def clientModes(self):
        clientModes = {}
        clientModes['earthworm'] =  ('Earthworm', EarthwormWaveclient)
        #clientModes['psysmonDb'] =  ('pSysmon database', PsysmonDbWaveClient)
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
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Edit the waveclients", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=size)

        self.psyBase = psyBase

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Get the inventory from the database.
        inventoryDbController = InventoryDatabaseController(self.psyBase.project)
        self.inventory = inventoryDbController.load()

        # Create the scnl-datasource list.
        self.scnl = []
        for curNetwork in self.inventory.networks.itervalues():
            for curStation in curNetwork.stations.itervalues():
                self.scnl.extend(curStation.getScnl())

        # Sort the scnl list.
        self.scnl = sorted(self.scnl, key = itemgetter(0,1,2,3))

        for curScnl in self.scnl:
            if curScnl not in self.psyBase.project.scnlDataSources.keys():
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





## The create a new project dialog window.
#
# This window is used to get the parameters needed to create a new pSysmon 
# project.
class CreateNewProjectDlg(wx.Dialog):

    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, psyBase, parent, size=(500, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new project", 
                           size=size, 
                           style=wx.DEFAULT_DIALOG_STYLE)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

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
        self.edit['db_host'].SetValue('localhost')

        # Add the validators.
        self.edit['name'].SetValidator(NotEmptyValidator())         # Not empty.
        self.edit['base_dir'].SetValidator(NotEmptyValidator())         # Not empty.
        self.edit['db_host'].SetValidator(NotEmptyValidator())        # Not empty.
        self.edit['user_name'].SetValidator(NotEmptyValidator())        # Not empty.
        self.edit['agency_uri'].SetValidator(NotEmptyValidator())        # Not empty.
        self.edit['author_uri'].SetValidator(NotEmptyValidator())        # Not empty.
        #self.edit['userPwd'].SetValidator(NotEmptyValidator())        # Not empty.

        # Show the example URI.
        self.edit['resource_id'].SetValue('smi:AGENCY_URI.AUTHOR_URI/psysmon/NAME')

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_TEXT, self.onUpdateRid, self.edit['name'])
        self.Bind(wx.EVT_TEXT, self.onUpdateRid, self.edit['author_uri'])
        self.Bind(wx.EVT_TEXT, self.onUpdateRid, self.edit['agency_uri'])

    def onUpdateRid(self, event):
        agency_uri  = self.edit['agency_uri'].GetValue()
        author_uri = self.edit['author_uri'].GetValue()
        project_uri = self.edit['name'].GetValue()
        project_uri = project_uri.lower().replace(' ', '_')

        rid = 'smi:' + agency_uri + '.' + author_uri + '/psysmon/' + project_uri
        self.edit['resource_id'].SetValue(rid)

    def onBaseDirBrowse(self, event):

        # Create the directory dialog.
        dlg = wx.DirDialog(self, message="Choose a directory:",
                           defaultPath=self.edit['base_dir'].GetValue(),
                           style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # Get the selected directory
        if dlg.ShowModal() == wx.ID_OK:
            self.edit['base_dir'].SetValue(dlg.GetPath())

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

    def onOk(self, event):  
        isValid = self.Validate()

        if(isValid):
            keys_2_pass = ['name', 'base_dir', 'db_host', 'user_name', 'user_pwd',
                           'author_name', 'author_uri', 'agency_name', 'agency_uri']
            projectData = {};
            for _, curKey, _, _, _, _ in self.dialogData():
                if curKey in keys_2_pass:
                    projectData[curKey] = self.edit[curKey].GetValue()

            try:
                self.createProject(projectData)
                self.GetParent().enableGuiElements(mode = 'project')
                self.Destroy()
            except Exception as e:
                raise


    def dialogData(self):
        return(("name:", "name", wx.TE_RIGHT, False, "", 'edit'),
               ("base directory:", "base_dir", wx.TE_LEFT, True, self.onBaseDirBrowse, 'edit'),
               ("database host:", "db_host", wx.TE_RIGHT, False, "", 'edit'),
               ("username:", "user_name", wx.TE_RIGHT, False, "", 'edit'),
               ("user pwd:", "user_pwd", wx.TE_PASSWORD|wx.TE_RIGHT, False, "", 'edit'),
               ("author name:", "author_name", wx.TE_RIGHT, False, "", 'edit'),
               ("author URI:", "author_uri", wx.TE_RIGHT, False, "", 'edit'),
               ("agency name:", "agency_name", wx.TE_RIGHT, False, "", 'edit'),
               ("agency URI:", "agency_uri", wx.TE_RIGHT, False, "", 'edit'),
               ("resource ID:", "resource_id", wx.TE_RIGHT, False, "", 'static')
               )

    def createDialogFields(self):
        dialogData = self.dialogData()
        gbSizer = wx.GridBagSizer(5, 5)
        rowCount = 0

        for curLabel, curKey, curStyle, hasBrowseBtn, curBtnHandler, curType in dialogData:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(300, -1), 
                                            style=curStyle)

            if curType == 'static':
                self.edit[curKey].SetEditable(False)
                self.edit[curKey].Disable()

            if(hasBrowseBtn):
                browseButton = wx.Button(self, wx.ID_ANY, "browse", (50,-1))
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0), 
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1), 
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL)
                gbSizer.Add(browseButton, pos=(rowCount, 2), 
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL)

                self.Bind(wx.EVT_BUTTON, curBtnHandler, browseButton)
            elif(curStyle == 'static'):
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
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
        except Exception as e:
            self.logger.error("Error while creating the project: %s", e)
            raise



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




class FoldPanelBar(scrolled.ScrolledPanel):
    ''' pSysmon custom foldpanelbar class.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.sizer = wx.GridBagSizer(0, 0)
        self.sizer.AddGrowableCol(0)
        self.SetSizer(self.sizer)

        self.SetupScrolling()

        self.subPanels = []


    def addPanel(self, subPanel, icon):
        foldPanel = self.makeFoldPanel(subPanel, icon)
        curRow = len(self.subPanels)
        self.subPanels.append(foldPanel)
        best = foldPanel.GetBestSize()
        foldPanel.SetMinSize(best)
        foldPanel.SetSize(best)
        self.sizer.Add(foldPanel, pos=(curRow, 0), flag=wx.EXPAND|wx.ALL, border=0)
        self.sizer.AddGrowableRow(curRow)
        self.sizer.Layout()
        self.SetupScrolling()

        return foldPanel



    def hidePanel(self, subPanel):
        self.subPanels.remove(subPanel)
        self.sizer.Detach(subPanel)
        subPanel.Hide()
        self.rearrangePanels()
        
        if subPanel.minimizeButton.IsPressed():
            subPanel.minimizeButton.SetState(platebtn.PLATE_NORMAL)
            # The _pressed attribute is not reset when setting the
            # state. Do it explicitely.
            subPanel.minimizeButton._pressed = False



    def showPanel(self, subPanel):
        self.subPanels.append(subPanel)
        if subPanel.isMinimized:
            subPanel.toggleMinimize()
        self.rearrangePanels()


    def toggleMinimizePanel(self, subPanel):
        subPanel.toggleMinimize()
        self.rearrangePanels()


    def rearrangePanels(self):

        for curPanel in self.subPanels:
            self.sizer.Hide(curPanel)
            self.sizer.Detach(curPanel)

        for k, curPanel in enumerate(self.subPanels):
            self.sizer.Add(curPanel, pos=(k,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
            self.sizer.Show(curPanel)

        self.Layout()
        #self.SetupScrolling()


    def makeFoldPanel(self, panel, icon):
        foldPanel = FoldPanel(self, panel, icon)
        return foldPanel


    def onCloseButtonClick(self, event):
        self.hidePanel(event.GetEventObject().GetParent())


    def onMinimizeButtonClick(self, event):
        self.toggleMinimizePanel(event.GetEventObject().GetParent())



class FoldPanel(wx.Panel):

    def __init__(self, parent, contentPanel, icon):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.SetMinSize((50, 10))

        self.isMinimized = False

        self.icon = icon
        self.contentPanel = contentPanel

        contentPanel.Reparent(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        headerSizer = wx.GridBagSizer(0,0)

        bmp = icon.GetBitmap()
        self.headerButton = wx.StaticBitmap(self, -1, bmp, (0,0), 
                                       (bmp.GetWidth(), bmp.GetHeight()),
                                       style=wx.NO_BORDER)
        headerSizer.Add(self.headerButton, pos=(0,0), flag=wx.ALL, border=2)

        bmp = iconsBlack10.minus_icon_10.GetBitmap()
        #self.minimizeButton = wx.BitmapButton(self, -1, bmp, (0,0), 
        #                               style=wx.NO_BORDER)
        self.minimizeButton = platebtn.PlateButton(self, wx.ID_ANY, bmp=bmp, style=platebtn.PB_STYLE_DEFAULT|platebtn.PB_STYLE_TOGGLE)
        self.minimizeButton.SetPressColor(wx.NamedColor('peachpuff4'))
        headerSizer.Add(self.minimizeButton, pos=(0,2), flag=wx.ALL|wx.ALIGN_RIGHT, border=0)

        bmp = iconsBlack10.delete_icon_10.GetBitmap()
        #self.closeButton = wx.BitmapButton(self, -1, bmp, (0,0), 
        #                               style=wx.NO_BORDER)
        self.closeButton = platebtn.PlateButton(self, wx.ID_ANY, bmp=bmp)
        self.closeButton.SetPressColor(wx.NamedColor('peachpuff4'))
        headerSizer.Add(self.closeButton, pos=(0,3), flag=wx.ALL|wx.ALIGN_RIGHT, border=0)
        headerSizer.AddGrowableCol(1)

        sizer.Add(headerSizer, 0, flag=wx.EXPAND|wx.ALL, border=0)
        sizer.Add(self.contentPanel, 0, flag=wx.EXPAND|wx.ALL|wx.ALIGN_LEFT, border=0)
        self.SetSizer(sizer)
        self.sizer = sizer
        self.headerSizer = headerSizer

        self.Bind(wx.EVT_BUTTON, parent.onCloseButtonClick, self.closeButton)
        self.Bind(wx.EVT_TOGGLEBUTTON, parent.onMinimizeButtonClick, self.minimizeButton)


    def toggleMinimize(self):
        if self.contentPanel.IsShown():
            #self.sizer.Detach(self.contentPanel)
            self.contentPanel.Hide()
            self.SetMinSize(self.GetBestSize())
            self.SetSize(self.GetBestSize())
            self.sizer.Layout()
            self.isMinimized = True
            self.minimizeButton.SetPressColor(wx.NamedColor('darkolivegreen4'))
        else:
            #self.sizer.Add(self.contentPanel, 0, flag=wx.EXPAND|wx.ALL, border = 0)
            self.contentPanel.Show()
            self.SetMinSize(self.GetBestSize())
            self.SetSize(self.GetBestSize())
            self.sizer.Layout()
            self.isMinimized = False
            self.minimizeButton.SetPressColor(wx.NamedColor('peachpuff4'))


class FoldPanelBarSplitter(scrolled.ScrolledPanel):
    ''' pSysmon custom foldpanelbar class.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        #wx.ScrolledWindow.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.splitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetOrientation(wx.VERTICAL)

        self.sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.splitter.SetMinimumPaneSize(100)

        #self.EnableScrolling(True, True)
        self.SetupScrolling()

        self.subPanels = []

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSashChanged, self.splitter)


    def onSashChanged(self, event):
        print 'Changed sash: %d; %s\n' % (event.GetSashIdx(), event.GetSashPosition())


    def addPanel(self, subPanel):
        subPanel.Reparent(self.splitter)
        self.subPanels.append(subPanel)
        self.splitter.AppendWindow(subPanel, 200)
        self.SetupScrolling()



    def hidePanel(self, subPanel):
        self.subPanels.remove(subPanel)
        self.splitter.DetachWindow(subPanel)
        subPanel.Hide()
        #self.rearrangePanels()


    def showPanel(self, subPanel):
        subPanel.Show()
        self.addPanel(subPanel)


    def rearrangePanels(self):
        for curPanel in self.subPanels:
            self.sizer.Hide(curPanel)
            self.sizer.Detach(curPanel)

        for curPanel in self.subPanels:
            self.sizer.Add(curPanel, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        #self.SetupScrolling()



class PsysmonDockingFrame(wx.Frame):
    ''' A base class for a frame holding AUI docks.
    '''

    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = 'docking frame', size = (1000, 600)):
        ''' Initialize the instance.
        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # The docking manager.
        self.mgr = wx.aui.AuiManager(self)

        # Create the tool ribbon bar instance.
        # The ribbon bar itself is filled using the init_ribbon_bar method
        # by the instance inheriting the PsysmonDockingFrame.
        self.ribbon = ribbon.RibbonBar(self, wx.ID_ANY)

        # Initialize the viewport.
        self.init_viewport()

        # Initialize the ribbon bar aui manager pane.
        self.init_ribbon_pane()

        # Create the plugins shared information bag, which holds all the
        # information, that's shared by the tracedisplay plugins.
        self.plugins_information_bag = psysmon.core.plugins.SharedInformationBag()

        # Create the hook manager and fill it with the allowed hooks.
        self.hook_manager = psysmon.core.util.HookManager(self)

        self.hook_manager.add_hook(name = 'plugin_activated',
                                   description = 'Called after a plugin was activated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'plugin_deactivated',
                                   description = 'Called after a plugin was deactivated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'shared_information_added',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'origin_rid': 'The resource id of the source of the shared information.',
                                                  'name': 'The name of the shared information.'})
        self.hook_manager.add_hook(name = 'shared_information_updated',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'updated_info': 'The shared information instance which was updated.'})
        self.hook_manager.add_view_hook(name = 'button_press_event',
                                        description = 'The matplotlib button_press_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'button_release_event',
                                        description = 'The matplotlib button_release_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'motion_notify_event',
                                        description = 'The matplotlib motion_notify_event in the view axes.')


    def init_viewport(self):
        ''' Initialize the viewport.
        '''
        self.center_panel = wx.Panel(parent = self, id = wx.ID_ANY)
        self.viewport_sizer = wx.GridBagSizer()
        self.viewport = psysmon.core.gui_view.Viewport(parent = self.center_panel)
        self.viewport_sizer.Add(self.viewport,
                                pos = (0,0),
                                flag = wx.EXPAND|wx.ALL,
                                border = 0)
        self.viewport_sizer.AddGrowableRow(0)
        self.viewport_sizer.AddGrowableCol(0)
        self.center_panel.SetSizer(self.viewport_sizer)

        self.mgr.AddPane(self.center_panel,
                         wx.aui.AuiPaneInfo().Name('viewport').CenterPane())


    def init_ribbon_pane(self):
        ''' Initialize the aui manager pane for the ribbon bar.
        '''
        self.mgr.AddPane(self.ribbon,
                         wx.aui.AuiPaneInfo().Top().
                                              Name('palette').
                                              Caption('palette').
                                              Layer(1).
                                              Row(0).
                                              Position(0).
                                              BestSize(wx.Size(-1,50)).
                                              MinSize(wx.Size(-1,80)).
                                              CloseButton(False))



    def init_ribbon_bar(self):
        ''' Initialize the ribbon bar with the plugins.
        '''
        # Build the ribbon bar based on the plugins.
        # First create all the pages according to the category.
        self.ribbonPages = {}
        self.ribbonPanels = {}
        self.ribbonToolbars = {}
        self.foldPanels = {}
        for curGroup, curCategory in sorted([(x.group, x.category) for x in self.plugins], key = itemgetter(0,1)):
            if curGroup not in self.ribbonPages.keys():
                self.logger.debug('Creating page %s', curGroup)
                self.ribbonPages[curGroup] = ribbon.RibbonPage(self.ribbon, wx.ID_ANY, curGroup)

            if curCategory not in self.ribbonPanels.keys():
                self.ribbonPanels[curCategory] = ribbon.RibbonPanel(self.ribbonPages[curGroup],
                                                                    wx.ID_ANY,
                                                                    curCategory,
                                                                    wx.NullBitmap,
                                                                    wx.DefaultPosition,
                                                                    wx.DefaultSize,
                                                                    agwStyle=ribbon.RIBBON_PANEL_NO_AUTO_MINIMISE)
                # TODO: Find out what I wanted to do with these lines!?!
                if curCategory == 'interactive':
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)
                else:
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)


        # Fill the ribbon bar with the plugin buttons.
        option_plugins = [x for x in self.plugins if x.mode == 'option']
        command_plugins = [x for x in self.plugins if x.mode == 'command']
        interactive_plugins = [x for x in self.plugins if x.mode == 'interactive']
        view_plugins = [x for x in self.plugins if x.mode == 'view']
        id_counter = 0

        for curPlugin in sorted(option_plugins, key = attrgetter('position_pref', 'name')):
                # Create a tool.
                curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter, 
                                                                          bitmap = curPlugin.icons['active'].GetBitmap(), 
                                                                          help_string = curPlugin.name,
                                                                          kind = ribbon.RIBBON_BUTTON_TOGGLE)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED, 
                                                             lambda evt, curPlugin=curPlugin : self.on_option_tool_clicked(evt, curPlugin), id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(command_plugins, key = attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)
                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_command_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_command_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        for curPlugin in sorted(interactive_plugins, key = attrgetter('position_pref', 'name')):
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                help_string = curPlugin.name)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_interactive_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                             lambda evt, curPlugin=curPlugin: self.on_interactive_tool_dropdown_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(view_plugins, key = attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)

                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_view_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_view_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        self.ribbon.Realize()



    def on_option_tool_clicked(self, event, plugin):
        ''' Handle the click of an option plugin toolbar button.

        Show or hide the foldpanel of the plugin.
        '''
        self.logger.debug('Clicked the option tool: %s', plugin.name)

        cur_toolbar = event.GetEventObject()
        if cur_toolbar.GetToolState(event.GetId()) != ribbon.RIBBON_TOOLBAR_TOOL_TOGGLED:
            if plugin.name not in self.foldPanels.keys():
                # The panel of the option tool does't exist. Create it and add
                # it to the panel manager.
                curPanel = plugin.buildFoldPanel(self)
                self.mgr.AddPane(curPanel,
                                 wx.aui.AuiPaneInfo().Right().
                                                      Name(plugin.name).
                                                      Caption(plugin.name).
                                                      Layer(2).
                                                      Row(0).
                                                      Position(0).
                                                      BestSize(wx.Size(300,-1)).
                                                      MinSize(wx.Size(200,100)).
                                                      MinimizeButton(True).
                                                      MaximizeButton(True).
                                                      CloseButton(False))
                # TODO: Add a onOptionToolPanelClose method to handle clicks of
                # the CloseButton in the AUI pane of the option tools. If the
                # pane is closed, the toggle state of the ribbonbar button has
                # be changed. The according event is aui.EVT_AUI_PANE_CLOSE.
                self.mgr.Update()
                self.foldPanels[plugin.name] = curPanel
            else:
                if not self.foldPanels[plugin.name].IsShown():
                    curPanel = self.foldPanels[plugin.name]
                    self.mgr.GetPane(curPanel).Show()
                    self.mgr.Update()
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
        else:
            if self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Hide()
                self.mgr.Update()

            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)




    def on_command_tool_clicked(self, event, plugin):
        ''' Handle the click of a command plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the command tool: %s', plugin.name)
        plugin.run()


    def on_command_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an command plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin : self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)



    def on_interactive_tool_clicked(self, event, plugin):
        ''' Handle the click of an interactive plugin toolbar button.

        Activate the tool.
        '''
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')
        elif len(active_plugin) == 1:
            active_plugin = active_plugin[0]
            self.deactivate_interactive_plugin(active_plugin)
        self.activate_interactive_plugin(plugin)


    def on_interactive_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an interactive plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin : self.onEditToolPreferences(evt, plugin), item)
        event.PopupMenu(menu)


    def on_edit_tool_preferences(self, event, plugin):
        ''' Handle the edit preferences dropdown click.

        '''
        self.logger.debug('Dropdown clicked -> editing preferences.')

        if plugin.name not in self.foldPanels.keys():
            #curPanel = plugin.buildFoldPanel(self.foldPanelBar)
            #foldPanel = self.foldPanelBar.addPanel(curPanel, plugin.icons['active'])

            curPanel = plugin.buildFoldPanel(self)
            self.mgr.AddPane(curPanel,
                             wx.aui.AuiPaneInfo().Right().
                                                  Name(plugin.name).
                                                  Caption(plugin.name).
                                                  Layer(2).
                                                  Row(0).
                                                  Position(0).
                                                  BestSize(wx.Size(300,-1)).
                                                  MinSize(wx.Size(200,100)).
                                                  MinimizeButton(True).
                                                  MaximizeButton(True))
            self.mgr.Update()
            self.foldPanels[plugin.name] = curPanel
        else:
            if not self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Show()
                self.mgr.Update()


    def on_view_tool_clicked(self, event, plugin):
        ''' Handle the click of an view plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the view tool: %s', plugin.name)

        if plugin.active == True:
            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
            self.displayManager.removeViewTool(plugin)
        else:
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.viewport.register_view_plugin(plugin)

        self.viewport.Refresh()
        self.viewport.Update()

        self.update_display()


    def on_view_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an view plugin toolbar button.

        '''
        self.logger.debug('Clicked the view tool dropdown button: %s', plugin.name)
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin : self.onEditToolPreferences(evt, plugin), item)
        event.PopupMenu(menu)


    def call_hook(self, hook_name, **kwargs):
        ''' Call the hook of the plugins.
        '''
        # TODO: Think about calling the hooks of all plugins, even if they are
        # not activated. This would keep track of changes within deactivated
        # plugins. It might cause some troubles with plugins, for which the
        # fold panel was not yet created, check this.
        active_plugins = [x for x in self.plugins if x.active or x.mode == 'command']
        self.hook_manager.call_hook(receivers = active_plugins,
                                    hook_name = hook_name,
                                    **kwargs)


    def add_shared_info(self, origin_rid, name, value):
        ''' Add a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information

        value : Dictionary
            The value of the shared information
        '''
        self.plugins_information_bag.add_info(origin_rid = origin_rid,
                                              name = name,
                                              value = value)
        self.call_hook('shared_information_added',
                       origin_rid = origin_rid,
                       name = name)


    def notify_shared_info_change(self, updated_info):
        ''' Notify tracedisplay, that a shared informtion was changed.
        '''
        self.call_hook('shared_information_updated',
                       updated_info = updated_info)


    def get_shared_info(self, **kwargs):
        ''' Get a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information
        '''
        return self.plugins_information_bag.get_info(**kwargs)
