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

import logging
from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorParameter


class DbInventory:

    def __init__(self, name, project):
        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.name = name

        self.type = 'db'

        self.project = project;

        self.db_session = self.project.getDbSession()

        self.networks = []

        self.recorders = []

    
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


    def __del__(self):
        ''' Clean up the database connection.
        '''
        print "Deleting DbInventory - closing the session.\n"
        self.db_session.close()


    def close(self):
        ''' Close the inventory database connection.
        '''
        print "Closing the session.\n"
        self.db_session.close()


    def get_network(self, code):
        ''' Get a network from the inventory.

        Parameters
        ----------
        coder : String
            The code of the network.
        '''
        cur_network = [x for x in self.networks if x.name == code]
        if len(cur_network) == 1:
            return cur_network[0]
        elif len(cur_network) > 1:
            self.logger.error('Found more than one network with the same code %s in the inventory.', code)
            return cur_network
        else:
            return None


    def load_networks(self):
        ''' Load the networks from the database.
        '''
        geom_network_orm = self.project.dbTables['geom_network']
        for cur_geom_network in self.db_session.query(geom_network_orm).order_by(geom_network_orm.name):
            db_network = DbNetwork.from_sqlalchemy_orm(self, cur_geom_network)

            for cur_geom_station in cur_geom_network.stations:
                pass

            self.networks.append(db_network)


    def load_recorders(self):
        ''' Load the recorders from the database.
        '''
        geom_recorder_orm = self.project.dbTables['geom_recorder']
        for cur_geom_recorder in self.db_session.query(geom_recorder_orm).order_by(geom_recorder_orm.serial):
            db_recorder = DbRecorder.from_sqlalchemy_orm(self, cur_geom_recorder)

            for cur_geom_sensor in cur_geom_recorder.sensors:
                db_sensor = DbSensor.from_sqlalchemy_orm(db_recorder, cur_geom_sensor)
                db_recorder.sensors.append(db_sensor)

                for cur_geom_sensor_param in cur_geom_sensor.parameters:
                    db_sensor_param = DbSensorParameter.from_sqlalchemy_orm(db_sensor, cur_geom_sensor_param)
                    db_sensor.parameters.append(db_sensor_param)

            self.recorders.append(db_recorder)


    def add_network(self, network):
        ''' Add a new network to the database inventory.

        Parameters
        ----------
        network : :class:`psysmon.packages.geometry.inventory.Network`
            The network to add to the database inventory.
        '''
        available_networks = [x.name for x in self.networks]
        if network.name not in available_networks:
            db_network = DbNetwork.from_inventory_network(self, network)

            for cur_station in network.stations:
                db_station = DbStation.from_inventory_station(self, cur_station)
                db_network.add_station(db_station)

            self.networks.append(db_network)
            self.db_session.add(db_network.geom_network)
            return db_network
        else:
            self.logger.error('The network %s already exists in the inventory.', network.name)
            return None


    def remove_network(self, name):
        ''' Remove a network from the database inventory.

        Parameters
        ----------
        name : String
            The name of the network to remove.
        '''
        net_2_remove = [x for x in self.networks if x.name == name]

        if len(net_2_remove) == 0:
            return None
        elif len(net_2_remove) == 1:
            self.networks.remove(net_2_remove[0])
            self.db_session.expunge(net_2_remove[0].geom_network)
            return net_2_remove[0]
        else:
            # This shouldn't happen.
            self.logger.error('Found more than one network with the name %s.', name)
            return None


    def add_station(self, station):
        ''' Add a station to the database inventory.
        The station is added only, if a corresponding network is found.

        Parameters
        ----------
        station : :class:`~psysmon.packages.geometery.inventory.Station`
            The station to add to the inventory.
        '''
        cur_net = self.get_network(station.network)

        if cur_net is not None:
            db_station = DbStation.from_inventory_station(cur_net, station)
            added_station = cur_net.add_station(db_station)
            return added_station
        else:
            self.logger.error('The network %s of the station is not found in the inventory.', station.network)
            return None


    def remove_station(self, snl):
        ''' Remove a station from the inventory.

        Parameters
        ----------
        scnl : tuple (String, String, String)
            The SNL code of the station to remove from the inventory.
        '''
        cur_net = self.get_network(snl[1])

        if cur_net is not None:
            removed_station = cur_net.remove_station(name = snl[0], location = snl[2])
            return removed_station
        else:
            return None


    def add_recorder(self, recorder):
        ''' Add a recorder to the inventory.

        Parameters
        ----------
        recorder : :class:`~psysmon.packages.geometery.inventory.Recorder`
            The recorder to add to the inventory.
        '''
        available_recorders = [(x.serial, x.type) for x in self.recorders]

        if (recorder.serial, recorder.type) not in available_recorders:
            db_recorder = DbRecorder.from_inventory_recorder(self, recorder)
            self.recorders.append(db_recorder)
            self.db_session.add(db_recorder.geom_recorder)

            for cur_sensor in recorder.sensors:
                db_sensor = db_recorder.add_sensor(DbSensor.from_inventory_sensor(db_recorder, cur_sensor))
                for cur_parameter in cur_sensor.parameters:
                    db_parameter = db_sensor.add_parameter(DbSensorParameter.from_inventory_sensor_parameter(db_sensor, cur_parameter))

            return db_recorder
        else:
            return None



    def commit(self):
        ''' Commit the database changes.
        '''
        self.db_session.commit()
        self.db_session.flush()




