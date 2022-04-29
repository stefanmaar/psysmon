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
from __future__ import absolute_import      # Used for the signal import.
from __future__ import print_function

from builtins import str
from builtins import range
from builtins import object
import logging
import warnings
from operator import attrgetter

import wx
import wx.aui
import wx.html
import wx.grid
from wx import Choicebook
from operator import itemgetter
import wx.lib.mixins.listctrl as listmix
import wx.lib.dialogs
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub
import wx.lib.colourdb
try:
    from agw import ribbon as ribbon
except ImportError:  # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.ribbon as ribbon

try:
    from wx import SimpleHtmlListBox
except ImportError:
    from wx.html import SimpleHtmlListBox

import os
import signal
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy
import psysmon
import psysmon.core.gui_view
from psysmon.core.error import PsysmonError
from psysmon.core.waveclient import PsysmonDbWaveClient
from psysmon.core.waveclient import EarthwormWaveClient
from psysmon.core.waveclient import SeedlinkWaveClient
import psysmon.core.preferences_manager as pm
from psysmon.artwork.icons import iconsBlack10, iconsBlack16
import datetime
import webbrowser
#from wx.lib.mixins.inspection import InspectionMixin
import wx.lib.mixins.inspection as wit
import wx.lib.scrolledpanel as scrolled
from wx.lib.splitter import MultiSplitterWindow
import wx.lib.platebtn as platebtn

import psysmon.core.gui_preference_dialog

try:
    from agw import advancedsplash as splash
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.advancedsplash as splash


## The new psysmon.gui imports
import psysmon.gui as psy_gui
import psysmon.gui.dialog as psy_dlg
import psysmon.gui.dialog.data_source
import psysmon.gui.dialog.login
import psysmon.gui.dialog.new_project
import psysmon.gui.dialog.new_user
import psysmon.gui.validator as psy_val
import psysmon.gui.context_menu as psy_cm


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

            file_container = psysmon.core.json_util.FileContainer(config)
            try:
                with open(config_file, mode = 'w') as fid:
                    json.dump(file_container,
                              fp = fid,
                              cls = psysmon.core.json_util.ConfigFileEncoder)
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
        self.statusbar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
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
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
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
        dlg = psy_dlg.login.ProjectLoginDlg()
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
        dlg = psy_dlg.new_user.CreateNewDbUserDlg(parent=self,
                                                  psyBase=self.psyBase)
        dlg.ShowModal()
        dlg.Destroy()


    def onPsysmonPreferences(self, event):
        ''' The psysmon preferences callback.

        Parameters
        ----------
        event :
            The event passed to the callback.
        '''
        dlg = psysmon.core.gui_preference_dialog.ListbookPrefDialog(preferences = self.psyBase.pref_manager)
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
            dlg = psy_dlg.data_source.DataSourceDlg(parent = self,
                                                    psyBase = self.psyBase)
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
            EditScnlDataSourcesDlg = psy_dlg.data_source.EditScnlDataSourcesDlg
            dlg = EditScnlDataSourcesDlg(parent = self,
                                         psyBase = self.psyBase)
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
            dlg = psysmon.core.gui_preference_dialog.ListbookPrefDialog(preferences = self.psyBase.project.pref)
            dlg.ShowModal()
        else:
            self.logger.warning('You have to open a project first to edit the preferences.')


    ## Create new project menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onCreateNewProject(self, event):
        dlg = psy_dlg.new_project.CreateNewProjectDlg(psyBase=self.psyBase,
                                                      parent = self)
        dlg.ShowModal()


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



