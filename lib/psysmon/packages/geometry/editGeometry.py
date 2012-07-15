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
The editGeometry module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classes of the editGeometry dialog window.
'''

import logging
from threading import Thread
import psysmon
from psysmon.core.packageNodes import CollectionNode
from psysmon.packages.geometry.inventory import Inventory, InventoryDatabaseController
from psysmon.packages.geometry.util import lon2UtmZone, zone2UtmCentralMeridian, ellipsoids
import wx.aui
import wx.grid
import os
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

from wx.lib.pubsub import Publisher as pub
import numpy as np
from mpl_toolkits.basemap import Basemap 
from obspy.signal import pazToFreqResp
from obspy.core.utcdatetime import UTCDateTime


class EditGeometry(CollectionNode):
    '''
    The EditGeometry class.
    '''

    ## The edit method.
    #
    # The EditGeometry node is a standalone node - ignore the edit method.
    def edit(self):
        '''
        The edit method.

        The EditGeometry node is a standalone node. Ignore the edit method.

        :param self: The object pointer.
        :type self: A `~psysmon.packages.geometry.editGeometry.EditGeometry` instance.
        '''
        pass


    ## The execute method.
    #
    # Show the EditGeometry dialog window.
    #
    # @param self The object pointer.
    # @param psyProject The current pSysmon project.
    # @param prevNodeOutput The output of the previous collection node. 
    # Not used in this method.
    def execute(self, prevNodeOutput={}):
        dlg = EditGeometryDlg(self, self.project)
        dlg.Show()




## The pSysmon main GUI
# 
# 
class EditGeometryDlg(wx.Frame):

    ## The constructor
    #
    # @param self The Object pointer.
    # @param psyBase The pSysmn base object.
    def __init__(self, collectionNode, psyProject, parent=None, id=wx.ID_ANY, title='edit geometry', 
                 size=(1000,600)):
        wx.Frame.__init__(self, parent=parent, id=id, 
                           title=title, 
                           pos=wx.DefaultPosition,
                           style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        ## The collection node calling this dialog.
        self.collectionNode = collectionNode


        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        ## The current pSysmon project.
        self.psyProject = psyProject

        ## The loaded inventories.
        #
        # The keys of the dictionaries are the inventory names.
        self.inventories = {}

        # The inventory currently selected by the user.
        self.selectedInventory = None

        # initialize the user interface
        self.initUI()

        #self.initUserSelections()

        # The inventory database controller.
        self.dbController = InventoryDatabaseController(self.psyProject)

        # Load the inventory from the database.
        self.loadInventoryFromDb()




    def initUserSelections(self):
        if self.collectionNode.property['inputFiles']:
            self.logger.debug("Set the list to the previously selected files.")

            index = 0
            for curFile in self.collectionNode.property['inputFiles']:
                fSize = os.path.getsize(curFile['filename']);
                fSize = fSize/1024.0
                self.fileListCtrl.InsertStringItem(index, curFile['format'])
                self.fileListCtrl.SetStringItem(index, 1, curFile['filename'])
                self.fileListCtrl.SetStringItem(index, 2, "%.2f" % fSize)
                index += 1


    ## Initialize the user interface.
    #
    # @param self The object pointer.
    def initUI(self):       
        self.mgr = wx.aui.AuiManager(self)

        self.createMenuBar()

        self.inventoryTree = InventoryTreeCtrl(self, wx.ID_ANY, wx.DefaultPosition, (300, 400),
                               wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT
                               #wx.TR_HAS_BUTTONS
                               #| wx.TR_EDIT_LABELS
                               #| wx.TR_MULTIPLE
                               #| wx.TR_HIDE_ROOT
                               )

        self.inventoryViewNotebook = InventoryViewNotebook(self, wx.ID_ANY)

        self.mgr.AddPane(self.inventoryTree, wx.aui.AuiPaneInfo().Name("inventory").
                         Caption("inventory").Left().CloseButton(False).
                         BestSize(wx.Size(200,-1)).MinSize(wx.Size(200,-1)))

        self.mgr.AddPane(self.inventoryViewNotebook, wx.aui.AuiPaneInfo().Name("view").
                          CenterPane().BestSize(wx.Size(300,300)).MinSize(wx.Size(100,-1)))

        # Create the status bar.
        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -3])
        self.statusbar.SetStatusText("Ready", 0)
        self.statusbar.SetStatusText("Edit the pSysmon inventory.", 1)

        # tell the manager to 'commit' all the changes just made
        self.mgr.Update()


    def loadInventoryFromDb(self):
        ''' Load the inventory from the project database.

        '''
        try:
            curInventory = self.dbController.load()
        except Warning as w:
                print w

        self.inventories[curInventory.name] = curInventory
        self.inventoryTree.updateInventoryData()
        self.selectedInventory = curInventory


    ## Define the EditGeometryDlg menus.  
    #
    # The EditGeometryDlg menus are created depending on the list returned.
    #
    # @param self The Object pointer.
    def menuData(self):
        return (("File",
                 ("Import from XML", "Import inventory from XML file.", self.onImportFromXml),
                 ("", "", ""),
                 ("&Exit", "Exit pSysmon.", self.onExit)),
                ("Edit",
                 ("Save to database", "Save the selected inventory to database.", self.onSave2Db)),
                ("Help",
                 ("&About", "About pSysmon", self.onAbout))
               )   


    ## Import from XML menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onImportFromXml(self, event):
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard="xml file (*.xml)"\
                     "All files (*.*)|*.*",
            style=wx.OPEN | wx.CHANGE_DIR
            )

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            path = dlg.GetPath()
            curInventory = Inventory("new inventory")

            try:
                curInventory.importFromXml(path)
            except Warning as w:
                    print w

            self.inventories[curInventory.name] = curInventory
            self.inventoryTree.updateInventoryData()

    ## Save to database menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onSave2Db(self, event):
        if not self.selectedInventory:
            self.logger.info("No inventory selected.")
            return

        if self.selectedInventory.__class__.__name__  != 'Inventory' :
            self.logger.info("Please select the inventory to be written to the database.")
            return

        self.logger.debug("inventory type: %s",self.selectedInventory.type)

        if self.selectedInventory.type not in 'db':
            self.logger.debug("Saving a non db inventory to the database.")
            self.dbController.write(self.selectedInventory)
            self.loadInventoryFromDb()

        else:
            self.logger.debug("Updating the existing project inventory database.")
            self.dbController.updateDb(self.selectedInventory)


    ## Exit menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onExit(self, event):
        # Check if an unsaved database inventory exists.
        for curInventory in self.inventories.itervalues():
            if curInventory.hasChanged():
                if curInventory.type.lower() == 'db':
                    curInventory.updateDb()

        # delete the frame
        self.Destroy()

    ## About menu button callback.
    #
    # @param self The Object pointer.
    # @param event The event object.       
    def onAbout(self, event):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "The edit geometry dialog!!!!!!", "About EditGeometryDlg", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()


    ## Create the EditGeometryDlg menubar.
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





class InventoryTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)

        self.logger = self.GetParent().logger

        il = wx.ImageList(16, 16)
        self.icons = {}
        self.icons['xmlInventory'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','notebook_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()) 
        self.icons['recorderList'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','list_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()) 
        self.icons['stationList'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','list_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()) 
        self.icons['sensorList'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','list_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap()) 
        self.icons['networkList'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','list_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.icons['network'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','network_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.icons['station'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','flag_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.icons['recorder'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','help_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.icons['sensor'] = il.Add(wx.Image(os.path.join(os.path.dirname(__file__), 'icons','help_16.png'), wx.BITMAP_TYPE_PNG).ConvertToBitmap())

        self.AssignImageList(il)

        self.root = self.AddRoot("geometry")

        self.SetMinSize(size)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onItemSelectionChanged)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.onBeginDrag)
        self.Bind(wx.EVT_TREE_END_DRAG, self.onEndDrag)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKeyDown)



    ## Handle the key pressed events.
    def onKeyDown(self, event):
        keycode = event.GetKeyCode()
        source = self.GetPyData(self.GetSelection())

        if keycode == wx.WXK_DELETE:
            if isinstance(source, tuple):
                self.handleDeleteSensor(self.GetSelection())

        event.Skip()


    ## Allow drag'n drop for leaf items.
    def onBeginDrag(self, event):
        self.logger.debug("OnBeginDrag")
        event.Allow()
        self.dragItem = event.GetItem()

    ## End drag'n drop for leaf items.
    def onEndDrag(self, event):
        self.logger.debug("OnEndDrag")

        # If we dropped somewhere that isn't on top of an item, ignore the event
        if event.GetItem().IsOk():
              target = event.GetItem()
        else:
             return

        # Make sure this member exists.
        try:
            source = self.dragItem
        except:
            return

        # Prevent the user from dropping an item inside of itself
        if target is source:
            self.logger.info("The tree item can not be moved in to itself!")
            self.Unselect()
            return

        sourceData = self.GetPyData(source)

        if isinstance(sourceData, tuple):
            self.logger.info("You can only drag sensors from the Recorders section.")
            return

        if isinstance(sourceData, psysmon.packages.geometry.inventory.Sensor):
            self.handleSensorDrag(source, target)
        elif isinstance(sourceData, psysmon.packages.geometry.inventory.Station):
            self.handlesStationDrag(source, target)


    ## Handle the dragging of a sensor leaf.
    def handleSensorDrag(self, source, target):
        sourceData = self.GetPyData(source)
        targetData = self.GetPyData(target)

        self.logger.debug("SOURCE")
        self.logger.debug("%s", sourceData)

        self.logger.debug("TARGET")
        self.logger.debug("%s", targetData)

        if isinstance(targetData, psysmon.packages.geometry.inventory.Recorder):
            self.logger.debug("Dragging sensor to recorder.")
            # Remove source from parent recorder.
            oldRecorder = sourceData.parentRecorder
            sourceData.parentRecorder.popSensor(sourceData)

            # Add source to target recorder.
            targetData.addSensor(sourceData)

            # Send an inventory update event.
            msgTopic = 'inventory.update.sensorAssignment'
            msg = (sourceData, 'sensor2Recorder', (oldRecorder, targetData))
            pub.sendMessage(msgTopic, msg)

        elif isinstance(targetData, psysmon.packages.geometry.inventory.Station):
            self.logger.debug("Dragging sensor to a station")
            targetData.addSensor(sourceData, UTCDateTime('1976-01-01'), None)


        #targetData.addSensor(sourceData, None, None)
        self.updateInventoryData()



    ## Handle the dragging of a station leaf.
    def handleStationDrag(self, source, target):
        pass


    ## Handle the deletion of a sensor.
    def handleDeleteSensor(self, source):
       
        self.logger.debug('Removing a sensor from station.')
        
        sourceData = self.GetPyData(source)
        
        self.logger.debug('%s', sourceData)
        if not isinstance(sourceData, tuple):
            self.logger.warning('The object you are trying to delete is not a sensor.')
            return

        parent = self.GetItemParent(source)
        parentStation = self.GetPyData(parent)

        ret  = wx.MessageBox('Are you sure to remove this sensor?', 'Question', 
                             wx.YES_NO | wx.NO_DEFAULT, self)
        if ret == wx.YES:
            self.logger.debug("Removing the sensor")
            parentStation.removeSensor(sourceData)

        self.updateInventoryData()



    def onItemSelectionChanged(self, evt):
        self.logger.debug("onItemSelectionChanged: %s", self.GetItemText(evt.GetItem()))
        pyData = self.GetItemPyData(evt.GetItem())

        # The pydata of the stationsensors is a tuple.
        if isinstance(pyData, tuple):
            pyData = pyData[0]

        if(pyData.__class__.__name__ == 'Station'):
            self.Parent.inventoryViewNotebook.updateStationListView(pyData)
            self.Parent.selectedInventory = pyData.parentInventory
        elif(pyData.__class__.__name__ == 'Sensor'):
            self.Parent.inventoryViewNotebook.updateSensorListView(pyData)
            self.Parent.selectedInventory = pyData.parentInventory
        elif(pyData.__class__.__name__ == 'Inventory'):
            self.Parent.selectedInventory = pyData

    ## Update the inventory tree.
    #
    # @param self The object pointer.    
    def updateInventoryData(self):
        # Delete all items below the root.
        self.DeleteChildren(self.root)

        # rebuild the inventory tree.
        for curKey, curInventory in self.Parent.inventories.iteritems():
            inventoryItem = self.AppendItem(self.root, curKey + '(' + curInventory.type + ')')
            self.SetItemPyData(inventoryItem, curInventory)
            self.SetItemBold(inventoryItem, True)
            self.SetItemImage(inventoryItem, self.icons['xmlInventory'], wx.TreeItemIcon_Normal)

            recorderItem = self.AppendItem(inventoryItem, 'Recorders')
            self.SetItemPyData(recorderItem, curInventory.recorders)
            self.SetItemBold(recorderItem, True)
            self.SetItemImage(recorderItem, self.icons['recorderList'], wx.TreeItemIcon_Normal)

            networkItem = self.AppendItem(inventoryItem, 'Networks')
            self.SetItemPyData(networkItem, curInventory.stations)
            self.SetItemBold(networkItem, True)
            self.SetItemImage(networkItem, self.icons['networkList'], wx.TreeItemIcon_Normal)

            stationItem = self.AppendItem(inventoryItem, 'unassigned stations')
            self.SetItemPyData(stationItem, curInventory.stations)
            self.SetItemBold(stationItem, True)
            self.SetItemImage(stationItem, self.icons['stationList'], wx.TreeItemIcon_Normal)

            unassignedSensorItem = self.AppendItem(inventoryItem, 'unassigned sensors')
            self.SetItemPyData(unassignedSensorItem, curInventory.sensors)
            self.SetItemBold(unassignedSensorItem, True)
            self.SetItemImage(unassignedSensorItem, self.icons['sensorList'], wx.TreeItemIcon_Normal)

            # Fill the recorders.
            for curRecorder in sorted(curInventory.recorders, key=lambda recorder: recorder.serial):
                curRecorderItem = self.AppendItem(recorderItem, curRecorder.serial + '(' + curRecorder.type + ')')
                self.SetItemPyData(curRecorderItem, curRecorder)
                self.SetItemImage(curRecorderItem, self.icons['recorder'], wx.TreeItemIcon_Normal)
                for curSensor in sorted(curRecorder.sensors, key=lambda sensor: (sensor.serial, sensor.channelName)):
                    item = self.AppendItem(curRecorderItem, curSensor.serial + ':' +curSensor.recChannelName + ':' + curSensor.channelName + ':' + curSensor.type)

                    self.SetItemPyData(item, curSensor)
                    self.SetItemImage(item, self.icons['sensor'], wx.TreeItemIcon_Normal)

            # Fill the unasigned stations.
            for curStation in curInventory.stations:
                curStationItem = self.AppendItem(stationItem, curStation.name+':'+curStation.location)
                self.SetItemPyData(curStationItem, curStation)
                self.SetItemImage(curStationItem, self.icons['station'], wx.TreeItemIcon_Normal)
                for (curSensor, curBegin, curEnd) in curStation.sensors:
                    item = self.AppendItem(curStationItem, curSensor.recorderSerial + ':' + curSensor.serial + ':' + curSensor.recChannelName)
                    self.SetItemPyData(item, (curSensor, curBegin, curEnd))
                    self.SetItemImage(item, self.icons['sensor'], wx.TreeItemIcon_Normal)

            # Fill the unassigned sensors.
            for curSensor in curInventory.sensors:
                    item = self.AppendItem(unassignedSensorItem, curSensor.serial + '(' + curSensor.type + ')')
                    self.SetItemPyData(item, curSensor)
                    self.SetItemImage(item, self.icons['sensor'], wx.TreeItemIcon_Normal)

            # Fill the networks.
            for key in sorted(curInventory.networks.iterkeys()):
                curNetwork = curInventory.networks[key]
                curNetworkItem = self.AppendItem(networkItem, curNetwork.name)
                self.SetItemPyData(curNetworkItem, curNetwork)
                self.SetItemImage(curNetworkItem, self.icons['network'], wx.TreeItemIcon_Normal)

                for key in sorted(curNetwork.stations.iterkeys()):
                    curStation = curNetwork.stations[key]
                    curStationItem = self.AppendItem(curNetworkItem, curStation.name+':'+curStation.location)
                    self.SetItemPyData(curStationItem, curStation)
                    self.SetItemImage(curStationItem, self.icons['station'], wx.TreeItemIcon_Normal)
                    for (curSensor, curBegin, curEnd) in sorted(curStation.sensors, key = lambda sensor: (sensor[0].recorderSerial, sensor[0].serial, sensor[0].recChannelName)):
                        item = self.AppendItem(curStationItem, curSensor.recorderSerial + ':' + curSensor.serial + ':' + curSensor.recChannelName)
                        self.SetItemPyData(item, (curSensor, curBegin, curEnd))
                        self.SetItemImage(item, self.icons['sensor'], wx.TreeItemIcon_Normal)


        self.ExpandAll()



class InventoryViewNotebook(wx.Notebook):
    def __init__(self, parent, id):
        wx.Notebook.__init__(self, parent, id, size=(21,21), style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )

        self.logger = self.GetParent().logger

        self.inventory = None

        self.listViewPanel = ListViewPanel(self)
        self.AddPage(self.listViewPanel, "list view")

        #win = self.makePanel()
        #self.AddPage(win, "map view")

        self.mapViewPanel = MapViewPanel(self)
        self.AddPage(self.mapViewPanel, "map view")

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)


    ## Show the station data in the list view.
    #
    def updateStationListView(self, station):
        self.logger.debug("updating the station listview") 
        self.listViewPanel.showControlPanel('station', station)   

    ## Show the station data in the list view.
    #
    def updateSensorListView(self, sensor):
        self.logger.debug("updating the sensor listview") 
        self.listViewPanel.showControlPanel('sensor', sensor)  

    def updateMapView(self, inventory):
        '''
        Initialize the map view panel with the selected inventory.
        '''
        self.logger.debug("Initializing the mapview")
        #t = Thread(target = self.mapViewPanel.initMap, args = (inventory, ))
        #t.setDaemon(True)
        #t.start()
        if inventory != self.inventory:
            self.mapViewPanel.initMap(inventory)
            self.inventory = inventory

    def onPageChanged(self, event):
        if event.GetSelection() == 1:
            self.updateMapView(self.Parent.selectedInventory)
        event.Skip()


    ## Create a panel
    def makePanel(self):
        p = wx.Panel(self, wx.ID_ANY)
        return p


class ListViewPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.sizer = wx.GridBagSizer(5, 5)

        self.controlPanels = {}
        self.controlPanels['station'] = StationsPanel(self, wx.ID_ANY)
        #self.controlPanels['station'].SetBackgroundColour('maroon')

        self.controlPanels['sensor'] = SensorsPanel(self, wx.ID_ANY)
        #self.controlPanels['sensor'].SetBackgroundColour('orchid')
        self.controlPanels['station'].Hide()

        #sizer.Add(self.controlPanels['station'], pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.Add(self.controlPanels['sensor'], pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizerAndFit(self.sizer)



    def showControlPanel(self, name, data):   

        activePanel = self.sizer.FindItemAtPosition((0,0))
        activePanel.GetWindow().Hide()
        self.sizer.Detach(activePanel.GetWindow())

        self.controlPanels[name].updateData(data)

        self.controlPanels[name].Show()
        self.sizer.Add(self.controlPanels[name], pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.Layout()



class MapViewPanel(wx.Panel):
    '''
    The MapViewPanel class.

    This class creates a panel holding a mpl_toolkits.basemap map.
    This map is used to display the stations contained in the inventory.

    :ivar sizer: The sizer used for the panel layout.
    :ivar mapFigure: The matplotlib figure holding the map axes.
    :ivar mapAx: The matplotlib axes holding the Basemap.
    :ivar mapCanvas: The wxPython figureCanvas holding the matplotlib figure.
    :ivar map: The station map (`~mpl_toolkits.basemap.Basemap`).
    '''
    def __init__(self, parent, id=wx.ID_ANY):
        '''
        The constructor.

        Create an instance of the MapViewPanel class.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.geometry.MapViewPanel`
        :param parent: The parent object containing the panel.
        :type self: A wxPython window.
        :param id: The id of the panel.
        :type id: 
        '''
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.sizer = wx.GridBagSizer(5, 5)

        self.mapFigure = Figure((8,4), dpi=75, facecolor='white')
        self.mapAx = self.mapFigure.add_subplot(111)
        self.mapCanvas = FigureCanvas(self, -1, self.mapFigure)

        self.sizer.Add(self.mapCanvas, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizerAndFit(self.sizer)




    def initMap(self, inventory):
        '''
        Initialize the map parameters.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.geometry.MapViewPanel`
        '''
        self.mapConfig = {}
        self.stations = []

        # Get the lon/lat limits of the inventory.
        lonLat = []
        for curNet in inventory.networks.itervalues():
            lonLat.extend([stat.getLonLat() for stat in curNet.stations.itervalues()])
            self.stations.extend([stat for stat in curNet.stations.itervalues()])

        lonLatMin = np.min(lonLat, 0)
        lonLatMax = np.max(lonLat, 0)
        self.mapConfig['utmZone'] = lon2UtmZone(np.mean([lonLatMin[0], lonLatMax[0]]))
        self.mapConfig['ellips'] = 'wgs84'
        self.mapConfig['lon_0'] = zone2UtmCentralMeridian(self.mapConfig['utmZone'])
        self.mapConfig['lat_0'] = 0
        self.mapConfig['limits'] = np.hstack([np.floor(lonLatMin), np.ceil(lonLatMax)]) 
        #self.mapConfig['lon_0'] = np.mean([lonLatMin[0], lonLatMax[0]])
        #self.mapConfig['lat_0'] = np.mean([lonLatMin[1], lonLatMax[1]])

        lon = [x[0] for x in lonLat]
        lat = [x[1] for x in lonLat]

        self.logger.debug('Setting up the basemap.')
        self.map = Basemap(projection='tmerc',
                           lon_0 = self.mapConfig['lon_0'],
                           lat_0 = self.mapConfig['lat_0'],
                           k_0 = 0.9996,
                           rsphere=ellipsoids[self.mapConfig['ellips']],
                           llcrnrlon = self.mapConfig['limits'][0],
                           llcrnrlat = self.mapConfig['limits'][1],
                           urcrnrlon = self.mapConfig['limits'][2],
                           urcrnrlat = self.mapConfig['limits'][3],
                           resolution='h',
                           ax=self.mapAx, 
                           suppress_ticks=True)

        self.logger.debug('proj4string: %s', self.map.proj4string)

        self.map.drawcountries()
        self.map.drawcoastlines()
        self.map.drawrivers(color='b')
        #self.map.etopo()
        x,y = self.map(lon, lat)
        self.map.scatter(x, y, s=100, marker='^', color='r', picker=5)
        self.map.drawmapboundary()
        #self.map.ax.grid()
        self.map.drawparallels(np.arange(self.mapConfig['limits'][1], self.mapConfig['limits'][3], 0.5),
                               labels=[1,0,0,0]) # draw parallels
        self.map.drawmeridians(np.arange(self.mapConfig['limits'][0], self.mapConfig['limits'][2], 0.5),
                               labels=[0,0,0,1]) # draw parallels
        self.mapCanvas.mpl_connect('pick_event', self.onPick)

    def onPick(self, event):
        '''
        Handle the map pick event.
        '''
        pickedStation = self.stations[event.ind[0]]
        self.logger.debug("picked a station: %s", pickedStation.name)


    def updatemap(self):
        '''
        Update the map elements.
        '''
        pass


    def createMap(self):
        '''
        Create the basemap.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.geometry.MapViewPanel`
        '''
        # create Basemap instance for Robinson projection.
        self.map = Basemap(projection='robin', lon_0=0, ax=self.mapAx)
        self.map.drawcoastlines()
        self.map.drawcountries()
        self.map.drawmapboundary()
        # draw parallels and meridians.
        #m.drawparallels(np.arange(-60.,90.,30.),labels=[1,0,0,0])
        #m.drawmeridians(np.arange(0.,420.,60.),labels=[0,0,0,1])




class StationsPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        ## The currently displayed station.
        self.displayedStation = None;

        self.sizer = wx.GridBagSizer(5, 5)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True) 

        # Create the station grid.
        #stationColLabels = ['id', 'name', 'network', 'x', 'y', 'z', 'coordSystem', 'description']
        fields = self.getStationFields()
        self.stationGrid = wx.grid.Grid(self, size=(-1, 100))
        self.stationGrid.CreateGrid(1, len(fields))

        # Bind the stationGrid events.
        self.stationGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onStationCellChange)

        for k, (name, label, attr)  in enumerate(fields):
            self.stationGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.stationGrid.SetColAttr(k, roAttr)

        self.stationGrid.AutoSizeColumns() 

        self.sizer.Add(self.stationGrid, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)


        # Create the sensor grid.
        fields = self.getSensorFields()
        self.sensorGrid = wx.grid.Grid(self, size=(100,100))
        self.sensorGrid.CreateGrid(5, len(fields))

        # Bind the stationGrid events.
        self.sensorGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onSensorTimeCellChange)

        for k, (name, label, attr) in enumerate(fields):
            self.sensorGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.sensorGrid.SetColAttr(k, roAttr)


        self.sizer.Add(self.sensorGrid, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)


        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)
        self.SetSizerAndFit(self.sizer)



    ## The cell edit callback.    
    def onStationCellChange(self, evt):
        selectedParameter = self.stationGrid.GetColLabelValue(evt.GetCol())
        gridStationFields = self.getStationFields();
        colLabels = [x[1] for x in gridStationFields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridStationFields[ind][0]
            fieldAttr = gridStationFields[ind][2]
            if fieldAttr == 'editable':
                self.displayedStation[fieldName] =  self.stationGrid.GetCellValue(evt.GetRow(), evt.GetCol())
                self.displayedStation.parentInventory.refreshNetworks()
                self.GetParent().GetParent().GetParent().inventoryTree.updateInventoryData()
                self.logger.debug(self.GetParent().GetParent().GetParent())
        else:
            pass



    ## The cell edit callback.    
    def onSensorTimeCellChange(self, evt):
        selectedParameter = self.sensorGrid.GetColLabelValue(evt.GetCol())
        value = self.sensorGrid.GetCellValue(evt.GetRow(), evt.GetCol())

        self.logger.debug("Edited row: %d", evt.GetRow())

        sensor = self.tableSensors[evt.GetRow()][0]

        if selectedParameter == 'start':
            (timeSet, msg) = self.displayedStation.changeSensorStartTime(sensor, value)
        elif selectedParameter == 'end':
            (timeSet, msg) = self.displayedStation.changeSensorEndTime(sensor, value)

        self.sensorGrid.SetCellValue(evt.GetRow(), evt.GetCol(), str(timeSet))
        self.displayedStation.parentInventory.refreshNetworks()

        if msg:
            self.logger.debug("Message: %s", msg)
            dlg = wx.MessageDialog(self, msg,
                               'Error while changing the deployment time.',
                               wx.OK 
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
            dlg.ShowModal()
            dlg.Destroy()


    def updateData(self, station):

        self.displayedStation = station

        # Update the sensor grid fields.
        self.setGridValues(station, self.stationGrid, self.getStationFields(), 0)

        # Clear the sensor grid rows.
        self.sensorGrid.DeleteRows(0, self.sensorGrid.GetNumberRows())

        # Add the new number of rows.
        self.sensorGrid.AppendRows(len(station.sensors))

        # Sort the station sensors and save the sorted list. This list is 
        # used when changing the sensor values in the inventory.
        self.tableSensors = sorted(station.sensors, key = lambda sensor: (sensor[0].recorderSerial, sensor[0].serial, sensor[0].channelName))
        #self.tableSensors = sorted(station.sensors, key = attrgetter('channel'))
        # Set the sensor values.
        for k,(curSensor, startTime, endTime) in enumerate(self.tableSensors):
            self.sensorGrid.SetCellValue(k, 0, str(curSensor.id))
            self.sensorGrid.SetCellValue(k, 1, curSensor.label)
            self.sensorGrid.SetCellValue(k, 2, curSensor.recorderSerial)
            self.sensorGrid.SetCellValue(k, 3, curSensor.recorderType)
            self.sensorGrid.SetCellValue(k, 4, curSensor.serial)
            self.sensorGrid.SetCellValue(k, 5, curSensor.type)
            self.sensorGrid.SetCellValue(k, 6, curSensor.recChannelName)
            self.sensorGrid.SetCellValue(k, 7, curSensor.channelName)
            if startTime:
                self.sensorGrid.SetCellValue(k, 8, str(startTime))

            if endTime:
                self.sensorGrid.SetCellValue(k, 9, str(endTime))
            else:
                self.sensorGrid.SetCellValue(k, 9, 'running')

        self.sensorGrid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        for pos, (field, label, attr) in enumerate(fields):
            if field and object[field]:
                grid.SetCellValue(rowNumber, pos, str(object[field]))
            grid.AutoSizeColumns()

    ## The station grid columns. 
    def getStationFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('name', 'name', 'editable'))
        tableField.append(('location', 'location', 'editable'))
        tableField.append(('network', 'network', 'editable'))
        tableField.append(('x', 'x', 'editable'))
        tableField.append(('y', 'y', 'editable'))
        tableField.append(('z', 'z', 'editable'))
        tableField.append(('coordSystem', 'coord. system', 'editable'))
        tableField.append(('description', 'description', 'editable'))
        return tableField


    ## The sensor grid columns.
    def getSensorFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('label', 'label', 'readonly'))
        tableField.append(('recorderSerial', 'rec.serial', 'readonly'))
        tableField.append(('recorderType', 'rec. type', 'readonly'))
        tableField.append(('serial', 'serial', 'readonly'))
        tableField.append(('type', 'type', 'readonly'))
        tableField.append(('recorderChannel', 'rec. channel', 'readonly'))
        tableField.append(('channel', 'channel', 'readonly'))
        tableField.append(('start', 'start', 'editable'))
        tableField.append(('end', 'end', 'editable'))
        return tableField


class SensorsPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY, size=(-1,-1)):
        #from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
        #from matplotlib.figure import Figure

        ## The currently displayed sensor.
        self.displayedSensor = None

        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.mgr = wx.aui.AuiManager(self)


        #self.mgr.AddPane(self.inventoryViewNotebook, wx.aui.AuiPaneInfo().Name("view").
        #                  CenterPane().BestSize(wx.Size(500,300)).MinSize(wx.Size(500,-1)))

        # Create the sensor grid.
        #sensorLabels = ['id', 'rec. id', 'rec. serial', 'rec. type', 
        #                    'serial', 'type', 'rec. channel', 'channel']
        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True) 

        fields = self.getSensorFields()
        self.sensorGrid = wx.grid.Grid(self, size=(-1, -1))
        self.sensorGrid.CreateGrid(1, len(fields))

        # Bind the sensorGrid events.
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE,
                  self.onSensorCellChange,
                  self.sensorGrid)

        for k, (name, label, attr)  in enumerate(fields):
            self.sensorGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.sensorGrid.SetColAttr(k, roAttr)

        self.sensorGrid.AutoSizeColumns() 

        #self.sizer.Add(self.sensorGrid, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.mgr.AddPane(self.sensorGrid, wx.aui.AuiPaneInfo().Name("sensor").
                         CentrePane().Layer(1).Row(0).Position(0).BestSize(wx.Size(-1,20)))


        # Create the sensor grid.
        fields = self.getParameterFields()
        self.paramGrid = wx.grid.Grid(self, size=(-1, 100))
        #self.paramGrid.SetMinSize((-1, 100))
        self.paramGrid.CreateGrid(1, len(fields))

        # Bind the paramGrid events.
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE,
                  self.onSensorParameterCellChange,
                  self.paramGrid)

        for k, (name, label, attr)  in enumerate(fields):
            self.paramGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.paramGrid.SetColAttr(k, roAttr)

        self.paramGrid.AutoSizeColumns()

        #self.sizer.Add(self.tfGrid, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.mgr.AddPane(self.paramGrid, wx.aui.AuiPaneInfo().Name("parameters").Caption("parameters").
                         Bottom().Row(1).Position(0).Layer(0).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().
                         BestSize(wx.Size(300,80)).MinSize(wx.Size(100,100)))


        # Create the plot area.
        self.tfFigure = Figure((8,4), dpi=75, facecolor='white')
        #rect = 0.1,0.1,0.8,0.8
        #self.tfAxis = self.tfFigure.add_axes(rect, xscale='log', axis_bgcolor='w')
        self.tfMagAxis = self.tfFigure.add_subplot(121, xscale='linear', axis_bgcolor='w')
        self.tfMagAxis.set_xlabel('Frequency [Hz]', fontsize=10)
        self.tfMagAxis.set_ylabel('Amplitude', fontsize=10)
        self.tfMagAxis.set_title('Amplitude Response', fontsize=10)
        self.tfMagAxis.grid(True)

        self.tfPhaseAxis = self.tfFigure.add_subplot(122, xscale='linear', axis_bgcolor='w')
        self.tfPhaseAxis.set_xlabel('Frequency [Hz]', fontsize=10)
        self.tfPhaseAxis.set_ylabel('Phase [rad]', fontsize=10)
        self.tfPhaseAxis.set_title('Phase Response', fontsize=10)
        self.tfPhaseAxis.grid(True)

        self.tfCanvas = FigureCanvas(self, -1, self.tfFigure)
        self.logger.debug(self.tfCanvas.GetBestSize())
        self.tfCanvas.SetSize((-1, 320))
        self.tfCanvas.SetMinSize((-1, 320))
        #self.sizer.Add(self.tfCanvas, pos=(2,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.mgr.AddPane(self.tfCanvas, wx.aui.AuiPaneInfo().Name("transfer function").Caption("transfer function").
                         Bottom().Row(0).Position(0).Layer(0).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().
                         BestSize(wx.Size(-1,250)).MinSize(wx.Size(-1,250)))

        # tell the manager to 'commit' all the changes just made
        self.mgr.Update()

        #self.sizer.AddGrowableRow(2)
        #self.sizer.AddGrowableCol(0)
        #self.SetSizerAndFit(self.sizer)

    def onSensorCellChange(self, evt):
        selectedParameter = self.sensorGrid.GetColLabelValue(evt.GetCol())
        gridSensorFields = self.getSensorFields();
        colLabels = [x[1] for x in gridSensorFields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridSensorFields[ind][0]
            self.displayedSensor[fieldName] =  self.sensorGrid.GetCellValue(evt.GetRow(), evt.GetCol())
            self.displayedSensor.parentInventory.refreshRecorders()
            self.GetParent().GetParent().GetParent().inventoryTree.updateInventoryData()
        else:
            pass

    def onSensorParameterCellChange(self, evt):
        selectedParameter = self.paramGrid.GetColLabelValue(evt.GetCol())
        gridParamFields = self.getParameterFields();
        colLabels = [x[1] for x in gridParamFields]
        sensorParameter2Process = self.displayedSensor.parameters[evt.GetRow()]

        if selectedParameter == 'start':
            # Change the start time.
            value = self.paramGrid.GetCellValue(evt.GetRow(), evt.GetCol())
            (timeSet, msg) = self.displayedSensor.changeParameterStartTime(evt.GetRow(), value)

            self.paramGrid.SetCellValue(evt.GetRow(), evt.GetCol(), str(timeSet))
            #self.displayedSensor.parentInventory.refreshNetworks()

            if msg:
                dlg = wx.MessageDialog(self, msg,
                                   'Error while changing the deployment time.',
                                   wx.OK | wx.ICON_INFORMATION
                                   #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                   )
                dlg.ShowModal()
                dlg.Destroy()
        elif selectedParameter == 'end':
            # Change the end time.
            value = self.paramGrid.GetCellValue(evt.GetRow(), evt.GetCol())
            (timeSet, msg) = self.displayedSensor.changeParameterEndTime(evt.GetRow(), value)

            self.paramGrid.SetCellValue(evt.GetRow(), evt.GetCol(), str(timeSet))
            #self.displayedStation.parentInventory.refreshNetworks()

            if msg:
                dlg = wx.MessageDialog(self, msg,
                                   'Error while changing the deployment time.',
                                   wx.OK | wx.ICON_INFORMATION
                                   #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                   )
                dlg.ShowModal()
                dlg.Destroy()
        elif selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridParamFields[ind][0]
            sensorParameter2Process[0][fieldName] =  self.paramGrid.GetCellValue(evt.GetRow(), evt.GetCol())
            self.displayedSensor.parentInventory.refreshRecorders()
            self.GetParent().GetParent().GetParent().inventoryTree.updateInventoryData()
        else:
            pass

    def updateData(self, sensor):
        self.logger.debug("updating the sensors data")

        self.displayedSensor = sensor

        # Update the sensor grid fields.
        self.setGridValues(sensor, self.sensorGrid, self.getSensorFields(), 0)

        # Update the parameter grid fields.
        for k, (curParam, beginTime, endTime) in enumerate(sensor.parameters):
            self.setGridValues(curParam, self.paramGrid, self.getParameterFields(), k)

            if not endTime:
                endTime = 'running'

            self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'start', 'editable')), str(beginTime))
            self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'end', 'editable')), str(endTime))  

            # Handle the poles.
            poleStr = None
            for curPole in curParam.tfPoles:
                if not poleStr:
                    poleStr = curPole.__str__()
                else:
                    poleStr = poleStr + ',' + curPole.__str__()

            if poleStr:
                self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'poles', 'readonly')), poleStr) 

            # Handle the zeros.
            zeroStr = None
            for curZero in curParam.tfZeros:
                if not zeroStr:
                    zeroStr = curZero.__str__()
                else:
                    zeroStr = zeroStr + ',' + curZero.__str__()

            if zeroStr:
                self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'zeros', 'readonly')), zeroStr) 

        # Update the transfer function plot.
        if sensor.parameters[0][0]:
            self.updateTransferFunction(sensor.parameters[0][0])


        self.paramGrid.AutoSizeColumns() 


    def updateTransferFunction(self, parameter):
        #paz = {}
        #paz['poles'] = [-4.440+4.440j, -4.440-4.440j, -1.083+0.0j]
        #paz['zeros'] = [0.0 +0.0j, 0.0 +0.0j, 0.0 +0.0j]
        #paz['gain'] = 0.4

        if not parameter.tfPoles or not parameter.tfZeros or not parameter.tfNormalizationFactor:
            self.tfMagAxis.clear()
            self.tfPhaseAxis.clear()
            return


        h,f = pazToFreqResp(parameter.tfPoles, parameter.tfZeros, parameter.tfNormalizationFactor, 0.005, 8192, freq=True)
        #h,f = pazToFreqResp(paz['poles'], paz['zeros'], paz['gain'], 0.005, 8192, freq=True)
        phase = np.unwrap(np.arctan2(-h.imag, h.real)) #take negative of imaginary part

        lines = self.tfMagAxis.get_lines()
        if lines:
            for curLine in lines:
                curLine.remove()

        frequRange = [0.1,1,10,100,1000]
        self.tfMagAxis.plot(np.log10(f), 20*np.log10(abs(h)), color='k')
        self.tfMagAxis.set_xticks(np.log10(frequRange))
        self.tfMagAxis.set_xticklabels(frequRange)

        lines = self.tfPhaseAxis.get_lines()
        if lines:
            for curLine in lines:
                curLine.remove()
        self.tfPhaseAxis.plot(np.log10(f), phase, color='k')
        self.tfPhaseAxis.set_xticks(np.log10(frequRange))
        self.tfPhaseAxis.set_xticklabels(frequRange)


    def setGridValues(self, object, grid, fields, rowNumber):
        for pos, (field, label, attr) in enumerate(fields):
            if field and object[field]:
                grid.SetCellValue(rowNumber, pos, str(object[field]))
            grid.AutoSizeColumns()



    def getSensorFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('recorderId', 'rec. id', 'readonly'))
        tableField.append(('recorderSerial', 'rec. serial', 'readonly'))
        tableField.append(('recorderType', 'rec. type', 'readonly'))
        tableField.append(('label', 'label', 'editable'))
        tableField.append(('serial', 'serial', 'editable'))
        tableField.append(('type', 'type', 'editable'))
        tableField.append(('recChannelName', 'rec. channel', 'editable'))
        tableField.append(('channelName', 'channel', 'editable'))
        return tableField

    def getParameterFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append((None, 'start', 'editable'))
        tableField.append((None, 'end', 'editable'))
        tableField.append(('bitweight', 'bitweight', 'editable'))
        tableField.append(('bitweightUnits', 'bitweight units', 'editable'))
        tableField.append(('gain', 'gain', 'editable'))
        tableField.append(('sensitivity', 'sensitivity', 'editable'))
        tableField.append(('sensitivityUnits', 'sensitivity units', 'editable'))
        tableField.append(('tfNormalizationFactor', 'normalization factor', 'editable'))
        tableField.append(('tfNormalizationFrequency', 'normalization frequ.', 'editable'))
        tableField.append((None, 'poles', 'readonly'))      # Poles is a list. Handle them seperately
        tableField.append((None, 'zeros', 'readonly'))      # Zeros is a list. Handle them seperately.
        return tableField



class ContextMenu(wx.Menu):

        def __init__(self, cmData):
            wx.Menu.__init__(self)

            for cmLabel, cmHandler in cmData:
                item = self.Append(-1, cmLabel)
                self.Bind(wx.EVT_MENU, cmHandler, item)

