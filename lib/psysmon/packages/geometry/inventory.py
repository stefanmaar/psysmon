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

import itertools
import psysmon
from obspy.core.utcdatetime import UTCDateTime
from psysmon.core.error import PsysmonError
from mpl_toolkits.basemap import pyproj
import warnings
import logging
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub

class Inventory(object):

    def __init__(self, name, type = None):
        ''' Initialize the instance.

        Parameters
        ----------
        name : String
            The name of the inventory.

        type : String
            The type of the inventory.
        '''

        # The logger.
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

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

        ## The sensors contained in the inventory.
        self.sensors = []

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


    def add_recorder(self, recorder):
        ''' Add a recorder to the inventory.

        Parameters
        ----------
        recorder : :class:`Recorder`
            The recorder to add to the inventory.
        '''
        added_recorder = None

        if not self.get_recorder(serial = recorder.serial):
            self.recorders.append(recorder)
            recorder.parent_inventory = self
            added_recorder = recorder
        else:
            self.logger.warning('The recorder with serial %s already exists in the inventory.',
                    recorder.serial)

        return added_recorder


    def remove_recorder(self):
        ''' Remove a recorder from the inventory.
        '''
        pass



    def add_station(self, station_to_add):
        ''' Add a station to the inventory.

        Parameters
        ----------
        station_to_add : :class:`Station`
            The station to add to the inventory.
        '''
        added_station = None

        # If the network is found in the inventory, add it to the network.
        cur_net = self.get_network(name = station_to_add.network)
        if len(cur_net) == 1:
            cur_net = cur_net[0]
            added_station = cur_net.add_station(station_to_add)
        elif len(cur_net) > 1:
            self.logger.error("Multiple networks found with the same name. Don't know how to proceed.")
        else:
            self.logger.error("The network %s of station %s doesn't exist in the inventory.\n", station_to_add.network, station_to_add.name)

        return added_station



    def remove_station(self, snl):
        ''' Remove a station from the inventory.

        Parameters
        ----------
        scnl : tuple (String, String, String)
            The SNL code of the station to remove from the inventory.
        '''
        removed_station = None

        cur_net = self.get_network(snl[1])

        if cur_net is not None:
            removed_station = cur_net.remove_station(name = snl[0], location = snl[2])

        return removed_station



    def add_sensor(self, sensor_to_add):
        ''' Add a sensor to the inventory.

        Parameters
        ----------
        sensor_to_add : :class:`Sensor`
            The sensor to add to the inventory.
        '''
        added_sensor = None
        if not self.get_sensor(serial = sensor_to_add.serial,
                               component = sensor_to_add.component):
            self.sensors.append(sensor_to_add)
            sensor_to_add.parent_inventory = self
            added_sensor = sensor_to_add
        else:
            self.logger.warning('The sensor with serial %s and component %s already exists in the inventory.',
                    sensor_to_add.serial, sensor_to_add.component)

        return added_sensor


    def remove_sensor(self):
        ''' Remove a sensor from the inventory.
        '''
        pass


    def add_network(self, network):
        ''' Add a new network to the database inventory.

        Parameters
        ----------
        network : :class:`Network`
            The network to add to the database inventory.
        '''
        added_network = None

        if not self.get_network(name = network.name):
            self.networks.append(network)
            network.parent_inventory = self
            added_network = network
        else:
            self.logger.warning('The network %s already exists in the inventory.', network.name)

        return added_network



    def remove_network(self, name):
        ''' Remove a network from the inventory.

        Parameters
        ----------
        name : String
            The name of the network to remove.
        '''
        removed_network = None

        net_2_remove = [x for x in self.networks if x.name == name]

        if len(net_2_remove) == 1:
            self.networks.remove(net_2_remove[0])
            removed_network = net_2_remove[0]
        else:
            # This shouldn't happen.
            self.logger.error('Found more than one network with the name %s.', name)

        return removed_network


    def has_changed(self):
        ''' Check if any element in the inventory has been changed.
        '''
        for cur_recorder in self.recorders:
            if cur_recorder.has_changed:
                self.logger.debug('Recorder changed')
                return True

            for cur_sensor in cur_recorder.sensors:
                if cur_sensor.has_changed:
                    self.logger.debug('Sensor changed')
                    return True

        for cur_network in self.networks:
            if cur_network.has_changed:
                self.logger.debug('Network changed.')
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


    def get_recorder(self, **kwargs):
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
        ret_recorder = self.recorders

        valid_keys = ['serial', 'type', 'id']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_recorder = [x for x in ret_recorder if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_recorder



    def get_sensor(self, **kwargs):
        ''' Get a sensor from the inventory.

        Parameters
        ----------
        serial : String
            The serial number of the sensor.

        type : String
            The type of the sensor.

        label : String
            The label of the sensor

        id : Integer
            The database id of the sensor.
        '''
        ret_sensor = self.sensors

        valid_keys = ['serial', 'type', 'component', 'id']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_sensor = [x for x in ret_sensor if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_sensor


    def get_station(self, **kwargs):
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
        ret_station = list(itertools.chain.from_iterable([x.stations for x in self.networks]))

        valid_keys = ['name', 'network', 'location', 'id']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_station = [x for x in ret_station if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_station



    def get_network(self, **kwargs):
        ''' Get a network from the inventory.

        Parameters
        ----------
        name : String
            The name of the network.

        type : String
            The type of the network.
        '''
        ret_network = self.networks

        valid_keys = ['name', 'type']
        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_network = [x for x in ret_network if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_network


    @classmethod
    def from_db_inventory(cls, db_inventory):
        pass



class Recorder(object):
    ''' A seismic data recorder.
    '''

    def __init__(self, serial, type, description = None, id=None, parent_inventory=None,
            author_uri = None, agency_uri = None, creation_time = None):
        ''' Initialize the instance.

        '''
        ## The recorder database id.
        self.id = id

        ## The recorder serial number.
        self.serial = serial

        ## The recorder type.
        self.type = type

        # The description of the recorder.
        self.description = description

        # Indicates if the attributes have been changed.
        self.has_changed = False

        # A list of Stream instances related to the recorder.
        self.streams = [];

        ## The parent inventory.
        self.parent_inventory = parent_inventory

        # The author.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);


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
                                  'streams']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False



    def add_stream(self, cur_stream):
        ''' Add a stream to the recorder.

        Parameters
        ----------
        stream : :class:`Stream`
            The stream to add to the recorder.
        '''
        added_stream = None
        if cur_stream not in self.streams:
            self.streams.append(cur_stream)
            cur_stream.parent_recorder = self
            added_stream = cur_stream

        return added_stream


    def pop_stream(self, **kwargs):
        ''' Remove a stream from the recorder.

        Parameters
        ----------
        name : String
            The name of the stream.

        label : String
            The label of the stream.

        agency_uri : String
            The agency_uri of the stream.

        author_uri : string
            The author_uri of the stream.

        Returns
        -------
        streams_popped : List of :class:`Stream`
            The removed streams.
        '''
        streams_popped = []
        streams_to_pop = self.get_stream(**kwargs)

        for cur_stream in streams_to_pop:
            cur_stream.parent_recorder = None
            streams_popped.append(self.streams.pop(self.streams.index(cur_stream)))

        return streams_popped


    def get_stream(self, **kwargs):
        ''' Get a stream from the recorder.

        Parameters
        ----------
        name : String
            The name of the stream.

        label : String
            The label of the stream.

        agency_uri : String
            The agency_uri of the stream.

        author_uri : string
            The author_uri of the stream.
        '''
        ret_stream = self.streams

        valid_keys = ['name', 'label', 'agency_uri', 'author_uri']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_stream = [x for x in ret_stream if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_stream



class RecorderStream(object):
    ''' A digital stream of a data recorder.
    '''

    def __init__(self, name, label,
                 gain = None, bitweight = None, bitweight_units = None,
                 id = None, agency_uri = None, author_uri = None,
                 creation_time = None, parent_recorder = None):
        ''' Initialization of the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The database id of the stream.
        self.id = id

        # The name of the stream.
        self.name = name

        # The label of the stream.
        self.label = label

        # The gain of the stream.
        self.gain = gain

        # The bitweight of the stream.
        self.bitweight = bitweight

        # The bitweight units of the stream.
        self.bitweight_units = bitweight_units

        # The author.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);

        # The parent recorder holding the stream.
        self.parent_recorder = parent_recorder

        # Indicates if the attributes have been changed.
        self.has_changed = False

        # A list of tuples of sensors recorded by the stream.
        # The tuple is: (sensor, start_time, end_time).
        self.sensors = []

    @property
    def parent_inventory(self):
        if self.parent_recorder is not None:
            return self.parent_recorder.parent_inventory
        else:
            return None


    def __setitem__(self, name, value):
        self.__dict__[name] = value
        self.has_changed = True

        # Send an inventory update event.
        msgTopic = 'inventory.update.stream'
        msg = (self, name, value)
        pub.sendMessage(msgTopic, msg)


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['id', 'name', 'label', 'gain',
                    'bitweight', 'bitweight_units', 'sensors', 'has_changed']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False


    def add_sensor(self, sensor_serial, sensor_component, start_time, end_time):
        ''' Add a sensor to the stream.

        The sensor with specified sensor_serial and sensor_type is searched
        in the parent inventory and if available, the sensor is added to
        the stream for the specified time-span.

        Parameters
        ----------
        sensor_serial : String
            The serial number of the sensor.

        sensor_type : String
            The type of the sensor.

        sensor_component : String
            The component of the sensor.

        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time from which on the sensor has been operating at the station.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time up to which the sensor has been operating at the station. "None" if the station is still running.
        '''
        if self.parent_inventory is None:
            raise RuntimeError('The stream needs to be part of an inventory before a sensor can be added.')

        cur_sensor = self.parent_inventory.get_sensor(serial = sensor_serial,
                                                      component = sensor_component)
        if not cur_sensor:
            self.logger.error('The specified sensor (serial = %s, component = %s) was not found in the inventory.',
                              sensor_serial,
                              sensor_component)
        elif len(cur_sensor) == 1:
            added_sensor = None

            cur_sensor = cur_sensor[0]

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

            if self.get_sensor(start_time = start_time,
                               end_time = end_time,
                               serial = sensor_serial,
                               component = sensor_component):
                # The sensor is already assigned to the station for this timespan.
                if end_time is not None:
                    end_string = end_time.isoformat
                else:
                    end_string = 'running'

                self.logger.error('The sensor (serial: %s,  component: %s) is already deployed during the specified timespan from %s to %s.', sensor_serial, sensor_component, start_time.isoformat, end_string)
            else:
                self.sensors.append(TimeBox(item = cur_sensor,
                                            start_time = start_time,
                                            end_time = end_time))
                self.has_changed = True
                added_sensor = cur_sensor
        else:
            self.logger.error("Got more than one sensor with serial=%s and component = %s. Only one sensor with a serial-component combination should be in the inventory. Don't know how to proceed.", 
                               sensor_serial, sensor_component)

        return added_sensor


    def remove_sensor(self, sensor):
        ''' Remove a sensor from the stream.

        Parameters
        ----------
        sensor : tuple (:class:`Sensor`, :class:`~obspy.core.utcdatetime.UTCDateTime`, :class:`~obspy.core.utcdatetime.UTCDateTime`) 
            The sensor to be removed from the stream.
        '''
        # TODO: Implement this method.
        pass


    def get_sensor(self, start_time = None, end_time = None, **kwargs):
        ''' Get a sensor from the stream.

        Parameters
        ----------
        serial : String
            The serial number of the sensor.

        type : String
            The type of the sensor.

        id : Integer
            The database id.

        label : String
            The label of the sensor.

        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan to return.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan to return.

        '''
        ret_sensor = self.sensors

        valid_keys = ['serial', 'type', 'id',
                      'component']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_sensor = [x for x in ret_sensor if getattr(x.item, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        if start_time is not None:
            ret_sensor = [x for x in ret_sensor if (x.end_time is None) or (x.end_time > start_time)]

        if end_time is not None:
            ret_sensor = [x for x in ret_sensor if x.start_time < end_time]

        return ret_sensor



class Sensor(object):
    ''' A seismic sensor.
    '''

    def __init__(self, serial, type, component, id=None,
                 author_uri = None, agency_uri = None, creation_time = None,
                 parent_inventory = None):
        ''' Initialize the instance.

        '''
        # The logger instance.
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

        ## The database id of the sensor.
        self.id = id

        ## The component of the sensor (e.g. a 3-axis geophone has 3 components.)
        self.component = component

        ## The serial number of the sensor.
        self.serial = serial

        ## The type of the sensor.
        self.type = type

        ## The sensor parameters.
        # The sensor paramters are stored in a list with the start and end time 
        # during which these paramters have been valid.
        self.parameters = []

        # The inventory containing this sensor.
        self.parent_inventory = parent_inventory

        # Indicates if the attributes have been changed.
        self.has_changed = False

        # The author.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);


    #def __getattr__(self, attrname):
        #''' Handle call of attributes which are derived from the parent recorder.
        #'''
        #if attrname == 'recorder_id':
        #    return self.parent_recorder.id
        #elif attrname == 'recorder_serial':
        #    return self.parent_recorder.serial
        #elif attrname == 'recorder_type':
        #    return self.parent_recorder.type
        #else:
        #    raise AttributeError(attrname)


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
            compare_attributes = ['id', 'component', 'serial', 'type',
                                  'has_changed', 'parameters']
            for cur_attribute in compare_attributes:
                if getattr(self, cur_attribute) != getattr(other, cur_attribute):
                    return False

            return True
        else:
            return False


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
class SensorParameter:
    ## The constructor.
    #
    # @param self The object pointer.
    def __init__(self, sensitivity, sensitivity_units,
                 start_time, end_time, tf_type=None,
                 tf_units=None, tf_normalization_factor=None,
                 tf_normalization_frequency=None, tf_poles = None, tf_zeros = None,
                 id=None, parent_sensor = None,
                 author_uri = None, agency_uri = None, creation_time = None):

        # The logger instance.
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

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

        # The author.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);


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
            compare_attributes = ['sensitivity', 'tf_type',
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
    def __init__(self, name, location, x, y, z,
            parent_network=None, coord_system=None, description=None, network=None, id=None,
            author_uri = None, agency_uri = None, creation_time = None):

        # The logger instance.
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

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

        ## The station's network name.
        self.network = network

        # A list of tuples of channels assigned to the station.
        self.channels = []

        # The network containing this station.
        self.parent_network = parent_network

        # Indicates if the attributes have been changed.
        self.has_changed = False

        # The author.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);


    @property
    def snl(self):
        return (self.name, self.network, self.location)

    @property
    def snl_string(self):
        return str.join(':', self.get_snl())

    @property
    def parent_inventory(self):
        if self.parent_network is not None:
            return self.parent_network.parent_inventory
        else:
            return None


    def __setitem__(self, name, value):
        self.logger.debug("Setting the %s attribute to %s.", name, value)
        self.__dict__[name] = value
        self.has_changed = True


    def __eq__(self, other):
        if type(self) is type(other):
            compare_attributes = ['id', 'name', 'location', 'description', 'x', 'y', 'z',
                                  'coord_system', 'channels', 'has_changed']
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


    def add_channel(self, cur_channel):
        ''' Add a channel to the station

        Parameters
        ----------
        cur_channel : :class:`Channel`
            The channel to add to the station.
        '''
        added_channel = None
        if not self.get_channel(name = cur_channel.name):
            cur_channel.parent_station = self
            self.channels.append(cur_channel)
            self.has_changed = True
            added_channel = cur_channel

        return added_channel



    def get_channel(self, **kwargs):
        ''' Get a channel from the stream.

        Parameters
        ----------
        name : String
            The name of the channel.
        '''
        ret_channel = self.channels

        valid_keys = ['name']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_channel = [x for x in ret_channel if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_channel


    def get_unique_channel_names(self):
        channel_names = []

        for cur_channel, start, end in self.channels:
            if cur_channel.name not in channel_names:
                channel_names.append(cur_channel.name)

        return channel_names



class Channel(object):
    ''' A channel of a station.
    '''
    def __init__(self, name, description = None, id = None,
            agency_uri = None, author_uri = None, creation_time = None,
            parent_station = None):
        ''' Initialize the instance

        Parameters
        ----------
        name : String
            The name of the channel.

        streams : List of tuples.
            The streams assigned to the channel.

        '''
        # The database id of the channel.
        self.id = id

        # The name of the channel.
        self.name = name

        # The description of the channel.
        self.description = description

        # The streams assigned to the channel.
        self.streams = []

        # The station holding the channel.
        self.parent_station = parent_station

        # Indicates if the attributes have been changed.
        self.has_changed = False

        # The author.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);

    @property
    def parent_inventory(self):
        if self.parent_station is not None:
            return self.parent_station.parent_inventory
        else:
            return None


    def add_stream(self, cur_stream, start_time, end_time):
        ''' Add a stream to the channel.

        Parameters
        ----------
        cur_stream : :class:`Stream`
            The stream to add to the channel.

        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time from which on the stream has been operating at the channel.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time up to which the stream has been operating at the channel. "None" if the channel is still running.
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

        self.streams.append(TimeBox(item = cur_stream,
                                    start_time = start_time,
                                    end_time = end_time))
        self.has_changed = True


    def remove_stream(self, cur_stream):
        ''' Remove a stream from the channel.

        Parameters
        ----------
        cur_stream : tuple (:class:`Stream`, :class:`~obspy.core.utcdatetime.UTCDateTime`, :class:`~obspy.core.utcdatetime.UTCDateTime`) 
            The stream to be removed from the channel.
        '''
        self.logger.debug("Removing stream ")
        self.logger.debug("%s", cur_stream)

        #TODO: Implement this method.

        #if sensor not in self.sensors:

        # Remove the stream from the stream list.
        #self.streams.pop(self.stream.index(cur_stream))


    def get_stream(self, **kwargs):
        ''' Get a sensor from the recorder.

        Parameters
        ----------
        id : Integer
            The database id.

        name : String
            The name of the stream.

        label : String
            The label of the stream.
        '''
        ret_stream = self.streams

        valid_keys = ['id', 'name', 'label']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_stream = [x for x in ret_stream if getattr(x.item, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_stream


    # TODO: Implement the methods to change the stream start- and end-time.
    # This will be analog to the sensors in the streams. It would be great to
    # have these methods in the TimeBox class.
    # Keep in mind, that in the DbInventory, the ORM mapper values of the 
    # time-spans have to be changed as well.


class Network(object):

    def __init__(self, name, description=None, type=None, author_uri = None,
            agency_uri = None, creation_time = None, parent_inventory=None):
        ''' Initialize the instance.
        '''
        # The logger instance.
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

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

        # The author of the network.
        self.author_uri = author_uri

        # The agency of the author.
        self.agency_uri = agency_uri

        # The datetime of the creation.
        if creation_time == None:
            self.creation_time = UTCDateTime();
        else:
            self.creation_time = UTCDateTime(creation_time);


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
            station.parent_network = self
            self.stations.append(station)
            return station
        else:
            self.logger.error("The station with SL code %s is already in the network.", x.name + ':' + x.location)
            return None


    def remove_station(self, name, location):
        ''' Remove a station from the network.

        Parameters
        ----------
        name : String
            The name of the station to remove.

        location : String
            The location of the station to remove.
        '''
        station_2_remove = [x for x in self.stations if x.name == name and x.location == location]

        removed_station = None
        if len(station_2_remove) == 0:
            removed_station = None
        elif len(station_2_remove) == 1:
            station_2_remove = station_2_remove[0]
            self.stations.remove(station_2_remove)
            station_2_remove.network = None
            station_2_remove.parent_network = None
            removed_station = station_2_remove
        else:
            # This shouldn't happen.
            self.logger.error('Found more than one network with the name %s.', name)
            return None

        return removed_station


    def get_station(self, **kwargs):
        ''' Get a station from the network.

        Parameters
        ----------
        name : String
            The name (code) of the station.

        location : String
            The location code of the station.

        id : Integer
            The database id of the station.

        snl : Tuple (station, network, location)
            The SNL tuple of the station.

        snl_string : String
            The SNL string in the format 'station:network:location'.
        '''
        ret_station = self.stations

        valid_keys = ['name', 'network', 'location', 'id', 'snl', 'snl_string']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_station = [x for x in ret_station if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_station




class TimeBox(object):
    ''' A container to hold an instance with an assigned time-span.

    '''

    def __init__(self, item, start_time, end_time = None):
        ''' Initialize the instance.

        Parameters
        ----------

        '''
        # The item contained in the box.
        self.item = item

        # The start_time of the time-span.
        self.start_time = start_time

        # The end_time of the time-span.
        self.end_time = end_time


    def __eq__(self, other):
        is_equal = False
        try:
            if self.item is other.item:
                if self.start_time == other.start_time:
                    if self.end_time == other.end_time:
                        is_equal = True
        except:
            pass

        return is_equal