class Logger(object):

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
class CollectionListBox(SimpleHtmlListBox):

    ## The constructor
    #
    # @param self The object pointer. 
    def __init__(self, parent, id=wx.ID_ANY):
        SimpleHtmlListBox.__init__(self, parent=parent, id=id)
        cmData = (("edit node", parent.onEditNode),
                  ("remove node", parent.onRemoveNode),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))

        # create the context menu.
        self.contextMenu = psy_cm.psyContextMenu(cmData)

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
        self.contextMenu = psy_cm.psyContextMenu(cmData)

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
                  ("move up", parent.onMoveUp),
                  ("move down", parent.onMoveDown),
                  ("separator", None),
                  ("load collection", parent.onCollectionLoad),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))
        self.contextMenu = psy_cm.psyContextMenu(cmData)
        # Disable the delete collection menu item. It's not yet implemented.
        self.contextMenu.Enable(self.contextMenu.FindItemByPosition(6).GetId(), False)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onShowContextMenu)


    def onShowContextMenu(self, event):
        try:
            # Enable all node relevant context menu items.
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(2).GetId(), True)

            if self.Parent.selectedNodeType in ['node', 'looper']:
                selectedNode = self.GrandParent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
            elif self.Parent.selectedNodeType == 'looper_child':
                selectedLooper = self.GrandParent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
                selectedNode = selectedLooper.children[self.Parent.selectedLooperChildNodeIndex]
            else:
                selectedNode = None

            if selectedNode:
                if(selectedNode.mode == 'execute only'):
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
                else:
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)

                if selectedNode.enabled:
                    self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'disable node')
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
                else:
                    self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'enable node')
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            else:
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(2).GetId(), False)

        except Exception:
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
            self.logger.exception("Problems setting the context menu labels.")
        finally:
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

            for colNum, name in columns.items():
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
        self.contextMenu = psy_cm.psyContextMenu(cmData)

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

    def onMoveUp(self, event):
        ''' Move a node up in the collection.
        '''
        collection = self.psyBase.project.getActiveCollection()

        if self.selectedNodeType in ['node', 'looper']:
            # Move the node in the collection.
            selected_node = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            collection.moveNodeUp(selected_node)
        elif self.selectedNodeType == 'looper_child':
            # Move the node in the looper.
            selected_looper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            selected_node = selected_looper.children[self.selectedLooperChildNodeIndex]
            selected_looper.move_node_up(selected_node)
        self.refreshCollection()

    def onMoveDown(self, event):
        ''' Move a node up in the collection.
        '''
        collection = self.psyBase.project.getActiveCollection()
        if self.selectedNodeType in ['node', 'looper']:
            # Move the node in the collection.
            selected_node = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            collection.moveNodeDown(selected_node)
        elif self.selectedNodeType == 'looper_child':
            # Move the node in the looper.
            selected_looper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            selected_node = selected_looper.children[self.selectedLooperChildNodeIndex]
            selected_looper.move_node_down(selected_node)
        self.refreshCollection()


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
        if not evt.GetItem():
            return
        item_data = self.collectionTreeCtrl.GetItemPyData(evt.GetItem())
        node_type = item_data['node_type']
        node_pos = item_data['node_pos']
        self.logger.debug("Selected node %s at position %d in collection.", node_type, node_pos)
        self.selectedNodeType = node_type
        self.selectedCollectionNodeIndex = node_pos
        if node_type == 'looper_child':
            self.selectedLooperChildNodeIndex = item_data['child_pos']
        else:
            self.selectedLooperChildNodeIndex = -1


    # Load a collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onCollectionLoad(self, event):
        collections = self.psyBase.project.getCollection()
        choices = [x.name for x in collections.values()]
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
        self.logger.warning("Deleting a collection is not yet implemented.")
        # TODO: Implement the removal of a collection. Take care of the saved
        # collection file. Think about removing the currently active collection
        # or showing a dialog from which to select the collection to delete.

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
                    item_data = {'node_pos': k,
                                 'node_type': 'looper'}
                    self.collectionTreeCtrl.SetItemPyData(looper_node_item, item_data)
                    self.collectionTreeCtrl.SetItemImage(looper_node_item, self.collectionTreeCtrl.icons['looper_node'], wx.TreeItemIcon_Normal)
                    if k == self.selectedCollectionNodeIndex:
                        self.collectionTreeCtrl.SelectItem(looper_node_item)
                    if not curNode.enabled:
                        self.collectionTreeCtrl.SetItemTextColour(looper_node_item, wx.TheColourDatabase.Find('GREY70'))

                    for child_pos, cur_child in enumerate(curNode.children):
                        node_string = cur_child.name + '(child)'
                        node_item = self.collectionTreeCtrl.AppendItem(looper_node_item, node_string)
                        item_data = {'node_pos': k,
                                     'child_pos': child_pos,
                                     'node_type': 'looper_child'}
                        self.collectionTreeCtrl.SetItemPyData(node_item, item_data)
                        self.collectionTreeCtrl.SetItemImage(node_item, self.collectionTreeCtrl.icons['looper_node_child'], wx.TreeItemIcon_Normal)
                        if not curNode.enabled:
                            self.collectionTreeCtrl.SetItemTextColour(node_item, wx.TheColourDatabase.Find('GREY70'))
                else:
                    node_string = curNode.name
                    node_item = self.collectionTreeCtrl.AppendItem(self.collectionTreeCtrl.root, node_string)
                    item_data = {'node_pos': k,
                                 'node_type': 'node'}
                    self.collectionTreeCtrl.SetItemPyData(node_item, item_data)
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
        self.contextMenu = psy_cm.psyContextMenu(cmData)

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
        for colNum, name in columns.items():
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
        error_code = {1: 'general error', 2: 'collection execution error', 3: 'collection preparation error', 4: 'finalization error', 5: 'looper child error'}
        if data['procName'] in iter(self.processMap.keys()):
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
        logFile = os.path.join(self.GetParent().psyBase.project.tmpDir,
                               procName + ".log")
        self.logger.info("Showing the log file %s.", logFile)
        try:
            psysmon.core.util.display_file(logFile)
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

        for colNum, name in columns.items():
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
            child_pos = self.collectionPanel.selectedLooperChildNodeIndex
            self.psyBase.project.addNode2Looper(self.selectedCollectionNodeTemplate, pos,
                                                looper_pos = child_pos)
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
        for curPkg in self.psyBase.packageMgr.packages.values():
            nodeTemplates.update(curPkg.collectionNodeTemplates)

        self.updateNodeInvenotryList(nodeTemplates)
        listmix.ColumnSorterMixin.__init__(self, 4)
        self.nodeListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.nodeListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.nodeListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)


    def updateNodeInvenotryList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates.values():
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