class DbNetwork:

    def __init__(self, parent_inventory, name, description, type, geom_network = None):

        self.parent_inventory = parent_inventory

        self.name = name

        self.description = description

        self.type = type

        self.stations = []

        if geom_network is None:
            # Create a new database network instance.
            geom_network_orm = self.parent_inventory.project.dbTables['geom_network']
            self.geom_network = geom_network_orm(self.name, self.description, self.type)
        else:
            self.geom_network = geom_network


    @classmethod
    def from_sqlalchemy_orm(cls, parent_inventory, geom_network):
        return cls(parent_inventory, geom_network.name, geom_network.description, geom_network.type, geom_network)


    @classmethod
    def from_inventory_network(cls, parent_inventory, network):
        return cls(parent_inventory, network.name, network.description, network.type)


    def add_station(self, station):
        ''' Add a station to the network.

        Parameters
        ----------
        station : :class:`DbStation`
            The station instance to add to the network.
        '''
        available_sl = [(x.name, x.location) for x in self.stations]
        if((station.name, station.location) not in available_sl):
            station.set_parent_network(self)
            self.stations.append(station)
            self.geom_network.stations.append(station.geom_station)
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

        if len(station_2_remove) == 0:
            return None
        elif len(station_2_remove) == 1:
            station_2_remove = station_2_remove[0]
            self.stations.remove(station_2_remove)
            self.geom_network.stations.remove(station_2_remove.geom_station)
            return station_2_remove
        else:
            # This shouldn't happen.
            self.logger.error('Found more than one network with the name %s.', name)
            return None




class DbStation:

    def __init__(self, parent_network, network, name, location, x, y, z, coord_system, description, geom_station = None):

        self.parent_network = parent_network

        self.network = network

        self.name = name

        self.location = location

        self.x = x

        self.y = y

        self.z = z

        self.coord_system = coord_system

        self.description = description

        self.parent_inventory = parent_network.parent_inventory

        if geom_station is None:
            # Create a new database station instance.
            geom_station_orm = self.parent_inventory.project.dbTables['geom_station']
            self.geom_station = geom_station_orm(self.network,
                                                self.name,
                                                self.location,
                                                self.x,
                                                self.y,
                                                self.z,
                                                self.coord_system,
                                                self.description)
        else:
            self.geom_station = geom_station



    @classmethod
    def from_sqlalchemy_orm(cls, parent_network, geom_station):
        return cls(parent_network,
                   geom_station.network,
                   geom_station.name,
                   geom_station.location,
                   geom_station.x,
                   geom_station.y,
                   geom_station.z,
                   geom_station.coord_system,
                   geom_station.description,
                   geom_station)


    @classmethod
    def from_inventory_station(cls, parent_network, station):
        return cls(parent_network,
                   station.network,
                   station.name,
                   station.location,
                   station.x,
                   station.y,
                   station.z,
                   station.coord_system,
                   station.description)

    def set_parent_network(self, network):
        self.network = network.name
        self.parent_network = network
        self.parent_inventory = network.parent_inventory



