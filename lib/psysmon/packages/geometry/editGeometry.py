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
from __future__ import print_function
from __future__ import division

from builtins import zip
from builtins import str
from past.utils import old_div
import logging
from threading import Thread
from operator import attrgetter
import psysmon
from psysmon.core.packageNodes import CollectionNode
from psysmon.packages.geometry.inventory_parser import InventoryXmlParser
from psysmon.packages.geometry.db_inventory import DbInventory
import psysmon.packages.geometry.util as geom_util
from psysmon.artwork.icons import iconsBlack16 as icons
import wx.aui
import wx.grid
import os
#import matplotlib
#matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from pubsub import pub
import numpy as np
import obspy.signal.invsim
import pyproj

# TODO: Remove all methods related to the mpl_toolkits Basemap.
#try:
#    from mpl_toolkits.basemap import Basemap
#    mpltk_basemap_available = True
#except Exception:
#    mpltk_basemap_available = False
    
from matplotlib.patches import Polygon
from obspy.core.utcdatetime import UTCDateTime
from psysmon.packages.geometry.inventory import Inventory
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import RecorderStream
from psysmon.packages.geometry.inventory import RecorderStreamParameter
from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Channel
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorComponent
from psysmon.packages.geometry.inventory import SensorComponentParameter
from psysmon.gui.context_menu import psyContextMenu
import psysmon.gui.bricks as guibricks
import psysmon.core.preferences_manager as pref_manager
import seaborn as sns
import scipy.signal

import psysmon.gui.main.app as psy_app

sns.set_style('whitegrid')


