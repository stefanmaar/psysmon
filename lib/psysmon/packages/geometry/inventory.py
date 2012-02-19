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
The inventory module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classed needed to build a pSysmon geometry 
inventory.
'''

from obspy.core.utcdatetime import UTCDateTime
from psysmon.core.util import PsysmonError
from mpl_toolkits.basemap import pyproj
import warnings
import logging
from wx.lib.pubsub import Publisher as pub

## The Inventory class.
#
class Inventory:

    ## The constructor.
    #
    # @param self The object pointer.
    # @param name The inventory name.
    def __init__(self, name):

        ## The name of the inventory.
        self.name = name

        ## The type of the inventory.
        #
        # Based on the source the inventory can be of the following types:
        # - xml
        # - database
        # - manual
        self.type = None

        ## The recorders contained in the inventory.
        self.recorders = []

        ## The sensors contained in the inventory and not assigned to a recorder.
        self.sensors = []

        ## The stations contained in the inventory and not assigned to a network.
        self.stations = []

        ## The networks contained in the inventory.
        self.networks = {}



    ## Add a recorder to the inventory.
    def addRecorder(self, recorder):
        self.recorders.append(recorder)
        recorder.setParentInventory(self)


    ## Remove a recorder from the inventory.
    def removeRecorder(self, position):
        pass

    ## Add a station to the inventory.
    def addStation(self, station):

        # If the network is found in the inventory, add it to the network.
        curNet = self.getNetwork(station.network)
        if curNet:
            curNet.addStation(station)
        else:
            # Append the station to the unassigned stations list.
            self.stations.append(station)

        station.setParentInventory(self)


    ## Add a sensor to the inventory.
    def addSensor(self, sensor):

        for curRecorder in self.recorders:
            if curRecorder.serial == sensor.recorderSerial and curRecorder.type == sensor.recorderType:
                curRecorder.addSensor(sensor)
                if sensor in self.sensors:
                    self.sensors.remove(sensor)
                return

        # If no suitable recorder has been found, add it to the unassigned sensors list.
        self.sensors.append(sensor)
        self.sensors = list(set(self.sensors))
        sensor.recorderId = None
        sensor.setParentInventory(self)


    ## Add a Network to the inventory.
    def addNetwork(self, network):
        self.networks[network.name] = network
        network.setParentInventory(self)


    ## Remove a station from the inventory.
    def removeStation(self, position):
        pass

    ## Check the inventory for changed objects.
    def hasChanged(self):
        for curRecorder in self.recorders:
            if curRecorder.history.hasActions():
                return True

            for curSensor in curRecorder.sensors:
                if curSensor.history.hasActions():
                    return True

            for curStation in self.stations:
                if curStation.history.hasActions():
                    return True



    ## Refresh the inventory networks.
    def refreshNetworks(self):            
        for curNetwork in self.networks.itervalues():
            curNetwork.refreshStations(self.stations)

    ## Refresh the inventory recorders.
    def refreshRecorders(self):            
        for curRecorder in self.recorders:
            curRecorder.refreshSensors()

        for curSensor in self.sensors:
            self.addSensor(curSensor)


    ## Read the inventory from an XML file.
    def importFromXml(self, filename):
        inventoryParser = InventoryXmlParser(self, filename)
        try:
            inventoryParser.parse()
        except PsysmonError as e:
            raise e

        self.type = 'xml'   


    ## Get a sensor from the inventory.
    def getSensor(self, recSerial, senSerial, recChannelName):
        recorder2Process = filter((lambda curRec: curRec.serial==recSerial), self.recorders)

        if recorder2Process:
            recorder2Process = recorder2Process[0]
            return filter((lambda x: (x.serial==senSerial) and (x.recChannelName == recChannelName)), recorder2Process.sensors)
        else:
            return None

    ## Get a sensor from the inventory by id.
    def getSensorById(self, id):

        for curRecorder in self.recorders:
            sensorFound = filter((lambda curSensor: curSensor.id==id), curRecorder.sensors)

            if sensorFound:
                return sensorFound[0]

        return None

    ## Get a sensor from the inventory by label.
    def getSensorByLabel(self, label):
        for curRecorder in self.recorders:
            sensorFound = filter((lambda curSensor: curSensor.label==label), curRecorder.sensors)

            if sensorFound:
                return sensorFound[0]

        return None


    ## Get a network form the inventory.
    def getNetwork(self, code):
        if self.networks.has_key(code):
            return self.networks[code]
        else:
            return None


## Load the inventory from a pSysmon database.
class InventoryDatabaseController:

    def __init__(self, project):   

        ## The pSysmon project.
        self.project = project

        # The database session.
        self.dbSession = self.project.getDbSession()

        self.mapper = {}

        # Subscribe to the events signalling inventory attribute changes of 
        # of the loaded database inventory.
        pub.subscribe(self.updateNetworkMapper,
                      'inventory.update.network')
        pub.subscribe(self.updateStationMapper,
                      'inventory.update.station')
        pub.subscribe(self.updateRecorderMapper,
                      'inventory.update.recorder')
        pub.subscribe(self.updateSensorMapper,
                      'inventory.update.sensor')
        pub.subscribe(self.updateSensorParamMapper,
                      'inventory.update.sensorParameter')
        pub.subscribe(self.updateSensorTimeMapper,
                      'inventory.update.sensorDeploymentTime')
        pub.subscribe(self.updateSensorAssignmentMapper,
                      'inventory.update.sensorAssignment')
        pub.subscribe(self.updateSensor2StationMapper,
                      'inventory.update.addSensor2Station')



    def load(self):
        ''' Load the inventory from the pSysmon database.

        Returns
        -------
        inventory : :class:`Inventory`
            The psysmon inventory loaded from the database. 
        '''
        inventory = Inventory('project inventory')
        inventory.type = 'db'

        self.loadRecorders(inventory)
        self.loadNetworks(inventory)

        return inventory


    def write(self, inventory):
        ''' Write the in inventory to the database.

        Parameters
        ----------
        inventory : :class:`Inventory`
            The inventory to be written to the database.
        '''
        for curRecorder in inventory.recorders:
            self.insertRecorder(curRecorder) 

        for curNetwork in inventory.networks.values():
            self.insertNetwork(curNetwork)


    def loadRecorders(self, inventory):
        ''' Load the recorder data from the geom_recorder table.

        Parameters
        ----------
        inventory : :class:`Inventory`
            The inventory to which the loaded recorders should be added.
        '''
        dbRecorder = self.project.dbTables['geom_recorder']

        for curDbRecorder in self.dbSession.query(dbRecorder).order_by(dbRecorder.serial):
            curRecorder = Recorder(id = curDbRecorder.id,
                                   serial = curDbRecorder.serial,
                                   type = curDbRecorder.type)

            self.mapper[curRecorder] = curDbRecorder

            for curDbSensor in curDbRecorder.sensors:
                curSensor = self.convertDbSensor(curDbSensor)
                curRecorder.addSensor(curSensor)
                self.mapper[curSensor] = curDbSensor

                for curDbParam in curDbSensor.parameters:
                    curParam = self.convertDbSensorParam(curDbParam)

                    if curDbParam.start_time:
                        startTime = UTCDateTime(curDbParam.start_time)
                    else:
                        startTime = None

                    if curDbParam.end_time:
                        endTime = UTCDateTime(curDbParam.end_time)
                    else:
                        endTime = None

                    curSensor.addParameter(curParam, 
                                           startTime, 
                                           endTime)
                    self.mapper[curParam] = curDbParam

            inventory.addRecorder(curRecorder)


    def loadNetworks(self, inventory):
        ''' Load the inventory networks from the pSysmon database.

        Parameters
        ----------
        inventory : :class:`Inventory`
        '''
        dbNetwork = self.project.dbTables['geom_network']

        for curDbNetwork in self.dbSession.query(dbNetwork).order_by(dbNetwork.name):
            curNetwork = Network(curDbNetwork.name,
                                 curDbNetwork.description,
                                 curDbNetwork.type)
            self.mapper[curNetwork] = curDbNetwork

            for curDbStation in curDbNetwork.stations:
                curStation = Station(curDbStation.name,
                                     curDbStation.location,
                                     curDbStation.X,
                                     curDbStation.Y,
                                     curDbStation.Z,
                                     coordSystem=curDbStation.coord_system,
                                     description=curDbStation.description,
                                     network=curNetwork.name,
                                     id=curDbStation.id)
                self.mapper[curStation] = curDbStation
                curNetwork.addStation(curStation)

                for curDbSensorTime in curDbStation.sensors:
                    curDbSensor = curDbSensorTime.child

                    if curDbSensorTime.start_time:
                        startTime = UTCDateTime(curDbSensorTime.start_time)
                    else:
                        startTime = None

                    if curDbSensorTime.end_time:
                        endTime = UTCDateTime(curDbSensorTime.end_time)
                    else:
                        endTime = None

                    # Get the correct Sensor instance from the inventory.
                    curSensor = inventory.getSensorById(curDbSensor.id)
                    curStation.sensors.append((curSensor, startTime, endTime))

            inventory.addNetwork(curNetwork)



    def insertRecorder(self, recorder):
        ''' Write a recorder to the database.

        '''
        dbRecorder = self.project.dbTables['geom_recorder']
        dbSensor = self.project.dbTables['geom_sensor']
        dbParameter = self.project.dbTables['geom_sensor_param']
        dbTfPz = self.project.dbTables['geom_tf_pz']

        rec2Add = dbRecorder(recorder.serial, recorder.type)

        # Add all sensors assigned to the recorder. 
        for curSensor in recorder.sensors:
            sensor2Add = dbSensor(recorder.id, 
                                  curSensor.label,
                                  curSensor.serial,
                                  curSensor.type,
                                  curSensor.recChannelName,
                                  curSensor.channelName)
            rec2Add.sensors.append(sensor2Add)
            self.mapper[curSensor] = sensor2Add

            # Add the sensor parameters.
            for curParam, startTime, endTime in curSensor.parameters:
                if startTime:
                    startTime = startTime.getTimeStamp()

                if endTime:
                    endTime = endTime.getTimeStamp()

                param2Add = dbParameter(curSensor.id,
                                        startTime,
                                        endTime,
                                        curParam.tfNormalizationFactor, 
                                        curParam.tfNormalizationFrequency,
                                        curParam.tfType,
                                        curParam.tfUnits,
                                        curParam.gain,
                                        curParam.sensitivity,
                                        curParam.bitweight,
                                        curParam.bitweightUnits)
                sensor2Add.parameters.append(param2Add)
                self.mapper[curParam] = param2Add

                # Add the the transfer function poles. 
                for curPole in curParam.tfPoles:
                    complex2Add = dbTfPz(curParam.id,
                                         1,
                                         curPole.real,
                                         curPole.imag)
                    curParam.tfPz.append(complex2Add)

                # Add the the transfer function zeros. 
                for curPole in curParam.tfZeros:
                    complex2Add = dbTfPz(curParam.id,
                                         0,
                                         curPole.real,
                                         curPole.imag)
                    curParam.tfPz.append(complex2Add)

        self.dbSession.add(rec2Add)
        self.dbSession.commit()


    def convertDbRecorder(self, dbRecorder):
        ''' Convert the recorder database table mapper instance to a 
        :class:`Recorder` instance.

        Parameters:
        -----------
        dbRecorder : Object
            The sqlAlchemy geom_recorder table mapper instance.

        ''' 

    def convertDbSensor(self, dbSensor):
        ''' Convert the sensor database table mapper instance to a sensor 
        instance.

        Parameters
        ----------
        dbSensor : Object
            The sqlAlchemy geom_sensor table mapper instance.

        recorder : :class:`Recorder`
            The recorder to which the sensor will be assigned to.

        '''
        curSensor = Sensor(dbSensor.serial,
                           dbSensor.type,
                           dbSensor.rec_channel_name,
                           dbSensor.channel_name,
                           dbSensor.label,
                           id = dbSensor.id,
                           recorderId = dbSensor.parent.id,
                           recorderSerial = dbSensor.parent.serial,
                           recorderType = dbSensor.parent.type)
        return curSensor


    def convertDbSensorParam(self, dbParam):
        curParam = SensorParameter(dbParam.parent.id,
                                   dbParam.gain,
                                   dbParam.bitweight,
                                   dbParam.bitweight_units,
                                   dbParam.sensitivity,
                                   dbParam.sensitivity_units,
                                   tfType = dbParam.type,
                                   tfUnits = dbParam.tf_units,
                                   tfNormalizationFactor = dbParam.normalization_factor,
                                   tfNormalizationFrequency = dbParam.normalization_frequency,
                                   id = dbParam.id,
                                   startTime = dbParam.start_time,
                                   endTime = dbParam.end_time)
        return curParam

    def insertNetwork(self, network):
        ''' Insert a network in to the psysmon database.

        Parameters
        ----------
        network : :class:`Network`
            The network to insert into the database.
        '''
        dbNetwork = self.project.dbTables['geom_network']
        dbStation = self.project.dbTables['geom_station']
        dbSensorTime = self.project.dbTables['geom_sensor_time']

        network2Add = dbNetwork(network.name, 
                                network.description,
                                network.type)

        for curStation in network.stations.values():
            station2Add = dbStation(network.name,
                                    curStation.name,
                                    curStation.location,
                                    curStation.x,
                                    curStation.y,
                                    curStation.z,
                                    curStation.coordSystem,
                                    curStation.description)
            network2Add.stations.append(station2Add)

            for curSensor, startTime, endTime in curStation.sensors:
                if startTime:
                    startTime = startTime.getTimeStamp()

                if endTime:
                    endTime = endTime.getTimeStamp()

                sensorTime2Add = dbSensorTime(curStation.id,
                                              curSensor.id,
                                              startTime, 
                                              endTime)

                sensorTime2Add.child = self.mapper[curSensor]
                station2Add.sensors.append(sensorTime2Add)


        self.dbSession.add(network2Add)
        self.dbSession.commit()


    def updateStationMapper(self, msg):
        print "***********************"
        print "Updating station mapper."


        attrMap = {}
        attrMap['id'] = 'id'
        attrMap['network'] = 'net_name'
        attrMap['name'] = 'name'
        attrMap['location'] = 'location'
        attrMap['x'] = 'X'
        attrMap['y'] = 'Y'
        attrMap['z'] = 'Z'
        attrMap['coordSystem'] = 'coord_system'
        attrMap['description'] = 'description'

        masterStation = msg.data[0]

        if masterStation.parentInventory.type != 'db':
            print "Not a db type inventory."
            return

        name = msg.data[1]
        stat2Update = self.mapper[masterStation]

        setattr(stat2Update, 
                attrMap[name], 
                getattr(masterStation, name))


    def updateRecorderMapper(self, msg):
        print "***********************"
        print "Updating recorder mapper."

        attrMap = {}
        attrMap['id'] = 'id'
        attrMap['serial'] = 'serial'
        attrMap['type'] = 'type'

        masterRecorder = msg.data[0]
        name = msg.data[1]
        rec2Update = self.mapper[masterRecorder]
        setattr(rec2Update, 
                attrMap[name],
                getattr(masterRecorder, name))


    def updateSensorMapper(self, msg):
        print "***********************"
        print "Updating sensor mapper."

        attrMap = {};
        attrMap['id'] = 'id'
        attrMap['label'] = 'label'
        attrMap['recorderId'] = 'recorder_id'
        #attrMap['recorderSerial'] = None
        #attrMap['recorderType'] = None
        attrMap['serial'] = 'serial'
        attrMap['type'] = 'type'
        attrMap['recChannelName'] = 'rec_channel_name'
        attrMap['channelName'] = 'channel_name'

        masterSensor = msg.data[0]
        name = msg.data[1]

        if name not in attrMap.keys():
            return

        sensor2Update = self.mapper[masterSensor]
        setattr(sensor2Update,
                attrMap[name],
                getattr(masterSensor, name))


    def updateSensorParamMapper(self, msg):

        ## The mapping of the station attributes to the database columns.
        attrMap = {};
        attrMap['id'] = 'id'
        attrMap['sensorId'] = 'sensor_id'
        attrMap['tfNormalizationFactor'] = 'normalization_factor'
        attrMap['tfNormalizationFrequency'] = 'normalization_frequency'
        attrMap['tfType'] = 'type'
        attrMap['tfUnits'] = 'tf_units'
        attrMap['gain'] = 'gain'
        attrMap['sensitivity'] = 'sensitivity'
        attrMap['sensitivityUnits'] = 'sensitivity_units'
        attrMap['bitweight'] = 'bitweight'
        attrMap['bitweightUnits'] = 'bitweight_units' 
        attrMap['startTime'] = 'start_time'
        attrMap['endTime'] = 'end_time' 

        masterParam = msg.data[0]
        name = msg.data[1]
        param2Update = self.mapper[masterParam]

        if name in ['startTime', 'endTime']:
            value = getattr(masterParam, name)
            if value:
                value = value.getTimeStamp()
        else:
            value = getattr(masterParam, name)

        setattr(param2Update,
                attrMap[name],
                value)


    def updateNetworkMapper(self, msg):
        ## The mapping of the network attributes to the database columns.
        attrMap = {};
        attrMap['name'] = 'name'
        attrMap['description'] = 'description'
        attrMap['type'] = 'type'

        masterNetwork = msg.data[0]
        name = msg.data[1]
        network2Update = self.mapper[masterNetwork]
        setattr(network2Update,
                attrMap[name],
                getattr(masterNetwork, name))


    def updateSensorTimeMapper(self, msg):

        masterStation = msg.data[0]
        masterSensor = msg.data[2][0]
        station2Update = self.mapper[masterStation]
        sensor2Update = self.mapper[masterSensor]
        print "*****************"
        print station2Update
        for curSensorTime in station2Update.sensors:
            if curSensorTime.child == sensor2Update:
                print curSensorTime

                startTime = msg.data[2][1]
                endTime = msg.data[2][2]

                if startTime:
                    startTime = startTime.getTimeStamp()

                if endTime:
                    endTime = endTime.getTimeStamp()

                curSensorTime.start_time = startTime
                curSensorTime.end_time = endTime
        print "*****************"


    def updateSensorAssignmentMapper(self, msg):

        sensorChanged = msg.data[0]
        assignmentType = msg.data[1]
        oldRecorder = msg.data[2][0]
        newRecorder = msg.data[2][1]

        oldDbRec = self.mapper[oldRecorder]
        newDbRec = self.mapper[newRecorder]
        dbSensor = self.mapper[sensorChanged]

        print "+++++++++++++++++++"
        print "oldDbRec:"
        print oldDbRec
        print "newDbRec:"
        print newDbRec
        print "dbSensor:"
        print dbSensor
        print "+++++++++++++++++++"

        print oldDbRec.sensors
        tmp = oldDbRec.sensors.pop(oldDbRec.sensors.index(dbSensor))
        print oldDbRec.sensors

        print "Popped sensor:"
        print tmp
        print "sensor parent:"
        print tmp.parent
        print "\n"

        print "****************"
        print "newDbRec"
        print newDbRec

        tmp.parent = newDbRec
        newDbRec.sensors.append(tmp)


    def updateSensor2StationMapper(self, msg):

        station = msg.data[0]
        sensor = msg.data[2][0]
        startTime = msg.data[2][1]
        endTime = msg.data[2][2]

        dbStation = self.mapper[station]
        dbSensor = self.mapper[sensor]

        geomSensorTime = self.project.dbTables['geom_sensor_time']

        # Convert the time limits to unixseconds.
        if startTime:
            startTime = startTime.getTimeStamp()

        if endTime:
            endTime = endTime.getTimeStamp()

        sensorTime = geomSensorTime(station.id, sensor.id, startTime, endTime)
        sensorTime.child = dbSensor
        dbStation.sensors.append(sensorTime)





    ## Update the inventory database tables.
    def updateDb(self, inventory):

        if inventory.type != 'db':
            return

        self.dbSession.commit()
        self.dbSession.flush()


class InventoryXmlParser:
    '''
    Parse a pSysmon inventory XML file.
    '''
    def __init__(self, parentInventory, filename):
        self.parentInventory = parentInventory
        self.filename = filename

        # The required attributes which have to be present in the tags.
        self.requiredAttributes = {}
        self.requiredAttributes['inventory'] = ('name',)
        self.requiredAttributes['recorder'] = ('serial',)
        self.requiredAttributes['sensorUnit'] = ('label',)
        self.requiredAttributes['station'] = ('code',)
        self.requiredAttributes['network'] = ('code',)

        # The required tags which have to be present in the inventory.
        self.requiredTags = {}
        self.requiredTags['recorder'] = ('type',)
        self.requiredTags['sensorUnit'] = ('rec_channel_name', 'channel_name', 
                                        'sensor_serial', 'sensor_type')
        self.requiredTags['channel_parameters'] = ('start_time', 'end_time', 
                                        'gain', 'bitweight', 'bitweight_units', 
                                        'sensitivity', 'sensitivity_units')
        self.requiredTags['response_paz'] = ('type', 'units', 'A0_normalization_factor', 
                                             'normalization_frequency')
        self.requiredTags['complex_zero'] = ('real_zero', 'imaginary_zero')
        self.requiredTags['complex_pole'] = ('real_pole', 'imaginary_pole')
        self.requiredTags['station'] = ('location', 'xcoord', 'ycoord', 'elevation', 
                                        'coordSystem', 'description', 'network_code')
        self.requiredTags['assignedSensorUnit'] = ('sensorUnitLabel', 'start_time', 'end_time')
        self.requiredTags['network'] = ('description', 'type')



    def parse(self):
        from xml.etree.ElementTree import parse

        print "parsing file...\n"

        # Parse the xml file passed as argument.
        tree = parse(self.filename)
        inventory = tree.getroot()

        # Check if the root element is of type inventory.
        if inventory.tag != 'inventory':
            return
        else:
            print("found inventory root tag\n")

        # Set the name of the inventory.
        self.parentInventory.name = inventory.attrib['name']

        # Get the recorders and stations of the inventory.
        recorders = tree.findall('recorder')
        stations = tree.findall('station')
        networks = tree.findall('network')

        # First process the recorders.
        # For each recorder create a Recorder object, add the channels to it and 
        # finally add it to the inventory.
        self.processRecorders(recorders)

        self.processNetworks(networks)  

        self.processStations(stations)

        print "Success reading the XML file."



    ## Process the recorder element.
    def processRecorders(self, recorders):
        for curRecorder in recorders:
            recorderContent = self.parseNode(curRecorder)

            # Test the recorder tags for completeness.
            missingAttrib = self.keysComplete(curRecorder.attrib, self.requiredAttributes['recorder'])
            missingKeys = self.keysComplete(recorderContent, self.requiredTags['recorder']);
            if not missingKeys and not missingAttrib:
                print "recorder xml content:"
                print recorderContent
            else:
                print "Not all required fields present!\nMissing Keys:\n"
                print missingKeys
                print missingAttrib
                continue

            # Create the Recorder instance.
            rec2Add = Recorder(serial=curRecorder.attrib['serial'], 
                               type = recorderContent['type']) 

            # Process the channels of the recorder.
            self.processChannels(curRecorder, rec2Add)

            # Add the recorder to the inventory.
            self.parentInventory.addRecorder(rec2Add)


    ## Process the channel elements.      
    def processChannels(self, recorderNode, recorder):
        channels = recorderNode.findall('sensorUnit')
        for curChannel in channels:
            channelContent = self.parseNode(curChannel)

            missingAttrib = self.keysComplete(curChannel.attrib, self.requiredAttributes['sensorUnit'])
            missingKeys = self.keysComplete(channelContent, self.requiredTags['sensorUnit']);
            if not missingKeys and not missingAttrib:
                print "Adding sensor to recorder."
                sensor2Add = Sensor(serial=channelContent['sensor_serial'],
                                    type=channelContent['sensor_type'],
                                    recChannelName=channelContent['rec_channel_name'],
                                    channelName=channelContent['channel_name'],
                                    label=curChannel.attrib['label']) 
                print sensor2Add.label
                # Process the channel parameters.
                self.processChannelParameters(curChannel, sensor2Add)

                recorder.addSensor(sensor2Add)

            else:
                print "Not all required fields present!\nMissing Keys:\n"
                print missingKeys 
                print missingAttrib

    ## Process the channel_parameter elements.
    def processChannelParameters(self, channelNode, sensor):
        channelParameters = channelNode.findall('channel_parameters')
        for curParameter in channelParameters:
            content = self.parseNode(curParameter)
            missingKeys = self.keysComplete(content, self.requiredTags['channel_parameters'])
            if not missingKeys:
                print "Adding the channel parameters to the sensor"
                parameter2Add = SensorParameter(sensorId = sensor.id,
                                                 gain = float(content['gain']),
                                                 bitweight = float(content['bitweight']),
                                                 bitweightUnits = content['bitweight_units'],
                                                 sensitivity = float(content['sensitivity']),
                                                 sensitivityUnits = content['sensitivity_units']
                                                 )
                self.processResponsePaz(curParameter, parameter2Add)

                # Convert the time strings to UTC times.
                if content['start_time']:
                    beginTime = UTCDateTime(content['start_time'])
                else:
                    beginTime = None


                if content['end_time']:
                    endTime = UTCDateTime(content['end_time'])
                else:
                    endTime = None

                sensor.addParameter(parameter2Add, 
                                    beginTime, 
                                    endTime)



    ## Process the response_paz elements.
    def processResponsePaz(self, parameterNode, parameter):
        tf = parameterNode.findall('response_paz')
        for curTf in tf:
            content = self.parseNode(curTf)
            missingKeys = self.keysComplete(content, self.requiredTags['response_paz'])
            if not missingKeys:
                print "Adding the tf to the parameter"                
                parameter.setTransferFunction(content['type'], 
                                              content['units'],
                                              float(content['A0_normalization_factor']), 
                                              float(content['normalization_frequency']))

                self.processComplexZero(curTf, parameter)
                self.processComplexPole(curTf, parameter)

    ## Process the complex_zero elements.
    def processComplexZero(self, tfNode, parameter):
        cz = tfNode.findall('complex_zero')
        for curCz in cz:
            zero = curCz.text.replace(' ', '')
            parameter.tfAddComplexZero(complex(zero))


    ## Process the complex_pole elements.
    def processComplexPole(self, tfNode, parameter):
        cp = tfNode.findall('complex_pole')
        for curCp in cp:
            pole = curCp.text.replace(' ', '')
            parameter.tfAddComplexPole(complex(pole))



    ## Process the station elements.
    def processStations(self, stations):
        for curStation in stations:
            stationContent = self.parseNode(curStation)
            missingAttrib = self.keysComplete(curStation.attrib, self.requiredAttributes['station'])
            missingKeys = self.keysComplete(stationContent, self.requiredTags['station'])

            if not missingKeys and not missingAttrib:
                station2Add = Station(name=curStation.attrib['code'],
                                      location=stationContent['location'],
                                      x=stationContent['xcoord'],
                                      y=stationContent['ycoord'],
                                      z=stationContent['elevation'],
                                      coordSystem=stationContent['coordSystem'],
                                      description=stationContent['description'],
                                      network=stationContent['network_code'] 
                                      )

                self.processSensors(curStation, station2Add)                      

                self.parentInventory.addStation(station2Add)

            else:
                print "Not all required tags or attributes present."
                print missingKeys
                print missingAttrib


    def processSensors(self, stationNode, station):
        sensors = stationNode.findall('assignedSensorUnit')
        for curSensor in sensors:
            sensorContent = self.parseNode(curSensor)

            missingKeys = self.keysComplete(sensorContent, self.requiredTags['assignedSensorUnit'])

            if not missingKeys: 
                # Find the sensor in the inventory.
                #sensor2Add = self.parentInventory.getSensor(recSerial = sensorContent['recorder_serial'],
                #                                            senSerial = sensorContent['sensor_serial'],
                #                                            recChannelName = sensorContent['rec_channel_name'])
                print sensorContent['sensorUnitLabel']
                sensor2Add = self.parentInventory.getSensorByLabel(label=sensorContent['sensorUnitLabel'])
                print sensor2Add
                if sensor2Add:
                    # Convert the time strings to UTC times.
                    if sensorContent['start_time']:
                        beginTime = UTCDateTime(sensorContent['start_time'])
                    else:
                        beginTime = None


                    if sensorContent['end_time']:
                        endTime = UTCDateTime(sensorContent['end_time'])
                    else:
                        endTime = None

                    station.addSensor(sensor2Add, 
                                      beginTime,
                                      endTime)
                else:
                    msg =  "Sensor to add (%s-%s-%s) not found in inventory.\nSkipping this sensor." % (sensorContent['recorder_serial'], 
                                                                                                        sensorContent['sensor_serial'], 
                                                                                                        sensorContent['rec_channel_name']) 
                    warnings.warn(msg)
            else:
                msg = "Not all required fields presents!\nMissing keys:\n"
                print msg
                print missingKeys


     ## Process the network element.
    def processNetworks(self, networks):
        for curNetwork in networks:
            content = self.parseNode(curNetwork)

            # Test the recorder tags for completeness.
            missingAttrib = self.keysComplete(curNetwork.attrib, self.requiredAttributes['network'])
            missingKeys = self.keysComplete(content, self.requiredTags['network']);
            if not missingKeys and not missingAttrib:
                print content
            else:
                print "Not all required fields present!\nMissing Keys:\n"
                print missingKeys
                print missingAttrib
                continue

            # Create the Recorder instance.
            net2Add = Network(name=content['code'],
                              description=content['description'],
                              type=content['type']) 

            # Add the network to the inventory.
            self.parentInventory.addNetwork(net2Add)


    def getNodeText(self, xmlElement, tag):
        node = xmlElement.find(tag)
        if node is not None:
            return node.text
        else:
            return None

    def parseNode(self, xmlElement):
        nodeContent = {}
        for curNode in list(xmlElement):
            nodeContent[curNode.tag] = curNode.text

        return nodeContent

    def keysComplete(self, nodeContent, requiredKeys):
        missingKeys = []
        for curKey in requiredKeys:
            if nodeContent.has_key(curKey):
                continue
            else:
                missingKeys.append(curKey)

        return missingKeys





## The pSysmon recorder class.
# 
# A recorder is more or less the representation of a digitizer.@n
#     
class Recorder:

    ## The constructor.
    #
    # @param self The object pointer.
    # @param serial The recorder serial number.
    # @param type The recorder type.
    # @param id The recorder database id.
    def __init__(self, serial, type, id=None, parentInventory=None):
        ## The recorder database id.
        # -1 if the recorder is not yet present in the database.
        self.id = id

        ## The recorder serial number.
        self.serial = serial

        ## The recorder type.
        self.type = type

        # The mapping of the station attributes to the database columns.
        attrMap = {};

        # The allowed actions to be saved in the history.
        actionTypes = {};
        actionTypes['changeAttribute'] = 'Changed a station attribute.'


        ## The station action history.
        self.history = InventoryHistory(attrMap, actionTypes)

        ## A list of Sensor instances related to the recorder.
        self.sensors = [];

        ## The parent inventory.
        self.parentInventory = parentInventory

    def __setitem__(self, name, value):
        self.__dict__[name] = value
        self.hasChanged = True 
        self.changedFields.append(name)
        print "Setitem in recorder."



    def setParentInventory(self, parentInventory):
        ''' Set the parentInventory attribute.

        Also update the parent inventory of all children.

        Parameters
        ----------
        parentInventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parentInventory = parentInventory
        for curSensor in self.sensors:
            curSensor.setParentInventory(parentInventory)

    ## Add a sensor to the recorder.
    def addSensor(self, sensor):
        sensor.recorderId = self.id
        sensor.recorderSerial = self.serial
        sensor.recorderType = self.type
        sensor.parentRecorder = self
        self.sensors.append(sensor)
        self.sensors = list(set(self.sensors))
        sensor.setParentInventory(self.parentInventory)


    def popSensor(self, sensor):
        ''' Remove a sensor from the recorder.

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor to be removed from the recorder.

        Returns
        -------
        sensor : :class:`Sensor`
            The removed sensor instance.
        '''
        if sensor in self.sensors:
            sensor.parentRecorder = None
            # sensor.recorderId = None
            sensor.recorderSerial = None
            sensor.recorderType = None
            return self.sensors.pop(self.sensors.index(sensor))
        else:
            return None

    ## Refresh the sensor list.
    #
    # Check the association of the stations to the network. 
    # Remove stations that are no longer linked to the network.
    def refreshSensors(self, sensors=None):
        # Remove invalid stations from the network.
        for curSensor in self.sensors:
            if curSensor.recorderSerial != self.serial or curSensor.recorderType != self.type:
                self.sensors.remove(curSensor)
                self.parentInventory.addSensor(curSensor)


        #for curStation in stations:
        #    if curStation.network == self.name:
        #        self.parentInventory.addStation(curStation)
        #        stations.remove(curStation)



    ## Update the recorder database entry.    
    def updateDb(self, project):
        # Write the recorder data to the geom_recorder table.
        tableName = project.dbTableNames['geom_recorder']

        query =  ("UPDATE %s "
                  "%s "
                  "WHERE id=%d") % (tableName, self.getUpdateString, self.id)

        res = project.executeQuery(query)

        if not res['isError']:
            print("Successfully wrote the recorders to the database.")
        else:
            print res['msg']  


    ## Build the database query update string.
    def getUpdateString(self):
        updateString = ''
        for curField in self.changedFields:
            curStr = "SET %s = %s" %(curField, str(self[curField]))
            updateString.join([curStr, ','])

        return updateString[:-1]