class DbRecorder(Recorder):

    def __init__(self, parent_inventory, id, serial, type, geom_recorder = None):
        Recorder.__init__(self, id = id, serial = serial, type = type, 
                        parent_inventory = parent_inventory)

        if geom_recorder is None:
            # Create a new database recorder instance.
            geom_recorder_orm = self.parent_inventory.project.dbTables['geom_recorder']
            self.geom_recorder = geom_recorder_orm(self.serial, self.type)
        else:
            self.geom_recorder = geom_recorder


    @classmethod
    def from_sqlalchemy_orm(cls, parent_inventory, geom_recorder):
        return cls(parent_inventory,
                   geom_recorder.id,
                   geom_recorder.serial,
                   geom_recorder.type,
                   geom_recorder = geom_recorder)


    @classmethod
    def from_inventory_recorder(cls, parent_inventory, recorder):
        return cls(parent_inventory,
                   recorder.id,
                   recorder.serial,
                   recorder.type)



    def add_sensor(self, sensor):
        ''' Add a sensor to the recorder.

        Parameters
        ----------
        sensor : :class:`DbSensor`
            The sensor to add to the recorder.
        '''
        sensor.recorder_id = self.id
        sensor.recorder_serial = self.serial
        sensor.recorder_type = self.type
        sensor.parentRecorder = self
        sensor.set_parent_inventory(self.parent_inventory)
        self.sensors.append(sensor)
        self.geom_recorder.sensors.append(sensor.geom_sensor)
        return sensor



class DbSensor(Sensor):

    def __init__(self, parent_recorder, serial, type, rec_channel_name,
                 channel_name, label, id, recorder_id, recorder_serial,
                 recorder_type, geom_sensor = None):
        Sensor.__init__(self, id = id, serial = serial, type = type,
                        rec_channel_name = rec_channel_name, label = label,
                        channel_name = channel_name, recorder_id = recorder_id,
                        recorder_serial = recorder_serial, recorder_type = recorder_type,
                        parent_recorder = parent_recorder)

        if geom_sensor is None:
            geom_sensor_orm = self.parent_inventory.project.dbTables['geom_sensor']
            self.geom_sensor = geom_sensor_orm(self.id,
                                               self.label,
                                               self.serial,
                                               self.type,
                                               self.rec_channel_name,
                                               self.channel_name)
        else:
            self.geom_sensor = geom_sensor


    @classmethod
    def from_sqlalchemy_orm(cls, parent_recorder, geom_sensor):
        return cls(parent_recorder,
                   geom_sensor.serial,
                   geom_sensor.type,
                   geom_sensor.rec_channel_name,
                   geom_sensor.channel_name,
                   geom_sensor.label,
                   geom_sensor.id,
                   geom_sensor.recorder_id,
                   parent_recorder.serial,
                   parent_recorder.type,
                   geom_sensor)


    @classmethod
    def from_inventory_sensor(cls, parent_recorder, sensor):
        return cls(parent_recorder,
                   sensor.serial,
                   sensor.type,
                   sensor.rec_channel_name,
                   sensor.channel_name,
                   sensor.label,
                   sensor.id,
                   parent_recorder.id,
                   parent_recorder.serial,
                   parent_recorder.type)


    def add_parameter(self, parameter):
        ''' Add a parameter to the sensor

        Parameters
        ----------
        parameter : :class:`DbSensorParameter`
            The parameter to add to the sensor.
        '''
        self.logger.debug('Adding parameter.')
        self.parameters.append(parameter)
        self.geom_sensor.parameters.append(parameter.geom_sensor_parameter)
        
        # Add the tf poles and zeros to the database orm.
        geom_tfpz_orm = self.parent_inventory.project.dbTables['geom_tf_pz']
        for cur_pole in parameter.tf_poles:
            parameter.geom_sensor_parameter.tf_pz.append(geom_tfpz_orm(parameter.id, 1, cur_pole.real, cur_pole.imag))
        for cur_zero in parameter.tf_zeros:
            parameter.geom_sensor_parameter.tf_pz.append(geom_tfpz_orm(parameter.id, 0, cur_zero.real, cur_zero.imag))

        return parameter



