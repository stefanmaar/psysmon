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


    ## Add a Network to the inventory.
    def addNetwork(self, network):
        self.networks[network.name] = network


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


    ## Load the inventory from a pSysmon database.
    def loadFromDb(self, project):
        self.type = 'db'
        self.name = 'project inventory'

        self.dbController = InventoryDatabaseController(self, project)

        try:
            self.dbController.loadRecorder()
            #self.dbController.loadNetwork()
            #self.dbController.loadStation()
            #self.dbController.loadUnassignedSensor()
        except PsysmonError as e:
            raise e


    ## Update the inventory database tables.
    def updateDb(self):

        if self.type.lower() != 'db':
            return

        self.dbController.updateDb()



    ## Save the inventory to the pSysmon database.
    #
    # Write a non-database inventory (e.g. imported from xml file) to the pSysmon database. 
    def write2Db(self, project):
        print "Writing inventory to the database."

        # Write the recorders and sensors to the database.
        for curRecorder in self.recorders:
            self.dbController.insertRecorder(curRecorder)


        # Write the networks and the contained stations to the database.
        #for curNetwork in self.networks.itervalues():
        #    curNetwork.write2Db(project)

        #    for curStation in curNetwork.stations.itervalues():
        #        curStation.write2Db(project)

        # Write the unassigned stations to the database.
        #for curStation in self.stations:
        #    curStation.write2Db(project)



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

        self.sensorMappers = {}


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

        for curInstance in self.dbSession.query(dbRecorder).order_by(dbRecorder.serial):
            print "Loading recorder %s.\n" % curInstance.serial
            curRecorder = Recorder(id=curInstance.id,
                                   serial=curInstance.serial,
                                   type=curInstance.type,
                                   parentInventory=inventory)

            for curDbSensor in curInstance.sensors:
                curSensor = Sensor(curDbSensor.serial,
                                   curDbSensor.type,
                                   curDbSensor.rec_channel_name,
                                   curDbSensor.channel_name,
                                   curDbSensor.label,
                                   id=curDbSensor.id,
                                   recorderId=curRecorder.id,
                                   recorderType=curRecorder.type,
                                   parentInventory=inventory)
                curRecorder.addSensor(curSensor)

                for curDbParam in curDbSensor.parameters:
                    curParam = SensorParameter(curSensor.id,
                                               curDbParam.gain,
                                               curDbParam.bitweight,
                                               curDbParam.bitweight_units,
                                               curDbParam.sensitivity,
                                               curDbParam.sensitivity_units,
                                               tfType = curDbParam.type,
                                               tfUnits = curDbParam.tf_units,
                                               tfNormalizationFactor = curDbParam.normalization_factor,
                                               tfNormalizationFrequency = curDbParam.normalization_frequency,
                                               id=curDbParam.id)
                    curSensor.addParameter(curParam, curDbParam.start_time, curDbParam.end_time)


                

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
                                 curDbNetwork.type,
                                 parentInventory=inventory)

            for curDbStation in curDbNetwork.stations:
                curStation = Station(curDbStation.name,
                                     curDbStation.location,
                                     curDbStation.X,
                                     curDbStation.Y,
                                     curDbStation.Z,
                                     coordSystem=curDbStation.coord_system,
                                     description=curDbStation.description,
                                     network=curNetwork.name,
                                     id=curDbStation.id,
                                     parentInventory=inventory)
                curNetwork.addStation(curStation)

                for curDbSensor in curDbStation.sensors:
                    print "\n\n##########################"
                    print curDbSensor
                    print "##############################"

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
            self.sensorMappers[curSensor] = sensor2Add

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

                sensorTime2Add.child = self.sensorMappers[curSensor]
                station2Add.sensors.append(sensorTime2Add)


        self.dbSession.add(network2Add)
        self.dbSession.commit()



    ## Load the networks from the database.
    def loadNetwork(self):
        # Load the network data from the geom_network table.
        tableName = self.project.dbTableNames['geom_network']
        query =  ("SELECT name, description, type FROM %s ") % tableName 
        res = self.project.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                print "Loading network %s.\n" % curData['name']
                curNetwork = Network(name=curData['name'],
                                     description=curData['description'],
                                     type=curData['type'],
                                     parentInventory=self.inventory
                                     )
                self.inventory.addNetwork(curNetwork)
        else:
            print res['msg']

    ## Load the stations from the database.
    def loadStation(self):
        # Load the station data from the geom_station table.
        tableName = self.project.dbTableNames['geom_station']
        query =  ("SELECT "
                  "id, net_name, name, location, X, Y, Z, coord_system, description "
                  "FROM %s") % tableName 
        res = self.project.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                print "Loading station %s.\n" % curData['name']
                curStation = Station(id=curData['id'],
                                     name=curData['name'],
                                     location=curData['location'],
                                     x=curData['X'],
                                     y=curData['Y'],
                                     z=curData['Z'],
                                     coordSystem=curData['coord_system'],
                                     description=curData['description'],
                                     network=curData['net_name'],
                                     parentInventory=self.inventory
                                     )

                # Load the sensors associated with the station.
                curStation.loadSensorFromDb(self.project, self.inventory)

                self.inventory.addStation(curStation)
        else:
            print res['msg']

    ## Load the unassigned sensors from the database.
    def loadUnassignedSensor(self):
        tableName = self.project.dbTableNames['geom_sensor']
        query =  ("SELECT id, label, serial, type, rec_channel_name, channel_name FROM  %s "
                  "WHERE recorder_id = -1") % tableName

        res = self.project.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                curSensor = Sensor(id=curData['id'],
                                   serial=curData['serial'],
                                   type=curData['type'],
                                   recChannelName=curData['rec_channel_name'],
                                   channelName=curData['channel_name'],
                                   label=curData['label'],
                                   parentInventory=self.inventory)

                self.inventory.addSensor(curSensor)
                curSensor.loadParameterFromDb(self.project)

        else:
            print res['msg']  

    ## Update the inventory database tables.
    def updateDb(self):
        for curRecorder in self.inventory.recorders:
            if curRecorder.history.hasActions():
                curRecorder.updateDb(self.project)

            for curSensor in curRecorder.sensors:
                if curSensor.history.hasActions():
                    curSensor.updateDb(self.project)

                for (curParam, beginTime, endTime) in curSensor.parameters:
                    if curParam.history.hasActions():
                        curParam.updateDb(self.project)


        for curStation in self.inventory.stations:
            if curStation.history.hasActions():
                curStation.updateDb(self.project)  

        for curSensor in self.inventory.sensors:
            if curSensor.history.hasActions():
                curSensor.updateDb(self.project) 


        for curNetwork in self.inventory.networks.itervalues():
            if curNetwork.history.hasActions():
                curNetwork.updateDb(self.project)
            for curStation in curNetwork.stations.itervalues():
                if curStation.history.hasActions():
                    curStation.updateDb(self.project)


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
                               type = recorderContent['type'],
                               parentInventory = self.parentInventory)  

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
                                    label=curChannel.attrib['label'],
                                    parentInventory=self.parentInventory)
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
                                      network=stationContent['network_code'],
                                      parentInventory=self.parentInventory
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
                              type=content['type'],
                              parentInventory=self.parentInventory)  

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

    ## Add a sensor to the recorder.
    def addSensor(self, sensor):
        sensor.recorderId = self.id
        sensor.recorderSerial = self.serial
        sensor.recorderType = self.type
        self.sensors.append(sensor)
        self.sensors = list(set(self.sensors))


    ## Remove a sensor from the recorder.
    def removeSensor(self, position):
        pass

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


    ## Load the recorder sensor data from the datbase.
    def loadSensorFromDb(self, project):
        tableName = project.dbTableNames['geom_sensor']
        query =  ("SELECT id, label, serial, type, rec_channel_name, channel_name FROM  %s "
                  "WHERE recorder_id = %d") % (tableName, self.id)

        res = project.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                curSensor = Sensor(id=curData['id'],
                                   serial=curData['serial'],
                                   type=curData['type'],
                                   recChannelName=curData['rec_channel_name'],
                                   channelName=curData['channel_name'],
                                   label=curData['label'],
                                   parentInventory=self.parentInventory)

                self.addSensor(curSensor)               # This also sets the recorder id of the sensor.
                curSensor.loadParameterFromDb(project)

        else:
            print res['msg'] 

    ## Write the recorder to the pSysmon database.
    def write2Db(self, project):                         

        dbRecorder = project.dbTables['geom_recorder']
        dbSensor = project.dbTables['geom_sensor']

        newRecorder = dbRecorder(self.serial, self.type)
        self.dbSession.add(newRecorder)

        # Write the recorder data to the geom_recorder table.
        #tableName = project.dbTableNames['geom_recorder']
        #query =  ("INSERT IGNORE INTO %s "
        #          "(serial, type) "
        #          "VALUES ('%s', '%s')") % (tableName, self.serial, self.type)  
        #res = project.executeQuery(query)

        #if not res['isError']:
        #    print("Successfully wrote the recorders to the database.")
        #else:
        #    print res['msg']  

        #query = ("SELECT id, serial, type FROM %s WHERE serial LIKE '%s' AND type LIKE '%s'") % (tableName, self.serial, self.type)  
        #res = project.executeQuery(query)
        #recData = res['data']

        #if not res['isError']:
        #    if not recData:
        #        print "No id found for recorder %s-%s" %(self.serial, self.type)
        #        recId = -1
        #    else:
        #        recId = recData[0]['id']
        #        print "Assigned id %s to recorder %s-%s." % (recId, self.serial, self.type)
        #else:
        #    print res['msg']  


        #for curSensor in self.sensors:
        #    curSensor.write2Db(project, recId)


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

        ## The mapping of the station attributes to the database columns.
        attrMap = {};
        attrMap['id'] = 'id'
        attrMap['label'] = 'label'
        attrMap['recorderId'] = 'recorder_id'
        attrMap['recorderSerial'] = None
        attrMap['recorderType'] = None
        attrMap['serial'] = 'serial'
        attrMap['type'] = 'type'
        attrMap['recChannelName'] = 'rec_channel_name'
        attrMap['channel_name'] = 'channel_name'

        # The allowed actions to be saved in the history.
        actionTypes = {};
        actionTypes['changeAttribute'] = 'Changed a station attribute.'

        ## The station action history.
        self.history = InventoryHistory(attrMap, actionTypes)

        ## The database table name holding the station data.
        self.dbTableName = 'geom_sensor'

        # The inventory containing this sensor.
        self.parentInventory = parentInventory


    def __getitem__(self, name):
        return self.__dict__[name]

    def __setitem__(self, name, value):
        if name in ['recorderSerial', 'recorderType']:
            action = {}
            action['type'] = 'changeRecorderAssignment'
            action['attrName'] = name
            action['dataBefore'] = self.__dict__[name]
            action['dataAfter'] = value
        else:
            action = {}
            action['type'] = 'changeAttribute'
            action['attrName'] = name
            action['dataBefore'] = self.__dict__[name]
            action['dataAfter'] = value

        self.__dict__[name] = value
        self.history.do(action)


    def addParameter(self, parameter, beginTime, endTime):
        self.parameters.append(
                               (parameter,
                               beginTime,
                               endTime)
                               )
        self.hasChanged = True

    ## Load the sensor parameters from the database.
    def loadParameterFromDb(self, project):

        tableName = project.dbTableNames['geom_sensor_param']
        query =  ("SELECT id, sensor_id, start_time, end_time, normalization_factor, "
                  "normalization_frequency, type, tf_units, gain, sensitivity, "
                  "sensitivity_units, bitweight, bitweight_units, "
                  "start_time, end_time "
                  "FROM  %s "
                  "WHERE sensor_id = %d") % (tableName, self.id)

        res = project.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                curParam = SensorParameter(id=curData['id'],
                                           sensorId=curData['sensor_id'],
                                           gain = curData['gain'],
                                           bitweight = curData['bitweight'],
                                           bitweightUnits = curData['bitweight_units'],
                                           sensitivity = curData['sensitivity'],
                                           sensitivityUnits = curData['sensitivity_units']
                                           )

                curParam.setTransferFunction(tfType=curData['type'], 
                                             tfUnits=curData['tf_units'],
                                             tfNormalizationFactor=curData['normalization_factor'], 
                                             tfNormalizationFrequency=curData['normalization_frequency']
                                             )

                query = ("SELECT type, complex_real, complex_imag FROM %s "
                         "WHERE param_id = %d") % (project.dbTableNames['geom_tf_pz'], curParam.id)

                res = project.executeQuery(query)

                for curPz in res['data']:
                    if curPz['type'] == 0:
                        # Process a zero.
                        curParam.tfAddComplexZero(complex(curPz['complex_real'], curPz['complex_imag']))

                    else:
                        # Process a pole
                        curParam.tfAddComplexPole(complex(curPz['complex_real'], curPz['complex_imag']))

                # Convert the time strings to UTC times.
                if curData['start_time']:
                    startTime = UTCDateTime(curData['start_time'])
                else:
                    startTime = None


                if curData['end_time']:
                    endTime = UTCDateTime(curData['end_time'])
                else:
                    endTime = None

                self.addParameter(curParam, 
                                    startTime, 
                                    endTime)

        else:
            print res['msg'] 

    ## Write the sensor to the database.
    def write2Db(self, project, recorderId):              

        # Write the sensor data to the geom_sensor table..
        tableName = project.dbTableNames['geom_sensor']
        query =  ("REPLACE INTO %s "
                  "(recorder_id, label, serial, type, rec_channel_name, channel_name) "
                  "VALUES ('%s', '%s', '%s', '%s', '%s', '%s')") % (tableName, 
                                                              recorderId,
                                                              self.label,
                                                              self.serial, 
                                                              self.type,
                                                              self.recChannelName,
                                                              self.channelName)

        res = project.executeQuery(query)

        if not res['isError']:
            print("Successfully wrote the sensors to the database.")
        else:
            print res['msg'] 

        ## Get the id of the inserted sensor.
        query = ("SELECT id FROM %s " 
                 "WHERE recorder_id = %s "
                 "AND serial LIKE '%s' "
                 "AND type LIKE '%s' "
                 "AND rec_channel_name LIKE '%s' "
                 "AND channel_name LIKE '%s'") % (tableName, 
                                                  recorderId, 
                                                  self.serial, 
                                                  self.type, 
                                                  self.recChannelName, 
                                                  self.channelName)  
        res = project.executeQuery(query)
        sensorData = res['data']

        if not res['isError']:
            if not sensorData:
                print "No id found for recorder %s-%s-%s-%s" % (self.serial, self.type, self.recChannelName, self.channelName)
                sensorId = -1
            else:
                sensorId = sensorData[0]['id']
                print "Assigned id %s to sensor %s-%s-%s-%s." % (sensorId, self.serial, self.type, self.recChannelName, self.channelName)
        else:
            print res['msg']  


        for (curParam, curStart, curEnd) in self.parameters:
            curParam.write2Db(project, sensorId, curStart, curEnd) 


    ## Update the sensor database entry.    
    def updateDb(self, project):

        if not self.history.hasActions():
            # No actions to perform.
            return

        # Process the changed attributes of the station.
        curAction = self.history.fetchAction('changeAttribute')
        self.dbUpdateAttributes(project, curAction)

        # Process the changed Recorder assignments.
        curAction = self.history.fetchAction('changeRecorderAssignment')
        self.dbUpdateRecorderAssignment(project, curAction)

        # Process all other actions. 
        while(self.history.hasActions()):
            curAction = self.history.fetchAction()
            print "Processing action " + curAction['type']
            print curAction



    ## Update the changed attribute fields in the database table.      
    def dbUpdateAttributes(self, project, actions):

        tableName = project.dbTableNames[self.dbTableName]
        updateString = self.history.getUpdateString(actions)

        if updateString:
            query =  ("UPDATE %s "
                      "SET %s "
                      "WHERE id=%d") % (tableName, updateString, self.id)

            res = project.executeQuery(query)

            if not res['isError']:
                print("Successfully updated the sensor attributes of recorder %s-%s-%s.") % (self.recorderSerial, self.serial, self.recChannelName)
            else:
                print res['msg'] 


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
            # Register an action in the history.

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

        if not isinstance(endTime, UTCDateTime):
            try:
                endTime = UTCDateTime(endTime)
            except:
                endTime = curRow[2]
                msg = "The entered value is not a valid time."


        if not curRow[1] or endTime > curRow[1]:
            self.parameters[position] = (curRow[0], curRow[1], endTime)
            # Resister the corresponding action.
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
                 tfNormalizationFrequency=None, id=None):

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

        # The allowed actions to be saved in the history.
        actionTypes = {};
        actionTypes['changeAttribute'] = 'Changed a station attribute.'

        ## The station action history.
        self.history = InventoryHistory(attrMap, actionTypes)

        ## The database table name holding the station data.
        self.dbTableName = 'geom_sensor_param'




    def __getitem__(self, name):
        return self.__dict__[name]


    def __setitem__(self, name, value):
        action = {}
        action['type'] = 'changeAttribute'
        action['attrName'] = name
        action['dataBefore'] = self.__dict__[name]
        action['dataAfter'] = value

        self.__dict__[name] = value
        self.history.do(action)




    ## Set the transfer function paramters.
    def setTransferFunction(self, tfType, tfUnits, tfNormalizationFactor, 
                            tfNormalizationFrequency):
        self.tfType = tfType
        self.tfUnits = tfUnits
        self.tfNormalizationFactor = tfNormalizationFactor
        self.tfNormalizationFrequency = tfNormalizationFrequency


    ## Add a complex zero to the transfer function PAZ.
    def tfAddComplexZero(self, zero):
        self.tfZeros.append(zero)

    ## Add a complex zero to the transfer function PAZ.
    def tfAddComplexPole(self, pole):
        self.tfPoles.append(pole)

    ## Write the sensor paramters to the database.
    def write2Db(self, project, sensorId, startTime, endTime):
        # Write the sensor parameter data to the geom_sensor_param table.

        if startTime:
            startTime = startTime.getTimeStamp()
        else:
            startTime = None

        if endTime:
            endTime = endTime.getTimeStamp()
        else:
            endTime = None


        tableName = project.dbTableNames['geom_sensor_param']
        query =  ("INSERT IGNORE INTO %s "
                  "(sensor_id, start_time, end_time, normalization_factor, "
                  "normalization_frequency, type, tf_units, gain, sensitivity, "
                  "sensitivity_units, bitweight, bitweight_units) "
                  "VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)") % tableName

        dbData = [(sensorId, 
                  startTime,
                  endTime,
                  self.tfNormalizationFactor,
                  self.tfNormalizationFrequency,
                  self.tfType,
                  self.tfUnits,
                  self.gain,
                  self.sensitivity,
                  self.sensitivityUnits,
                  self.bitweight,
                  self.bitweightUnits)] 

        res = project.executeManyQuery(query, dbData)  # I'm using executeManyQuery to handle NULL values.

        if not res['isError']:
            print("Successfully wrote the sensor parameters to the database.")

            ## Get the id of the inserted sensor parameter.
            query = ("SELECT LAST_INSERT_ID()") 

            res = project.executeQuery(query)

            if not res['isError']:
                data = res['data']
                if data:
                    paramrecorderTypeId = data[0]['LAST_INSERT_ID()']

                    dbData = []
                    for curPole in self.tfPoles:
                        dbData.append((paramId, 1, curPole.real, curPole.imag))

                    for curZero in self.tfZeros:
                        dbData.append((paramId, 0, curZero.real, curZero.imag))

                    tableName = project.dbTableNames['geom_tf_pz']
                    query =  ("INSERT INTO %s "
                              "(param_id, type, complex_real, complex_imag) "
                              "VALUES (%%s, %%s, %%s, %%s)") % tableName 
                    res = project.executeManyQuery(query, dbData)
            else:
                print res['msg']  

        else:
            print res['msg'] 


    ## Update the sensor parameter database entry.    
    def updateDb(self, project):

        if not self.history.hasActions():
            # No actions to perform.
            return

        # Process the changed attributes of the sensor paramter.
        curAction = self.history.fetchAction('changeAttribute')
        self.dbUpdateAttributes(project, curAction)


        # Process all other actions. 
        while(self.history.hasActions()):
            curAction = self.history.fetchAction()
            print "Processing action " + curAction['type']
            print curAction



    ## Update the changed attribute fields in the database table.      
    def dbUpdateAttributes(self, project, actions):

        tableName = project.dbTableNames[self.dbTableName]
        updateString = self.history.getUpdateString(actions)

        if updateString:
            query =  ("UPDATE %s "
                      "SET %s "
                      "WHERE id=%d") % (tableName, updateString, self.id)

            res = project.executeQuery(query)

            if not res['isError']:
                print("Successfully updated the sensor attributes of sensor parameter %s.") % self.id
            else:
                print res['msg'] 




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


        # The mapping of the station attributes to the database columns.
        attrMap = {};
        attrMap['id'] = 'id'
        attrMap['network'] = 'net_name'
        attrMap['name'] = 'name'
        attrMap['location'] = 'location'
        attrMap['x'] = 'X'
        attrMap['y'] = 'Y'
        attrMap['z'] = 'Z'
        attrMap['coordSystem'] = 'coord_system'
        attrMap['description'] = 'description'

        # The allowed actions to be saved in the history.
        actionTypes = {};
        actionTypes['changeAttribute'] = 'Changed a station attribute.'
        actionTypes['addSensor'] = 'Added a sensor to the station.'
        actionTypes['removeSensor'] = 'Removed a sensor from the station.'

        ## The station action history.
        self.history = InventoryHistory(attrMap, actionTypes)


        ## The database table name holding the station data.
        self.dbTableName = 'geom_station'

        # The inventory containing this sensor.
        self.parentInventory = parentInventory


    def __getitem__(self, name):
        return self.__dict__[name]


    def __setitem__(self, name, value):
        action = {}
        action['type'] = 'changeAttribute'
        action['attrName'] = name
        action['dataBefore'] = self.__dict__[name]
        action['dataAfter'] = value

        self.__dict__[name] = value
        self.history.do(action)


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

    ## Add a sensor to the station.
    #
    # 
    def addSensor(self, sensor, startTime, endTime):
        self.sensors.append((sensor, startTime, endTime))
        self.hasChanged = True

        #if 'sensorAdded' in self.changedFields.keys():
        #    self.changedFields['sensorAdded'].append((sensor, startTime, endTime))
        #else:
        #    self.changedFields['sensorAdded'] = [(sensor, startTime, endTime)]


    ## Remove a sensor to the station.
    #
    # 
    def removeSensor(self, sensor):
        print "Removing sensor "
        print sensor


    ## Change the sensor deployment start time.
    #
    # 
    def changeSensorStartTime(self, position, startTime):
        msg = ''    
        curRow = self.sensors[position]

        if not isinstance(startTime, UTCDateTime):
            try:
                startTime = UTCDateTime(startTime)
            except:
                startTime = curRow[1]
                msg = "The entered value is not a valid time."


        if not curRow[2] or startTime < curRow[2]:
            self.sensors[position] = (curRow[0], startTime, curRow[2])
           # self.hasChanged = True

           # if 'sensorTime' in self.changedFields.keys():
           #     if curRow[0] in self.changedFields['sensorTime'].keys():
           #         tmp = self.changedFields['sensorTime'][curRow[0]]
           #         self.changedFields['sensorTime'][curRow[0]] = (startTime, curRow[2], tmp[2], tmp[3])
           #     else:
           #         self.changedFields['sensorTime'] = {curRow[0]: (startTime, curRow[2], curRow[1], curRow[2])}
           # else:
           #     self.changedFields['sensorTime'] = {curRow[0]: (startTime, curRow[2], curRow[1], curRow[2])}
        else:
            startTime = curRow[1]
            msg = "The start-time has to be smaller than the begin time."

        return (startTime, msg)

    ## Change the sensor deployment start time.
    #
    # 
    def changeSensorEndTime(self, position, endTime):
        msg = ''    
        curRow = self.sensors[position]

        if not isinstance(endTime, UTCDateTime):
            try:
                endTime = UTCDateTime(endTime)
            except:
                endTime = curRow[2]
                msg = "The entered value is not a valid time."


        if not curRow[1] or endTime > curRow[1]:
            self.sensors[position] = (curRow[0], curRow[1], endTime)
            #self.hasChanged = True

            #if 'sensorTime' in self.changedFields.keys():
            #    if curRow[0] in self.changedFields['sensorTime'].keys():
            #        tmp = self.changedFields['sensorTime'][curRow[0]]
            #        self.changedFields['sensorTime'][curRow[0]] = (curRow[1], endTime, tmp[2], tmp[3])
            #    else:
            #        self.changedFields['sensorTime'] = {curRow[0]: (curRow[1], endTime, curRow[1], curRow[2])}
            #else:
            #    self.changedFields['sensorTime'] = {curRow[0]: (curRow[1], endTime, curRow[1], curRow[2])}
        else:
            endTime = curRow[2]
            msg = "The end-time has to be larger than the begin time."

        return (endTime, msg)

    ## Load the sensors from the database.
    #
    # @param self The object pointer.
    # @param project The pSysmon project.
    def loadSensorFromDb(self, project, inventory):

        tableName = project.dbTableNames['geom_sensor_time']
        query =  ("SELECT "
                  "stat_id, sensor_id, start_time, end_time "
                  "FROM  %s "
                  "WHERE stat_id = %d") % (tableName, self.id)

        res = project.executeQuery(query)

        if not res['isError']:
            for curData in res['data']:
                sensor2Add = inventory.getSensorById(id = curData['sensor_id'])

                if not sensor2Add:
                    continue

                # Convert the time strings to UTC times.
                if curData['start_time']:
                    startTime = UTCDateTime(curData['start_time'])
                else:
                    startTime = None


                if curData['end_time']:
                    endTime = UTCDateTime(curData['end_time'])
                else:
                    endTime = None

                self.addSensor(sensor2Add, startTime, endTime)

            # Reset the station to unchanged state.
            self.hasChanged = False
            self.changedFields = {}
        else:
            print res['msg']

    ## Write the station to the database.
    #
    #
    def write2Db(self, project):
        # Write the station data to the geom_sensor_param table.

        tableName = project.dbTableNames['geom_station']
        query =  ("INSERT IGNORE INTO %s "
                  "(net_name, name, location, x, y, z, coord_system, description) "
                  "VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)") % tableName

        dbData = [(self.network,
                   self.name,
                   self.location,
                   self.x,
                   self.y,
                   self.z,
                   self.coordSystem,
                   self.description)] 

        res = project.executeManyQuery(query, dbData)  # I'm using executeManyQuery to handle NULL values.

        if not res['isError']:
            print("Successfully wrote the station to the database.")
        else:
            print res['msg']

        # Get the station database id.
        query = ("SELECT "
                 "id "
                 "FROM %s "
                 "WHERE name LIKE '%s'"
                 ) % (tableName, self.name)

        res = project.executeQuery(query)

        if not res['isError']:
            data = res['data']
            statId = data[0]['id']
        else:
            statId = -1


        # Now add the sensors to the geom_sensor_time table.
        sensorTable = project.dbTableNames['geom_sensor']
        recorderTable = project.dbTableNames['geom_recorder']
        sensorTimeTable = project.dbTableNames['geom_sensor_time']

        for (curSensor, curStartTime, curEndTime) in self.sensors:
            # Get the sensor database id.
            query = ("SELECT sensor.id FROM %s as sensor, %s as recorder " 
                     "WHERE sensor.serial LIKE '%s' "
                     "AND sensor.type LIKE '%s' "
                     "AND sensor.rec_channel_name LIKE '%s' "
                     "AND sensor.channel_name LIKE '%s' "
                     "AND sensor.recorder_id = recorder.id "
                     "AND recorder.serial LIKE '%s' "
                     "AND recorder.type LIKE '%s'"
                     ) % (sensorTable, 
                          recorderTable,
                          curSensor.serial, 
                          curSensor.type, 
                          curSensor.recChannelName, 
                          curSensor.channelName,
                          curSensor.recorderSerial,
                          curSensor.recorderType)  
            res = project.executeQuery(query)

            if not res['isError']:
                data = res['data']
                sensorId = data[0]['id']

                if curStartTime:
                    curStartTime = curStartTime.getTimeStamp()
                else:
                    curStartTime = None

                if curEndTime:
                    curEndTime = curEndTime.getTimeStamp()
                else:
                    curEndTime = None

                query = ("INSERT IGNORE INTO %s "
                         "(stat_id, sensor_id, start_time, end_time) "
                         "VALUES (%%s, %%s, %%s, %%s)") % sensorTimeTable
                dbData = [(statId,
                           sensorId,
                           curStartTime,
                           curEndTime
                           )]

                project.executeManyQuery(query, dbData)
            else:
                print res['msg']

        else:
            print res['msg'] 


        query = ("SELECT id FROM %s WHERE name LIKE '%s'") % (tableName, self.name)  
        res = project.executeQuery(query)
        statData = res['data']

        if not res['isError']:
            if not statData:
                print "No id found for station %s" % self.name
                statId = -1
            else:
                statId = statData[0]['id']
                print "Assigned id %s to station %s." % (statId, self.name)
        else:
            print res['msg']  


    ## Update the station database entry.    
    def updateDb(self, project):

        if not self.history.hasActions():
            # No actions to perform.
            return

        # Process the changed attributes of the station.
        curAction = self.history.fetchAction('changeAttribute')
        self.dbUpdateAttributes(project, curAction)

        # Process all other actions. 
        while(self.history.hasActions()):
            curAction = self.history.fetchAction()
            print "Processing action " + curAction

        return



        # Add new sensors to the station table.        
        if 'sensorAdded' in self.changedFields.keys():
            tableName = project.dbTableNames['geom_sensor_time']
            for (curSensor, curStartTime, curEndTime) in self.changedFields['sensorAdded']:
                if curStartTime:
                    curStartTime = curStartTime.getTimeStamp()
                else:
                    curStartTime = 0

                if curEndTime:
                    curEndTime = curEndTime.getTimeStamp()
                else:
                    curEndTime = None

                query = ("INSERT IGNORE INTO %s "
                         "(stat_id, sensor_id, start_time, end_time) "
                         "VALUES (%%s, %%s, %%s, %%s)") % tableName

                dbData = [(str(self.id),
                           str(curSensor.id),
                           curStartTime,
                           curEndTime
                           )]

                res = project.executeManyQuery(query, dbData)

                if not res['isError']:
                    print("Successfully wrote the station to the database.")
                else:
                    print res['msg'] 


        # Update the sensor deployment time.
        if 'sensorTime' in self.changedFields.keys():
            tableName = project.dbTableNames['geom_sensor_time']
            for  curSensor, (curStartTime, curEndTime, origStartTime, origEndTime) in self.changedFields['sensorTime'].items():
                if curStartTime:
                    curStartTime = curStartTime.getTimeStamp()
                else:
                    curStartTime = 'NULL'

                if curEndTime:
                    curEndTime = curEndTime.getTimeStamp()
                else:
                    curEndTime = 'NULL'

                if origStartTime:
                    origStartStr = "start_time=%s" % origStartTime.getTimeStamp()
                else:
                    origStartStr = "start_time = 0"

                if origEndTime:
                    origEndStr = "end_time=%s" % origEndTime.getTimeStamp()
                else:
                    origEndStr = "end_time is NULL"

                query =  ("UPDATE %s "
                      "SET start_time = %s, end_time = %s "
                      "WHERE stat_id=%d AND sensor_id=%s AND %s AND %s") % (tableName, curStartTime, curEndTime, self.id, curSensor.id, origStartStr, origEndStr)

                print query

                res = project.executeQuery(query)
                if not res['isError']:
                    print("Successfully updated the sensor time.")
                else:
                    print res['msg']  


        self.hasChanged = False
        self.changedFields = {}


    ## Update the changed attribute fields in the database table.      
    def dbUpdateAttributes(self, project, actions):

        tableName = project.dbTableNames[self.dbTableName]
        updateString = self.history.getUpdateString(actions)

        if updateString:
            query =  ("UPDATE %s "
                      "SET %s "
                      "WHERE id=%d") % (tableName, updateString, self.id)

            res = project.executeQuery(query)

            if not res['isError']:
                print("Successfully updated the station attributes of station %s.") % self.name
            else:
                print res['msg']  


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

        ## The mapping of the network attributes to the database columns.
        attrMap = {};
        attrMap['name'] = 'name'
        attrMap['description'] = 'description'
        attrMap['type'] = 'type'

        # The allowed actions to be saved in the history.
        actionTypes = {};
        actionTypes['changeAttribute'] = 'Changed a station attribute.'

        ## The network action history.
        self.history = InventoryHistory(attrMap, actionTypes)

        ## The database table name.
        self.dbTableName = 'geom_network'



    ## The index and slicing operator.
    def __getitem__(self, name):
        return self.__dict__[name]


    ## The index and slicing operator.
    def __setitem__(self, name, value):
        action = {}
        action['type'] = 'changeAttribute'
        action['attrName'] = name
        action['dataBefore'] = self.__dict__[name]
        action['dataAfter'] = value

        self.__dict__[name] = value
        self.history.do(action)



    ## Add a station to the network. 
    def addStation(self, station):
        station.network = self.name
        self.stations[(station.name, station.location)] = station


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



    ## Write the network to the database.
    #
    #
    def write2Db(self, project):
        # Write the network data to the geom_network table.

        tableName = project.dbTableNames['geom_network']
        query =  ("INSERT IGNORE INTO %s "
                  "(name, description, type) "
                  "VALUES (%%s, %%s, %%s)") % tableName

        dbData = [(self.name,
                   self.description,
                   self.type)] 

        res = project.executeManyQuery(query, dbData)  # I'm using executeManyQuery to handle NULL values.

        if not res['isError']:
            print("Successfully wrote the network to the database.")
        else:
            print res['msg'] 


    ## Update the network database entry.    
    def updateDb(self, project):

        if not self.history.hasActions():
            # No actions to perform.
            return

        # Process the changed attributes of the station.
        curAction = self.history.fetchAction('changeAttribute')
        self.dbUpdateAttributes(project, curAction)

        # Process all other actions. 
        while(self.history.hasActions()):
            curAction = self.history.fetchAction()
            print "Processing action " + curAction




    ## Update the changed attribute fields in the database table.      
    def dbUpdateAttributes(self, project, actions):

        tableName = project.dbTableNames[self.dbTableName]
        updateString = self.history.getUpdateString(actions)

        if updateString:
            query =  ("UPDATE %s "
                      "SET %s "
                      "WHERE id=%d") % (tableName, updateString, self.id)

            res = project.executeQuery(query)

            if not res['isError']:
                print("Successfully updated the station attributes of network %s.") % self.name
            else:
                print res['msg']  



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








