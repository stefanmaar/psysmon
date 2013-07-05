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
from psysmon.packages.geometry.inventory import Inventory
from psysmon.packages.geometry.inventory import InventoryXmlParser
from psysmon.packages.geometry.db_inventory import DbInventory
import psysmon.packages.geometry.util as geom_util
from psysmon.artwork.icons import iconsBlack16 as icons
import wx.aui
import wx.grid
import os
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from wx.lib.pubsub import Publisher as pub
import numpy as np
from mpl_toolkits.basemap import pyproj
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from obspy.signal import pazToFreqResp
from obspy.core.utcdatetime import UTCDateTime
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorParameter
from psysmon.core.gui import psyContextMenu
import psysmon.core.guiBricks as guibricks
import psysmon.core.preferences_manager as pref_manager


class EditGeometry(CollectionNode):
    '''
    The EditGeometry class.
    '''
    name = 'edit geometry'
    mode = 'standalone'
    category = 'Geometry'
    tags = ['stable']

    def __init__(self):
        CollectionNode.__init__(self)
        pref_item = pref_manager.TextEditPrefItem(name = 'projection_coordinate_system', label = 'proj. coord. sys.', value = '')
        self.pref_manager.add_item(item = pref_item)
        pref_item = pref_manager.FileBrowsePrefItem(name = 'shape_file', label = 'shape file', value = '')
        self.pref_manager.add_item(item = pref_item)

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

        # The inventory controlling the database.
        self.db_inventory = DbInventory('db_inventory', self.psyProject)

        # The inventory currently selected by the user.
        self.selected_inventory = None

        # The network currently selected by the user.
        self.selected_network = None

        # The network currently selected by the user.
        self.selected_recorder = None
        
        # The network currently selected by the user.
        self.selected_sensor = None
        
        # initialize the user interface
        self.initUI()

        #self.initUserSelections()

        ## The inventory database controller.
        #self.dbController = InventoryDatabaseController(self.psyProject)

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

        # Bind some events.
        self.Bind(wx.EVT_CLOSE, self.onExit)


    def loadInventoryFromDb(self):
        ''' Load the inventory from the project database.

        '''
        try:
            self.db_inventory.load()
            cur_inventory = self.db_inventory
        except Warning as w:
                print w

        self.inventories[cur_inventory.name] = cur_inventory
        self.inventoryTree.updateInventoryData()
        self.selected_inventory = cur_inventory


    ## Define the EditGeometryDlg menus.  
    #
    # The EditGeometryDlg menus are created depending on the list returned.
    #
    # @param self The Object pointer.
    def menuData(self):
        return (("File",
                 ("Import from XML", "Import inventory from XML file.", self.onImportFromXml),
                 ("Export to XML", "Export the selected inventory to an XML file.", self.onExport2Xml),
                 ("", "", ""),
                 ("&Exit", "Exit pSysmon.", self.onExit)),
                ("Edit",
                 ("Add network", "Add a network to the selected inventory.", self.onAddNetwork),
                 ("Add station", "Add a station to the selected inventory.", self.onAddStation),
                 ("Add recorder", "Add a recorder to the selected inventory.", self.onAddRecorder),
                 ("", "", ""),
                 ("Write to database", "Write the selected inventory to database.", self.onSave2Db)),
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
            inventory_parser = InventoryXmlParser()

            try:
                cur_inventory = inventory_parser.parse(path)
            except Warning as w:
                    print w

            self.inventories[cur_inventory.name] = cur_inventory
            self.inventoryTree.updateInventoryData()


    def onExport2Xml(self, event):
        if not self.selected_inventory:
            self.logger.info("No inventory selected.")
            return

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard="xml file (*.xml)"\
                     "All files (*.*)|*.*",
            style=wx.SAVE | wx.CHANGE_DIR
            )

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            path = dlg.GetPath()
            inventory_parser = InventoryXmlParser()

            try:
                inventory_parser.export_xml(self.selected_inventory, path)
            except Warning as w:
                    print w



    def onAddRecorder(self, event):
        self.addRecorder()

    def onAddNetwork(self, event):
        ''' Handle the add network menu click.
        '''
        self.addNetwork()


    def onAddStation(self, event):
        ''' Handle the add station menu click.
        '''
        self.addStation()


    def addNetwork(self):
        ''' Add a new network to the inventory.
        '''
        if self.selected_inventory is None:
            self.logger.error('You have to create or select an inventory first.')
            return

        net2Add = Network(name = '-9999', description = 'A new network.') 
        self.selected_inventory.add_network(net2Add)
        self.inventoryTree.updateInventoryData()


    def addStation(self):
        ''' Add a new station to the inventory.
        '''
        if self.selected_network is None:
            self.logger.error('You have to create or select a network first.')
            return

        station2Add = Station(name = '-9999', 
                           location = '00',
                           network = self.selected_network.name,
                           x = 0,
                           y = 0,
                           z = 0,
                           coord_system = 'epsg:4326') 
        self.selected_inventory.add_station(station2Add)
        self.inventoryTree.updateInventoryData()


    def addRecorder(self):
        ''' Add a recorder to the inventory.
        '''
        if self.selected_inventory is None:
            self.logger.error('You have to create of select an inventory first.')
            return
        
        # Create the Recorder instance.
        rec_2_add = Recorder(serial='-9999', 
                             type = 'new recorder') 
        self.selected_inventory.add_recorder(rec_2_add)
        self.inventoryTree.updateInventoryData()


    def addSensor(self):
        ''' Add a sensor to the inventory.
        '''
        if self.selected_recorder is None:
            self.logger.error('You have to create or select a recorder first.')
            return

        # Create the Sensor instance.
        sensor_2_add = Sensor(serial = 'AAAA',
                              type = 'test sensor',
                              rec_channel_name = '001',
                              channel_name = 'HHZ',
                              label = 'AAAA-001-HHZ') 

        self.selected_recorder.add_sensor(sensor_2_add)
        self.inventoryTree.updateInventoryData()


    def addSensorParameter(self):
        ''' Add a new sensor parameter to the inventory.
        '''
        if self.selected_sensor is None:
            self.logger.error('You have to create or select a sensor first.')
            return
        
        # Create the SensorParameter instance.
        parameter_2_add = SensorParameter(gain = 1,
                                          bitweight = 2,
                                          bitweight_units = 'bw_units',
                                          sensitivity = 3,
                                          sensitivity_units = 'sens_units',
                                          start_time = UTCDateTime('1970-01-01'),
                                          end_time = None,
                                          tf_poles = [-4.440 + 4.440j, -4.440 - 4.440j, -1.083 + 0.0j],
                                          tf_zeros = [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
                                          tf_normalization_factor = 1,
                                          tf_normalization_frequency = 1)

        self.selected_sensor.add_parameter(parameter_2_add)
        self.inventoryTree.updateInventoryData()




    ## Save to database menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onSave2Db(self, event):
        if not self.selected_inventory:
            self.logger.info("No inventory selected.")
            return

        if self.selected_inventory.__class__.__name__ is not 'Inventory'  and self.selected_inventory.__class__.__name__ is not 'DbInventory':
            self.logger.info("Please select the inventory to be written to the database.")
            return

        self.logger.debug("inventory type: %s",self.selected_inventory.type)

        if self.selected_inventory.type not in 'db':
            self.logger.debug("Saving a non db inventory to the database.")
            for cur_recorder in self.selected_inventory.recorders:
                self.db_inventory.add_recorder(cur_recorder)

            for cur_network in self.selected_inventory.networks:
                self.db_inventory.add_network(cur_network)

            self.db_inventory.commit()

        else:
            if len(self.selected_inventory.stations) > 0:
                self.logger.error('There are still unassigned stations in the inventory.\nAdd them to a network or remove them before writing the inventory to the database.')
            else:
                self.logger.debug("Updating the existing project inventory database.")
                self.db_inventory.commit()

                # TODO: Check if it's needed to reload the database to get the
                # autoincrement ids.
                #cur_inventory = self.dbController.reloadDb()
                #self.inventories[cur_inventory.name] = cur_inventory
                #self.inventoryTree.updateInventoryData()
                #self.selected_inventory = cur_inventory


        self.inventoryTree.updateInventoryData()



    ## Exit menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onExit(self, event):
        self.logger.debug("onExit")
        # Check if an unsaved database inventory exists.
        for curInventory in self.inventories.itervalues():
            if curInventory.has_changed():
                self.logger.warning('There are unsaved elements in the inventory.')

        self.db_inventory.close()

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

        self.selected_item = None

        # Setup the context menu.
        cmData = (("add", self.onAddElement),
                  ("remove", self.onRemoveElement),
                  ("separator", None),
                  ("expand", self.on_expand_element),
                  ("collapse", self.on_collapse_element))

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)


        il = wx.ImageList(16, 16)
        self.icons = {}
        self.icons['xmlInventory'] = il.Add(icons.db_icon_16.GetBitmap()) 
        self.icons['recorderList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['stationList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['sensorList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['networkList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['network'] = il.Add(icons.network_icon_16.GetBitmap())
        self.icons['station'] = il.Add(icons.pin_map_icon_16.GetBitmap())
        self.icons['recorder'] = il.Add(icons.cassette_icon_16.GetBitmap())
        self.icons['sensor'] = il.Add(icons.playback_rec_icon_16.GetBitmap())

        self.AssignImageList(il)

        self.root = self.AddRoot("geometry")

        self.SetMinSize(size)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onItemSelectionChanged)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.onBeginDrag)
        self.Bind(wx.EVT_TREE_END_DRAG, self.onEndDrag)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKeyDown)


    def onShowContextMenu(self, evt):
        ''' Show the context menu.
        '''
        if(self.selected_item == 'station'):
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add sensor')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove station')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
        elif(self.selected_item == 'sensor'):
            #self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add parameter')
            #self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            #self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove sensor')
            #self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            # Create the sensor context menu.
            sub_data = []
            for cur_network in self.GetParent().selected_inventory.get_network():
                if len(cur_network.stations) > 0:
                    for cur_station in cur_network.stations:
                        sub_data.append((cur_station.get_snl_string(), self.on_assign_sensor_2_station))

            cm_data = (("add parameter", self.onAddElement),
                       ("remove sensor", self.onRemoveElement),
                       ("assign to station", sub_data))

            context_menu_sensor = psyContextMenu(cm_data)
            pos = evt.GetPosition()
            pos = self.ScreenToClient(pos)
            self.PopupMenu(context_menu_sensor, pos)
            return
        elif(self.selected_item == 'inventory'):
            self.logger.debug('Handling an inventory.')
        elif(self.selected_item == 'recorder_list'):
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add recorder')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove recorder')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
        elif(self.selected_item == 'recorder'):
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add sensor')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove recorder')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
        elif(self.selected_item == 'network'):
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add station')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove network')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
        elif(self.selected_item == 'network_list'):
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add network')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove network')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
        else:
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(0).GetId(), 'add')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'remove')
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)

        pos = evt.GetPosition()
        pos = self.ScreenToClient(pos)
        self.selected_tree_item_id = self.HitTest(pos)[0]
        self.PopupMenu(self.contextMenu, pos)


    def onAddElement(self, event):
        ''' Handle the context menu add click.
        '''
        if(self.selected_item == 'station'):
            self.logger.debug('Handling a station.')
        elif(self.selected_item == 'sensor'):
            # Add a new sensor parameter to the selected sensor.
            self.Parent.addSensorParameter()  
        elif(self.selected_item == 'inventory'):
            self.logger.debug('Handling an inventory.')
        elif(self.selected_item == 'recorder_list'):
            # Add a new recorder to the inventory.
            self.Parent.addRecorder()
        elif(self.selected_item == 'recorder'):
            # Add a new sensor to the selected recorder.
            self.Parent.addSensor()
        elif(self.selected_item == 'network'):
            # Add a new station to the selected network.
            self.Parent.addStation()
        elif(self.selected_item == 'network_list'):
            # Add a new network to the inventory.
            self.Parent.addNetwork()


    def onRemoveElement(self, event):
        ''' Handle the context menu remove click.
        '''
        pass


    def on_collapse_element(self, event):
        ''' Collapse the selected element.
        '''
        self.CollapseAllChildren(self.selected_tree_item_id)


    def on_expand_element(self, event):
        ''' Expand the selected element.
        '''
        self.ExpandAllChildren(self.selected_tree_item_id)


    def on_assign_sensor_2_station(self, event):
        ''' Assign a sensor to a station.
        '''
        item_id = event.GetId()
        menu = event.GetEventObject()
        label = menu.GetLabel(item_id)
        name, network, location = label.split(':')
        station = self.Parent.selected_inventory.get_station(name = name,
                                                             network = network,
                                                             location = location)

        if len(station) == 1:
            station = station[0]
            station.add_sensor(self.Parent.selected_sensor,
                                   start_time = UTCDateTime('1976-01-01'),
                                   end_time = None)
            self.updateInventoryData()
        elif len(station) > 1:
            self.logger.error('More than one station found. Expected exactly one. SNL = %s:%s:%s', name, network, location)
        else:
            self.logger.error('No station found. SNL = %s:%s:%s', name, network, location)



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
            targetData.add_sensor(sourceData, UTCDateTime('1976-01-01'), None)


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

        if(pyData.__class__.__name__ == 'Station' or pyData.__class__.__name__ == 'DbStation'):
            self.Parent.inventoryViewNotebook.updateStationListView(pyData)
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_network = pyData.parent_network
            self.Parent.selected_station = pyData
            self.selected_item = 'station'
        elif(pyData.__class__.__name__ == 'Sensor' or pyData.__class__.__name__ == 'DbSensor'):
            self.Parent.inventoryViewNotebook.updateSensorListView(pyData)
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_recorder = pyData.parent_recorder
            self.Parent.selected_sensor = pyData
            self.selected_item = 'sensor'
        elif(pyData.__class__.__name__ == 'Inventory' or pyData.__class__.__name__ == 'DbInventory'):
            self.Parent.selected_inventory = pyData
            self.selected_item = 'inventory'
        elif(pyData.__class__.__name__ == 'Recorder' or pyData.__class__.__name__ == 'DbRecorder'):
            self.Parent.inventoryViewNotebook.updateRecorderListView(pyData)
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_recorder = pyData
            self.selected_item = 'recorder'
        elif(pyData.__class__.__name__ == 'Network' or pyData.__class__.__name__ == 'DbNetwork'):
            self.Parent.inventoryViewNotebook.updateNetworkListView(pyData)
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_network = pyData
            self.selected_item = 'network'
        elif(self.GetItemText(evt.GetItem()) == 'Networks'):
            self.selected_item = 'network_list'
        elif(self.GetItemText(evt.GetItem()) == 'Recorders'):
            self.selected_item = 'recorder_list'
        elif(self.GetItemText(evt.GetItem()) == 'unassigned stations'):
            self.selected_item = 'unassigned_station_list'
        elif(self.GetItemText(evt.GetItem()) == 'unassigned sensors'):
            self.selected_item = 'unassigned_sensor_list'


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
                for curSensor in sorted(curRecorder.sensors, key=lambda sensor: (sensor.serial, sensor.channel_name)):
                    item = self.AppendItem(curRecorderItem, curSensor.serial + ':' +curSensor.rec_channel_name + ':' + curSensor.channel_name + ':' + curSensor.type)

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
            for curNetwork in curInventory.networks:
                curNetworkItem = self.AppendItem(networkItem, curNetwork.name)
                self.SetItemPyData(curNetworkItem, curNetwork)
                self.SetItemImage(curNetworkItem, self.icons['network'], wx.TreeItemIcon_Normal)

                for curStation in curNetwork.stations:
                    curStationItem = self.AppendItem(curNetworkItem, curStation.name+':'+curStation.location)
                    self.SetItemPyData(curStationItem, curStation)
                    self.SetItemImage(curStationItem, self.icons['station'], wx.TreeItemIcon_Normal)
                    for (curSensor, curBegin, curEnd) in sorted(curStation.sensors, key = lambda sensor: (sensor[0].recorder_serial, sensor[0].serial, sensor[0].rec_channel_name)):
                        item = self.AppendItem(curStationItem, curSensor.recorder_serial + ':' + curSensor.serial + ':' + curSensor.rec_channel_name)
                        self.SetItemPyData(item, (curSensor, curBegin, curEnd))
                        self.SetItemImage(item, self.icons['sensor'], wx.TreeItemIcon_Normal)


            self.Expand(inventoryItem)


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

        self.mapViewPanel = MapViewPanel(self)
        self.AddPage(self.mapViewPanel, 'map view')

        self.mapViewPropertiesPanel = MapViewPropertiesPanel(self)
        self.AddPage(self.mapViewPropertiesPanel, 'map properties')

        #self.mapViewSplitter = MapViewSplitter(self)
        #self.mapViewPanel = MapViewPanel(self.mapViewSplitter)
        #self.mapViewPropertiesPanel = MapViewPropertiesPanel(self.mapViewSplitter)
        #self.mapViewPanel.SetMinSize((50, 50))
        #self.mapViewPropertiesPanel.SetMinSize((-1, -1))
        #self.mapViewSplitter.SetMinimumPaneSize(1)
        #self.mapViewSplitter.SetSashGravity(1.)
        #self.mapViewSplitter.SplitVertically(self.mapViewPanel, self.mapViewPropertiesPanel, -200)
        #self.AddPage(self.mapViewSplitter, "map view")

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)


    def updateNetworkListView(self, network):
        ''' Show the network data in the list view.
        '''
        self.logger.debug("updating the network listview") 
        self.listViewPanel.showControlPanel('network', network)   


    def updateRecorderListView(self, recorder):
        ''' Show the recorder data in the list view.
        '''
        self.logger.debug("updating the recorder listview") 
        self.listViewPanel.showControlPanel('recorder', recorder)   


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

        def init_map(panel, cur_inventory):
            panel.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
            panel.mapViewPanel.initMap(cur_inventory)
            panel.inventory = cur_inventory
            panel.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

        if inventory != self.inventory:
            #t = Thread(target = init_map, args = (self, inventory))
            #t.setDaemon(True)
            #t.start()

            wx.BeginBusyCursor()
            self.mapViewPanel.initMap(inventory)
            self.inventory = inventory
            wx.EndBusyCursor()

    def onPageChanged(self, event):
        if event.GetSelection() == 1:
            self.updateMapView(self.Parent.selected_inventory)
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
        self.controlPanels['recorder'] = RecorderPanel(self, wx.ID_ANY)
        self.controlPanels['network'] = NetworkPanel(self, wx.ID_ANY)

        for cur_panel in self.controlPanels.values():
            cur_panel.Hide()

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