## The sensor class.
#
# 
class Sensor:

    ## The constructor.
    #
    #
    def __init__(self, serial, type, 
                 recChannelName, channelName, label, id=None, recorderId=None, 
                 recorderSerial=None, recorderType=None, parentInventory=None):

        ## The database id of the sensor.
        self.id = id

        ## The sensor label specified by the user.
        self.label = label

        ## The id of the recorder to which the sensor is attached to.
        self.recorderId = recorderId

        ## The serial of the recorder to which the sensor is attached to.
        self.recorderSerial = recorderSerial

        ## The type of the recorder to which the sensor is attached to.
        self.recorderType = recorderType

        ## The serial number of the sensor.
        self.serial = serial

        ## The type of the sensor.
        self.type = type

        ## The recorder channel name.
        # 
        # The name of the channel as defined by the recording system. For example 
        # Reftek 130 recorders name the individual channels as 101, 102, ... with 
        # the first digit being the number of the stream, the last the number of 
        # the channel. Other recording systems have different, custom channel 
        # naming schemes. 
        # The recChannelName is used to map the raw data files to a common channel 
        # name named by the channelName attribute.
        self.recChannelName = recChannelName

        ## The channel name.
        # 
        # The channel name is the actual name used by pSysmon to work with the 
        # data of the sensor.
        self.channelName = channelName


        ## The sensor parameters.
        # The sensor paramters are stored in a list with the start and end time 
        # during which these paramters have been valid.
        self.parameters = []


        # The inventory containing this sensor.
        self.parentInventory = parentInventory

        
        # The parent recorder.
        self.parentRecorder = None


    def __getitem__(self, name):
        return self.__dict__[name]


    def __setitem__(self, name, value):
        self.__dict__[name] = value
        # Send an inventory update event.
        msgTopic = 'inventory.update.sensor'
        msg = (self, name, value)
        pub.sendMessage(msgTopic, msg)


    def setParentInventory(self, parentInventory):
        ''' Set the parentInventory attribute.

        Parameters
        ----------
        parentInventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parentInventory = parentInventory


    def addParameter(self, parameter, beginTime, endTime):
        ''' Add a sensor paramter instance to the sensor.

        Parameters
        ----------
        parameter : :class:`SensorParameter`
            The sensor parameter instance to be added.

        beginTime : :class:`obspy.core.utcdatetime.UTCDateTime`
            The begin time of the parameter values.

        endTime : :class:`obspy.core.utcdatetime.UTCDateTime`
            The end time of the parameter values.

        '''
        self.parameters.append(
                               (parameter,
                               beginTime,
                               endTime)
                               )
        self.hasChanged = True



    ## Update the changed attribute fields in the database table.      
    def dbUpdateRecorderAssignment(self, project, actions):

        if not actions:
            return

        # Get all attributes names to process.
        attrNames = [curAction['attrName'] for curAction in actions]
        attrNames = list(set(attrNames))        # Remove duplicates.

        if 'recorderSerial' in attrNames:
            actions2Process = [curAction for curAction in actions if curAction['attrName'] == 'recorderSerial']
            newRecSerial = actions2Process[0]['dataAfter']
        else:
            newRecSerial = self.recorderSerial

        if 'recorderType' in attrNames:
            actions2Process = [curAction for curAction in actions if curAction['attrName'] == 'recorderType']
            newRecType = actions2Process[0]['dataAfter']
        else:
            newRecType = self.recorderType


        # Update the recorder id of the sensor.
        tableName = project.dbTableNames['geom_recorder']
        query = ("SELECT id FROM %s "
                 "WHERE "
                 "serial LIKE '%s' "
                 "AND type LIKE '%s' "
                 ) % (tableName, newRecSerial, newRecType)
        res = project.executeQuery(query)

        if not res['isError']:
            if not res['data']:
                newRecId = '-1'
            else:
                newRecId = res['data'][0]['id']
        else:
            print res['msg'] 

        tableName = project.dbTableNames['geom_sensor']
        query = ("UPDATE %s "
                "SET recorder_id = %s "
                "WHERE id = %s") % (tableName, newRecId, self.id)

        res = project.executeQuery(query)

        if not res['isError']:
            print("Successfully updated the sensor assignment of sensor %s-%s-%s.") % (self.recorderSerial, self.serial, self.recChannelName)
        else:
            print res['msg'] 


    ## Change the sensor deployment start time.
    #
    # 
    def changeParameterStartTime(self, position, startTime):
        msg = ''    
        curRow = self.parameters[position]

        if not isinstance(startTime, UTCDateTime):
            try:
                startTime = UTCDateTime(startTime)
            except:
                startTime = curRow[1]
                msg = "The entered value is not a valid time."


        if not curRow[2] or startTime < curRow[2]:
            self.parameters[position] = (curRow[0], startTime, curRow[2])
            curRow[0]['startTime'] = startTime
        else:
            startTime = curRow[1]
            msg = "The start-time has to be smaller than the begin time."

        return (startTime, msg)


    ## Change the sensor deployment start time.
    #
    # 
    def changeParameterEndTime(self, position, endTime):
        msg = ''    
        curRow = self.parameters[position]

        if endTime == 'running':
            self.parameters[position] = (curRow[0], curRow[1], None)
            curRow[0]['endTime'] = None
            return(endTime, msg)

        if not isinstance(endTime, UTCDateTime):
            try:
                endTime = UTCDateTime(endTime)
            except:
                endTime = curRow[2]
                msg = "The entered value is not a valid time."


        if endTime:
            if not curRow[1] or endTime > curRow[1]:
                self.parameters[position] = (curRow[0], curRow[1], endTime)
                curRow[0]['endTime'] = endTime
                # Send an inventory update event.
                #msgTopic = 'inventory.update.sensorParameterTime'
                #msg = (curRow[0], 'time', (self, curRow[0], curRow[1], endTime))
                #pub.sendMessage(msgTopic, msg)
            else:
                endTime = curRow[2]
                msg = "The end-time has to be larger than the begin time."

        return (endTime, msg)





## The sensor parameter class.
#
class SensorParameter:
    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, sensorId, gain, bitweight, bitweightUnits, sensitivity, 
                 sensitivityUnits, tfType=None, tfUnits=None, tfNormalizationFactor=None, 
                 tfNormalizationFrequency=None, id=None, startTime=None, endTime=None):

        ## The id of the sensor to which this SensorParamter instance is assigned 
        # to. 
        self.sensorId = sensorId

        ## The sensor gain.
        self.gain = gain

        ## The sensor bitweight.
        self.bitweight = bitweight

        ## The units of the bitweight.
        self.bitweightUnits = bitweightUnits

        ## The sensor sensitivity.
        self.sensitivity = sensitivity

        ## The units of the sensitivity.
        self.sensitivityUnits = sensitivityUnits

        ## The transfer function type.
        # - displacement
        # - velocity
        # - acceleration
        self.tfType = tfType

        ## The transfer function units.
        self.tfUnits = tfUnits

        ## The transfer function normalization factor.
        self.tfNormalizationFactor = tfNormalizationFactor

        ## The transfer function normalization factor frequency.
        self.tfNormalizationFrequency = tfNormalizationFrequency

        ## The id of the sensor paramteer instance.
        self.id = id 

        ## The transfer function as PAZ.
        self.tfPoles = []
        self.tfZeros = []

        # The startTime from which the parameters are valid.
        self.startTime = startTime

        # The end time up to which the parameters are valid.
        self.endTime = endTime



    def __getitem__(self, name):
        return self.__dict__[name]


    def __setitem__(self, name, value):
        self.__dict__[name] = value
        print "Setting sensor Parameter: %s" % name
        msgTopic = 'inventory.update.sensorParameter'
        msg = (self, name, value)
        pub.sendMessage(msgTopic, msg)


    def setTransferFunction(self, tfType, tfUnits, tfNormalizationFactor, 
                            tfNormalizationFrequency):
        ''' Set the transfer function parameters.

        '''
        self.tfType = tfType
        self.tfUnits = tfUnits
        self.tfNormalizationFactor = tfNormalizationFactor
        self.tfNormalizationFrequency = tfNormalizationFrequency


    def tfAddComplexZero(self, zero):
        ''' Add a complex zero to the transfer function PAZ.

        '''
        self.tfZeros.append(zero)

    def tfAddComplexPole(self, pole):
        ''' Add a complec pole to the transfer function PAZ.

        '''
        self.tfPoles.append(pole)



## The station class.
#
class Station:

    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, name, location, x, y, z, parentInventory=None, coordSystem=None, description=None, network=None, id=None):

        ## The station id.
        self.id = id

        ## The station name.
        self.name = name

        ## The station location.
        self.location = location

        ## The station description.
        #
        # The extended name of the station.
        self.description = description

        ## The x coordinate of the station location.
        #
        # The coordinate system used is a right handed coordinate system with 
        # x pointing in the East direction, y pointing in the North direction and 
        # z pointing upwards.@n 
        # Depending on the coordinate system used x and y can also represent 
        # longitude and latitude.
        self.x = x

        ## The y coordinate of the station location.
        #
        # The coordinate system used is a right handed coordinate system with 
        # x pointing in the East direction, y pointing in the North direction and 
        # z pointing upwards.@n 
        # Depending on the coordinate system used x and y can also represent 
        # longitude and latitude.
        self.y = y

        ## The z coordinate of the station location.
        #
        # The coordinate system used is a right handed coordinate system with 
        # x pointing in the East direction, y pointing in the North direction and 
        # z pointing upwards.@n 
        # Depending on the coordinate system used x and y can also represent 
        # longitude and latitude.
        self.z = z

        ## The coordinate system in which the x/y coordinates are given.
        # 
        # The coordSystem string should be a valid EPSG code.@n 
        # See http://www.epsg-registry.org/ to find your EPSG code.
        self.coordSystem = coordSystem

        ## The station's network.
        #
        self.network = network

        ## A list of sensors assigned to the station.
        # 
        # Each sensor knows during which time it has been operating at the sensor.
        # 1. column: sensor object
        # 2. column: start time
        # 3. column: end time
        self.sensors = []

        # The inventory containing this sensor.
        self.parentInventory = parentInventory


    def __getitem__(self, name):
        return self.__dict__[name]


    def __setitem__(self, name, value):
        self.__dict__[name] = value
        msgTopic = 'inventory.update.station'
        msg = (self, name, value)
        pub.sendMessage(msgTopic, msg)


    def setParentInventory(self, parentInventory):
        ''' Set the parentInventory attribute.

        Also update the parent inventory of all children.

        Parameters
        ----------
        parentInventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parentInventory = parentInventory
        for curSensor, beginTime, endTime in self.sensors:
            curSensor.setParentInventory(self.parentInventory) 

    def getLonLat(self):
        '''
        Return the coordinate system as WGS84 longitude latitude tuples.
        '''
        # TODO: Add a check for valid epsg string.
        srcProj = pyproj.Proj(init=self.coordSystem)
        dstProj = pyproj.Proj(init="epsg:4326") 
        lon, lat = pyproj.transform(srcProj, dstProj, self.x, self.y)
        print 'Converting from "%s" to "%s"' % (srcProj.srs, dstProj.srs)
        return (lon, lat)


    def addSensor(self, sensor, startTime, endTime):
        ''' Add a sensor to the station.

        Parameters
        ----------
        sensor : :class:`Sensor`
            The :class:`Sensor` instance to be added to the station.

        startTime : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time from which on the sensor has been operating at the station.

        endTime : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time up to which the sensor has been operating at the station. "None" if the station is still running.
        '''
        self.sensors.append((sensor, startTime, endTime))
        self.hasChanged = True
        sensor.setParentInventory(self.parentInventory)

        # Send an inventory update event.
        msgTopic = 'inventory.update.addSensor2Station'
        msg = (self, 'addSensor', (sensor, startTime, endTime))
        pub.sendMessage(msgTopic, msg)

        #if 'sensorAdded' in self.changedFields.keys():
        #    self.changedFields['sensorAdded'].append((sensor, startTime, endTime))
        #else:
        #    self.changedFields['sensorAdded'] = [(sensor, startTime, endTime)]



    def removeSensor(self, sensor):
        ''' Remove a sensor from the station.

        Parameters
        ----------
        sensor : tuple (:class:`Sensor`, :class:`~obspy.core.utcdatetime.UTCDateTime`, :class:`~obspy.core.utcdatetime.UTCDateTime`) 
            The sensor to be removed from the station.
        '''
        print "Removing sensor "
        print sensor

        logger = logging.getLogger('base')
        logger.debug('Removing sensor')

        #if sensor not in self.sensors:
        
        # Remove the sensor from the sensors list.
        #self.sensors.pop(self.sensors.index(sensor))





    def changeSensorStartTime(self, sensor, startTime):
        ''' Change the sensor deployment start time

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor which should be changed.

        startTime : :class:`~obspy.core.utcdatetime.UTCDateTime or String
            A :class:`~obspy.core.utcdatetime.UTCDateTime` instance or a data-time string which can be used by :class:`~obspy.core.utcdatetime.UTCDateTime`.
        '''
        sensor2Change = [(s, b, e, k) for k, (s, b, e) in enumerate(self.sensors) if s == sensor]

        if sensor2Change:
            sensor2Change = sensor2Change[0]
            position = sensor2Change[3]
        else:
            msg = 'The sensor can''t be found in the station.'
            return (None, msg)

        msg = ''    


        if not isinstance(startTime, UTCDateTime):
            try:
                startTime = UTCDateTime(startTime)
            except:
                startTime = sensor2Change[2]
                msg = "The entered value is not a valid time."


        if not sensor2Change[2] or (sensor2Change[2] and startTime < sensor2Change[2]):
            self.sensors[position] = (sensor2Change[0], startTime, sensor2Change[2])
            # Send an inventory update event.
            msgTopic = 'inventory.update.sensorDeploymentTime'
            evtMsg = (self, 'startTime', (sensor2Change[0], startTime, sensor2Change[2]))
            pub.sendMessage(msgTopic, evtMsg)

        else:
            startTime = sensor2Change[1]
            msg = "The end-time has to be larger than the begin time."

        return (startTime, msg)



    def changeSensorEndTime(self, sensor, endTime):
        ''' Change the sensor deployment end time

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor which should be changed.

        endTime : String
            A data-time string which can be used by :class:`~obspy.core.utcdatetime.UTCDateTime`.
        '''
        sensor2Change = [(s, b, e, k) for k, (s, b, e) in enumerate(self.sensors) if s == sensor]

        if sensor2Change:
            sensor2Change = sensor2Change[0]
            position = sensor2Change[3]
        else:
            msg = 'The sensor can''t be found in the station.'
            return (None, msg)

        msg = ''    

        if endTime == 'running':
            self.sensors[position] = (sensor2Change[0], sensor2Change[1], None)
            # Send an inventory update event.
            msgTopic = 'inventory.update.sensorDeploymentTime'
            evtMsg = (self, 'endTime', (sensor2Change[0], sensor2Change[1], None))
            pub.sendMessage(msgTopic, evtMsg)
            return(endTime, msg)

        if not isinstance(endTime, UTCDateTime):
            try:
                endTime = UTCDateTime(endTime)
            except:
                endTime = sensor2Change[2]
                msg = "The entered value is not a valid time."


        if not sensor2Change[1] or endTime > sensor2Change[1]:
            self.sensors[position] = (sensor2Change[0], sensor2Change[1], endTime)
            # Send an inventory update event.
            msgTopic = 'inventory.update.sensorDeploymentTime'
            evtMsg = (self, 'endTime', (sensor2Change[0], sensor2Change[1], endTime))
            pub.sendMessage(msgTopic, evtMsg)

        else:
            endTime = sensor2Change[2]
            msg = "The end-time has to be larger than the begin time."

        return (endTime, msg)



