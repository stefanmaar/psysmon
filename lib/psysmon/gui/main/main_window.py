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
import os
import webbrowser

import wx
import wx.aui
import wx.html
import wx.grid
import wx.lib.dialogs
from pubsub import pub
import wx.lib.colourdb


try:
    from agw import advancedsplash as splash
except ImportError:
    # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.advancedsplash as splash

import psysmon
import psysmon.gui.view as psy_view
import psysmon.gui
import psysmon.gui.dialog as psy_dlg
import psysmon.gui.dialog.data_source
import psysmon.gui.dialog.login
import psysmon.gui.dialog.new_project
import psysmon.gui.dialog.new_user
import psysmon.gui.dialog.pref_listbook
import psysmon.gui.main.logging_panel as psy_gmlp
import psysmon.gui.main.collection_panel as psy_gmcp
import psysmon.gui.main.inventory_panel as psy_gmip


class PsysmonGui(wx.Frame):

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
                menuItem = menu.Append(wx.ID_ANY, curLabel, cur_sub_menu)
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

        self.collectionPanel = psy_gmcp.CollectionPanel(self, self.psyBase, size=(300, -1))
        self.collectionNodeInventoryPanel = psy_gmip.CollectionNodeInventoryPanel(self, self.psyBase)

        self.loggingPanel = psy_gmlp.LoggingPanel(self, 
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
        dlg = psy_dlg.pref_listbook.ListbookPrefDialog(preferences = self.psyBase.pref_manager)
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
            dlg = psy_dlg.pref_listbook.ListbookPrefDialog(preferences = self.psyBase.project.pref)
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