class MapViewSplitter(wx.SplitterWindow):
    ''' A splitter window used to separate the MapViewPanel and the MapViewPropertiesPanel.

    '''
    def __init__(self, parent, id = wx.ID_ANY):
        wx.SplitterWindow.__init__(self, parent, id,
                                   style = wx.SP_LIVE_UPDATE
                                   )
        self.logger = self.GetParent().logger

        self.SetSashSize(20)


class MapViewAUI(wx.Frame):
    ''' A AUI docking window to separate the MapViewPanel and the MapViewPropertiesPanel.

    '''
    def __init__(self, parent, id = wx.ID_ANY):
        wx.Frame.__init__(self, parent = parent, id = id)

        self.logger = self.GetParent().logger

        self.mgr = wx.aui.AuiManager(self)

        self.mgr.Update()




class MapViewPropertiesPanel(wx.Panel):
    ''' The editor panel for the mapview properties.

    '''
    def __init__(self, parent, id = wx.ID_ANY):
        ''' The constructor.

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

        button_sizer = wx.BoxSizer(wx.VERTICAL)
        # Create the buttons to control the stack.
        redraw_map_button = wx.Button(self, wx.ID_ANY, "redraw map")
        reset_button = wx.Button(self, wx.ID_ANY, "reset")

        # Fill the button sizer.
        button_sizer.Add(redraw_map_button, 0, wx.ALL)
        button_sizer.Add(reset_button, 0, wx.ALL)

        pref_manager = wx.GetTopLevelParent(self).collectionNode.pref_manager
        self.pref_panel = guibricks.PrefEditPanel(pref = pref_manager, parent = self)

        self.sizer = wx.GridBagSizer(5, 5)

        self.sizer.Add(self.pref_panel, pos = (0,0), flag = wx.EXPAND|wx.ALL, border = 0)
        self.sizer.Add(button_sizer, pos = (0,1), flag = wx.ALL, border = 0)
        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(0)

        self.Bind(wx.EVT_BUTTON, self.on_redraw_map, redraw_map_button)

        self.SetSizerAndFit(self.sizer)


    def on_redraw_map(self, event):
        self.GetParent().mapViewPanel.update_map()



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

        self.pref_manager = wx.GetTopLevelParent(self).collectionNode.pref_manager


        self.sizer = wx.GridBagSizer(0, 0)

        self.mapFigure = Figure((8,4), dpi=75, facecolor='white')
        self.mapAx = self.mapFigure.add_subplot(111)
        self.mapAx.set_aspect('equal')
        self.mapCanvas = FigureCanvas(self, -1, self.mapFigure)

        self.sizer.Add(self.mapCanvas, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=0)
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
        for curNet in inventory.networks:
            lonLat.extend([stat.get_lon_lat() for stat in curNet.stations])
            self.stations.extend([stat for stat in curNet.stations])

        lonLatMin = np.min(lonLat, 0)
        lonLatMax = np.max(lonLat, 0)
        self.mapConfig['utmZone'] = geom_util.lon2UtmZone(np.mean([lonLatMin[0], lonLatMax[0]]))
        self.mapConfig['ellips'] = 'wgs84'
        self.mapConfig['lon_0'] = geom_util.zone2UtmCentralMeridian(self.mapConfig['utmZone'])
        self.mapConfig['lat_0'] = 0
        if np.mean([lonLatMin[1], lonLatMax[1]]) >= 0:
            self.mapConfig['hemisphere'] = 'north'
        else:
            self.mapConfig['hemisphere'] = 'south'

        map_extent = lonLatMax - lonLatMin
        self.mapConfig['limits'] = np.hstack([lonLatMin - map_extent * 0.1, lonLatMax + map_extent * 0.1]) 

        lon = [x[0] for x in lonLat]
        lat = [x[1] for x in lonLat]

        # Get the epsg code of the UTM projection.
        search_dict = {'projection': 'utm', 'ellps': self.mapConfig['ellips'].upper(), 'zone': self.mapConfig['utmZone'], 'no_defs': True, 'units': 'm'}
        if self.mapConfig['hemisphere'] == 'south':
            search_dict['south'] = True

        epsg_dict = geom_util.get_epsg_dict()
        code = [(c, x) for c, x in epsg_dict.items() if  x == search_dict]

        # Setup the pyproj projection.projection
        #proj = pyproj.Proj(proj = 'utm', zone = self.mapConfig['utmZone'], ellps = self.mapConfig['ellips'].upper())
        self.pref_manager.set_value('projection_coordinate_system', 'epsg:'+code[0][0])
        proj = pyproj.Proj(init = 'epsg:'+code[0][0])

        # Plot the stations.
        x,y = proj(lon, lat)
        self.mapAx.scatter(x, y, s=100, marker='^', color='r', picker=5, zorder = 3)
        for cur_station, cur_x, cur_y in zip(self.stations, x, y):
            self.mapAx.text(cur_x, cur_y, cur_station.name)


        # Add some map annotation.
        self.mapAx.text(1, 1.02, geom_util.epsg_from_srs(proj.srs),
            ha = 'right', transform = self.mapAx.transAxes)

        self.mapCanvas.mpl_connect('pick_event', self.onPick)


    def initMapBasemap(self, inventory):
        '''
        Initialize the map parameters.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.geometry.MapViewPanel`
        '''
        self.mapConfig = {}
        self.stations = []

        # Get the lon/lat limits of the inventory.
        lonLat = []
        for curNet in inventory.networks:
            lonLat.extend([stat.get_lon_lat() for stat in curNet.stations])
            self.stations.extend([stat for stat in curNet.stations])

        lonLatMin = np.min(lonLat, 0)
        lonLatMax = np.max(lonLat, 0)
        self.mapConfig['utmZone'] = lon2UtmZone(np.mean([lonLatMin[0], lonLatMax[0]]))
        self.mapConfig['ellips'] = 'wgs84'
        self.mapConfig['lon_0'] = zone2UtmCentralMeridian(self.mapConfig['utmZone'])
        self.mapConfig['lat_0'] = 0
        #self.mapConfig['limits'] = np.hstack([np.floor(lonLatMin), np.ceil(lonLatMax)]) 
        map_extent = lonLatMax - lonLatMin
        self.mapConfig['limits'] = np.hstack([lonLatMin - map_extent * 0.1, lonLatMax + map_extent * 0.1]) 
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
                           resolution='i',
                           ax=self.mapAx,
                           suppress_ticks=True)

        self.logger.debug('proj4string: %s', self.map.proj4string)

        self.map.drawcountries(color = 'k')
        self.map.drawcoastlines()
        self.map.drawrivers(color='b')

        #s_river = self.map.readshapefile('/home/stefan/01_gtd/04_aktuelleProjekte/2012-0007_pSysmon/01_src/psysmon/lib/psysmon/packages/geometry/data/naturalearth/10m_physical/ne_10m_rivers_lake_centerlines', 'rivers', drawbounds = False)


        #for k, cur_river in enumerate(self.map.rivers):
        #    xx, yy = zip(*cur_river)
        #    if (max(xx) == 1e30 or max(yy) == 1e30):
        #        continue
        #    if (((min(xx) >= self.map.xmin and min(xx) <= self.map.xmax) or 
        #        (max(xx) >= self.map.xmin and max(xx) <= self.map.xmax) or
        #        (min(xx) <= self.map.xmin and max(xx) >= self.map.xmax)) and
        #        ((min(yy) >= self.map.ymin and min(yy) <= self.map.ymax) or
        #        (max(yy) >= self.map.ymin and max(yy) <= self.map.ymax) or
        #        (min(yy) <= self.map.ymin and max(yy) >= self.map.ymax))):
        #        print "plotting river %d" % k
        #        self.map.plot(xx, yy, color = 'b', zorder = 2)

        try:
            pass
            #self.map.etopo()
        except Exception as e:
            self.logger.exception("Can't plot etopo:\n%s", e)
            try:
                self.map.bluemarble()
            except Exception as e:
                self.logger.exception("Can't plot bluemarble:\n%s", e)

        # Plot the stations.
        x,y = self.map(lon, lat)
        self.map.scatter(x, y, s=100, marker='^', color='r', picker=5, zorder = 3)
        for cur_station, cur_x, cur_y in zip(self.stations, x, y):
            self.mapAx.text(cur_x, cur_y, cur_station.name)

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


    def update_map(self):
        '''
        Update the map elements.
        '''
        # Clear the map.
        self.mapAx.clear()
        self.mapAx.set_xlim(0, 1)
        self.mapAx.set_ylim(0, 1)
        self.mapAx.autoscale(True)

        # Get the lon/lat limits of the inventory.
        lonLat = []
        lonLat.extend([stat.get_lon_lat() for stat in self.stations])

        lon = [x[0] for x in lonLat]
        lat = [x[1] for x in lonLat]

        # Setup the pyproj projection.projection
        proj = pyproj.Proj(init = self.pref_manager.get_value('projection_coordinate_system'))

        # Plot the stations.
        x,y = proj(lon, lat)
        self.mapAx.scatter(x, y, s=100, marker='^', color='g', picker=5, zorder = 3)
        for cur_station, cur_x, cur_y in zip(self.stations, x, y):
            self.mapAx.text(cur_x, cur_y, cur_station.name)

        # Plot the shape file.
        cur_shapefile = self.pref_manager.get_value('shape_file')
        if len(cur_shapefile) > 0:
            import shapefile
            sf = shapefile.Reader(cur_shapefile)
            shapes = sf.shapes()
            for cur_shape in shapes:
                print cur_shape.points
                lon = [x[0] for x in cur_shape.points]
                lat = [x[1] for x in cur_shape.points]

            x,y = proj(lon, lat)
            self.mapAx.plot(x, y)


        # Add some map annotation.
        self.mapAx.text(1, 1.02, geom_util.epsg_from_srs(proj.srs),
            ha = 'right', transform = self.mapAx.transAxes)

        #self.mapCanvas.mpl_connect('pick_event', self.onPick)

        self.mapCanvas.draw()


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


class NetworkPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        ## The currently displayed station.
        self.displayedNetwork = None;

        self.sizer = wx.GridBagSizer(5, 5)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True) 

        # Create the recorder grid.
        #stationColLabels = ['id', 'name', 'network', 'x', 'y', 'z', 'coordSystem', 'description']
        fields = self.getNetworkFields()
        self.network_grid = wx.grid.Grid(self, size=(-1, 100))
        self.network_grid.CreateGrid(1, len(fields))

        # Bind the network_grid events.
        self.network_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onNetworkCellChange)

        for k, (name, label, attr)  in enumerate(fields):
            self.network_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.network_grid.SetColAttr(k, roAttr)

        self.network_grid.AutoSizeColumns() 

        self.sizer.Add(self.network_grid, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)

        # Create the station grid.
        fields = self.getStationFields()
        self.station_grid = wx.grid.Grid(self, size=(100,100))
        self.station_grid.CreateGrid(5, len(fields))

        # Bind the stationGrid events.
        #self.sensorGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onSensorTimeCellChange)

        for k, (name, label, attr) in enumerate(fields):
            self.station_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.station_grid.SetColAttr(k, roAttr)


        self.sizer.Add(self.station_grid, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)

        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)
        self.SetSizerAndFit(self.sizer)


    def getNetworkFields(self):
        ''' The recorder grid columns.
        '''
        tableField = []
        tableField.append(('name', 'name', 'editable'))
        tableField.append(('description', 'description', 'editable'))
        tableField.append(('type', 'type', 'editable'))
        return tableField


    def getStationFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('name', 'name', 'editable'))
        tableField.append(('location', 'location', 'editable'))
        tableField.append(('network', 'network', 'editable'))
        tableField.append(('x', 'x', 'editable'))
        tableField.append(('y', 'y', 'editable'))
        tableField.append(('z', 'z', 'editable'))
        tableField.append(('coord_system', 'coord. system', 'editable'))
        tableField.append(('description', 'description', 'editable'))
        return tableField


    def updateData(self, network):
        ''' Update the displayed data.
        '''
        self.displayedNetwork = network

        # Update the sensor grid fields.
        self.setGridValues(network, self.network_grid, self.getNetworkFields(), 0)

        self.network_grid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        ''' Set the grid values of the specified grid.
        '''
        for pos, (field, label, attr) in enumerate(fields):
            if field is not None and getattr(object, field) is not None:
                grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
            grid.AutoSizeColumns()


    def onNetworkCellChange(self, evt):
        ''' The network_grid cell edit callback.
        '''
        selectedParameter = self.network_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getNetworkFields();
        colLabels = [x[1] for x in grid_fields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = grid_fields[ind][0]
            fieldAttr = grid_fields[ind][2]
            if fieldAttr == 'editable':
                setattr(self.displayedNetwork, fieldName, self.network_grid.GetCellValue(evt.GetRow(), evt.GetCol()))
                #self.displayedNetwork[fieldName] =  self.network_grid.GetCellValue(evt.GetRow(), evt.GetCol())
                # TODO: For non-db inventories, reassign the stations to the
                # network.
                if self.displayedNetwork.parent_inventory.type is not 'db':
                    self.displayedNetwork.parent_inventory.refreshNetworks()
                self.GetParent().GetParent().GetParent().inventoryTree.updateInventoryData()
                self.logger.debug(self.GetParent().GetParent().GetParent())
        else:
            pass


class RecorderPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        ## The currently displayed station.
        self.displayedRecorder = None;

        self.sizer = wx.GridBagSizer(5, 5)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True) 

        # Create the recorder grid.
        #stationColLabels = ['id', 'name', 'network', 'x', 'y', 'z', 'coordSystem', 'description']
        fields = self.getRecorderFields()
        self.recorder_grid = wx.grid.Grid(self, size=(-1, 100))
        self.recorder_grid.CreateGrid(1, len(fields))

        # Bind the recorder_grid events.
        self.recorder_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onRecorderCellChange)

        for k, (name, label, attr)  in enumerate(fields):
            self.recorder_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.recorder_grid.SetColAttr(k, roAttr)

        self.recorder_grid.AutoSizeColumns() 

        self.sizer.Add(self.recorder_grid, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)

        # Create the sensor grid.
        fields = self.getSensorFields()
        self.sensorGrid = wx.grid.Grid(self, size=(100,100))
        self.sensorGrid.CreateGrid(5, len(fields))

        # Bind the stationGrid events.
        #self.sensorGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onSensorTimeCellChange)

        for k, (name, label, attr) in enumerate(fields):
            self.sensorGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.sensorGrid.SetColAttr(k, roAttr)


        self.sizer.Add(self.sensorGrid, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)

        self.sizer.AddGrowableRow(1)
        self.sizer.AddGrowableCol(0)
        self.SetSizerAndFit(self.sizer)


    def getRecorderFields(self):
        ''' The recorder grid columns.
        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly'))
        tableField.append(('serial', 'serial', 'editable'))
        tableField.append(('type', 'type', 'editable'))
        return tableField


    def getSensorFields(self):
        ''' Get the sensor grid columns.
        '''
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


    def updateData(self, recorder):
        ''' Update the displayed data.
        '''
        self.displayedRecorder = recorder

        # Update the sensor grid fields.
        self.setGridValues(recorder, self.recorder_grid, self.getRecorderFields(), 0)

        self.recorder_grid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        ''' Set the grid values of the specified grid.
        '''
        for pos, (field, label, attr) in enumerate(fields):
            if field is not None and getattr(object, field) is not None:
                grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
            grid.AutoSizeColumns()


    def onRecorderCellChange(self, evt):
        ''' The recorder_grid cell edit callback.
        '''
        selected_parameter = self.recorder_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getRecorderFields();
        col_labels = [x[1] for x in grid_fields]
        
        if selected_parameter in col_labels:
            ind = col_labels.index(selected_parameter)
            fieldName = grid_fields[ind][0]
            fieldAttr = grid_fields[ind][2]
            if fieldAttr == 'editable':
                setattr(self.displayedRecorder, fieldName, self.recorder_grid.GetCellValue(evt.GetRow(), evt.GetCol()))
                self.GetParent().GetParent().GetParent().inventoryTree.updateInventoryData()
                self.logger.debug(self.GetParent().GetParent().GetParent())
        else:
            pass
        



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
                value = self.stationGrid.GetCellValue(evt.GetRow(), evt.GetCol())
                # If the network name has been changed, check if the
                # network exists and if so, add the station to it.

                if fieldName == 'network':
                    #new_net = self.displayedStation.parent_inventory.get_network(value)
                    if self.displayedStation.parent_network is not None:
                        self.displayedStation.parent_network.remove_station(name = self.displayedStation.name,
                                                                            location = self.displayedStation.location)
                    setattr(self.displayedStation, fieldName, value)
                    self.displayedStation.parent_inventory.move_station(self.displayedStation)

                setattr(self.displayedStation, fieldName, value)

                #self.displayedStation.parent_inventory.refreshNetworks()
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
        start_time = self.tableSensors[evt.GetRow()][1]
        end_time = self.tableSensors[evt.GetRow()][2]

        if selectedParameter == 'start':
            (timeSet, msg) = self.displayedStation.change_sensor_start_time(sensor, start_time, end_time, value)
            self.tableSensors[evt.GetRow()] = (sensor, timeSet, end_time)
        elif selectedParameter == 'end':
            (timeSet, msg) = self.displayedStation.change_sensor_end_time(sensor, start_time, end_time, value)
            self.tableSensors[evt.GetRow()] = (sensor, start_time, timeSet)

        self.sensorGrid.SetCellValue(evt.GetRow(), evt.GetCol(), str(timeSet))

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
        self.tableSensors = sorted(station.sensors, key = lambda sensor: (sensor[0].recorder_serial, sensor[0].serial, sensor[0].channel_name))
        #self.tableSensors = sorted(station.sensors, key = attrgetter('channel'))
        # Set the sensor values.
        for k,(curSensor, startTime, endTime) in enumerate(self.tableSensors):
            self.sensorGrid.SetCellValue(k, 0, str(curSensor.id))
            self.sensorGrid.SetCellValue(k, 1, curSensor.label)
            self.sensorGrid.SetCellValue(k, 2, curSensor.recorder_serial)
            self.sensorGrid.SetCellValue(k, 3, curSensor.recorder_type)
            self.sensorGrid.SetCellValue(k, 4, curSensor.serial)
            self.sensorGrid.SetCellValue(k, 5, curSensor.type)
            self.sensorGrid.SetCellValue(k, 6, curSensor.rec_channel_name)
            self.sensorGrid.SetCellValue(k, 7, curSensor.channel_name)
            if startTime:
                self.sensorGrid.SetCellValue(k, 8, str(startTime))

            if endTime:
                self.sensorGrid.SetCellValue(k, 9, str(endTime))
            else:
                self.sensorGrid.SetCellValue(k, 9, 'running')

        self.sensorGrid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        for pos, (field, label, attr) in enumerate(fields):
            if field is not None and getattr(object, field) is not None:
                grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
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
        tableField.append(('coord_system', 'coord. system', 'editable'))
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

        for k, (name, label, attr, converter)  in enumerate(fields):
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

        for k, (name, label, attr, convert)  in enumerate(fields):
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
            setattr(self.displayedSensor, fieldName, self.sensorGrid.GetCellValue(evt.GetRow(), evt.GetCol()))
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
            converter = gridParamFields[ind][3]
            setattr(sensorParameter2Process, fieldName, converter(self.paramGrid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetParent().GetParent().GetParent().inventoryTree.updateInventoryData()
        else:
            pass

    def updateData(self, sensor):
        self.logger.debug("updating the sensors data")

        self.displayedSensor = sensor

        # Update the sensor grid fields.
        self.setGridValues(sensor, self.sensorGrid, self.getSensorFields(), 0)

        # Update the parameter grid fields.
        for k, curParam in enumerate(sensor.parameters):
            self.setGridValues(curParam, self.paramGrid, self.getParameterFields(), k)

            if curParam.end_time is None:
                endTimeString = 'running'
            else:
                endTimeString = str(curParam.end_time)

            self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'start', 'editable', UTCDateTime)), str(curParam.start_time))
            self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'end', 'editable', UTCDateTime)), endTimeString)  

            # Handle the poles.
            poleStr = None
            if len(curParam.tf_poles) > 0:
                for curPole in curParam.tf_poles:
                    if not poleStr:
                        poleStr = curPole.__str__()
                    else:
                        poleStr = poleStr + ',' + curPole.__str__()

            if poleStr:
                self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'poles', 'readonly', str)), poleStr) 

            # Handle the zeros.
            zeroStr = None
            if len(curParam.tf_zeros) > 0:
                for curZero in curParam.tf_zeros:
                    if not zeroStr:
                        zeroStr = curZero.__str__()
                    else:
                        zeroStr = zeroStr + ',' + curZero.__str__()

            if zeroStr:
                self.paramGrid.SetCellValue(k, self.getParameterFields().index((None, 'zeros', 'readonly', str)), zeroStr) 

        # Update the transfer function plot.
        if len(sensor.parameters) > 0:
            self.updateTransferFunction(sensor.parameters[0])


        self.paramGrid.AutoSizeColumns() 


    def updateTransferFunction(self, parameter):
        #paz = {}
        #paz['poles'] = [-4.440+4.440j, -4.440-4.440j, -1.083+0.0j]
        #paz['zeros'] = [0.0 +0.0j, 0.0 +0.0j, 0.0 +0.0j]
        #paz['gain'] = 0.4

        if not parameter.tf_poles or not parameter.tf_zeros or not parameter.tf_normalization_factor:
            self.tfMagAxis.clear()
            self.tfPhaseAxis.clear()
            return


        h,f = pazToFreqResp(parameter.tf_poles, parameter.tf_zeros, parameter.tf_normalization_factor, 0.005, 8192, freq=True)
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
        for pos, (field, label, attr, converter) in enumerate(fields):
            if field is not None and getattr(object, field) is not None:
                grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
            grid.AutoSizeColumns()



    def getSensorFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', str))
        tableField.append(('recorder_id', 'rec. id', 'readonly', str))
        tableField.append(('recorder_serial', 'rec. serial', 'readonly', str))
        tableField.append(('recorder_type', 'rec. type', 'readonly', str))
        tableField.append(('label', 'label', 'editable', str))
        tableField.append(('serial', 'serial', 'editable', str))
        tableField.append(('type', 'type', 'editable', str))
        tableField.append(('rec_channel_name', 'rec. channel', 'editable', str))
        tableField.append(('channel_name', 'channel', 'editable', str))
        return tableField

    def getParameterFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append((None, 'start', 'editable', UTCDateTime))
        tableField.append((None, 'end', 'editable', UTCDateTime))
        tableField.append(('bitweight', 'bitweight', 'editable', float))
        tableField.append(('bitweight_units', 'bitweight units', 'editable', str))
        tableField.append(('gain', 'gain', 'editable', float))
        tableField.append(('sensitivity', 'sensitivity', 'editable', float))
        tableField.append(('sensitivity_units', 'sensitivity units', 'editable', str))
        tableField.append(('tf_normalization_factor', 'normalization factor', 'editable', float))
        tableField.append(('tf_normalization_frequency', 'normalization frequ.', 'editable', float))
        tableField.append((None, 'poles', 'readonly', str))      # Poles is a list. Handle them seperately
        tableField.append((None, 'zeros', 'readonly', str))      # Zeros is a list. Handle them seperately.
        return tableField



class ContextMenu(wx.Menu):

        def __init__(self, cmData):
            wx.Menu.__init__(self)

            for cmLabel, cmHandler in cmData:
                item = self.Append(-1, cmLabel)
                self.Bind(wx.EVT_MENU, cmHandler, item)