## The network class.
class Network:

    def __init__(self, name, description=None, type=None, parentInventory=None):

        ## The parent inventory.
        self.parentInventory = parentInventory

        ## The network name (code).
        self.name = name

        ## The network description.
        self.description = description

        ## The network type.
        self.type = type

        ## The stations contained in the network.
        self.stations = {}

        ## The database table name.
        self.dbTableName = 'geom_network'



    ## The index and slicing operator.
    def __getitem__(self, name):
        return self.__dict__[name]


    ## The index and slicing operator.
    def __setitem__(self, name, value):
        self.__dict__[name] = value
        msgTopic = 'inventory.update.network'
        msg = (self, name, value)
        pub.sendMessage(msgTopic, msg)




    def setParentInventory(self, parentInventory):
        ''' Set the parentInventory attribute.

        Also update the parent inventory of all children.

        Parameters
        ----------
        parentInventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parentInventory = parentInventory

        for curStation in self.stations.values():
            curStation.setParentInventory(self.parentInventory)

    ## Add a station to the network. 
    def addStation(self, station):
        station.network = self.name
        self.stations[(station.name, station.location)] = station
        station.setParentInventory(self.parentInventory)


    ## Refresh the station list.
    #
    # Check the association of the stations to the network. 
    # Remove stations that are no longer linked to the network.
    def refreshStations(self, stations):
        # Remove invalid stations from the network.
        for curStation in self.stations.values():
            if curStation.network != self.name:
                self.stations.pop((curStation.name, curStation.location))
                self.parentInventory.addStation(curStation)


        for curStation in stations:
            if curStation.network == self.name:
                self.parentInventory.addStation(curStation)
                stations.remove(curStation)




class InventoryHistory:
    def __init__(self, attrMap, actionTypes):

        self.attrMap = attrMap

        self.actionTypes = actionTypes

        self.actions = []


    ## Register an action in the history.
    def do(self, action):
        print "Registering action: " + action['type']
        self.actions.append(action)


    ## Undo the last action in the history.
    def undo(self, object):
        pass


    ## Check if actions have been registered.
    def hasActions(self):
        if self.actions:
            return True
        else:
            return False

    ## Fetch the first action in the stack.
    def fetchAction(self, type=None):
        if not self.actions:
            return None

        if not type:
            if self.actions:
                curAction = self.actions[0]
                self.actions.pop(0)
                return curAction
        else:
            actions2Fetch = [curAction for curAction in self.actions if curAction['type'] == type]
            if actions2Fetch:
                for curAction in actions2Fetch:
                    self.actions.remove(curAction)
            return actions2Fetch


    ## Build the database query update string.
    def getUpdateString(self, actions):

        updateString = ''

        # Get all attributes names to process.
        attrNames = [curAction['attrName'] for curAction in actions]
        attrNames = list(set(attrNames))        # Remove duplicates.

        # Process the attribute names.
        for curAttr in attrNames:
            actions2Process = [curAction for curAction in actions if curAction['attrName'] == curAttr]
            firstAction = actions2Process[0]

            if(len(actions2Process) >= 2):
                lastAction = actions2Process[-1]
            else:
                lastAction = firstAction

            # If the attribute exists in the attribute map, create the update string.
            if curAttr in self.attrMap.keys():
                curStr = "%s = '%s'," %(self.attrMap[curAttr], str(lastAction['dataAfter']))
                updateString += curStr 


        # Remove the trailing comma from the string.            
        return updateString[:-1]


