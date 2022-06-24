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
The inventory module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classed needed to build a pSysmon geometry 
inventory.
'''

from builtins import filter
from builtins import str
from builtins import object
import psysmon
from obspy.core.utcdatetime import UTCDateTime
from psysmon.core.error import PsysmonError
import pyproj
import warnings
import logging
from pubsub import pub

## The Inventory class.
#
class Inventory(object):

    ## The constructor.
    #
    # @param self The object pointer.
    # @param name The inventory name.
    def __init__(self, name, type = None):

        # The logger.
        self.logger = psysmon.get_logger(self)

        ## The name of the inventory.
        self.name = name

        ## The type of the inventory.
        #
        # Based on the source the inventory can be of the following types:
        # - xml
        # - db
        # - manual
        self.type = type

        ## The recorders contained in the inventory.
        self.recorders = []

        ## The sensors contained in the inventory and not assigned to a recorder.
        self.sensors = []

        ## The stations contained in the inventory and not assigned to a network.
        self.stations = []

        ## The networks contained in the inventory.
        self.networks = []


    def __str__(self):
        ''' Print the string representation of the inventory.
        '''
        out = "Inventory %s of type %s\n" % (self.name, self.type) 

        # Print the networks.
        out =  out + str(len(self.networks)) + " network(s) in the inventory:\n"
        out = out + "\n".join([net.__str__() for net in self.networks])

        # Print the recorders.
        out = out + '\n\n'
        out =  out + str(len(self.recorders)) + " recorder(s) in the inventory:\n"
        out = out + "\n".join([rec.__str__() for rec in self.recorders])

        return out



    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['name', 'type', 'recorders', 'networks'] 
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False


    ## Add a recorder to the inventory.
    def add_recorder(self, recorder):
        ''' Add a recorder to the inventory.

        Parameters
        ----------
        recorder : :class:`~psysmon.packages.geometery.inventory.Recorder`
            The recorder to add to the inventory.
        '''
        available_recorders = [(x.serial, x.type) for x in self.recorders]

        if (recorder.serial, recorder.type) not in available_recorders:
            self.recorders.append(recorder)
            recorder.set_parent_inventory(self)


    ## Remove a recorder from the inventory.
    def remove_recorder(self, position):
        pass

    ## Add a station to the inventory.
    def add_station(self, station):

        # If the network is found in the inventory, add it to the network.
        cur_net = self.get_network(station.network)
        if cur_net:
            cur_net.add_station(station)
            station.set_parent_inventory(self)
        else:
            self.logger.error("The network %s of station %s doesn't exist in the inventory.\nAdding it to the unassigned stations.", station.network, station.name)
            # Append the station to the unassigned stations list.
            self.stations.append(station)



    ## Add a sensor to the inventory.
    def add_sensor(self, sensor):

        for cur_recorder in self.recorders:
            if cur_recorder.serial == sensor.recorder_serial and cur_recorder.type == sensor.recorder_type:
                cur_recorder.add_sensor(sensor)
                if sensor in self.sensors:
                    self.sensors.remove(sensor)
                return

        # If no suitable recorder has been found, add it to the unassigned sensors list.
        self.sensors.append(sensor)
        self.sensors = list(set(self.sensors))
        sensor.recorder_Id = None
        sensor.set_parent_inventory(self)


    def add_network(self, network):
        ''' Add a new network to the database inventory.

        Parameters
        ----------
        network : :class:`psysmon.packages.geometry.inventory.Network`
            The network to add to the database inventory.
        '''
        available_networks = [x.name for x in self.networks]
        if network.name not in available_networks:
            self.networks.append(network)
            network.set_parent_inventory(self)
        else:
            self.logger.error('The network %s already exists in the inventory.', network.name)


    ## Remove a station from the inventory.
    def remove_station(self, position):
        pass

    ## Check the inventory for changed objects.
    def has_changed(self):
        for cur_recorder in self.recorders:
            if cur_recorder.has_changed:
                self.logger.debug('Recorder changed')
                return True

            for cur_sensor in cur_recorder.sensors:
                if cur_sensor.has_changed:
                    self.logger.debug('Sensor changed')
                    return True

        for cur_station in self.stations:
            if cur_station.has_changed:
                self.logger.debug('Station changed')
                return True

        return False



    ## Refresh the inventory networks.
    def refresh_networks(self):
        for cur_network in self.networks:
            cur_network.refresh_stations(self.stations)

    ## Refresh the inventory recorders.
    def refresh_recorders(self):
        for cur_recorder in self.recorders:
            cur_recorder.refresh_sensors()

        for cur_sensor in self.sensors:
            self.add_sensor(cur_sensor)


    ## Read the inventory from an XML file.
    def import_from_xml(self, filename):
        inventory_parser = InventoryXmlParser(self, filename)
        try:
            inventory_parser.parse()
        except PsysmonError as e:
            raise e

        self.type = 'xml'   


    def get_recorder(self, serial = None, type = None, id = None):
        ''' Get a recorder from the inventory.

        Parameters
        ----------
        serial : String
            The serial number of the recorder.

        type : String
            The recorder type.

        id : Integer
            The database id of the recorder.

        Returns
        -------
        recorder : List of :class:'~Recorder'
            The recorder(s) in the inventory matching the search criteria.
        '''
        recorder = self.recorders

        if serial is not None:
            recorder = [x for x in recorder if x.serial == serial]

        if type is not None:
            recorder = [x for x in recorder if x.type == type]

        if id is not None:
            recorder = [x for x in recorder if x.id == id]

        return recorder



    ## Get a sensor from the inventory.
    def get_sensor(self, rec_serial = None, sen_serial = None, sen_type = None,
                   rec_channel_name = None, channel_name = None, id = None,
                   label = None):
        ''' Get a sensor from the inventory.

        Parameters
        ----------
        rec_serial : String
            The serial number of the recorder.

        sen_serial : String
            The serial number of the sensor.

        sen_type : String
            The type of the sensor.

        rec_channel_name : String
            The recorder channel name of the sensor.

        channel_name : String
            The assigned channel name of the sensor.

        id : Integer
            The database id of the sensor.

        label : String
            The label of the sensor.
        '''
        if rec_serial is not None:
            recorder_2_process = [x for x in self.recorders if x.serial == rec_serial]
        else:
            recorder_2_process = self.recorders

        sensor = []
        for cur_recorder in recorder_2_process:
            sensor.extend(cur_recorder.get_sensor(serial = sen_serial, type = sen_type, rec_channel_name = rec_channel_name, channel_name = channel_name, id = id, label = label))
        return sensor


    ## Get a station from the inventory.
    def get_station(self, name = None, network = None, location = None,
                    id = None):
        ''' Get a station from the inventory.

        Parameters
        ----------
        name : String
            The name (code) of the station.

        network : String
            The name of the network of the station.

        location : String
            The location code of the station.

        id : Integer
            The database id of the station.
        '''
        if network is not None:
            network_2_process = [x for x in self.networks if x.name == network]
        else:
            network_2_process = self.networks

        station = []
        for cur_network in network_2_process:
            station.extend(cur_network.get_station(name = name, 
                                                   location = location,
                                                   id = id))
        return station



    ## Get a sensor from the inventory by id.
    def get_sensor_by_id(self, id):

        for cur_recorder in self.recorders:
            sensor_found = list(filter((lambda cur_sensor: cur_sensor.id==id), cur_recorder.sensors))

            if sensor_found:
                return sensor_found[0]

        return None

    ## Get a sensor from the inventory by label.
    def get_sensor_by_label(self, label):
        for cur_recorder in self.recorders:
            sensor_found = list(filter((lambda cur_sensor: cur_sensor.label==label), cur_recorder.sensors))

            if sensor_found:
                return sensor_found[0]

        return None


    ## Get a network form the inventory.
    def get_network(self, code = None):
        if code is None:
            return self.networks

        cur_network = [x for x in self.networks if x.name == code]
        if len(cur_network) == 1:
            return cur_network[0]
        elif len(cur_network) > 1:
            self.logger.error('Found more than one network with the same code %s in the inventory.', code)
            return cur_network
        else:
            return None


    @classmethod
    def from_db_inventory(cls, db_inventory):
        pass



class InventoryXmlParser(object):
    '''
    Parse a pSysmon inventory XML file.
    '''
    def __init__(self):

        # the logger instance.
        self.logger = psysmon.get_logger(self)

        # The required attributes which have to be present in the tags.
        self.required_attributes = {}
        self.required_attributes['inventory'] = ('name',)
        self.required_attributes['recorder'] = ('serial',)
        self.required_attributes['sensor_unit'] = ('label',)
        self.required_attributes['station'] = ('code',)
        self.required_attributes['network'] = ('code',)

        # The required tags which have to be present in the inventory.
        self.required_tags = {}
        self.required_tags['recorder'] = ('type', 'description')
        self.required_tags['sensor_unit'] = ('rec_channel_name', 'channel_name', 
                                        'sensor_serial', 'sensor_type')
        self.required_tags['channel_parameters'] = ('start_time', 'end_time', 
                                        'gain', 'bitweight', 'bitweight_units', 
                                        'sensitivity', 'sensitivity_units')
        self.required_tags['response_paz'] = ('type', 'units', 'A0_normalization_factor', 
                                             'normalization_frequency')
        self.required_tags['complex_zero'] = ('real_zero', 'imaginary_zero')
        self.required_tags['complex_pole'] = ('real_pole', 'imaginary_pole')
        self.required_tags['station'] = ('location', 'xcoord', 'ycoord', 'elevation', 
                                        'coord_system', 'description')
        self.required_tags['assigned_sensor_unit'] = ('sensor_unit_label', 'start_time', 'end_time')
        self.required_tags['network'] = ('description', 'type')



    def parse(self, filename):
        from lxml.etree import parse

        self.logger.debug("parsing file...\n")

        inventory = Inventory('new xml inventory', type = 'xml')

        # Parse the xml file passed as argument.
        tree = parse(filename)
        inventory_root = tree.getroot()

        # Check if the root element is of type inventory.
        if inventory_root.tag != 'inventory':
            return
        else:
            self.logger.debug("found inventory root tag\n")

        # Set the name of the inventory.
        inventory.name = inventory_root.attrib['name']

        # Get the recorders and stations of the inventory.
        recorders = tree.findall('recorder')
        networks = tree.findall('network')

        # First process the recorders.
        # For each recorder create a Recorder object, add the channels to it and 
        # finally add it to the inventory.
        self.process_recorders(inventory, recorders)

        self.process_networks(inventory, networks)  

        self.logger.debug("Success reading the XML file.")

        return inventory


    def export_xml(self, inventory, filename):
        ''' Export an inventory to xml file.
        '''
        from lxml import etree

        root = etree.Element('inventory', name = inventory.name)

        for cur_recorder in inventory.recorders:
            rec_element = etree.SubElement(root, 'recorder', serial = cur_recorder.serial)
            type = etree.SubElement(rec_element, 'type')
            type.text = cur_recorder.type
            description = etree.SubElement(rec_element, 'description')
            description.text = cur_recorder.description

            for cur_sensor in cur_recorder.sensors:
                sen_element = etree.SubElement(rec_element, 'sensor_unit', label = cur_sensor.label)
                rec_channel_name = etree.SubElement(sen_element, 'rec_channel_name')
                rec_channel_name.text = cur_sensor.rec_channel_name
                channel_name = etree.SubElement(sen_element, 'channel_name')
                channel_name.text = cur_sensor.channel_name
                sensor_serial = etree.SubElement(sen_element, 'sensor_serial')
                sensor_serial.text = cur_sensor.serial
                sensor_type = etree.SubElement(sen_element, 'sensor_type')
                sensor_type.text = cur_sensor.type

                for cur_parameter in cur_sensor.parameters:
                    par_element = etree.SubElement(sen_element, 'channel_parameters')
                    start_time = etree.SubElement(par_element, 'start_time')
                    if cur_parameter.start_time is not None:
                        start_time.text = cur_parameter.start_time.isoformat()
                    else:
                        start_time.text = ''
                    end_time = etree.SubElement(par_element, 'end_time')
                    if cur_parameter.end_time is not None:
                        end_time.text = cur_parameter.end_time.isoformat()
                    else:
                        end_time.text = ''
                    gain = etree.SubElement(par_element, 'gain')
                    gain.text = str(cur_parameter.gain)
                    bitweight = etree.SubElement(par_element, 'bitweight')
                    bitweight.text = str(cur_parameter.bitweight)
                    bitweight_units = etree.SubElement(par_element, 'bitweight_units')
                    bitweight_units.text = cur_parameter.bitweight_units
                    sensitivity = etree.SubElement(par_element, 'sensitivity')
                    sensitivity.text = str(cur_parameter.sensitivity)
                    sensitivity_units = etree.SubElement(par_element, 'sensitivity_units')
                    sensitivity_units.text = cur_parameter.sensitivity_units

                    paz_element = etree.SubElement(par_element, 'response_paz')
                    type = etree.SubElement(paz_element, 'type')
                    type.text = cur_parameter.tf_type
                    units = etree.SubElement(paz_element, 'units')
                    units.text = cur_parameter.tf_units
                    normalization_factor = etree.SubElement(paz_element, 'A0_normalization_factor')
                    normalization_factor.text = str(cur_parameter.tf_normalization_factor)
                    normalization_frequency = etree.SubElement(paz_element, 'normalization_frequency')
                    normalization_frequency.text = str(cur_parameter.tf_normalization_frequency)
                    for cur_zero in cur_parameter.tf_zeros:
                        zero = etree.SubElement(paz_element, 'complex_zero')
                        zero.text = str(cur_zero).replace('(', '').replace(')','')
                    for cur_pole in cur_parameter.tf_poles:
                        pole = etree.SubElement(paz_element, 'complex_pole')
                        pole.text = str(cur_pole).replace('(', '').replace(')', '')

        for cur_network in inventory.networks:
            net_element = etree.SubElement(root, 'network', code = cur_network.name)
            description = etree.SubElement(net_element, 'description')
            description.text = cur_network.description
            type = etree.SubElement(net_element, 'type')
            type.text = cur_network.type

            for cur_station in cur_network.stations:
                stat_element = etree.SubElement(net_element, 'station', code = cur_station.name)
                location = etree.SubElement(stat_element, 'location')
                location.text = cur_station.location
                xcoord = etree.SubElement(stat_element, 'xcoord')
                xcoord.text = str(cur_station.x)
                ycoord = etree.SubElement(stat_element, 'ycoord')
                ycoord.text = str(cur_station.y)
                elevation = etree.SubElement(stat_element, 'elevation')
                elevation.text = str(cur_station.z)
                coord_system = etree.SubElement(stat_element, 'coord_system')
                coord_system.text = cur_station.coord_system
                description = etree.SubElement(stat_element, 'description')
                description.text = cur_station.description

                for cur_sensor, cur_start_time, cur_end_time in cur_station.sensors:
                    sensor_element = etree.SubElement(stat_element, 'assigned_sensor_unit', )
                    sensor_unit_label = etree.SubElement(sensor_element, 'sensor_unit_label')
                    sensor_unit_label.text = cur_sensor.label
                    start_time = etree.SubElement(sensor_element, 'start_time')
                    if cur_start_time is not None:
                        start_time.text = cur_start_time.isoformat()
                    else:
                        start_time.text = ''

                    end_time = etree.SubElement(sensor_element, 'end_time')
                    if cur_end_time is not None:
                        end_time.text = cur_end_time.isoformat()
                    else:
                        end_time.text = ''

        # Write the xml string to a file.
        et = etree.ElementTree(root)
        et.write(filename, pretty_print = True, xml_declaration = True, encoding = 'UTF-8')
        #fid = open(filename, 'w')
        #fid.write(etree.tostring(root, pretty_print = True))
        #fid.close()



    ## Process the recorder element.
    def process_recorders(self, inventory, recorders):
        for cur_recorder in recorders:
            recorder_content = self.parse_node(cur_recorder)

            # Test the recorder tags for completeness.
            missing_attrib = self.keys_complete(cur_recorder.attrib, self.required_attributes['recorder'])
            missing_keys = self.keys_complete(recorder_content, self.required_tags['recorder']);
            if not missing_keys and not missing_attrib:
                self.logger.debug("recorder xml content:")
                self.logger.debug("%s", recorder_content)
            else:
                self.logger.debug("Not all required fields present!\nMissing Keys:\n")
                self.logger.debug("%s", missing_keys)
                self.logger.debug("%s", missing_attrib)
                continue

            # Create the Recorder instance.
            rec_2_add = Recorder(serial=cur_recorder.attrib['serial'], 
                               type = recorder_content['type'],
                               description = recorder_content['description']) 

            # Add the recorder to the inventory.
            inventory.add_recorder(rec_2_add)

            # Process the channels of the recorder.
            self.process_channels(cur_recorder, rec_2_add)



    ## Process the channel elements.      
    def process_channels(self, recorder_node, recorder):
        channels = recorder_node.findall('sensor_unit')
        for cur_channel in channels:
            channel_content = self.parse_node(cur_channel)

            missing_attrib = self.keys_complete(cur_channel.attrib, self.required_attributes['sensor_unit'])
            missing_keys = self.keys_complete(channel_content, self.required_tags['sensor_unit']);
            if not missing_keys and not missing_attrib:
                self.logger.debug("Adding sensor to recorder.")
                sensor2Add = Sensor(serial=channel_content['sensor_serial'],
                                    type=channel_content['sensor_type'],
                                    rec_channel_name=channel_content['rec_channel_name'],
                                    channel_name=channel_content['channel_name'],
                                    label=cur_channel.attrib['label']) 
                self.logger.debug("%s", sensor2Add.label)

                recorder.add_sensor(sensor2Add)

                # Process the channel parameters.
                self.process_channel_parameters(cur_channel, sensor2Add)


            else:
                self.logger.debug("Not all required fields present!\nMissing Keys:\n")
                self.logger.debug("%s", missing_keys)
                self.logger.debug("%s", missing_attrib)


    ## Process the channel_parameter elements.
    def process_channel_parameters(self, channel_node, sensor):
        channel_parameters = channel_node.findall('channel_parameters')
        for cur_parameter in channel_parameters:
            content = self.parse_node(cur_parameter)
            missing_keys = self.keys_complete(content, self.required_tags['channel_parameters'])
            if not missing_keys:
                self.logger.debug("Adding the channel parameters to the sensor")
                # Convert the time strings to UTC times.
                if content['start_time']:
                    start_time = UTCDateTime(content['start_time'])
                else:
                    start_time = None


                if content['end_time']:
                    end_time = UTCDateTime(content['end_time'])
                else:
                    end_time = None

                parameter2Add = SensorParameter(gain = float(content['gain']),
                                                bitweight = float(content['bitweight']),
                                                bitweight_units = content['bitweight_units'],
                                                sensitivity = float(content['sensitivity']),
                                                sensitivity_units = content['sensitivity_units'],
                                                start_time = start_time,
                                                end_time = end_time
                                                 )
                self.logger.debug('Processing PAZ of parameter %s.', parameter2Add)
                self.process_response_paz(cur_parameter, parameter2Add)


                sensor.add_parameter(parameter2Add)



    ## Process the response_paz elements.
    def process_response_paz(self, parameter_node, parameter):
        tf = parameter_node.findall('response_paz')
        for cur_tf in tf:
            content = self.parse_node(cur_tf)
            missing_keys = self.keys_complete(content, self.required_tags['response_paz'])
            if not missing_keys:
                self.logger.debug("Adding the tf to the parameter %s", parameter)
                parameter.set_transfer_function(content['type'], 
                                              content['units'],
                                              float(content['A0_normalization_factor']), 
                                              float(content['normalization_frequency']))

                self.process_complex_zero(cur_tf, parameter)
                self.process_complex_pole(cur_tf, parameter)

    ## Process the complex_zero elements.
    def process_complex_zero(self, tf_node, parameter):
        cz = tf_node.findall('complex_zero')
        for curCz in cz:
            self.logger.debug('Adding zero to the parameter %s', parameter)
            zero = curCz.text.replace(' ', '')
            parameter.tf_add_complex_zero(complex(zero))


    ## Process the complex_pole elements.
    def process_complex_pole(self, tf_node, parameter):
        cp = tf_node.findall('complex_pole')
        for cur_cp in cp:
            pole = cur_cp.text.replace(' ', '')
            parameter.tf_add_complex_pole(complex(pole))



    ## Process the station elements.
    def process_stations(self, inventory, network_node, network):
        stations = network_node.findall('station')
        for cur_station in stations:
            station_content = self.parse_node(cur_station)
            missing_attrib = self.keys_complete(cur_station.attrib, self.required_attributes['station'])
            missing_keys = self.keys_complete(station_content, self.required_tags['station'])

            if not missing_keys and not missing_attrib:
                station2Add = Station(name=cur_station.attrib['code'],
                                      location=station_content['location'],
                                      x=float(station_content['xcoord']),
                                      y=float(station_content['ycoord']),
                                      z=float(station_content['elevation']),
                                      coord_system=station_content['coord_system'],
                                      description=station_content['description'],
                                      network=network.name 
                                      )

                inventory.add_station(station2Add)

                self.process_sensors(inventory, cur_station, station2Add)


            else:
                self.logger.error("Not all required tags or attributes present.")
                self.logger.debug("%s", missing_keys)
                self.logger.debug("%s", missing_attrib)


    def process_sensors(self, inventory, station_node, station):
        sensors = station_node.findall('assigned_sensor_unit')
        for cur_sensor in sensors:
            sensor_content = self.parse_node(cur_sensor)

            missing_keys = self.keys_complete(sensor_content, self.required_tags['assigned_sensor_unit'])

            if not missing_keys: 
                # Find the sensor in the inventory.
                #sensor2Add = self.parent_inventory.getSensor(recSerial = sensor_content['recorder_serial'],
                #                                            senSerial = sensor_content['sensor_serial'],
                #                                            rec_channel_name = sensor_content['rec_channel_name'])
                self.logger.debug(sensor_content['sensor_unit_label'])
                sensor_2_add = inventory.get_sensor(label=sensor_content['sensor_unit_label'])
                self.logger.debug("%s", sensor_2_add)
                if sensor_2_add:
                    # Convert the time strings to UTC times.
                    if sensor_content['start_time']:
                        begin_time = UTCDateTime(sensor_content['start_time'])
                    else:
                        begin_time = None


                    if sensor_content['end_time']:
                        end_time = UTCDateTime(sensor_content['end_time'])
                    else:
                        end_time = None

                    for cur_sensor in sensor_2_add:
                        station.add_sensor(cur_sensor, 
                                           begin_time,
                                           end_time)
                else:
                    msg =  "Sensor to add with label '%s' not found in inventory.\nSkipping this sensor." % sensor_content['sensor_unit_label'], 
                    warnings.warn(msg)
            else:
                msg = "Not all required fields presents!\nMissing keys:\n"
                self.logger.debug("%s", msg)
                self.logger.debug("%s", missing_keys)


     ## Process the network element.
    def process_networks(self, inventory, networks):
        for cur_network in networks:
            content = self.parse_node(cur_network)

            # Test the recorder tags for completeness.
            missing_attrib = self.keys_complete(cur_network.attrib, self.required_attributes['network'])
            missing_keys = self.keys_complete(content, self.required_tags['network']);
            if not missing_keys and not missing_attrib:
                self.logger.debug("%s", content)
            else:
                self.logger.debug("Not all required fields present!\nMissing Keys:\n")
                self.logger.debug("%s", missing_keys)
                self.logger.debug("%s", missing_attrib)
                continue

            # Create the Recorder instance.
            net2Add = Network(name=cur_network.attrib['code'],
                              description=content['description'],
                              type=content['type'])

            # Add the network to the inventory.
            inventory.add_network(net2Add)

            self.process_stations(inventory, cur_network, net2Add)


    def get_node_text(self, xml_element, tag):
        node = xml_element.find(tag)
        if node is not None:
            return node.text
        else:
            return None

    def parse_node(self, xml_element):
        node_content = {}
        for cur_node in list(xml_element):
            node_content[cur_node.tag] = cur_node.text

        return node_content

    def keys_complete(self, node_content, required_keys):
        missing_keys = []
        for cur_key in required_keys:
            if cur_key in node_content:
                continue
            else:
                missing_keys.append(cur_key)

        return missing_keys





## The pSysmon recorder class.
# 
# A recorder is more or less the representation of a digitizer.@n
#     
class Recorder(object):

    ## The constructor.
    #
    # @param self The object pointer.
    # @param serial The recorder serial number.
    # @param type The recorder type.
    # @param id The recorder database id.
    def __init__(self, serial, type, description = None, id=None, parent_inventory=None):
        ## The recorder database id.
        # -1 if the recorder is not yet present in the database.
        self.id = id

        ## The recorder serial number.
        self.serial = serial

        ## The recorder type.
        self.type = type

        # The description of the recorder.
        self.description = description

        # Indicates if the attributes have been changed.
        self.has_changed = False

        # A list of Sensor instances related to the recorder.
        self.sensors = [];

        ## The parent inventory.
        self.parent_inventory = parent_inventory


    def __str__(self):
        ''' Returns a readable representation of the Recorder instance.
        '''
        out = 'id:\t%s\nserial:\t%s\ntype:\t%s\n%d sensor(s):\n' % (str(self.id), self.serial, self.type, len(self.sensors))
        return out


    def __setitem__(self, name, value):
        self.__dict__[name] = value
        self.has_changed = True 


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['id', 'serial', 'type', 'description', 'has_changed',
                                  'sensors']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False




    def set_parent_inventory(self, parent_inventory):
        ''' Set the parent_inventory attribute.

        Also update the parent inventory of all children.

        Parameters
        ----------
        parent_inventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parent_inventory = parent_inventory
        for cur_sensor in self.sensors:
            cur_sensor.set_parent_inventory(parent_inventory)

    ## Add a sensor to the recorder.
    def add_sensor(self, sensor):
        if sensor not in self.sensors:
            self.sensors.append(sensor)
            sensor.parent_recorder = self
            sensor.set_parent_inventory(self.parent_inventory)


    def pop_sensor(self, sensor):
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
            sensor.parent_recorder = None
            return self.sensors.pop(self.sensors.index(sensor))
        else:
            return None


    def get_sensor(self, serial = None, type = None, rec_channel_name = None, channel_name = None, id = None, label = None):
        ''' Get a sensor from the recorder.

        Parameters
        ----------
        serial : String
            The serial number of the sensor.

        type : String
            The type of the sensor.

        rec_channel_name : String
            The recorder channel name of the sensor.

        channel_name : String
            The assigned channel name of the sensor.

        label : String
            The label of the sensor.
        '''
        sensor = self.sensors

        if serial is not None:
            sensor = [x for x in sensor if x.serial == serial]

        if type is not None:
            sensor = [x for x in sensor if x.type == type]

        if rec_channel_name is not None:
            sensor = [x for x in sensor if x.rec_channel_name == rec_channel_name]

        if channel_name is not None:
            sensor = [x for x in sensor if x.channel_name == channel_name]

        if id is not None:
            sensor = [x for x in sensor if x.id == id]

        if label is not None:
            sensor = [x for x in sensor if x.label == label]

        return sensor



    ## Refresh the sensor list.
    #
    # Check the association of the stations to the network. 
    # Remove stations that are no longer linked to the network.
    def refreshSensors(self, sensors=None):
        # Remove invalid stations from the network.
        for cur_sensor in self.sensors:
            if cur_sensor.recorder_serial != self.serial or cur_sensor.recorder_type != self.type:
                self.sensors.remove(cur_sensor)
                self.parent_inventory.add_sensor(cur_sensor)


        #for cur_station in stations:
        #    if cur_station.network == self.name:
        #        self.parent_inventory.add_station(cur_station)
        #        stations.remove(cur_station)




