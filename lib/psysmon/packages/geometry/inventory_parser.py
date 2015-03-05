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
The inventory parser module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains parser classes to read inventory data from files.
'''

import logging

from psysmon.packages.geometry.inventory import Inventory
from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Channel
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorComponent
from psysmon.packages.geometry.inventory import SensorComponentParameter
from psysmon.packages.geometry.inventory import RecorderStream
from obspy.core.utcdatetime import UTCDateTime

class InventoryXmlParser:
    '''
    Parse a pSysmon inventory XML file.
    '''
    def __init__(self):

        # the logger instance.
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

        # The required attributes which have to be present in the tags.
        self.required_attributes = {}
        self.required_attributes['inventory'] = ('name', )
        self.required_attributes['sensor'] = ('serial', )
        self.required_attributes['component'] = ('name', )
        self.required_attributes['recorder'] = ('serial', )
        self.required_attributes['stream'] = ('name', )
        self.required_attributes['network'] = ('name', )
        self.required_attributes['station'] = ('name', )
        self.required_attributes['channel'] = ('name', )

        # The required tags which have to be present in the inventory.
        self.required_tags = {}
        self.required_tags['sensor'] = ('model', 'producer')
        self.required_tags['component'] = ('description', 'component_parameter', )
        self.required_tags['component_parameter'] = ('start_time', 'end_time',
                                                     'sensitivity', 'sensitivity_units')
        self.required_tags['response_paz'] = ('type', 'units', 'A0_normalization_factor',
                                              'normalization_frequency')
        #self.required_tags['complex_zero'] = ('real_zero', 'imaginary_zero')
        #self.required_tags['complex_pole'] = ('real_pole', 'imaginary_pole')

        self.required_tags['recorder'] = ('type', 'description')
        self.required_tags['stream'] = ('label', )
        self.required_tags['stream_parameter'] = ('start_time', 'end_time', 'gain',
                                        'bitweight', 'bitweight_units')

        self.required_tags['network'] = ('description', 'type')
        self.required_tags['station'] = ('location', 'xcoord', 'ycoord', 'elevation',
                                        'coord_system', 'description')
        self.required_tags['channel'] = ('description', )
        self.required_tags['assigned_component'] = ('recorder_serial', 'recorder_stream',
                                                    'sensor_serial', 'sensor_component',
                                                    'start_time', 'end_time')



    def parse(self, filename, inventory_name = 'new xml inventory'):
        from lxml.etree import parse

        self.logger.debug("parsing file...\n")

        inventory = Inventory(inventory_name, type = 'xml')

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
        sensors = tree.findall('sensor')
        recorders = tree.findall('recorder')
        networks = tree.findall('network')

        # Process the sensors first.
        self.process_sensors(inventory, sensors)

        # Next process the recorders. These might depend on sensors.
        #self.process_recorders(inventory, recorders)

        # And last process the networks which might depend on recorders.
        #self.process_networks(inventory, networks)

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




    def process_sensors(self, inventory, sensors):
        ''' Process the extracted sensor tags.

        '''
        self.logger.debug("Processing the sensors.")
        for cur_sensor in sensors:
            sensor_content = self.parse_node(cur_sensor)

            if self.check_completeness(cur_sensor, sensor_content, 'sensor') is False:
                continue

            sensor_content.pop('component')
            sensor_to_add = Sensor(serial = cur_sensor.attrib['serial'], **sensor_content)
            inventory.add_sensor(sensor_to_add)

            components = cur_sensor.findall('component')
            self.process_components(sensor_to_add, components)


    def process_components(self, sensor, components):
        ''' Process the component nodes of a sensor.
        '''
        for cur_component in components:
            component_content = self.parse_node(cur_component)

            if self.check_completeness(cur_component, component_content, 'component') is False:
                continue

            component_content.pop('component_parameter')
            component_to_add = SensorComponent(name = cur_component.attrib['name'],
                                               **component_content)
            sensor.add_component(component_to_add)


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


    def process_sensors_OLD(self, inventory, station_node, station):
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
            if node_content.has_key(cur_key):
                continue
            else:
                missing_keys.append(cur_key)

        return missing_keys


    def check_completeness(self, node, content, node_type):
            missing_attrib = self.keys_complete(node.attrib, self.required_attributes[node_type])
            missing_keys = self.keys_complete(content, self.required_tags[node_type]);
            if not missing_keys and not missing_attrib:
                self.logger.debug(node_type + " xml content:")
                self.logger.debug("%s", content)
                return True
            else:
                self.logger.debug("Not all required fields present!\nMissing Keys:\n")
                self.logger.debug("%s", missing_keys)
                self.logger.debug("%s", missing_attrib)
                return False