class DbSensorParameter(SensorParameter):

    def __init__(self, parent_sensor, sensor_id, gain, bitweight,
                 bitweight_units, sensitivity, sensitivity_units, tf_type,
                 tf_units, tf_normalization_factor, tf_normalization_frequency,
                 id, start_time, end_time, tf_poles = [], tf_zeros = [],
                 geom_sensor_parameter = None):

        SensorParameter.__init__(self, parent_sensor = parent_sensor,
                                 sensor_id = sensor_id, gain = gain, bitweight = bitweight,
                                 bitweight_units = bitweight_units, sensitivity = sensitivity,
                                 sensitivity_units = sensitivity_units, 
                                 start_time = start_time, end_time = end_time, tf_type = tf_type,
                                 tf_units = tf_units, tf_normalization_factor = tf_normalization_factor,
                                 tf_normalization_frequency = tf_normalization_frequency,
                                 tf_poles = tf_poles, tf_zeros = tf_zeros, id = id)

        if geom_sensor_parameter is None:
            geom_sensor_param_orm = self.parent_inventory.project.dbTables['geom_sensor_param']
            self.geom_sensor_parameter = geom_sensor_param_orm(sensor_id = self.id,
                                                     start_time = self.start_time,
                                                     end_time = self.end_time,
                                                     tf_normalization_factor = self.tf_normalization_factor,
                                                     tf_normalization_frequency = self.tf_normalization_frequency,
                                                     tf_type = self.tf_type,
                                                     tf_units = self.tf_units,
                                                     gain = self.gain,
                                                     bitweight = self.bitweight,
                                                     bitweight_units = self.bitweight_units,
                                                     sensitivity = self.sensitivity,
                                                     sensitivity_units = self.sensitivity_units
                                            )
        else:
            self.geom_sensor_parameter = geom_sensor_parameter


    @classmethod
    def from_inventory_sensor_parameter(cls, parent_sensor, sensor_parameter):
        return cls(parent_sensor,
                   sensor_id = sensor_parameter.sensor_id,
                   start_time = sensor_parameter.start_time,
                   end_time = sensor_parameter.end_time,
                   tf_normalization_factor = sensor_parameter.tf_normalization_factor,
                   tf_normalization_frequency = sensor_parameter.tf_normalization_frequency,
                   tf_type = sensor_parameter.tf_type,
                   tf_units = sensor_parameter.tf_units,
                   tf_poles = sensor_parameter.tf_poles,
                   tf_zeros = sensor_parameter.tf_zeros,
                   gain = sensor_parameter.gain,
                   bitweight = sensor_parameter.bitweight,
                   bitweight_units = sensor_parameter.bitweight_units,
                   sensitivity = sensor_parameter.sensitivity,
                   sensitivity_units = sensor_parameter.sensitivity_units,
                   id = sensor_parameter.id)


    @classmethod
    def from_sqlalchemy_orm(cls, parent_sensor, geom_sensor_parameter):


        sensor = cls(parent_sensor,
                   sensor_id = geom_sensor_parameter.sensor_id,
                   start_time = geom_sensor_parameter.start_time,
                   end_time = geom_sensor_parameter.end_time,
                   tf_normalization_factor = geom_sensor_parameter.tf_normalization_factor,
                   tf_normalization_frequency = geom_sensor_parameter.tf_normalization_frequency,
                   tf_type = geom_sensor_parameter.tf_type,
                   tf_units = geom_sensor_parameter.tf_units,
                   gain = geom_sensor_parameter.gain,
                   bitweight = geom_sensor_parameter.bitweight,
                   bitweight_units = geom_sensor_parameter.bitweight_units,
                   sensitivity = geom_sensor_parameter.sensitivity,
                   sensitivity_units = geom_sensor_parameter.sensitivity_units,
                   id = geom_sensor_parameter.id,
                   geom_sensor_parameter = geom_sensor_parameter)
        
        # Collect the poles and zeros of the transfer function.
        for cur_pz in geom_sensor_parameter.tf_pz:
            if cur_pz.type == 0:
                sensor.tf_zeros.append(complex(cur_pz.complex_real, cur_pz.complex_imag))
            elif cur_pz.type == 1:
                sensor.tf_poles.append(complex(cur_pz.complex_real, cur_pz.complex_imag))

        return sensor