## The sensor class.
#
# 
class Sensor(object):

    ## The constructor.
    #
    #
    def __init__(self, serial, type, 
                 rec_channel_name, channel_name, label, id=None, 
                 parent_recorder=None):
        # The logger instance.
        self.logger = psysmon.get_logger(self)

        ## The database id of the sensor.
        self.id = id

        ## The sensor label specified by the user.
        self.label = label

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
        # The rec_channel_name is used to map the raw data files to a common channel 
        # name named by the channel_name attribute.
        self.rec_channel_name = rec_channel_name

        ## The channel name.
        # 
        # The channel name is the actual name used by pSysmon to work with the 
        # data of the sensor.
        self.channel_name = channel_name


        ## The sensor parameters.
        # The sensor paramters are stored in a list with the start and end time 
        # during which these paramters have been valid.
        self.parameters = []


        # The parent recorder.
        self.parent_recorder = parent_recorder


        # The inventory containing this sensor.
        if self.parent_recorder is not None:
            self.parent_inventory = parent_recorder.parent_inventory
        else:
            self.parent_inventory = None

        # Indicates if the attributes have been changed.
        self.has_changed = False


    def __getattr__(self, attrname):
        ''' Handle call of attributes which are derived from the parent recorder.
        '''
        if attrname == 'recorder_id':
            return self.parent_recorder.id
        elif attrname == 'recorder_serial':
            return self.parent_recorder.serial
        elif attrname == 'recorder_type':
            return self.parent_recorder.type
        else:
            raise AttributeError(attrname)


    def __setitem__(self, name, value):
        self.__dict__[name] = value
        self.has_changed = True
        self.logger.debug('Changing attribute %s of sensor %d', name, self.id)

        # Send an inventory update event.
        msgTopic = 'inventory.update.sensor'
        msg = (self, name, value)
        pub.sendMessage(msgTopic, msg)


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['id', 'label', 'serial', 'type', 'rec_channel_name',
                                  'channel_name', 'has_changed', 'parameters']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False


    def set_parent_inventory(self, parent_inventory):
        ''' Set the parent_inventory attribute.

        Parameters
        ----------
        parent_inventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parent_inventory = parent_inventory


    def add_parameter(self, parameter):
        ''' Add a sensor paramter instance to the sensor.

        Parameters
        ----------
        parameter : :class:`SensorParameter`
            The sensor parameter instance to be added.
        '''
        self.logger.debug('Adding parameter.')
        if parameter not in self.parameters:
            self.parameters.append(parameter)


    def get_parameter(self, start_time = None, end_time = None):
        ''' Get a sensor from the recorder.

        Parameters
        ----------

        '''
        parameter = self.parameters

        if start_time is not None:
            start_time = UTCDateTime(start_time)
            parameter = [x for x in parameter if x.end_time is None or x.end_time > start_time]

        if end_time is not None:
            end_time = UTCDateTime(end_time)
            parameter = [x for x in parameter if x.start_time is None or x.start_time < end_time]

        return parameter



    ## Change the sensor deployment start time.
    #
    # 
    def change_parameter_start_time(self, position, start_time):
        msg = ''    
        cur_row = self.parameters[position]

        if not isinstance(start_time, UTCDateTime):
            try:
                start_time = UTCDateTime(start_time)
            except:
                start_time = cur_row[1]
                msg = "The entered value is not a valid time."


        if not cur_row[2] or start_time < cur_row[2]:
            self.parameters[position] = (cur_row[0], start_time, cur_row[2])
            cur_row[0]['start_time'] = start_time
        else:
            start_time = cur_row[1]
            msg = "The start-time has to be smaller than the begin time."

        return (start_time, msg)


    ## Change the sensor deployment start time.
    #
    # 
    def change_parameter_end_time(self, position, end_time):
        msg = ''    
        cur_row = self.parameters[position]

        if end_time == 'running':
            self.parameters[position] = (cur_row[0], cur_row[1], None)
            cur_row[0]['end_time'] = None
            return(end_time, msg)

        if not isinstance(end_time, UTCDateTime):
            try:
                end_time = UTCDateTime(end_time)
            except:
                end_time = cur_row[2]
                msg = "The entered value is not a valid time."


        if end_time:
            if not cur_row[1] or end_time > cur_row[1]:
                self.parameters[position] = (cur_row[0], cur_row[1], end_time)
                cur_row[0]['end_time'] = end_time
                # Send an inventory update event.
                #msgTopic = 'inventory.update.sensorParameterTime'
                #msg = (cur_row[0], 'time', (self, cur_row[0], cur_row[1], end_time))
                #pub.sendMessage(msgTopic, msg)
            else:
                end_time = cur_row[2]
                msg = "The end-time has to be larger than the begin time."

        return (end_time, msg)





## The sensor parameter class.
#
class SensorParameter(object):
    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, gain, bitweight, bitweight_units, sensitivity, 
                 sensitivity_units, start_time, end_time, tf_type=None, 
                 tf_units=None, tf_normalization_factor=None, 
                 tf_normalization_frequency=None, tf_poles = None, tf_zeros = None,
                 id=None, parent_sensor = None):
        # The logger instance.
        self.logger = psysmon.get_logger(self)

        ## The sensor gain.
        self.gain = gain

        ## The sensor bitweight.
        self.bitweight = bitweight

        ## The units of the bitweight.
        self.bitweight_units = bitweight_units

        ## The sensor sensitivity.
        self.sensitivity = sensitivity

        ## The units of the sensitivity.
        self.sensitivity_units = sensitivity_units

        ## The transfer function type.
        # - displacement
        # - velocity
        # - acceleration
        self.tf_type = tf_type

        ## The transfer function units.
        self.tf_units = tf_units

        ## The transfer function normalization factor.
        self.tf_normalization_factor = tf_normalization_factor

        ## The transfer function normalization factor frequency.
        self.tf_normalization_frequency = tf_normalization_frequency

        ## The id of the sensor paramteer instance.
        self.id = id 

        ## The transfer function as PAZ.
        if tf_poles is None:
            tf_poles = []

        if tf_zeros is None:
            tf_zeros = []

        self.tf_poles = tf_poles
        self.tf_zeros = tf_zeros

        # The start_time from which the parameters are valid.
        self.start_time = start_time

        # The end time up to which the parameters are valid.
        self.end_time = end_time

        # The parent sensor holding the parameter.
        self.parent_sensor = parent_sensor

        # The inventory in which the parameter is contained.
        if self.parent_sensor is not None:
            self.parent_inventory = self.parent_sensor.parent_inventory
        else:
            self.parent_inventory = None

        # Indicates if the attributes have been changed.
        self.has_changed = False


    def __getattr__(self, attrname):
        ''' Handle call of attributes which are derived from the parent recorder.
        '''
        if attrname == 'sensor_id':
            if self.parent_sensor is not None:
                return self.parent_sensor.id
            else:
                return None
        else:
            raise AttributeError(attrname)


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['gain', 'bitweight', 'bitweight_units', 'sensitivity', 'tf_type',
                                  'tf_units', 'tf_normalization_factor', 'tf_normalization_frequency',
                                  'id', 'tf_poles', 'tf_zeros', 'start_time', 'end_time',
                                  'has_changed']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False


    def set_transfer_function(self, tf_type, tf_units, tf_normalization_factor, 
                            tf_normalization_frequency):
        ''' Set the transfer function parameters.

        '''
        self.tf_type = tf_type
        self.tf_units = tf_units
        self.tf_normalization_factor = tf_normalization_factor
        self.tf_normalization_frequency = tf_normalization_frequency


    def tf_add_complex_zero(self, zero):
        ''' Add a complex zero to the transfer function PAZ.

        '''
        self.logger.debug('Adding zero %s to parameter %s.', zero, self)
        self.logger.debug('len(self.tf_zeros): %s', len(self.tf_zeros))
        self.tf_zeros.append(zero)
        self.logger.debug('len(self.tf_zeros): %s', len(self.tf_zeros))

    def tf_add_complex_pole(self, pole):
        ''' Add a complec pole to the transfer function PAZ.

        '''
        self.tf_poles.append(pole)



## The station class.
#
class Station(object):

    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, name, location, x, y, z, parent_network=None, coord_system=None, description=None, network=None, id=None):

        # The logger instance.
        self.logger = psysmon.get_logger(self)

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
        self.x = float(x)

        ## The y coordinate of the station location.
        #
        # The coordinate system used is a right handed coordinate system with 
        # x pointing in the East direction, y pointing in the North direction and 
        # z pointing upwards.@n 
        # Depending on the coordinate system used x and y can also represent 
        # longitude and latitude.
        self.y = float(y)

        ## The z coordinate of the station location.
        #
        # The coordinate system used is a right handed coordinate system with 
        # x pointing in the East direction, y pointing in the North direction and 
        # z pointing upwards.@n 
        # Depending on the coordinate system used x and y can also represent 
        # longitude and latitude.
        self.z = float(z)

        ## The coordinate system in which the x/y coordinates are given.
        # 
        # The coord_system string should be a valid EPSG code.@n 
        # See http://www.epsg-registry.org/ to find your EPSG code.
        self.coord_system = coord_system

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

        # The network containing this station.
        self.parent_network = parent_network

        # The inventory containing this station.
        self.parent_inventory = None

        if self.parent_network is not None:
            self.parent_inventory = self.parent_network.parent_inventory

        # Indicates if the attributes have been changed.
        self.has_changed = False



    def __setitem__(self, name, value):
        self.logger.debug("Setting the %s attribute to %s.", name, value)
        self.__dict__[name] = value
        self.has_changed = True


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['id', 'name', 'location', 'description', 'x', 'y', 'z',
                                  'coord_system', 'sensors', 'has_changed']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    self.logger.error('Attribute %s not matching %s != %s.', cur_attribute, str(getattr(self, cur_attribute)), str(getattr(other, cur_attribute)))
                    return False

            return True
        else:
            return False


    def get_scnl(self):
        scnl = []
        for cur_sensor, start_time, end_time in self.sensors:
            cur_scnl = (self.name, cur_sensor.channel_name, self.network, self.location)
            if cur_scnl not in scnl:
                scnl.append(cur_scnl)

        return scnl


    def get_snl(self):
        return (self.name, self.network, self.location)


    def get_snl_string(self):
        return str.join(':', self.get_snl())



    def set_parent_inventory(self, parent_inventory):
        ''' Set the parent_inventory attribute.

        Also update the parent inventory of all children.

        Parameters
        ----------
        parent_inventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parent_inventory = parent_inventory
        for cur_sensor, begin_time, end_time in self.sensors:
            cur_sensor.set_parent_inventory(self.parent_inventory) 


    def get_lon_lat(self):
        '''
        Return the coordinate system as WGS84 longitude latitude tuples.
        '''
        # TODO: Add a check for valid epsg string.

        dest_sys = "epsg:4326"

        if self.coord_system == dest_sys:
            return(self.x, self.y)

        src_proj = pyproj.Proj(init=self.coord_system)
        dst_proj = pyproj.Proj(init=dest_sys) 


        lon, lat = pyproj.transform(src_proj, dst_proj, self.x, self.y)
        self.logger.debug('Converting from "%s" to "%s"', src_proj.srs, dst_proj.srs)
        return (lon, lat)


    def add_sensor(self, sensor, start_time, end_time):
        ''' Add a sensor to the station.

        Parameters
        ----------
        sensor : :class:`Sensor`
            The :class:`Sensor` instance to be added to the station.

        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time from which on the sensor has been operating at the station.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time up to which the sensor has been operating at the station. "None" if the station is still running.
        '''
        if not isinstance(start_time, UTCDateTime):
            if start_time is not None:
                start_time = UTCDateTime(start_time)
            else:
                start_time = None

        if not isinstance(end_time, UTCDateTime):
            if end_time is not None:
                end_time = UTCDateTime(end_time)
            else:
                end_time = None

        self.sensors.append((sensor, start_time, end_time))
        self.has_changed = True
        #sensor.set_parent_inventory(self.parent_inventory)


    def remove_sensor(self, sensor):
        ''' Remove a sensor from the station.

        Parameters
        ----------
        sensor : tuple (:class:`Sensor`, :class:`~obspy.core.utcdatetime.UTCDateTime`, :class:`~obspy.core.utcdatetime.UTCDateTime`) 
            The sensor to be removed from the station.
        '''
        self.logger.debug("Removing sensor ")
        self.logger.debug("%s", sensor)

        #if sensor not in self.sensors:
        
        # Remove the sensor from the sensors list.
        #self.sensors.pop(self.sensors.index(sensor))


    def get_sensor(self, serial = None, type = None, rec_channel_name = None, channel_name = None, id = None, label = None, start_time = None, end_time = None):
        ''' Get a sensor from the recorder.

        Parameters
        ----------
        serial : String
            The serial number of the sensor.

        type : String
            The type of the sensor.

        rec_channel_name : String
            The recorder channel name of the sensor.

        channel_name : String
            The assigned channel name of the sensor.

        label : String
            The label of the sensor.
        '''
        sensor = self.sensors

        if serial is not None:
            sensor = [x for x in sensor if x[0].serial == serial]

        if type is not None:
            sensor = [x for x in sensor if x[0].type == type]

        if rec_channel_name is not None:
            sensor = [x for x in sensor if x[0].rec_channel_name == rec_channel_name]

        if channel_name is not None:
            sensor = [x for x in sensor if x[0].channel_name == channel_name]

        if id is not None:
            sensor = [x for x in sensor if x[0].id == id]

        if label is not None:
            sensor = [x for x in sensor if x[0].label == label]

        if start_time is not None:
            start_time = UTCDateTime(start_time)
            sensor = [x for x in sensor if x[2] is None or x[2] > start_time]

        if end_time is not None:
            end_time = UTCDateTime(end_time)
            sensor = [x for x in sensor if x[1] is None or x[1] < end_time]

        return sensor



    def change_sensor_start_time(self, sensor, start_time):
        ''' Change the sensor deployment start time

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor which should be changed.

        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime or String
            A :class:`~obspy.core.utcdatetime.UTCDateTime` instance or a data-time string which can be used by :class:`~obspy.core.utcdatetime.UTCDateTime`.
        '''
        sensor_2_change = [(s, b, e, k) for k, (s, b, e) in enumerate(self.sensors) if s == sensor]

        if sensor_2_change:
            sensor_2_change = sensor_2_change[0]
            position = sensor_2_change[3]
        else:
            msg = 'The sensor can''t be found in the station.'
            return (None, msg)

        msg = ''    


        if not isinstance(start_time, UTCDateTime):
            try:
                start_time = UTCDateTime(start_time)
            except:
                start_time = sensor_2_change[2]
                msg = "The entered value is not a valid time."


        if not sensor_2_change[2] or (sensor_2_change[2] and start_time < sensor_2_change[2]):
            self.sensors[position] = (sensor_2_change[0], start_time, sensor_2_change[2])
            # Send an inventory update event.

        else:
            start_time = sensor_2_change[1]
            msg = "The end-time has to be larger than the begin time."

        return (start_time, msg)



    def change_sensor_end_time(self, sensor, end_time):
        ''' Change the sensor deployment end time

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor which should be changed.

        end_time : String
            A data-time string which can be used by :class:`~obspy.core.utcdatetime.UTCDateTime`.
        '''
        sensor_2_change = [(s, b, e, k) for k, (s, b, e) in enumerate(self.sensors) if s == sensor]

        if sensor_2_change:
            sensor_2_change = sensor_2_change[0]
            position = sensor_2_change[3]
        else:
            msg = 'The sensor can''t be found in the station.'
            return (None, msg)

        msg = ''    

        if end_time == 'running':
            self.sensors[position] = (sensor_2_change[0], sensor_2_change[1], None)
            return(end_time, msg)

        if not isinstance(end_time, UTCDateTime):
            try:
                end_time = UTCDateTime(end_time)
            except:
                end_time = sensor_2_change[2]
                msg = "The entered value is not a valid time."


        if not sensor_2_change[1] or end_time > sensor_2_change[1]:
            self.sensors[position] = (sensor_2_change[0], sensor_2_change[1], end_time)
        else:
            end_time = sensor_2_change[2]
            msg = "The end-time has to be larger than the begin time."

        return (end_time, msg)


    def get_unique_channel_names(self):
        channel_names = []

        for cur_sensor, start, end in self.sensors:
            if cur_sensor.channel_name not in channel_names:
                channel_names.append(cur_sensor.channel_name)

        return channel_names