class EditGeometry(CollectionNode):
    '''
    The EditGeometry class.
    '''
    name = 'edit geometry'
    mode = 'execute only'
    category = 'Geometry'
    tags = ['stable']

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        pref_item = pref_manager.TextEditPrefItem(name = 'projection_coordinate_system', label = 'proj. coord. sys.', value = '')
        gen_group.add_item(pref_item)
        pref_item = pref_manager.FileBrowsePrefItem(name = 'shape_file', label = 'shape file', value = '')
        gen_group.add_item(pref_item)

    def edit(self):
        '''
        The edit method.

        The EditGeometry node is a standalone node. Ignore the edit method.

        :param self: The object pointer.
        :type self: A `~psysmon.packages.geometry.editGeometry.EditGeometry` instance.
        '''
        pass


    def execute(self, prevNodeOutput={}):
        ''' Execute the node.
        '''
        app = psy_app.PsysmonApp()
        dlg = EditGeometryDlg(self, self.project)
        dlg.Show()
        app.MainLoop()




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


        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        ## The current pSysmon project.
        self.psyProject = psyProject

        ## The loaded inventories.
        #
        # The keys of the dictionaries are the inventory names.
        self.inventories = {}

        # The inventory controlling the database.
        self.db_inventory = DbInventory(project = self.psyProject)

        # The inventory currently selected by the user.
        self.selected_inventory = None

        # The network currently selected by the user.
        self.selected_network = None

        # The array currently selected by the user.
        self.selected_array = None

        # The recorder currently selected by the user.
        self.selected_recorder = None

        # The recorder stream currently selected by the user.
        self.selected_recorder_stream = None

        # The recorder stream parameter currently selected by the user.
        self.selected_recorder_stream_parameter = None

        # The sensor component assigned to a recorder stream currently selected
        # by the user.
        self.selected_recorder_stream_assigned_component = None

        # The station currently selected by the user.
        self.selected_station = None

        # The channel currently selected by the user.
        self.selected_channel = None

        # The sensor currently selected by the user.
        self.selected_sensor = None

        # The sensor component currently selected by the user.
        self.selected_sensor_component = None

        # The sensor component parameter currently selected by the user.
        self.selected_sensor_component_parameters = None

        # initialize the user interface
        self.initUI()

        #self.initUserSelections()

        ## The inventory database controller.
        #self.dbController = InventoryDatabaseController(self.psyProject)

        # Load the inventory from the database.
        self.loadInventoryFromDb()


    def __del__(self):
        self.db_inventory.close()


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
        self.statusbar = self.CreateStatusBar(2, wx.STB_SIZEGRIP)
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
                print(w)

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
                 ("Export stations to CSV", "Export the stations of the selected inventory to a CSV file.", self.onExportStations2Csv),
                 ("Export channels to CSV", "Export the channels of the selected inventory to a CSV file.", self.onExportChannels2Csv),
                 ("Export stations to StationXML", "Export the stations of the selected inventory to a StationXML file.", self.onExportStations2StationXML),
                 ("", "", ""),
                 ("&Exit", "Exit pSysmon.", self.onExit)),
                ("Edit",
                 ("Create XML inventory", "Create an empty XML inventory.", self.onCreateXmlInventory),
                 #("Add network", "Add a network to the selected inventory.", self.onAddNetwork),
                 #("Add station", "Add a station to the selected inventory.", self.onAddStation),
                 #("Add recorder", "Add a recorder to the selected inventory.", self.onAddRecorder),
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
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
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
                self.logger.warning(w)
            except Exception:
                self.logger.exception("Error while parsing file %s.", path)

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
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR
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
                self.logger.warning(w)
            except Exception:
                self.logger.exception("Error while parsing file %s.", path)


    def onExportStations2Csv(self, event):
        ''' Export the stations to a CSV formatted file.
        '''
        if not self.selected_inventory:
            self.logger.info("No inventory selected.")
            return

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="csv file (*.csv)"\
                     "All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR
        )

        # Show the dialog and retrieve the user response. If it is the OK
        # response, process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            path = dlg.GetPath()

            df = self.selected_inventory.to_dataframe(level = 'station')

            df.to_csv(path,
                      index = False)
            
    def onExportChannels2Csv(self, event):
        ''' Export the channels to a CSV formatted file.
        '''
        if not self.selected_inventory:
            self.logger.info("No inventory selected.")
            return

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="csv file (*.csv)"\
                     "All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR
        )

        # Show the dialog and retrieve the user response. If it is the OK
        # response, process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            path = dlg.GetPath()

            df = self.selected_inventory.to_dataframe(level = 'channel')

            df.to_csv(path,
                      index = False)

            
    def onExportStations2Csv_old(self, event):
        ''' Import the stations to a CSV formatted file.
        '''
        import csv

        if not self.selected_inventory:
            self.logger.info("No inventory selected.")
            return

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="csv file (*.csv)"\
                     "All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR
            )

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            path = dlg.GetPath()

            export_values = []

            # Get the EPSG code for the best fitting UTM projection.
            code = self.selected_inventory.get_utm_epsg()
            proj = pyproj.Proj(init = 'epsg:' + code[0][0])

            for cur_network in self.selected_inventory.networks:
                for cur_station in cur_network.stations:
                    x, y = proj(cur_station.get_lon_lat()[0],
                                cur_station.get_lon_lat()[1])
                    value_list = [cur_station.name,
                                  cur_station.network,
                                  cur_station.location,
                                  cur_station.x,
                                  cur_station.y,
                                  cur_station.z,
                                  cur_station.coord_system,
                                  x,
                                  y,
                                  'epsg:' + code[0][0],
                                  cur_station.description]
                    #for k, cur_value in enumerate(value_list):
                    #    if isinstance(cur_value, str):
                    #        value_list[k] = cur_value.encode('utf8')
                    export_values.append(value_list)

            header = ['name',
                      'network',
                      'location',
                      'x',
                      'y',
                      'z',
                      'coord_system',
                      'x_utm',
                      'y_utm',
                      'coord_system_utm',
                      'description']
            with open(path, 'w', newline='') as fid:
                writer = csv.writer(fid,
                                    quoting = csv.QUOTE_MINIMAL)
                writer.writerow(header)
                writer.writerows(export_values)


    def onExportStations2StationXML(self, event):
        ''' Export the stations to s StationXML formatted file.
        '''
        import obspy.core.inventory as obs_inv

        if not self.selected_inventory:
            self.logger.info("No inventory selected.")
            return

        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="xml file (*.xml)"\
                     "All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR
            )

        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            filepath = dlg.GetPath()
        else:
            return

        exp_inv = self.selected_inventory.to_stationxml()

        exp_inv.write(filepath,
                      format = 'STATIONXML')
        self.logger.info("Exported the inventory to station-XML file {}.".format(filepath))


    def onCreateXmlInventory(self, event):
        ''' Handle the create new XML inventory menu click.
        '''
        inventory_name = wx.GetTextFromUser('new inventory name:', caption = 'Inventory name',
                                            default_value = '', parent = self)
        if not inventory_name:
            return
        else:
            self.addXmlInventory(name = inventory_name);


    def addXmlInventory(self, name = 'new inventory'):
        ''' Add a new XML inventory.
        '''
        inventory = Inventory(name, type = 'xml')
        self.inventories[inventory.name] = inventory
        self.inventoryTree.updateInventoryData()


    def remove_inventory(self):
        ''' Remove the selected inventory.
        '''
        if self.selected_inventory in list(self.inventories.values()):
            self.inventories.pop(self.selected_inventory.name)
            self.inventoryTree.updateInventoryData()


    def clear_inventory(self):
        ''' Clear all elements from the selected inventory.
        '''
        if self.selected_inventory:
            self.selected_inventory.clear()
            self.inventoryTree.updateInventoryData()

            if self.selected_inventory.type == 'db':
                # Clear all geometry database tables.
                project_slug = self.psyProject.slug
                tables_to_clear = [table for table in reversed(self.psyProject.dbMetaData.sorted_tables) if table.key.startswith(project_slug + '_geom')]
                for cur_table in tables_to_clear:
                    self.psyProject.dbEngine.execute(cur_table.delete())

                # Remove all elements from the session.
                self.selected_inventory.db_session.expunge_all()



    def add_network(self):
        ''' Add a new network to the inventory.
        '''
        if self.selected_inventory:
            net2Add = Network(name = '-9999', description = 'A new network.')
            self.selected_inventory.add_network(net2Add)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select an inventory first.')



    def remove_network(self):
        ''' Remove the selected network from the inventory.
        '''
        if self.selected_network:
            self.selected_inventory.remove_network_by_instance(self.selected_network)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select a network first.')


    def add_station(self):
        ''' Add a new station to the inventory.
        '''
        if self.selected_network:
            station2Add = Station(name = '-9999',
                                  location = '00',
                                  x = 0,
                                  y = 0,
                                  z = 0,
                                  coord_system = 'epsg:4326')
            self.selected_network.add_station(station2Add)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to create or select a network first.')
            return


    def remove_station(self):
        ''' Remove the selected station from the network.
        '''
        if self.selected_station:
            self.selected_network.remove_station_by_instance(self.selected_station)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select a station first.')


    def add_channel(self):
        ''' Add a channel to the selected station.
        '''
        if self.selected_station:
            channel_to_add = Channel('-99')
            self.selected_station.add_channel(channel_to_add)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select a station first.')


    def remove_channel(self):
        ''' Remove the selected channel from the station.
        '''
        if self.selected_channel:
            self.selected_station.remove_channel_by_instance(self.selected_channel)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select a channel first.')



    def add_recorder(self):
        ''' Add a recorder to the inventory.
        '''
        if self.selected_inventory is None:
            self.logger.error('You have to create of select an inventory first.')
            return

        # Create the Recorder instance.
        rec_2_add = Recorder(serial='-9999',
                             model = 'recorder model',
                             producer = 'recorder producer')
        self.selected_inventory.add_recorder(rec_2_add)
        self.inventoryTree.updateInventoryData()


    def add_recorder_stream(self):
        ''' Add a stream to the selected recorder.
        '''
        if self.selected_recorder is None:
            self.logger.error('You have to select a recorder first.')
            return

        # Create the stream instance.
        stream_to_add = RecorderStream(name = '-9999',
                                       label = 'stream label')
        self.selected_recorder.add_stream(stream_to_add)
        self.inventoryTree.updateInventoryData()


    def add_recorder_stream_parameter(self):
        ''' Add a parameter to the selected recorder stream.
        '''
        if self.selected_recorder_stream:
            slot = self.selected_recorder_stream.get_free_parameter_slot('both')
            if slot:
                parameter_to_add = RecorderStreamParameter(start_time = slot[0],
                                                           end_time = slot[1])
                try:
                    self.selected_recorder_stream.add_parameter(parameter_to_add)
                except RuntimeError as e:
                    self.logger.exception(e)
                    dlg = wx.MessageDialog(self, str(e),
                                           'Error while adding a new parameter.',
                                            wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                else:
                    self.inventoryTree.updateInventoryData()
            else:
                msg = "There is no free time slot for a new parameter."
                dlg = wx.MessageDialog(self, msg,
                                       'Error while adding a new parameter.',
                                        wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

        else:
            self.logger.error('You have to select a recorder stream first.')


    def remove_recorder(self):
        ''' Remove the selected recorder from the inventory.
        '''
        if self.selected_recorder:
            has_assigned_streams = False
            # Check for assigned recorder streams.
            for cur_stream in self.selected_recorder.streams:
                if cur_stream.assigned_channels:
                    has_assigned_streams = True
                    break

            if has_assigned_streams:
                msg = "The recorder contains assigned streams. Unassign the streams first."
                dlg = wx.MessageDialog(self, msg,
                                       'Error while removing the recorder.',
                                        wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                self.selected_inventory.remove_recorder_by_instance(self.selected_recorder)
                self.selected_recorder = None
                self.selected_recorder_stream = None
                self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select a recorder first.')


    def remove_recorder_stream(self):
        ''' Remove the selected recorder stream from the recorder.
        '''
        if self.selected_recorder_stream is None:
            self.logger.error('You have to select a recorder stream first.')
        elif self.selected_recorder_stream.assigned_channels:
            self.logger.info("Can't remove the stream. It is assigned to the following stationchannels: %s", self.selected_recorder_stream.assigned_channels)
        else:
            removed_stream = self.selected_recorder.pop_stream_by_instance(self.selected_recorder_stream)
            if removed_stream:
                self.selected_recorder_stream = None
                self.inventoryTree.updateInventoryData()



    def addSensor(self):
        ''' Add a sensor to the inventory.
        '''
        if self.selected_inventory is None:
            self.logger.error('You have to create or select an inventory first.')
            return

        # Create the Sensor instance.
        sensor_2_add = Sensor(serial = 'AAAA',
                              model = 'sensor model',
                              producer = 'sensor_producer')
        self.selected_inventory.add_sensor(sensor_2_add)
        self.inventoryTree.updateInventoryData()
        return sensor_2_add


    def remove_sensor(self):
        ''' Remove the currently selected sensor.
        '''
        if self.selected_sensor:
            has_assigned_components = False
            # Check for assigned recorder streams.
            for cur_component in self.selected_sensor.components:
                if cur_component.assigned_streams:
                    has_assigned_components = True
                    break

            if has_assigned_components:
                msg = "The sensor contains assigned components. Unassign the components first."
                dlg = wx.MessageDialog(self, msg,
                                       'Error while removing the sensor.',
                                        wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                self.selected_inventory.remove_sensor_by_instance(self.selected_sensor)
                self.selected_sensor = None
                self.selected_sensor_component = None
                self.selected_sensor_component_parameters = None
                self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to select a recorder first.')


    def add_sensor_component(self):
        ''' Add a component to a sensor.
        '''
        if self.selected_sensor is None:
            self.logger.error('You have to select a sensor first.')
            return

        # Create the Sensor instance.
        component = SensorComponent(name = 'new component')
        self.selected_sensor.add_component(component)
        self.inventoryTree.updateInventoryData()
        return component


    def remove_sensor_component(self):
        ''' Remove the currently selected sensor component.
        '''
        if self.selected_sensor_component is None:
            self.logger.error('You have to select a sensor component first.')
            return

        removed_component = self.selected_sensor.pop_component_by_instance(self.selected_sensor_component)
        if removed_component:
            self.selected_sensor_component = None
            self.selected_sensor_component_parameters = None
            self.inventoryTree.updateInventoryData()
        else:
            msg = "Can't remove the component. It is assigned to the following recorder streams: %s." % [x.serial + ':' + x.name for x in self.selected_sensor_component.assigned_streams]
            self.logger.info(msg)
            dlg = wx.MessageDialog(self, msg,
                                   'Error while removing a sensor component.',
                                    wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()


    def add_sensor_component_parameter(self):
        ''' Add a parameter to a sensor component.
        '''
        if self.selected_sensor_component is None:
            self.logger.error('You have to select a sensor component first.')
            return

        # Create the paramter instance.
        parameter = SensorComponentParameter(sensitivity = 1,
                                             start_time = UTCDateTime('1970-01-01'),
                                             end_time = None)
        self.selected_sensor_component.add_parameter(parameter)
        self.inventoryTree.updateInventoryData()
        return parameter


    def remove_sensor_component_parameters(self):
        ''' Remove the currently selected parameter from the component.
        '''
        if self.selected_sensor_component_parameters is None:
            self.logger.error('You have to select a sensor component parameter first.')
            return

        self.selected_sensor_component.remove_parameter(self.selected_sensor_component_parameters)

        self.selected_sensor_component_parameters = None
        self.inventoryTree.updateInventoryData()


    def remove_recorder_stream_parameter(self):
        ''' Remove the currently selected recorder stream.
        '''
        if self.selected_recorder_stream_parameter:
            self.selected_recorder_stream.remove_parameter_by_instance(self.selected_recorder_stream_parameter)
            self.inventoryTree.updateInventoryData()
        else:
            self.logger.error('You have to selecte a stream parameter first.')


    def remove_recorder_stream_assigned_sensor_component(self):
        ''' Remove the currently selected sensor component assignment.
        '''
        if self.selected_recorder_stream_assigned_component is None:
            self.logger.error('You have to select a component assignment first.')
            return

        self.selected_recorder_stream.remove_component_by_instance(self.selected_recorder_stream_assigned_component)
        self.inventoryTree.updateInventoryData()


    def remove_channel_assigned_recorder_stream(self):
        ''' Remove the currently selected recorder stream assigned to a channel.
        '''
        if self.selected_channel_assigned_recorder_stream is None:
            self.logger.error('You have to select a recorder stream assignement first.')
            return

        self.selected_channel.remove_stream_by_instance(self.selected_channel_assigned_recorder_stream)
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

        if (self.selected_inventory.__class__.__name__ != 'Inventory') and (self.selected_inventory.__class__.__name__ != 'DbInventory'):
            self.logger.info("Please select the inventory to be written to the database.")
            return

        self.logger.debug("inventory type: %s",self.selected_inventory.type)

        if self.selected_inventory.type not in 'db':
            if self.db_inventory.sensors or self.db_inventory.recorders or self.db_inventory.networks:
                self.db_inventory.merge(self.selected_inventory)
                self.db_inventory.commit()
                #msg = "The database inventory is not empty. Adding elements to an existing database inventory is currently not working. Please clear the database inventory first and then write your new inventory to the database.."
                #dlg = wx.MessageDialog(self, msg,
                #                       'Error while updating the database inventory.',
                #                        wx.OK | wx.ICON_INFORMATION)
                #dlg.ShowModal()
                #dlg.Destroy()
            else:
                self.logger.debug("Saving a non db inventory to the database.")

                for cur_sensor in self.selected_inventory.sensors:
                    self.db_inventory.add_sensor(cur_sensor)

                for cur_recorder in self.selected_inventory.recorders:
                    self.db_inventory.add_recorder(cur_recorder)

                for cur_network in self.selected_inventory.networks:
                    self.db_inventory.add_network(cur_network)

                for cur_array in self.selected_inventory.arrays:
                    self.db_inventory.add_array(cur_array)

                self.db_inventory.commit()
        else:
            self.logger.debug("Updating the existing project inventory database.")
            self.db_inventory.commit()

        # Load the updated inventory into the project inventory.
        self.psyProject.load_geometry_inventory()

        self.inventoryTree.updateInventoryData()



    ## Exit menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onExit(self, event):
        self.logger.debug("onExit")
        # Check if an unsaved database inventory exists.
        for curInventory in self.inventories.values():
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

        il = wx.ImageList(16, 16)
        self.icons = {}
        self.icons['xmlInventory'] = il.Add(icons.db_icon_16.GetBitmap())
        self.icons['recorderList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['stationList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['sensorList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['networkList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['arrayList'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['recorder_stream_list'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['recorder_stream_parameter_list'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['recorder_assigned_components_list'] = il.Add(icons.notepad_icon_16.GetBitmap())
        self.icons['network'] = il.Add(icons.network_icon_16.GetBitmap())
        self.icons['array'] = il.Add(icons._2x2_grid_icon_16.GetBitmap())
        self.icons['station'] = il.Add(icons.pin_map_icon_16.GetBitmap())
        self.icons['channel'] = il.Add(icons.pin_sq_right_icon_16.GetBitmap())
        self.icons['channel_stream'] = il.Add(icons.cassette_icon_16.GetBitmap())
        self.icons['recorder'] = il.Add(icons.cassette_icon_16.GetBitmap())
        self.icons['recorder_stream'] = il.Add(icons.cassette_icon_16.GetBitmap())
        self.icons['recorder_stream_parameter'] = il.Add(icons.wrench_icon_16.GetBitmap())
        self.icons['sensor'] = il.Add(icons.playback_rec_icon_16.GetBitmap())
        self.icons['sensor_component'] = il.Add(icons.playback_rec_icon_16.GetBitmap())
        self.icons['sensor_component_parameter'] = il.Add(icons.wrench_icon_16.GetBitmap())

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
        context_menu = None
        if(self.selected_item == 'inventory'):
            self.logger.debug('Handling an inventory.')
            # Setup the context menu.
            cm_data = (("remove", self.on_remove_inventory),
                       ("clear", self.on_clear_inventory),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'sensor_list'):
            self.logger.debug('Handling a sensor list.')
            cm_data = (("add sensor", self.on_add_sensor),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'recorder_list'):
            self.logger.debug('Handling a recorder list.')
            cm_data = (("add recorder", self.on_add_recorder),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'network_list'):
            self.logger.debug('Handling a network list.')
            cm_data = (("add network", self.on_add_network),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'sensor'):
            # Create the sensor context menu.

            cm_data = (("add component", self.on_add_sensor_component),
                       ("remove sensor", self.on_remove_sensor),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'sensor_component'):
            self.logger.debug('Handling a sensor component.')
            sub_data = []
            for cur_recorder in self.GetParent().selected_inventory.get_recorder():
                for cur_stream in cur_recorder.streams:
                    sub_data.append(('%s:%s' % (cur_recorder.serial, cur_stream.name), None))

            cm_data = (("add parameters", self.on_add_sensor_component_parameters),
                       ("remove component", self.on_remove_sensor_component),
                       ("assign to recorder", sub_data),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'sensor_component_parameter'):
            self.logger.debug('Handling a sensor component parameter.')
            cm_data = (("remove parameters", self.on_remove_sensor_component_parameters),)

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'recorder'):
            self.logger.debug('Handling a recorder.')
            cm_data = (("add stream", self.on_add_recorder_stream),
                       ("remove recorder", self.on_remove_recorder),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'recorder_stream'):
            self.logger.debug('Handling a recorder stream.')
            sub_data = []
            for cur_sensor in self.GetParent().selected_inventory.get_sensor():
                for cur_component in cur_sensor.components:
                    sub_data.append(('%s:%s:%s:%s' % (cur_sensor.serial, cur_sensor.model, cur_sensor.producer, cur_component.name), self.on_assign_component_to_stream))

            cm_data = (("assign component", sub_data),
                       ("add parameter", self.on_add_recorder_stream_parameter),
                       ("remove stream", self.on_remove_recorder_stream),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'recorder_stream_assigned_component'):
            self.logger.debug('Handling a component assigned to a recorder stream.')
            cm_data = (('remove component assignment', self.on_remove_recorder_stream_assigned_sensor_component),)
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'recorder_stream_parameter'):
            cm_data = (('remove paramter', self.on_remove_recorder_stream_parameter),)
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'station'):
            # Setup the context menu.
            cm_data = (("add channel", self.on_add_channel),
                       ("remove station", self.on_remove_station),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'channel'):
            sub_data = []
            for cur_recorder in self.GetParent().selected_inventory.get_recorder():
                for cur_stream in cur_recorder.streams:
                    sub_data.append(('%s:%s:%s:%s' % (cur_stream.serial, cur_stream.model, cur_stream.producer, cur_stream.name), self.on_assign_stream_to_channel))

            cm_data = (("assign stream", sub_data),
                       ("remove channel", self.on_remove_channel),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'channel_assigned_recorder_stream'):
            # Setup the context menu.
            cm_data = (("remove stream assignement", self.on_remove_channel_assigned_recorder_stream),)
            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        elif(self.selected_item == 'network'):
            cm_data = (("add station", self.on_add_station),
                       ("remove_network", self.on_remove_network),
                       ("separator", None),
                       ("expand", self.on_expand_element),
                       ("collapse", self.on_collapse_element))

            # create the context menu.
            context_menu = psyContextMenu(cm_data)
        if context_menu:
            pos = evt.GetPosition()
            pos = self.ScreenToClient(pos)
            self.selected_tree_item_id = self.HitTest(pos)[0]
            self.PopupMenu(context_menu, pos)


    def on_remove_inventory(self, event):
        ''' Handle the context menu click.
        '''
        if self.Parent.selected_inventory.type not in 'db':
            self.Parent.remove_inventory()
            self.Parent.updateSensorListView()
        else:
            msg = "Can't remove the database inventory."
            dlg = wx.MessageDialog(self, msg,
                                   'Error while removing an inventory.',
                                    wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()


    def on_clear_inventory(self, event):
        ''' Handle the context menu click.
        '''
        msg = "Do you really want to clear the selected inventory?"
        dlg = wx.MessageDialog(self, msg,
                               'Confirm to clear the selected inventory.',
                                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.Parent.clear_inventory()


    def on_add_sensor(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.selected_sensor = self.Parent.addSensor()
        self.selected_item = 'sensor'
        self.Parent.inventoryViewNotebook.updateSensorListView()


    def on_remove_sensor(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_sensor()
        self.Parent.inventoryViewNotebook.updateSensorListView()


    def on_add_sensor_component(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.selected_sensor_component = self.Parent.add_sensor_component()
        self.selected_item = 'sensor_component'
        self.Parent.inventoryViewNotebook.updateSensorListView()


    def on_remove_sensor_component(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_sensor_component()
        self.Parent.inventoryViewNotebook.updateSensorListView()


    def on_add_sensor_component_parameters(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.selected_sensor_component_parameters = self.Parent.add_sensor_component_parameter()
        self.selected_item = 'sensor_component parameter'
        self.Parent.inventoryViewNotebook.updateSensorListView()


    def on_remove_sensor_component_parameters(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_sensor_component_parameters()
        self.Parent.inventoryViewNotebook.updateSensorListView()


    def on_add_recorder(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.add_recorder()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_add_recorder_stream(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.add_recorder_stream()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_add_recorder_stream_parameter(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.add_recorder_stream_parameter()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_remove_recorder(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_recorder()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_remove_recorder_stream(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_recorder_stream()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_remove_recorder_stream_parameter(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_recorder_stream_parameter()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_remove_recorder_stream_assigned_sensor_component(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_recorder_stream_assigned_sensor_component()
        self.Parent.inventoryViewNotebook.updateRecorderListView()


    def on_add_network(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.add_network()
        self.Parent.inventoryViewNotebook.updateNetworkListView()


    def on_remove_network(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_network()
        self.Parent.inventoryViewNotebook.updateNetworkListView()


    def on_add_station(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.add_station()
        self.Parent.inventoryViewNotebook.updateStationListView()

    def on_remove_station(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_station()
        self.Parent.inventoryViewNotebook.updateStationListView()


    def on_add_channel(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.add_channel()
        self.Parent.inventoryViewNotebook.updateStationListView()


    def on_remove_channel(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_channel()
        self.Parent.inventoryViewNotebook.updateStationListView()


    def on_remove_channel_assigned_recorder_stream(self, event):
        ''' Handle the context menu click.
        '''
        self.Parent.remove_channel_assigned_recorder_stream()
        self.Parent.inventoryViewNotebook.updateStationListView()




    def on_collapse_element(self, event):
        ''' Collapse the selected element.
        '''
        self.CollapseAllChildren(self.selected_tree_item_id)


    def on_expand_element(self, event):
        ''' Expand the selected element.
        '''
        self.ExpandAllChildren(self.selected_tree_item_id)


    def on_assign_stream_to_channel(self, event):
        ''' Assign a stream to a channel.
        '''
        item_id = event.GetId()
        menu = event.GetEventObject()
        label = menu.GetLabel(item_id)
        serial, model, producer, name = label.split(':')

        added_stream = self.Parent.selected_channel.add_stream(serial = serial,
                                                               model = model,
                                                               producer = producer,
                                                               name = name,
                                                               start_time = UTCDateTime('1970-1-1'),
                                                               end_time = None)

        self.Parent.inventoryViewNotebook.updateStationListView()
        self.updateInventoryData()


    def on_assign_component_to_stream(self, event):
        ''' Assign a sensor component to a recorder stream.
        '''
        item_id = event.GetId()
        menu = event.GetEventObject()
        label = menu.GetLabel(item_id)
        serial, model, producer, name = label.split(':')

        slot = self.Parent.selected_recorder_stream.get_free_component_slot()

        if slot:
            try:
                self.Parent.selected_recorder_stream.add_component(serial = serial,
                                                                   model = model,
                                                                   producer = producer,
                                                                   name = name,
                                                                   start_time = slot[0],
                                                                   end_time = slot[1])
            except RuntimeError as e:
                self.logger.excetion(e)
            else:
                self.Parent.inventoryViewNotebook.updateRecorderListView()
                self.updateInventoryData()
        else:
            msg = "There is no free time slot for a new component."
            dlg = wx.MessageDialog(self, msg,
                                   'Error while adding a component.',
                                    wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()




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
        source = self.GetItemData(self.GetSelection())

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

        old_inventory = self.Parent.selected_inventory
        if self.selected_item == 'array':
            old_array = self.Parent.selected_array
        else:
            old_array = None

        if(pyData.__class__.__name__ == 'Station' or pyData.__class__.__name__ == 'DbStation'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_network = pyData.parent_network
            self.Parent.selected_station = pyData
            if self.Parent.selected_station.channels:
                self.Parent.selected_channel = pyData.channels[0]
                if self.Parent.selected_channel.streams:
                    self.Parent.selected_channel_assigned_recorder_stream = self.Parent.selected_channel.streams[0]
            self.selected_item = 'station'
            self.Parent.inventoryViewNotebook.updateStationListView()
        elif(pyData.__class__.__name__ == 'Channel' or pyData.__class__.__name__ == 'DbChannel'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_network = pyData.parent_station.parent_network
            self.Parent.selected_station = pyData.parent_station
            self.Parent.selected_channel = pyData
            self.selected_item = 'channel'
            self.Parent.inventoryViewNotebook.updateStationListView()

        elif(pyData.__class__.__name__ == 'Sensor' or pyData.__class__.__name__ == 'DbSensor'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_sensor = pyData
            if self.Parent.selected_sensor.components:
                self.Parent.selected_sensor_component = self.Parent.selected_sensor.components[0]
                if self.Parent.selected_sensor_component.parameters:
                    self.Parent.selected_sensor_component_parameters = self.Parent.selected_sensor_component.parameters[0]
            self.selected_item = 'sensor'
            self.Parent.inventoryViewNotebook.updateSensorListView()
        elif(pyData.__class__.__name__ == 'SensorComponent' or pyData.__class__.__name__ == 'DbSensorComponent'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_sensor = pyData.parent_sensor
            self.Parent.selected_sensor_component = pyData
            if self.Parent.selected_sensor_component.parameters:
                self.Parent.selected_sensor_component_parameters = self.Parent.selected_sensor_component.parameters[0]
            self.selected_item = 'sensor_component'
            self.Parent.inventoryViewNotebook.updateSensorListView()
        elif(pyData.__class__.__name__ == 'SensorComponentParameter' or pyData.__class__.__name__ == 'DbSensorComponentParameter'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_sensor = pyData.parent_component.parent_sensor
            self.Parent.selected_sensor_component = pyData.parent_component
            self.Parent.selected_sensor_component_parameters = pyData
            self.selected_item = 'sensor_component_parameter'
            self.Parent.inventoryViewNotebook.updateSensorListView()
        elif(pyData.__class__.__name__ == 'Recorder' or pyData.__class__.__name__ == 'DbRecorder'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_recorder = pyData
            self.selected_item = 'recorder'
            self.Parent.inventoryViewNotebook.updateRecorderListView()
        elif(pyData.__class__.__name__ == 'RecorderStream' or pyData.__class__.__name__ == 'DbRecorderStream'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_recorder = pyData.parent_recorder
            self.Parent.selected_recorder_stream = pyData
            if self.GetItemText(evt.GetItem()) == 'parameters':
                self.selected_item = 'recorder_stream_parameter_list'
            elif self.GetItemText(evt.GetItem()) == 'assigned components':
                self.selected_item = 'recorder_assigned_components_list'
            else:
                self.selected_item = 'recorder_stream'
            self.Parent.inventoryViewNotebook.updateRecorderListView()
        elif(pyData.__class__.__name__ == 'TimeBox'):
            if pyData.item.__class__.__name__ == 'SensorComponent' or pyData.__class__.__name__ == 'DbSensorComponent':
                self.Parent.selected_inventory = pyData.parent.parent_inventory
                self.Parent.selected_recorder = pyData.parent.parent_recorder
                self.Parent.selected_recorder_stream = pyData.parent
                self.Parent.selected_recorder_stream_assigned_component = pyData
                self.selected_item = 'recorder_stream_assigned_component'
                self.Parent.inventoryViewNotebook.updateRecorderListView()
            elif(pyData.item.__class__.__name__ == 'RecorderStream' or pyData.item.__class__.__name__ == 'DbRecorderStream'):
                self.Parent.selected_inventory = pyData.parent.parent_inventory
                self.Parent.selected_network = pyData.parent.parent_station.parent_network
                self.Parent.selected_station = pyData.parent.parent_station
                self.Parent.selected_channel = pyData.parent
                self.Parent.selected_channel_assigned_recorder_stream = pyData
                self.selected_item = 'channel_assigned_recorder_stream'
                self.Parent.inventoryViewNotebook.updateStationListView()
            elif(pyData.item.__class__.__name__ == 'Station' or pyData.item.__class__.__name__ == 'DbStation'):
                self.Parent.selected_inventory = pyData.parent.parent_inventory
                self.Parent.selected_station = pyData.item
                if self.Parent.selected_station.channels:
                    self.Parent.selected_channel = pyData.channels[0]
                    if self.Parent.selected_channel.streams:
                        self.Parent.selected_channel_assigned_recorder_stream = self.Parent.selected_channel.streams[0]
                self.selected_item = 'station'
                self.Parent.inventoryViewNotebook.updateStationListView()

        elif(pyData.__class__.__name__ == 'RecorderStreamParameter' or pyData.__class__.__name__ == 'DbRecorderStreamParameter'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_recorder = pyData.parent_recorder_stream.parent_recorder
            self.Parent.selected_recorder_stream = pyData.parent_recorder_stream
            self.Parent.selected_recorder_stream_parameter = pyData
            self.selected_item = 'recorder_stream_parameter'
            self.Parent.inventoryViewNotebook.updateRecorderListView()
        elif(pyData.__class__.__name__ == 'Network' or pyData.__class__.__name__ == 'DbNetwork'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_network = pyData
            self.selected_item = 'network'
            self.Parent.inventoryViewNotebook.updateNetworkListView(pyData)
        elif(pyData.__class__.__name__ == 'Array' or pyData.__class__.__name__ == 'DbArray'):
            self.Parent.selected_inventory = pyData.parent_inventory
            self.Parent.selected_array = pyData
            self.selected_item = 'array'
            self.Parent.inventoryViewNotebook.updateArrayListView(pyData)
        elif(pyData.__class__.__name__ == 'Inventory' or pyData.__class__.__name__ == 'DbInventory'):
            # Check if on of the list items was selected.
            if(self.GetItemText(evt.GetItem()) == 'Networks'):
                self.selected_item = 'network_list'
                self.Parent.selected_inventory = pyData
            elif(self.GetItemText(evt.GetItem()) == 'Recorders'):
                self.selected_item = 'recorder_list'
                self.Parent.selected_inventory = pyData
            elif(self.GetItemText(evt.GetItem()) == 'Sensors'):
                self.selected_item = 'sensor_list'
                self.Parent.selected_inventory = pyData
            else:
                # The inventory item was selected.
                self.Parent.selected_inventory = pyData
                self.selected_item = 'inventory'


        if self.Parent.inventoryViewNotebook.GetSelection() == 1:
            if self.selected_item == 'array':
                selected_array = self.Parent.selected_array
            else:
                selected_array = None

            if self.Parent.selected_inventory != old_inventory or selected_array != old_array:
                self.Parent.inventoryViewNotebook.updateMapView(self.Parent.selected_inventory, array = selected_array)

    ## Update the inventory tree.
    #
    # @param self The object pointer.    
    def updateInventoryData(self):
        # Delete all items below the root.
        self.DeleteChildren(self.root)

        # rebuild the inventory tree.
        for curKey, curInventory in self.Parent.inventories.items():
            inventoryItem = self.AppendItem(self.root, curKey + '(' + curInventory.type + ')')
            self.SetItemPyData(inventoryItem, curInventory)
            self.SetItemBold(inventoryItem, True)
            self.SetItemImage(inventoryItem, self.icons['xmlInventory'], wx.TreeItemIcon_Normal)

            sensorListItem = self.AppendItem(inventoryItem, 'Sensors')
            self.SetItemPyData(sensorListItem, curInventory)
            self.SetItemBold(sensorListItem, True)
            self.SetItemImage(sensorListItem, self.icons['sensorList'], wx.TreeItemIcon_Normal)

            recorderListItem = self.AppendItem(inventoryItem, 'Recorders')
            self.SetItemPyData(recorderListItem, curInventory)
            self.SetItemBold(recorderListItem, True)
            self.SetItemImage(recorderListItem, self.icons['recorderList'], wx.TreeItemIcon_Normal)

            networkListItem = self.AppendItem(inventoryItem, 'Networks')
            self.SetItemPyData(networkListItem, curInventory)
            self.SetItemBold(networkListItem, True)
            self.SetItemImage(networkListItem, self.icons['networkList'], wx.TreeItemIcon_Normal)

            arrayListItem = self.AppendItem(inventoryItem, 'Arrays')
            self.SetItemPyData(arrayListItem, curInventory)
            self.SetItemBold(arrayListItem, True)
            self.SetItemImage(arrayListItem, self.icons['arrayList'], wx.TreeItemIcon_Normal)

            # Fill the sensors
            for curSensor in sorted(curInventory.sensors, key = attrgetter('serial')):
                if curSensor.model is None:
                    sensor_model = ''
                else:
                    sensor_model = curSensor.model
                curSensorItem = self.AppendItem(sensorListItem, curSensor.serial + ' (' + curSensor.producer + ':' + sensor_model + ')')
                self.SetItemPyData(curSensorItem, curSensor)
                self.SetItemImage(curSensorItem, self.icons['sensor'], wx.TreeItemIcon_Normal)

                for curComponent in sorted(curSensor.components, key = attrgetter('name')):
                    curComponentItem = self.AppendItem(curSensorItem, curComponent.name)
                    self.SetItemPyData(curComponentItem, curComponent)
                    self.SetItemImage(curComponentItem, self.icons['sensor_component'], wx.TreeItemIcon_Normal)

                    for curParameter in sorted(curComponent.parameters, key = attrgetter('start_time')):
                        item = self.AppendItem(curComponentItem, '(' + curParameter.start_time_string + ' to ' + curParameter.end_time_string + ')')
                        self.SetItemPyData(item, curParameter)
                        self.SetItemImage(item, self.icons['sensor_component_parameter'], wx.TreeItemIcon_Normal)


            # Fill the recorders.
            for curRecorder in sorted(curInventory.recorders, key = attrgetter('serial')):
                curRecorderItem = self.AppendItem(recorderListItem, curRecorder.serial + ' (' + curRecorder.producer + ':' + curRecorder.model + ')')
                self.SetItemPyData(curRecorderItem, curRecorder)
                self.SetItemImage(curRecorderItem, self.icons['recorder'], wx.TreeItemIcon_Normal)


                # Add the recorder streams.
                for curStream in sorted(curRecorder.streams, key = attrgetter('name')):
                    curStreamItem = self.AppendItem(curRecorderItem, curStream.name)
                    self.SetItemPyData(curStreamItem, curStream)
                    self.SetItemImage(curStreamItem, self.icons['recorder_stream'], wx.TreeItemIcon_Normal)

                    # Add the recorder stream parameter list icon.
                    list_item = self.AppendItem(curStreamItem, 'parameters')
                    self.SetItemPyData(list_item, curStream)
                    self.SetItemBold(list_item, True)
                    self.SetItemImage(list_item, self.icons['recorder_stream_parameter_list'], wx.TreeItemIcon_Normal)
                    for cur_parameter in sorted(curStream.parameters, key = attrgetter('start_time')):
                        item = self.AppendItem(list_item, '(' + cur_parameter.start_time_string + ' to ' + cur_parameter.end_time_string + ')')
                        self.SetItemPyData(item, cur_parameter)
                        self.SetItemImage(item, self.icons['recorder_stream_parameter'], wx.TreeItemIcon_Normal)

                    # Add the assigned component list icon.
                    list_item = self.AppendItem(curStreamItem, 'assigned components')
                    self.SetItemPyData(list_item, curStream)
                    self.SetItemBold(list_item, True)
                    self.SetItemImage(list_item, self.icons['recorder_assigned_components_list'], wx.TreeItemIcon_Normal)

                    for curTimebox in sorted(curStream.components, key = attrgetter('start_time')):
                        item = self.AppendItem(list_item, curTimebox.item.serial + ':' + curTimebox.item.name + ' (' + curTimebox.start_time_string + ' to ' + curTimebox.end_time_string + ')')
                        self.SetItemPyData(item, curTimebox)
                        self.SetItemImage(item, self.icons['sensor_component'], wx.TreeItemIcon_Normal)


            # Fill the networks.
            for curNetwork in curInventory.networks:
                curNetworkItem = self.AppendItem(networkListItem, curNetwork.name)
                self.SetItemPyData(curNetworkItem, curNetwork)
                self.SetItemImage(curNetworkItem, self.icons['network'], wx.TreeItemIcon_Normal)

                for curStation in sorted(curNetwork.stations,key = attrgetter('name')):
                    curStationItem = self.AppendItem(curNetworkItem, curStation.name + ':' + curStation.location_string)
                    self.SetItemPyData(curStationItem, curStation)
                    self.SetItemImage(curStationItem, self.icons['station'], wx.TreeItemIcon_Normal)

                    for curChannel in sorted(curStation.channels, key = attrgetter('name')):
                        curChannelItem = self.AppendItem(curStationItem, curChannel.name)
                        self.SetItemPyData(curChannelItem, curChannel)
                        self.SetItemImage(curChannelItem, self.icons['channel'], wx.TreeItemIcon_Normal)

                        for curTimebox in sorted(curChannel.streams, key = attrgetter('start_time')):
                            item = self.AppendItem(curChannelItem, curTimebox.item.serial + ':' + curTimebox.item.name + ' (' + curTimebox.start_time_string + ' to ' + curTimebox.end_time_string + ')')
                            self.SetItemPyData(item, curTimebox)
                            self.SetItemImage(item, self.icons['channel_stream'], wx.TreeItemIcon_Normal)

            # Fill the arrays.
            for curArray in curInventory.arrays:
                curArrayItem = self.AppendItem(arrayListItem, curArray.name)
                self.SetItemPyData(curArrayItem, curArray)
                self.SetItemImage(curArrayItem, self.icons['array'], wx.TreeItemIcon_Normal)

                for curStationTb in sorted(curArray.stations, key = attrgetter('name')):
                    curStationItem = self.AppendItem(curArrayItem, curStationTb.network + ':' + curStationTb.name + ':' + curStationTb.location_string)
                    print(curStationTb.item)
                    self.SetItemPyData(curStationItem, curStationTb)
                    self.SetItemImage(curStationItem, self.icons['station'], wx.TreeItemIcon_Normal)

            self.ExpandAllChildren(inventoryItem)


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
        self.array = None

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
        self.listViewPanel.showControlPanel('network')


    def updateArrayListView(self, network):
        ''' Show the array data in the list view.
        '''
        self.logger.debug("updating the array listview")
        self.listViewPanel.showControlPanel('array')

    def updateRecorderListView(self):
        ''' Show the recorder data in the list view.
        '''
        self.logger.debug("updating the recorder listview")
        self.listViewPanel.showControlPanel('recorder')


    ## Show the station data in the list view.
    #
    def updateStationListView(self):
        self.logger.debug("updating the station listview")
        self.listViewPanel.showControlPanel('station')

    ## Show the station data in the list view.
    #
    def updateSensorListView(self):
        self.logger.debug("updating the sensor listview")
        self.listViewPanel.showControlPanel('sensor')


    def updateMapView(self, inventory, array = None):
        '''
        Initialize the map view panel with the selected inventory.
        '''
        self.logger.debug("Initializing the mapview")

        def init_map(panel, cur_inventory):
            panel.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
            panel.mapViewPanel.initMap(cur_inventory)
            panel.inventory = cur_inventory
            panel.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

        if inventory != self.inventory or array != self.array:
            #t = Thread(target = init_map, args = (self, inventory))
            #t.setDaemon(True)
            #t.start()

            wx.BeginBusyCursor()
            #try:
            self.mapViewPanel.initMap(inventory = inventory, array = array)
            #finally:
            self.inventory = inventory
            self.array = array
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
        self.controlPanels['array'] = ArrayPanel(self, wx.ID_ANY)

        for cur_panel in list(self.controlPanels.values()):
            cur_panel.Hide()

        #sizer.Add(self.controlPanels['station'], pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.Add(self.controlPanels['sensor'], pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizerAndFit(self.sizer)



    def showControlPanel(self, name):

        activePanel = self.sizer.FindItemAtPosition((0,0))
        if activePanel is not None:
            activePanel.GetWindow().Hide()
            self.sizer.Detach(activePanel.GetWindow())

        self.controlPanels[name].updateData()

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


    def initMap(self, inventory, array = None):
        '''
        Initialize the map parameters.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.geometry.MapViewPanel`
        '''
        self.mapConfig = {}
        self.stations = []

        # Clear the map.
        self.mapAx.clear()
        self.mapAx.set_xlim(0, 1)
        self.mapAx.set_ylim(0, 1)

        if array is None:
            self.plot_networks(inventory = inventory)
        else:
            self.plot_array(array = array)

        # Set the map limits.
        self.mapAx.autoscale(True)
        #ll_x, ll_y = proj(lower_left[0], lower_left[1])
        #ur_x, ur_y = proj(upper_right[0], upper_right[1])
        #self.mapAx.set_xlim((ll_x, ur_x))
        #self.mapAx.set_ylim((ll_y, ur_y))

        # Change to plain tick label formatter.
        #self.mapAx.ticklabel_format(style = 'plain')
        self.mapAx.get_yaxis().get_major_formatter().set_useOffset(False)
        self.mapAx.get_yaxis().get_major_formatter().set_scientific(False)

        self.mapCanvas.mpl_connect('pick_event', self.onPick)
        self.mapCanvas.draw()


    def plot_networks(self, inventory):
        ''' Plot the stations of all networks in the inventory.
        '''
        # Get the lon/lat limits of the inventory.
        lonLat = []
        for curNet in inventory.networks:
            lonLat.extend([stat.get_lon_lat() for stat in curNet.stations])
            self.stations.extend([stat for stat in curNet.stations])

        if len(lonLat) == 0:
            self.mapAx.text(1, 1.02, 'NO STATIONS AVAILABLE',
                            ha = 'right', transform = self.mapAx.transAxes)
            self.mapCanvas.draw()
            return

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
        lower_left = lonLatMin - map_extent * 0.1
        upper_right = lonLatMax + map_extent * 0.1
        self.mapConfig['limits'] = np.hstack([lower_left, upper_right])

        lon = [x[0] for x in lonLat]
        lat = [x[1] for x in lonLat]

        # Get the epsg code of the UTM projection.
        search_dict = {'projection': 'utm', 'ellps': self.mapConfig['ellips'].upper(), 'zone': self.mapConfig['utmZone'], 'no_defs': True, 'units': 'm'}
        if self.mapConfig['hemisphere'] == 'south':
            search_dict['south'] = True

        epsg_dict = geom_util.get_epsg_dict()
        code = [(c, x) for c, x in list(epsg_dict.items()) if  x == search_dict]

        # Setup the pyproj projection.projection
        #proj = pyproj.Proj(proj = 'utm', zone = self.mapConfig['utmZone'], ellps = self.mapConfig['ellips'].upper())

        #TODO The call in the next line prevents the creation of the map.
        #self.pref_manager.set_value('projection_coordinate_system', 'epsg:'+code[0][0])
        proj = pyproj.Proj(init = 'epsg:'+code[0][0])


        # Plot the stations.
        station_palette = sns.color_palette(n_colors = len(inventory.arrays) + 1)
        x,y = proj(lon, lat)
        stat_color = []
        for cur_station, cur_x, cur_y in zip(self.stations, x, y):
            cur_color = station_palette[0]
            for k, cur_array in enumerate(inventory.arrays):
                if cur_array.get_station(snl = cur_station.snl):
                    cur_color = station_palette[k + 1]
                    break
            stat_color.append(cur_color)
            self.mapAx.text(cur_x, cur_y, cur_station.snl_string)
        self.mapAx.scatter(x, y, s=100, c = stat_color, marker='^', picker=5, zorder = 3)

        # Add some map annotation.
        self.mapAx.text(1, 1.02, geom_util.epsg_from_srs(proj.srs),
            ha = 'right', transform = self.mapAx.transAxes)


    def plot_array(self, array):
        ''' Plot the stations of a single array.
        '''
        # Get the lon/lat limits of the inventory.
        lonLat = []
        lonLat.extend([stat.get_lon_lat() for stat in array.stations])
        self.stations.extend([stat for stat in array.stations])

        if len(lonLat) == 0:
            self.mapAx.text(1, 1.02, 'NO STATIONS AVAILABLE',
                            ha = 'right', transform = self.mapAx.transAxes)
            self.mapCanvas.draw()
            return

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
        lower_left = lonLatMin - map_extent * 0.1
        upper_right = lonLatMax + map_extent * 0.1
        self.mapConfig['limits'] = np.hstack([lower_left, upper_right])

        lon = [x[0] for x in lonLat]
        lat = [x[1] for x in lonLat]

        # Get the epsg code of the UTM projection.
        search_dict = {'projection': 'utm', 'ellps': self.mapConfig['ellips'].upper(), 'zone': self.mapConfig['utmZone'], 'no_defs': True, 'units': 'm'}
        if self.mapConfig['hemisphere'] == 'south':
            search_dict['south'] = True

        epsg_dict = geom_util.get_epsg_dict()
        code = [(c, x) for c, x in list(epsg_dict.items()) if  x == search_dict]

        # Setup the pyproj projection.projection
        #proj = pyproj.Proj(proj = 'utm', zone = self.mapConfig['utmZone'], ellps = self.mapConfig['ellips'].upper())

        #TODO The call in the next line prevents the creation of the map.
        #self.pref_manager.set_value('projection_coordinate_system', 'epsg:'+code[0][0])
        proj = pyproj.Proj(init = 'epsg:'+code[0][0])


        # Plot the stations.
        x,y = proj(lon, lat)
        for cur_station, cur_x, cur_y in zip(array.stations, x, y):
            self.mapAx.text(cur_x, cur_y, cur_station.snl_string)
        self.mapAx.scatter(x, y, s=100, marker='^', picker=5, zorder = 3)

        # Add some map annotation.
        self.mapAx.text(1, 1.02, geom_util.epsg_from_srs(proj.srs),
            ha = 'right', transform = self.mapAx.transAxes)


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

        self.mgr = wx.aui.AuiManager(self)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)

        # Create the recorder grid.
        fields = self.getNetworkFields()
        self.network_grid = wx.grid.Grid(self)
        self.network_grid.CreateGrid(1, len(fields))

        # Bind the network_grid events.
        self.network_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onNetworkCellChange)

        # Set the column attributes.
        for k, (name, label, attr, converter)  in enumerate(fields):
            self.network_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.network_grid.SetColAttr(k, roAttr)

        self.network_grid.AutoSizeColumns()

        self.mgr.AddPane(self.network_grid, wx.aui.AuiPaneInfo().Name('network').
                         CentrePane().Layer(0).Position(0).MinSize(wx.Size(200, 100)))

        # Create the station grid.
        fields = self.getStationFields()
        self.station_grid = wx.grid.Grid(self)
        self.station_grid.CreateGrid(5, len(fields))

        # Bind the stationGrid events.
        #self.sensorGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onSensorTimeCellChange)

        # Set the column attributes.
        for k, (name, label, attr, converter) in enumerate(fields):
            self.station_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.station_grid.SetColAttr(k, roAttr)

        self.mgr.AddPane(self.station_grid, wx.aui.AuiPaneInfo().Name('stations').
                         Caption('stations of network').Bottom().Row(1).Position(0).Layer(0).
                         CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 300)))

        self.mgr.Update()


    @property
    def selected_network(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_network
        else:
            return None


    def getNetworkFields(self):
        ''' The recorder grid columns.
        '''
        tableField = []
        tableField.append(('name', 'name', 'editable', str))
        tableField.append(('description', 'description', 'editable', str))
        tableField.append(('type', 'type', 'editable', str))
        return tableField


    def getStationFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('network', 'network', 'readonly', str))
        tableField.append(('name', 'name', 'readonly', str))
        tableField.append(('location', 'location', 'readonly', str))
        tableField.append(('start_time', 'start', 'readonly', str))
        tableField.append(('end_time', 'end', 'readonly', str))
        tableField.append(('x', 'x', 'readonly', float))
        tableField.append(('y', 'y', 'readonly', float))
        tableField.append(('z', 'z', 'readonly', float))
        tableField.append(('coord_system', 'coord. system', 'readonly', str))
        tableField.append(('description', 'description', 'readonly', str))
        tableField.append(('available_channels_string', 'channels', 'readonly', str))
        tableField.append(('assigned_recorders_string', 'recorders', 'readonly', str))
        tableField.append(('assigned_sensors_string', 'sensors', 'readonly', str))
        return tableField


    def updateData(self):
        ''' Update the displayed data.
        '''
        # Update the sensor grid fields.
        self.setGridValues(self.selected_network, self.network_grid, self.getNetworkFields(), 0)
        self.network_grid.AutoSizeColumns()


        # Resize the grid rows.
        if self.station_grid.GetNumberRows() > 0:
            self.station_grid.DeleteRows(0, self.station_grid.GetNumberRows())
        self.station_grid.AppendRows(len(self.selected_network.stations))

        # Update the station grid fields.
        for k, cur_station in enumerate(self.selected_network.stations):
            self.setGridValues(cur_station,
                               self.station_grid,
                               self.getStationFields(),
                               k)
        self.station_grid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        ''' Set the grid values of the specified grid.
        '''
        for pos, (field, label, attr, converter) in enumerate(fields):
            try:
                # Take care of fields with custom strings. 
                custom_fields = {}
                custom_fields['start_time'] = 'start_time_string'
                custom_fields['end_time'] = 'end_time_string'
                if field in iter(custom_fields.keys()) and hasattr(object, custom_fields[field]):
                    field = custom_fields[field]

                if field is not None and getattr(object, field) is not None:
                    grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
                else:
                    grid.SetCellValue(rowNumber, pos, '')
            except Exception:
                pass

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
            converter = grid_fields[ind][3]

            setattr(self.selected_network, fieldName, converter(self.network_grid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()



class ArrayPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.mgr = wx.aui.AuiManager(self)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)

        # Create the array grid.
        fields = self.getArrayFields()
        self.array_grid = wx.grid.Grid(self)
        self.array_grid.CreateGrid(1, len(fields))

        # Bind the array_grid events.
        self.array_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onArrayCellChange)

        # Set the column attributes.
        for k, (name, label, attr, converter)  in enumerate(fields):
            self.array_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.array_grid.SetColAttr(k, roAttr)

        self.array_grid.AutoSizeColumns()

        self.mgr.AddPane(self.array_grid, wx.aui.AuiPaneInfo().Name('array').
                         CentrePane().Layer(0).Position(0).MinSize(wx.Size(200, 100)))

        # Create the station grid.
        fields = self.getStationFields()
        self.station_grid = wx.grid.Grid(self)
        self.station_grid.CreateGrid(5, len(fields))

        # Bind the stationGrid events.
        #self.sensorGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onSensorTimeCellChange)

        # Set the column attributes.
        for k, (name, label, attr, converter) in enumerate(fields):
            self.station_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.station_grid.SetColAttr(k, roAttr)

        self.mgr.AddPane(self.station_grid, wx.aui.AuiPaneInfo().Name('stations').
                         Caption('stations assigned to the array').Bottom().Row(1).Position(0).Layer(0).
                         CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 300)))

        self.mgr.Update()


    @property
    def selected_array(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_array
        else:
            return None


    def getArrayFields(self):
        ''' The array grid columns.
        '''
        tableField = []
        tableField.append(('name', 'name', 'editable', str))
        tableField.append(('description', 'description', 'editable', str))
        return tableField


    def getStationFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('name', 'name', 'readonly', str))
        tableField.append(('location', 'location', 'readonly', str))
        tableField.append(('network', 'network', 'readonly',str))
        tableField.append(('start_time', 'start time', 'readonly', str))
        tableField.append(('end_time', 'end time', 'readonly', str))
        tableField.append(('x', 'x', 'readonly', float))
        tableField.append(('y', 'y', 'readonly', float))
        tableField.append(('z', 'z', 'readonly', float))
        tableField.append(('coord_system', 'coord. system', 'readonly', str))
        tableField.append(('description', 'description', 'readonly', str))
        tableField.append(('available_channels_string', 'channels', 'readonly', str))
        tableField.append(('assigned_recorders_string', 'recorders', 'readonly', str))
        return tableField


    def updateData(self):
        ''' Update the displayed data.
        '''
        # Update the sensor grid fields.
        self.setGridValues(self.selected_array, self.array_grid, self.getArrayFields(), 0)
        self.array_grid.AutoSizeColumns()


        # Resize the grid rows.
        if self.station_grid.GetNumberRows() > 0:
            self.station_grid.DeleteRows(0, self.station_grid.GetNumberRows())
        self.station_grid.AppendRows(len(self.selected_array.stations))

        # Update the station grid fields.
        for k, cur_station in enumerate(self.selected_array.stations):
            self.setGridValues(cur_station,
                                      self.station_grid,
                                      self.getStationFields(),
                                      k)
        self.station_grid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        ''' Set the grid values of the specified grid.
        '''
        for pos, (field, label, attr, converter) in enumerate(fields):
            try:
                # Take care of fields with custom strings. 
                custom_fields = {}
                custom_fields['start_time'] = 'start_time_string'
                custom_fields['end_time'] = 'end_time_string'
                if field in iter(custom_fields.keys()) and hasattr(object, custom_fields[field]):
                    field = custom_fields[field]

                if field is not None and getattr(object, field) is not None:
                    grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
                else:
                    grid.SetCellValue(rowNumber, pos, '')
            except Exception:
                pass
            
            grid.AutoSizeColumns()



    def onArrayCellChange(self, evt):
        ''' The array_grid cell edit callback.
        '''
        selectedParameter = self.array_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getNetworkFields();
        colLabels = [x[1] for x in grid_fields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = grid_fields[ind][0]
            converter = grid_fields[ind][3]

            setattr(self.selected_network, fieldName, converter(self.network_grid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()




class RecorderPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.sizer = wx.GridBagSizer(5, 5)

        self.mgr = wx.aui.AuiManager(self)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)

        # Create the recorder grid.
        fields = self.getRecorderFields()
        self.recorder_grid = wx.grid.Grid(self, size=(-1, 40))
        self.recorder_grid.CreateGrid(1, len(fields))

        # Bind the recorder_grid events.
        self.recorder_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onRecorderCellChange)

        # Set the column attributes.
        for k, (name, label, attr, convert)  in enumerate(fields):
            self.recorder_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.recorder_grid.SetColAttr(k, roAttr)

        self.recorder_grid.AutoSizeColumns()

        self.mgr.AddPane(self.recorder_grid, wx.aui.AuiPaneInfo().Name('recorder').
                         CentrePane().Layer(0).Position(0).Row(0).Floatable(False).
                         MinSize(wx.Size(200, 100)))

        # Create the streams grid.
        fields = self.getStreamFields()
        self.stream_grid = wx.grid.Grid(self, size = (-1, 100))
        self.stream_grid.CreateGrid(1, len(fields))

        # Bind the stream_grid events.
        self.stream_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                              self.onStreamCellChange)
        self.stream_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                              self.onStreamCellLeftClick)

        # Set the column attributes.
        for k, (name, label, attr, convert)  in enumerate(fields):
            self.stream_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.stream_grid.SetColAttr(k, roAttr)

        self.stream_grid.AutoSizeColumns()

        self.mgr.AddPane(self.stream_grid, wx.aui.AuiPaneInfo().Name('streams').
                         Caption('streams of recorder').Bottom().Row(0).Position(0).Layer(1).
                         Floatable(False).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        # Create the stream parameters grid.
        fields = self.getStreamParameterFields()
        self.stream_parameter_grid = wx.grid.Grid(self, size = (-1, 100))
        self.stream_parameter_grid.CreateGrid(1, len(fields))

        # Bind the stream_parameter_grid events.
        self.stream_parameter_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                                        self.onStreamParameterCellChange)
        self.stream_parameter_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                                        self.onStreamParameterCellLeftClick)

        # Set the column attributes.
        for k, (name, label, attr, convert)  in enumerate(fields):
            self.stream_parameter_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.stream_parameter_grid.SetColAttr(k, roAttr)

        self.stream_parameter_grid.AutoSizeColumns()

        self.mgr.AddPane(self.stream_parameter_grid, wx.aui.AuiPaneInfo().Name('stream parameters').
                         Caption('parameters of stream').Bottom().Row(0).Position(0).Layer(2).
                         Floatable(False).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        # Create the assigned sensor components grid.
        fields = self.getAssignedComponentFields()
        self.assigned_component_grid = wx.grid.Grid(self, size = (-1, 100))
        self.assigned_component_grid.CreateGrid(1, len(fields))

        # Bind the assigned_component_grid events.
        self.assigned_component_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                                        self.onAssignedComponentCellChange)
        self.assigned_component_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                                        self.onAssignedComponentCellLeftClick)

        # Set the column attributes.
        for k, (name, label, attr, convert)  in enumerate(fields):
            self.assigned_component_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.assigned_component_grid.SetColAttr(k, roAttr)

        self.assigned_component_grid.AutoSizeColumns()

        self.mgr.AddPane(self.assigned_component_grid, wx.aui.AuiPaneInfo().Name('assigned components').
                         Caption('components assigned to stream').Bottom().Row(0).Position(0).Layer(3).
                         CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        self.mgr.Update()


    @property
    def selected_recorder(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_recorder
        else:
            return None


    @selected_recorder.setter
    def selected_recorder(self, value):
        self.GetTopLevelParent().selected_recorder = value


    @property
    def selected_stream(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_recorder_stream
        else:
            return None


    @selected_stream.setter
    def selected_stream(self, value):
        self.GetTopLevelParent().selected_recorder_stream = value


    @property
    def selected_stream_parameter(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_recorder_stream_parameter
        else:
            return None


    @selected_stream_parameter.setter
    def selected_stream_parameter(self, value):
        self.GetTopLevelParent().selected_recorder_stream_parameter = value


    @property
    def selected_assigned_component(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_recorder_stream_assigned_component
        else:
            return None

    @selected_assigned_component.setter
    def selected_assigned_component(self, value):
        self.GetTopLevelParent().selected_recorder_stream_assigned_component = value


    def getRecorderFields(self):
        ''' The recorder grid columns.
        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('serial', 'serial', 'editable', str))
        tableField.append(('model', 'model', 'editable', str))
        tableField.append(('producer', 'producer', 'editable', str))
        return tableField


    def getStreamFields(self):
        ''' The stream grid columns.
        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('name', 'name', 'editable', str))
        tableField.append(('label', 'label', 'editable', str))
        return tableField


    def getStreamParameterFields(self):
        ''' The stream parameter grid columns.
        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('start_time', 'start', 'editable', self.time_string_converter))
        tableField.append(('end_time', 'end', 'editable', self.time_string_converter))
        tableField.append(('gain', 'gain', 'editable', float))
        tableField.append(('bitweight', 'bitweight', 'editable', float))
        return tableField


    def getAssignedComponentFields(self):
        ''' The assigned component grid columns.
        '''
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('serial', 'serial', 'readonly', str))
        tableField.append(('model', 'model', 'readonly', str))
        tableField.append(('producer', 'producer', 'readonly', str))
        tableField.append(('name', 'name', 'readonly', str))
        tableField.append(('start_time', 'start', 'editable', self.time_string_converter))
        tableField.append(('end_time', 'end', 'editable', self.time_string_converter))
        return tableField


    def updatePaneCaption(self):
        # Change the pane captions.

        # Update the stream caption.
        if self.selected_recorder:
            caption = 'streams of recorder %s' % self.selected_recorder.serial
            pane = self.mgr.GetPane('streams')
            pane.Caption(caption)

        # Update the stream parameters caption.
        if self.selected_stream:
            caption = 'parameters of stream %s' % self.selected_stream.name
        else:
            caption = 'no stream selected'
        pane = self.mgr.GetPane('stream parameters')
        pane.Caption(caption)

       # Update the assigned components caption.
        if self.selected_stream:
            caption = 'sensor components assigned to stream %s' % self.selected_stream.name
        else:
            caption = 'no stream selected'
        pane = self.mgr.GetPane('assigned components')
        pane.Caption(caption)

        self.mgr.Update()


    def updateData(self):
        ''' Update the displayed data.
        '''
        self.updatePaneCaption()

        # Resize the grid rows.
        if self.recorder_grid.GetNumberRows() > 0:
            self.recorder_grid.DeleteRows(0, self.recorder_grid.GetNumberRows())
        if self.stream_grid.GetNumberRows() > 0:
            self.stream_grid.DeleteRows(0, self.stream_grid.GetNumberRows())

        if self.selected_recorder:
            self.recorder_grid.AppendRows(1)
            self.stream_grid.AppendRows(len(self.selected_recorder.streams))

            # Update the recorder grid fields
            self.setGridValues(self.selected_recorder,
                               self.recorder_grid, self.getRecorderFields(), 0)

            # Update the stream grid fields
            for k, cur_component in enumerate(self.selected_recorder.streams):
                self.setGridValues(cur_component,
                                   self.stream_grid,
                                   self.getStreamFields(),
                                   k)

            # Update the stream parameter grid.
            self.updateParameters()

            # Update the assigned sensor components grid.
            self.updateAssignedComponents()

            self.recorder_grid.AutoSizeColumns()


    def updateParameters(self):
        ''' Update the displayed stream parameters data.
        '''
        # Resize the grid rows.
        if self.stream_parameter_grid.GetNumberRows() > 0:
            self.stream_parameter_grid.DeleteRows(0, self.stream_parameter_grid.GetNumberRows())

        if self.selected_stream:
            self.stream_parameter_grid.AppendRows(len(self.selected_stream.parameters))

            # Update the parameter grid fields.
            for k, cur_parameter in enumerate(self.selected_stream.parameters):
                self.setGridValues(cur_parameter,
                                   self.stream_parameter_grid,
                                   self.getStreamParameterFields(),
                                   k)


        self.stream_parameter_grid.AutoSizeColumns()


    def updateAssignedComponents(self):
        ''' Update the displayed assigned components data.
        '''
        # Resize the grid rows.
        if self.assigned_component_grid.GetNumberRows() > 0:
            self.assigned_component_grid.DeleteRows(0, self.assigned_component_grid.GetNumberRows())

        if self.selected_stream:
            self.assigned_component_grid.AppendRows(len(self.selected_stream.components))

            # Update the assigned component grid fields.
            for k, cur_timebox in enumerate(self.selected_stream.components):
                cur_component = cur_timebox.item
                # Set the field values of the assigned sensor.
                self.setGridValues(cur_component,
                                   self.assigned_component_grid,
                                   self.getAssignedComponentFields(),
                                   k)
                # Set the field values of the timebox start- and end-time.
                self.setGridValues(cur_timebox,
                                   self.assigned_component_grid,
                                   self.getAssignedComponentFields(),
                                   k)



        self.assigned_component_grid.AutoSizeColumns()


    def setGridValues(self, object, grid, fields, rowNumber):
        ''' Set the grid values of the specified grid.
        '''
        for pos, (field, label, attr, converter) in enumerate(fields):
            # The id field will raise an error when normal inventory
            # instances are used. Ignore this error and continue.
            try:
                # Take care of fields with custom strings. 
                custom_fields = {}
                custom_fields['start_time'] = 'start_time_string'
                custom_fields['end_time'] = 'end_time_string'
                if field in iter(custom_fields.keys()) and hasattr(object, custom_fields[field]):
                    field = custom_fields[field]

                if field is not None and getattr(object, field) is not None:
                    grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
                else:
                    grid.SetCellValue(rowNumber, pos, '')
            except:
                pass
            grid.AutoSizeColumns()


    def onRecorderCellChange(self, evt):
        ''' The recorder_grid cell edit callback.
        '''
        selected_parameter = self.recorder_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getRecorderFields();
        col_labels = [x[1] for x in grid_fields]

        if selected_parameter in col_labels:
            ind = col_labels.index(selected_parameter)
            field_name = grid_fields[ind][0]
            converter = grid_fields[ind][3]
            setattr(self.selected_recorder, field_name, converter(self.recorder_grid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()
        else:
            pass


    def onStreamCellChange(self, evt):
        ''' The stream grid cell edit callback.
        '''
        selected_parameter = self.stream_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getStreamFields();
        col_labels = [x[1] for x in grid_fields]

        if selected_parameter in col_labels:
            ind = col_labels.index(selected_parameter)
            field_name = grid_fields[ind][0]
            converter = grid_fields[ind][3]
            setattr(self.selected_stream, field_name, converter(self.stream_grid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()
        else:
            pass


    def onStreamCellLeftClick(self, evt):
        ''' The stream grid cell left click callback.
        '''
        self.selected_stream = self.selected_recorder.streams[evt.GetRow()]
        self.updateParameters()
        self.updateAssignedComponents()
        self.updatePaneCaption()
        evt.Skip()


    def onStreamParameterCellChange(self, evt):
        ''' The stream parameter grid cell edit callback.
        '''
        selected_parameter = self.stream_parameter_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getStreamParameterFields();
        col_labels = [x[1] for x in grid_fields]

        if selected_parameter in col_labels:
            ind = col_labels.index(selected_parameter)
            field_name = grid_fields[ind][0]
            converter = grid_fields[ind][3]
            setattr(self.selected_stream_parameter, field_name, converter(self.stream_parameter_grid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()
        else:
            pass


    def onStreamParameterCellLeftClick(self, evt):
        ''' The stream grid cell left click callback.
        '''
        self.selected_stream_parameter = self.selected_stream.parameters[evt.GetRow()]
        evt.Skip()


    def onAssignedComponentCellChange(self, evt):
        ''' The assigned component grid cell edit callback.
        '''
        selected_parameter = self.assigned_component_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getAssignedComponentFields();
        col_labels = [x[1] for x in grid_fields]

        if selected_parameter in col_labels:
            ind = col_labels.index(selected_parameter)
            field_name = grid_fields[ind][0]
            converter = grid_fields[ind][3]
            setattr(self.selected_assigned_component, field_name, converter(self.assigned_component_grid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
        else:
            pass


    def onAssignedComponentCellLeftClick(self, evt):
        ''' The assigned component grid cell left click callback.
        '''
        self.selected_assigned_component = self.selected_stream.components[evt.GetRow()]
        evt.Skip()

    def time_string_converter(self, time_string):
        ''' Convert a start- or end-time string.
        '''
        if time_string in ['', 'running', 'big bang']:
            time_string = None
        else:
            time_string = UTCDateTime(time_string)

        return time_string


class StationsPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        ## The currently displayed station.
        self.displayedStation = None;

        self.mgr = wx.aui.AuiManager(self)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)

        # Create the stations grid.
        fields = self.getStationFields()
        self.station_grid = wx.grid.Grid(self, size=(-1, 100))
        self.station_grid.CreateGrid(1, len(fields))

        # Bind the stationGrid events.
        self.station_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onStationCellChange)

        for k, (name, label, attr, converter)  in enumerate(fields):
            self.station_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.station_grid.SetColAttr(k, roAttr)

        self.station_grid.AutoSizeColumns()

        self.mgr.AddPane(self.station_grid, wx.aui.AuiPaneInfo().Name("station").
                         CentrePane().Layer(0).Position(0).MinSize(wx.Size(200, 100)))


        # Create the channels grid.
        fields = self.getChannelFields()
        self.channel_grid = wx.grid.Grid(self, size=(100,100))
        self.channel_grid.CreateGrid(1, len(fields))

        # Bind the channel grid events.
        self.channel_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onChannelCellChange)
        self.channel_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onChannelCellLeftClick)

        for k, (name, label, attr, converter) in enumerate(fields):
            self.channel_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.channel_grid.SetColAttr(k, roAttr)


        caption = 'channels of station'
        self.mgr.AddPane(self.channel_grid, wx.aui.AuiPaneInfo().Name("channels").Caption(caption).
                         Bottom().Row(0).Position(0).Layer(1).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        # Create the assigned recorder stream grid.
        fields = self.getAssignedRecorderStreamFields()
        self.assigned_recorder_stream_grid = wx.grid.Grid(self, size = (100, 100))
        self.assigned_recorder_stream_grid.CreateGrid(1, len(fields))

        # Bind the assigned recorder streams grid events.
        self.assigned_recorder_stream_grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.onAssignedStreamCellChange)
        self.assigned_recorder_stream_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onAssignedStreamCellLeftClick)

        # Set the column attributes.
        for k, (name, label, attr, converter) in enumerate(fields):
            self.assigned_recorder_stream_grid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.assigned_recorder_stream_grid.SetColAttr(k, roAttr)

        caption = 'recorder streams assigned to channel'
        self.mgr.AddPane(self.assigned_recorder_stream_grid, wx.aui.AuiPaneInfo().Name("assigned recorder streams").Caption(caption).
                         Bottom().Row(0).Position(0).Layer(2).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        self.mgr.Update()


    @property
    def selected_station(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_station
        else:
            return None


    @property
    def selected_channel(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_channel
        else:
            return None

    @selected_channel.setter
    def selected_channel(self, value):
        self.GetTopLevelParent().selected_channel = value


    @property
    def selected_channel_assigned_recorder_stream(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_channel_assigned_recorder_stream
        else:
            return None

    @selected_channel_assigned_recorder_stream.setter
    def selected_channel_assigned_recorder_stream(self, value):
        self.GetTopLevelParent().selected_channel_assigned_recorder_stream = value


    def onStationCellChange(self, evt):
        selectedParameter = self.station_grid.GetColLabelValue(evt.GetCol())
        grid_fields = self.getStationFields();
        colLabels = [x[1] for x in grid_fields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = grid_fields[ind][0]
            converter = grid_fields[ind][3]
            value = self.station_grid.GetCellValue(evt.GetRow(), evt.GetCol())
            setattr(self.selected_station, fieldName, converter(value))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()


    def onChannelCellLeftClick(self, evt):
        self.selected_channel = self.selected_station.channels[evt.GetRow()]
        self.updateAssignedStreams()
        self.updatePaneCaption()
        evt.Skip()


    def onChannelCellChange(self, evt):
        selectedParameter = self.channel_grid.GetColLabelValue(evt.GetCol())
        gridFields = self.getChannelFields()
        colLabels = [x[1] for x in gridFields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridFields[ind][0]
            value = self.channel_grid.GetCellValue(evt.GetRow(), evt.GetCol())
            setattr(self.selected_channel, fieldName, value)
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()


    def onAssignedStreamCellLeftClick(self, evt):
        self.selected_channel_assigned_recorder_stream = self.selected_channel.streams[evt.GetRow()]
        evt.Skip()


    def onAssignedStreamCellChange(self, evt):
        selectedParameter = self.assigned_recorder_stream_grid.GetColLabelValue(evt.GetCol())
        gridFields = self.getAssignedRecorderStreamFields();
        colLabels = [x[1] for x in gridFields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridFields[ind][0]
            converter = gridFields[ind][3]
            value = self.assigned_recorder_stream_grid.GetCellValue(evt.GetRow(), evt.GetCol())
            # TODO: if the start- or end-time is changed, use the according
            # set and get methods of the parameter instance to check for valid
            # changes (e.g. no overlapping). The old
            # onSensorParameterCellChange method below could have some hints.
            setattr(self.selected_channel_assigned_recorder_stream, fieldName, converter(value))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()



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


    def updatePaneCaption(self):
        ''' Update the caption of the docking panes.
        '''

        # Update the channel caption. 
        if self.selected_station:
            caption = 'channels of station %s' % self.selected_station.name
            pane = self.mgr.GetPane('channels')
            pane.Caption(caption)

        # Update the assigned recorder streams caption
        if self.selected_channel:
            caption = 'streams assigned to channel %s' % self.selected_channel.name
        else:
            caption = 'assigned streams: no channel selected'
        pane = self.mgr.GetPane('assigned recorder streams')
        pane.Caption(caption)

        self.mgr.Update()


    def updateData(self):
        ''' Update the data shown in the grids.
        '''
        self.updatePaneCaption()

        # Update the sensor grid fields.
        self.setGridValues(self.selected_station, self.station_grid, self.getStationFields(), 0)

        # Resize the grid rows.
        if self.channel_grid.GetNumberRows() > 0:
            self.channel_grid.DeleteRows(0, self.channel_grid.GetNumberRows())
        self.channel_grid.AppendRows(len(self.selected_station.channels))

        # Update the channel grid.
        for k, cur_channel in enumerate(self.selected_station.channels):
            self.setGridValues(cur_channel, self.channel_grid, self.getChannelFields(), k)

        # Update the assigned streams grid.
        self.updateAssignedStreams()


    def updateAssignedStreams(self):
        ''' Update the displayed assigned streams data.
        '''
        # Resize the grid rows.
        if self.assigned_recorder_stream_grid.GetNumberRows() > 0:
            self.assigned_recorder_stream_grid.DeleteRows(0, self.assigned_recorder_stream_grid.GetNumberRows())

        if self.selected_channel:
            self.assigned_recorder_stream_grid.AppendRows(len(self.selected_channel.streams))

            # Update the assigned streams grid.
            for k, cur_timebox in enumerate(self.selected_channel.streams):
                # Set the field values of the assined stream.
                self.setGridValues(cur_timebox.item,
                                   self.assigned_recorder_stream_grid,
                                   self.getAssignedRecorderStreamFields(),
                                   k)

                # Set the field values of the timebox start- and end-time.
                self.setGridValues(cur_timebox,
                                   self.assigned_recorder_stream_grid,
                                   self.getAssignedRecorderStreamFields(),
                                   k)



    def setGridValues(self, object, grid, fields, rowNumber):
        for pos, (field, label, attr, converter) in enumerate(fields):
            # The id field will raise an error when normal inventory
            # instances are used. Ignore this error and continue.
            try:
                # Take care of fields with custom strings. 
                custom_fields = {}
                custom_fields['start_time'] = 'start_time_string'
                custom_fields['end_time'] = 'end_time_string'
                if field in iter(custom_fields.keys()) and hasattr(object, custom_fields[field]):
                    field = custom_fields[field]

                if field is not None and getattr(object, field) is not None:
                    try:
                        grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
                    except:
                        try:
                            grid.SetCellValue(rowNumber, pos, str(getattr(object, field).encode("utf8")))
                        except:
                            grid.SetCellValue(rowNumber, pos, 'Error converting the value to string.')
                else:
                    grid.SetCellValue(rowNumber, pos, '')
            except:
                # If the field doesn't exist in the object (e.g. id for non
                # database inventory instances). An AttributeError is raised in
                # this case.
                # TODO: handle the AttributeError individually in case other
                # errors are raised.
                grid.SetCellValue(rowNumber, pos, '')

            grid.AutoSizeColumns()


    ## The station grid columns. 
    def getStationFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('network', 'network', 'readonly', str))
        tableField.append(('name', 'name', 'editable', str))
        tableField.append(('location', 'location', 'editable', str))
        tableField.append(('start_time', 'start', 'readonly', str))
        tableField.append(('end_time', 'end', 'readonly', str))
        tableField.append(('x', 'x', 'editable', float))
        tableField.append(('y', 'y', 'editable', float))
        tableField.append(('z', 'z', 'editable', float))
        tableField.append(('coord_system', 'coord. system', 'editable', str))
        tableField.append(('description', 'description', 'editable', str))
        return tableField


    ## The channel grid columns.
    def getChannelFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('name', 'name', 'editable', str))
        tableField.append(('description', 'description', 'editable', str))
        tableField.append(('start_time', 'start', 'readonly', str))
        tableField.append(('end_time', 'end', 'readonly', str))
        return tableField


    def getAssignedRecorderStreamFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('serial', 'serial', 'readonly', str))
        tableField.append(('model', 'model', 'readonly', str))
        tableField.append(('producer', 'producer', 'readonly', str))
        tableField.append(('name', 'name', 'readonly', str))
        tableField.append(('label', 'label', 'readonly', str))
        tableField.append(('start_time', 'start', 'editable', self.time_string_converter))
        tableField.append(('end_time', 'end', 'editable', self.time_string_converter))
        return tableField


    def time_string_converter(self, time_string):
        ''' Convert a start- or end-time string.
        '''
        if time_string in ['', 'running', 'big bang']:
            time_string = None
        else:
            time_string = UTCDateTime(time_string)

        return time_string


class SensorsPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY, size=(-1,-1)):
        #from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
        #from matplotlib.figure import Figure

        ## The currently displayed sensor.
        #self.displayedSensor = None

        #self.displayedComponent = None

        #self.displayedCompnentParameter = None

        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.mgr = wx.aui.AuiManager(self)

        roAttr = wx.grid.GridCellAttr()
        roAttr.SetReadOnly(True)

        # Create the sensor grid.
        fields = self.getSensorFields()
        self.sensorGrid = wx.grid.Grid(self, size=(-1, 40))
        self.sensorGrid.CreateGrid(1, len(fields))

        # Bind the sensorGrid events.
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                  self.onSensorCellChange,
                  self.sensorGrid)

        for k, (name, label, attr, converter)  in enumerate(fields):
            self.sensorGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.sensorGrid.SetColAttr(k, roAttr)

        self.sensorGrid.AutoSizeColumns()

        self.mgr.AddPane(self.sensorGrid, wx.aui.AuiPaneInfo().Name("sensor").
                         CentrePane().Layer(0).Position(0).MinSize(wx.Size(200, 100)))


        # Create the sensor component grid.
        fields = self.getComponentFields()
        self.componentGrid = wx.grid.Grid(self, size=(-1, 100))
        self.componentGrid.CreateGrid(1, len(fields))

        # Bind the componentGrid events.
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                  self.onComponentCellChange,
                  self.componentGrid)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                  self.onComponentCellLeftClick,
                  self.componentGrid)


        for k, (name, label, attr, convert)  in enumerate(fields):
            self.componentGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.componentGrid.SetColAttr(k, roAttr)

        self.componentGrid.AutoSizeColumns()

        #self.sizer.Add(self.tfGrid, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)
        caption = 'components of sensor %s' % self.displayedSensor
        self.mgr.AddPane(self.componentGrid, wx.aui.AuiPaneInfo().Name("components").Caption(caption).
                         Bottom().Row(0).Position(0).Layer(1).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        # Create the sensor component paramter grid.
        fields = self.getComponentParameterFields()
        self.parameterGrid = wx.grid.Grid(self, size=(-1, 100))
        self.parameterGrid.CreateGrid(1, len(fields))

        # Bind the paramGrid events.
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED,
                  self.onComponentParameterCellChange,
                  self.parameterGrid)

        for k, (name, label, attr, convert)  in enumerate(fields):
            self.parameterGrid.SetColLabelValue(k, label)
            if(attr == 'readonly'):
                self.parameterGrid.SetColAttr(k, roAttr)

        self.componentGrid.AutoSizeColumns()

        #self.sizer.Add(self.tfGrid, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=5)
        caption = 'parameters of component %s' % self.displayedComponent
        self.mgr.AddPane(self.parameterGrid, wx.aui.AuiPaneInfo().Name("parameters").Caption(caption).
                         Bottom().Row(0).Position(0).Layer(2).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 100)))


        # Create the plot area.
        self.tfFigure = Figure((8,4), dpi=75, facecolor='white')
        #rect = 0.1,0.1,0.8,0.8
        #self.tfAxis = self.tfFigure.add_axes(rect, xscale='log', axis_bgcolor='w')
        self.tfMagAxis = self.tfFigure.add_subplot(121, xscale='log', yscale='linear')
        self.tfMagAxis.set_facecolor('w')
        self.tfMagAxis.set_xlabel('Frequency [Hz]', fontsize=10)
        self.tfMagAxis.set_ylabel('Amplitude [dB, 20*log10(A)]', fontsize=10)
        self.tfMagAxis.set_title('Amplitude Response', fontsize=10)
        self.tfMagAxis.grid(True)

        self.tfPhaseAxis = self.tfFigure.add_subplot(122, xscale='log', yscale = 'linear')
        self.tfPhaseAxis.set_facecolor('w')
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
                         Bottom().Row(0).Position(0).Layer(3).CloseButton(False).CaptionVisible().
                         MinimizeButton().MaximizeButton().MinSize(wx.Size(200, 200)))

        # tell the manager to 'commit' all the changes just made
        self.mgr.Update()

        #self.sizer.AddGrowableRow(2)
        #self.sizer.AddGrowableCol(0)
        #self.SetSizerAndFit(self.sizer)


    @property
    def displayedSensor(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_sensor
        else:
            return None


    @property
    def displayedComponent(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_sensor_component
        else:
            return None

    @displayedComponent.setter
    def displayedComponent(self, value):
        self.GetTopLevelParent().selected_sensor_component = value

    @property
    def displayedComponentParameters(self):
        if self.GetTopLevelParent() is not None:
            return self.GetTopLevelParent().selected_sensor_component_parameters
        else:
            return None


    def onSensorCellChange(self, evt):
        selectedParameter = self.sensorGrid.GetColLabelValue(evt.GetCol())
        gridSensorFields = self.getSensorFields();
        colLabels = [x[1] for x in gridSensorFields]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridSensorFields[ind][0]
            setattr(self.displayedSensor, fieldName, self.sensorGrid.GetCellValue(evt.GetRow(), evt.GetCol()))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()
        else:
            pass


    def onComponentCellChange(self, evt):
        selectedComponent = self.componentGrid.GetColLabelValue(evt.GetCol())
        gridComponentFields = self.getComponentFields();
        colLabels = [x[1] for x in gridComponentFields]
        cur_component = self.displayedSensor.components[evt.GetRow()]

        if selectedComponent in colLabels:
            ind = colLabels.index(selectedComponent)
            fieldName = gridComponentFields[ind][0]
            converter = gridComponentFields[ind][3]
            setattr(cur_component, fieldName, converter(self.componentGrid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
            self.updatePaneCaption()
        else:
            pass


    def onComponentCellLeftClick(self, evt):
        cur_component = self.displayedSensor.components[evt.GetRow()]
        self.displayedComponent = cur_component
        self.updateParameters()
        self.updatePaneCaption()
        evt.Skip()



    def onComponentParameterCellChange(self, evt):
        selectedParameter = self.parameterGrid.GetColLabelValue(evt.GetCol())
        gridComponentParameterFields = self.getComponentParameterFields();
        colLabels = [x[1] for x in gridComponentParameterFields]
        cur_parameter = self.displayedComponent.parameters[evt.GetRow()]

        if selectedParameter in colLabels:
            ind = colLabels.index(selectedParameter)
            fieldName = gridComponentParameterFields[ind][0]
            converter = gridComponentParameterFields[ind][3]
            # TODO: if the start- or end-time is changed, use the according
            # set and get methods of the parameter instance to check for valid
            # changes (e.g. no overlapping). The old
            # onSensorParameterCellChange method below could have some hints.
            setattr(cur_parameter, fieldName, converter(self.parameterGrid.GetCellValue(evt.GetRow(), evt.GetCol())))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
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
            #converter = gridParamFields[ind][3]
            setattr(sensorParameter2Process, fieldName, self.paramGrid.GetCellValue(evt.GetRow(), evt.GetCol()))
            self.GetTopLevelParent().inventoryTree.updateInventoryData()
        else:
            pass


    def updatePaneCaption(self):
        ''' Update the captions of the docking panels.
        '''
        # Update the caption of the sensor components.
        if self.displayedSensor:
            caption = 'components of sensor %s' % self.displayedSensor.serial
            pane = self.mgr.GetPane('components')
            pane.Caption(caption)


        # Update the caption of the component parameters.
        if self.displayedComponent:
            caption = 'parameters of component %s' % self.displayedComponent.name
        else:
            caption = 'no component selected'
        pane = self.mgr.GetPane('parameters')
        pane.Caption(caption)

        # Update the caption of the parameter transfer function.
        if self.displayedComponentParameters:
            tmp = self.displayedComponentParameters.parent_component.name + ':(' + self.displayedComponentParameters.start_time_string + ' to ' + self.displayedComponentParameters.end_time_string + ')'
            caption = 'transfer function of parameter %s' % tmp
        else:
            caption = 'no component parameter selected'
        pane = self.mgr.GetPane('transfer function')
        pane.Caption(caption)

        self.mgr.Update()


    def updateData(self):
        self.logger.debug("updating the sensors data")

        self.updatePaneCaption()

        # Resize the grid rows.
        if self.componentGrid.GetNumberRows() > 0:
            self.componentGrid.DeleteRows(0, self.componentGrid.GetNumberRows())
        self.componentGrid.AppendRows(len(self.displayedSensor.components))

        # Update the sensor grid fields.
        self.setGridValues(self.displayedSensor, self.sensorGrid, self.getSensorFields(), 0)

        # Update the component grid fields.
        for k, cur_component in enumerate(self.displayedSensor.components):
            self.setGridValues(cur_component, self.componentGrid, self.getComponentFields(), k)

        # Update the paramter grid fields.
        self.updateParameters()


    def updateParameters(self):
        # Clear the grid.
        if self.parameterGrid.GetNumberRows() > 0:
            self.parameterGrid.DeleteRows(0, self.parameterGrid.GetNumberRows())

        if self.displayedComponent:
            # Resize the grid rows.
            self.parameterGrid.AppendRows(len(self.displayedComponent.parameters))

            parameter_fields = self.getComponentParameterFields()
            #field_labels = [x[1] for x in parameter_fields]

            # Update the component grid fields.
            for k, cur_parameter in enumerate(self.displayedComponent.parameters):
                self.setGridValues(cur_parameter, self.parameterGrid, parameter_fields, k)

            self.updateTransferFunction()

            self.parameterGrid.AutoSizeColumns()


    def updateTransferFunction(self):
        if self.displayedComponentParameters:
            if not self.displayedComponentParameters.tf_poles or not self.displayedComponentParameters.tf_zeros or not self.displayedComponentParameters.tf_normalization_factor:
                self.tfMagAxis.clear()
                self.tfPhaseAxis.clear()
                return


            #h,f = obspy.signal.invsim.paz_to_freq_resp(self.displayedComponentParameters.tf_poles, self.displayedComponentParameters.tf_zeros, self.displayedComponentParameters.tf_normalization_factor, 0.005, 8192, freq=True)
            #h,f = obspy.signal.invsim.paz_to_freq_resp(paz['poles'], paz['zeros'], paz['gain'], 0.005, 8192, freq=True)
            b, a = scipy.signal.zpk2tf(self.displayedComponentParameters.tf_zeros,
                                       self.displayedComponentParameters.tf_poles,
                                       self.displayedComponentParameters.tf_normalization_factor)
            w, h = scipy.signal.freqs(b, a)
            f = w / (2 * np.pi)
            phase = np.unwrap(np.arctan2(-h.imag, h.real)) #take negative of imaginary part

            lines = self.tfMagAxis.get_lines()
            if lines:
                for curLine in lines:
                    curLine.remove()

            # Remove the zero frequency.
            mask = f != 0
            f = f[mask]
            h = h[mask]
            phase = phase[mask]
            #frequRange = [0.1,1,10,100,1000]
            self.tfMagAxis.plot(f, 20 * np.log10(np.abs(h)), color='k')
            #self.tfMagAxis.set_xticks(np.log10(frequRange))
            #self.tfMagAxis.set_xticklabels(frequRange)

            lines = self.tfPhaseAxis.get_lines()
            if lines:
                for curLine in lines:
                    curLine.remove()
            self.tfPhaseAxis.plot(f, phase, color='k')
            #self.tfPhaseAxis.set_xticks(np.log10(frequRange))
            #self.tfPhaseAxis.set_xticklabels(frequRange)
            self.tfCanvas.draw()


    def setGridValues(self, object, grid, fields, rowNumber):
        for pos, (field, label, attr, converter) in enumerate(fields):
            # The id field will raise an error when normal inventory
            # instances are used. Ignore this error and continue.
            try:
                # Take care of fields with custom strings. 
                custom_fields = {}
                custom_fields['start_time'] = 'start_time_string'
                custom_fields['end_time'] = 'end_time_string'
                custom_fields['tf_poles'] = 'poles_string'
                custom_fields['tf_zeros'] = 'zeros_string'
                if field in iter(custom_fields.keys()) and hasattr(object, custom_fields[field]):
                    field = custom_fields[field]

                if field is not None and getattr(object, field) is not None:
                    grid.SetCellValue(rowNumber, pos, str(getattr(object, field)))
                else:
                    grid.SetCellValue(rowNumber, pos, '')
            except:
                pass
            grid.AutoSizeColumns()



    def getSensorFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('serial', 'serial', 'editable', str))
        tableField.append(('model', 'model', 'editable', str))
        tableField.append(('producer', 'producer', 'editable', str))
        tableField.append(('description', 'description', 'editable', str))
        return tableField

    def getComponentFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('name', 'name', 'editable', str))
        tableField.append(('description', 'description', 'editable', str))
        tableField.append(('input_unit', 'input unit', 'editable', str))
        tableField.append(('output_unit', 'output unit', 'editable', str))
        tableField.append(('deliver_unit', 'deliver unit', 'editable', str))
        return tableField


    def getComponentParameterFields(self):
        tableField = []
        tableField.append(('id', 'id', 'readonly', int))
        tableField.append(('start_time', 'start', 'editable', self.time_string_converter))
        tableField.append(('end_time', 'end', 'editable', self.time_string_converter))
        tableField.append(('sensitivity', 'sensitivity', 'editable', float))
        tableField.append(('tf_normalization_factor', 'normalization factor', 'editable', float))
        tableField.append(('tf_normalization_frequency', 'normalization frequ.', 'editable', float))
        tableField.append(('tf_poles', 'poles', 'editable', self.tf_pz_converter))      # Poles is a list. Handle them seperately
        tableField.append(('tf_zeros', 'zeros', 'editable', self.tf_pz_converter))      # Zeros is a list. Handle them seperately.
        return tableField


    def time_string_converter(self, time_string):
        ''' Convert a start- or end-time string.
        '''
        if time_string in ['', 'running', 'big bang']:
            time_string = None
        else:
            time_string = UTCDateTime(time_string)

        return time_string


    def tf_pz_converter(self, pz_string):
        ''' Convert a poles or zeros string to a list.
        '''
        pz_list = pz_string.split(',')
        pz_list = [complex(x) for x in pz_list]
        return pz_list



class ContextMenu(wx.Menu):

        def __init__(self, cmData):
            wx.Menu.__init__(self)

            for cmLabel, cmHandler in cmData:
                item = self.Append(-1, cmLabel)
                self.Bind(wx.EVT_MENU, cmHandler, item)