## The network class.
class Network(object):

    def __init__(self, name, description=None, type=None, parent_inventory=None):
        # The logger instance.
        self.logger = psysmon.get_logger(self)

        ## The parent inventory.
        self.parent_inventory = parent_inventory

        ## The network name (code).
        self.name = name

        ## The network description.
        self.description = description

        ## The network type.
        self.type = type

        ## The stations contained in the network.
        self.stations = []

        # Indicates if the attributes have been changed.
        self.has_changed = False


    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        self.__dict__[attr] = value

        if attr == 'name' and 'stations' in self.__dict__:
            for cur_station in self.stations:
                # Set the station network value using the key to trigger the
                # change notification of the station.
                cur_station.network = value

        self.__dict__['has_changed'] = True


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['name', 'type', 'description', 'has_changed', 'stations'] 
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False


    def set_parent_inventory(self, parent_inventory):
        ''' Set the parent_inventory attribute.

        Also update the parent inventory of all children.

        Parameters
        ----------
        parent_inventory : :class:`Inventory`
            The new parent inventory of the station.
        '''
        self.parent_inventory = parent_inventory

        for cur_station in self.stations:
            cur_station.set_parent_inventory(self.parent_inventory)


    def add_station(self, station):
        ''' Add a station to the network.

        Parameters
        ----------
        station : :class:`Station`
            The station instance to add to the network.
        '''
        available_sl = [(x.name, x.location) for x in self.stations]
        if((station.name, station.location) not in available_sl):
            station.network = self.name
            self.stations.append(station)
            station.set_parent_inventory(self.parent_inventory)
            return station
        else:
            self.logger.error("The station with SL code %s is already in the network.", x.name + ':' + x.location)
            return None


    def get_station(self, name = None, location = None, id = None):
        ''' Get a station from the network.

        Parameters
        ----------
        name : String
            The name (code) of the station.

        location : String
            The location code of the station.

        id : Integer
            The database id of the station.
        '''
        station = self.stations

        if name is not None:
            station = [x for x in station if x.name == name]

        if location is not None:
            station = [x for x in station if x.location == location]

        if id is not None:
            station = [x for x in station if x.id == id]

        return station


