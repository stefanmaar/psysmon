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

from psysmon.packages.geometry.inventory import Inventory
from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Channel
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorParameter
from psysmon.packages.geometry.inventory import RecorderStream
from obspy.core.utcdatetime import UTCDateTime


class DbInventory(Inventory):

    def __init__(self, name, project):
        Inventory.__init__(self, name = name, type = 'db')

        # The pSysmon project containing the inventory.
        self.project = project;

        # The pSysmon database session.
        self.db_session = self.project.getDbSession()



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


    def add_recorder(self, recorder):
        ''' Add a recorder to the inventory.

        Parameters
        ----------
        recorder : :class:`~psysmon.packages.geometery.inventory.Recorder`
            The recorder to add to the inventory.
        '''
        if recorder.__class__ is Recorder:
            recorder = DbRecorder.from_inventory_recorder(self, recorder)

        added_recorder = Inventory.add_recorder(self, recorder)
        if added_recorder is not None:
            self.db_session.add(added_recorder.geom_recorder)

        return added_recorder


    def add_sensor(self, sensor):
        ''' Add a sensor to the inventory.

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor to add to the inventory.
        '''
        if sensor.__class__ is Sensor:
            sensor = DbSensor.from_inventory_sensor(self, sensor)

        added_sensor = Inventory.add_sensor(self, sensor)
        if added_sensor is not None:
            self.db_session.add(added_sensor.geom_sensor)

        return added_sensor


    def add_network(self, network):
        ''' Add a new network to the database inventory.

        Parameters
        ----------
        network : :class:`psysmon.packages.geometry.inventory.Network`
            The network to add to the database inventory.
        '''
        if network.__class__ is Network:
            network = DbNetwork.from_inventory_network(self, network)

        added_network =  Inventory.add_network(self, network)
        if added_network is not None:
            self.db_session.add(added_network.geom_network)

        return added_network


    def remove_network(self, name):
        ''' Remove a network from the database inventory.

        Parameters
        ----------
        name : String
            The name of the network to remove.
        '''
        removed_network = Inventory.remove_network(name)
        if removed_network is not None:
            self.db_session.expunge(removed_network.geom_network)

        return removed_network


    def load_networks(self):
        ''' Load the networks from the database.
        '''
        geom_network_orm = self.project.dbTables['geom_network']
        for cur_geom_network in self.db_session.query(geom_network_orm).order_by(geom_network_orm.name):
            db_network = DbNetwork.from_sqlalchemy_orm(self, cur_geom_network)

            for cur_geom_station in cur_geom_network.stations:
                db_station = DbStation.from_sqlalchemy_orm(db_network, cur_geom_station)

                for cur_geom_sensor in cur_geom_station.sensors:
                    db_sensor = self.get_sensor(id = cur_geom_sensor.sensor_id)
                    if len(db_sensor) == 1:
                        if cur_geom_sensor.start_time is not None:
                            start_time = UTCDateTime(cur_geom_sensor.start_time)
                        else:
                            start_time = None

                        if cur_geom_sensor.end_time is not None:
                            end_time = UTCDateTime(cur_geom_sensor.end_time)
                        else:
                            end_time = None
                        db_station.sensors.append((db_sensor[0], start_time, end_time))

                db_network.stations.append(db_station)

            self.networks.append(db_network)


    def load_recorders(self):
        ''' Load the recorders from the database.
        '''
        geom_recorder_orm = self.project.dbTables['geom_recorder']
        for cur_geom_recorder in self.db_session.query(geom_recorder_orm).order_by(geom_recorder_orm.serial):
            db_recorder = DbRecorder.from_sqlalchemy_orm(self, cur_geom_recorder)

            self.recorders.append(db_recorder)


    def load(self):
        ''' Load the inventory from the database.
        '''
        self.load_recorders()
        self.load_networks()


    def commit(self):
        ''' Commit the database changes.
        '''
        self.db_session.commit()
        #self.db_session.flush()

        # update the ids of the inventory elements.
        for cur_network in self.networks:
            for cur_station in cur_network.stations:
                cur_station.update_id()

        for cur_recorder in self.recorders:
            cur_recorder.update_id()
            for cur_stream in cur_recorder.streams:
                cur_stream.update_id()
                for cur_sensor, cur_start_time, cur_end_time in cur_stream.sensors:
                    cur_sensor.update_id()
                    for cur_param in cur_sensor.parameters:
                        cur_param.update_id()


    @classmethod
    def from_inventory(cls, name, project, inventory):
        db_inventory = cls(name = name, project = project)
        for cur_recorder in inventory.recorders:
            db_inventory.add_recorder(cur_recorder)

        for cur_network in inventory.networks:
            db_inventory.add_network(cur_network)

        return db_inventory


    @classmethod
    def load_inventory(cls, project):
        db_inventory = cls(name = 'db_inventory', project = project)
        db_inventory.load_recorders()
        db_inventory.load_networks()
        db_inventory.close()

        return db_inventory






class DbNetwork(Network):

    def __init__(self, parent_inventory, name, description, type,
            author_uri, agency_uri, creation_time, geom_network = None):
        Network.__init__(self, name = name, description = description, type = type,
                author_uri = author_uri, agency_uri = agency_uri,
                creation_time = creation_time, parent_inventory = parent_inventory)

        if geom_network is None:
            # Create a new database network instance.
            geom_network_orm = self.parent_inventory.project.dbTables['geom_network']
            self.geom_network = geom_network_orm(name = self.name,
                                    description = self.description,
                                    type = self.type,
                                    agency_uri = self.agency_uri,
                                    author_uri = self.author_uri,
                                    creation_time = self.creation_time)
        else:
            self.geom_network = geom_network


    @classmethod
    def from_sqlalchemy_orm(cls, parent_inventory, geom_network):
        return cls(parent_inventory = parent_inventory,
                   name = geom_network.name,
                   description = geom_network.description,
                   type = geom_network.type,
                   author_uri = geom_network.author_uri,
                   agency_uri = geom_network.agency_uri,
                   creation_time = geom_network.creation_time,
                   geom_network = geom_network)


    @classmethod
    def from_inventory_network(cls, parent_inventory, network):
        cur_network =  cls(parent_inventory = parent_inventory,
                   name = network.name,
                   description = network.description,
                   type = network.type,
                   author_uri = network.author_uri,
                   agency_uri = network.agency_uri,
                   creation_time = network.creation_time)

        for cur_station in network.stations:
            cur_network.add_station(cur_network)

        return cur_network



    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        Network.__setattr__(self, attr, value)
        attr_map = {};
        attr_map['name'] = 'name'
        attr_map['description'] = 'description'
        attr_map['type'] = 'type'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        if attr in attr_map.keys():
            if 'geom_network' in self.__dict__:
                setattr(self.geom_network, attr_map[attr], value)



    def add_station(self, station):
        ''' Add a station to the network.

        Parameters
        ----------
        station : :class:`DbStation`
            The station instance to add to the network.
        '''
        if station.__class__ is Station:
            station = DbStation.from_inventory_station(self, station)

        added_station = Network.add_station(self, station)
        if added_station is not None:
            self.geom_network.stations.append(station.geom_station)

        return added_station



    def remove_station(self, name, location):
        ''' Remove a station from the network.

        Parameters
        ----------
        name : String
            The name of the station to remove.

        location : String
            The location of the station to remove.
        '''
        removed_station = Station.remove_station(name = name, location = location)

        if removed_station is not None:
            self.geom_network.stations.remove(removed_station.geom_station)




class DbStation(Station):

    def __init__(self, id = None, geom_station = None, **kwargs):
        Station.__init__(self, id = id, **kwargs)

        if geom_station is None:
            # Create a new database station instance.
            geom_station_orm = self.parent_inventory.project.dbTables['geom_station']
            self.geom_station = geom_station_orm(network = self.network,
                                                name = self.name,
                                                location = self.location,
                                                x = self.x,
                                                y = self.y,
                                                z = self.z,
                                                coord_system = self.coord_system,
                                                description = self.description,
                                                agency_uri = self.agency_uri,
                                                author_uri = self.author_uri,
                                                creation_time = self.creation_time)
        else:
            self.geom_station = geom_station



    @classmethod
    def from_sqlalchemy_orm(cls, parent_network, geom_station):
        station = cls(parent_inventory = parent_network,
                      id = geom_station.id,
                      network = geom_station.network,
                      name = geom_station.name,
                      location = geom_station.location,
                      x = geom_station.x,
                      y = geom_station.y,
                      z = geom_station.z,
                      coord_system = geom_station.coord_system,
                      description = geom_station.description,
                      author_uri = geom_station.author_uri,
                      agency_uri = geom_station.agency_uri,
                      creation_time = geom_station.creation_time,
                      geom_station = geom_station)

        for cur_channel in geom_station.channels:
            db_channel = DbChannel.from_sqlalchemy_orm(station, cur_channel)
            station.channels.append(db_channel)

        return station



    @classmethod
    def from_inventory_station(cls, parent_network, station):
        cur_station =  cls(parent_network = parent_network,
                           network = station.network,
                           name = station.name,
                           location = station.location,
                           x = station.x,
                           y = station.y,
                           z = station.z,
                           coord_system = station.coord_system,
                           description = station.description,
                           author_uri = station.author_uri,
                           agency_uri = station.agency_uri,
                           creation_time = station.creation_time)

        for cur_channel in station.channels:
            cur_station.add_channel(cur_channel)

        return cur_station


    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        attr_map = {};
        attr_map['name'] = 'name'
        attr_map['network'] = 'network'
        attr_map['location'] = 'location'
        attr_map['x'] = 'x'
        attr_map['y'] = 'y'
        attr_map['z'] = 'z'
        attr_map['coord_system'] = 'coord_system'
        attr_map['description'] = 'description'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        self.__dict__[attr] = value

        if attr in attr_map.keys():
            if 'geom_station' in self.__dict__:
                setattr(self.geom_station, attr_map[attr], value)

        self.__dict__['has_changed'] = True


    def add_channel(self, cur_channel):
        ''' Add a channel to the station.

        Parameters
        ----------
        cur_channel : :class:`DbChannel`
            The channel to add to the station.
        '''
        if cur_channel.__class__ is Channel:
            cur_channel = DbChannel.from_inventory_channel(self, cur_channel)

        added_channel = Station.add_channel(self, cur_channel)
        if added_channel is not None:
            self.geom_station.channels.append(cur_channel.geom_channel)

        return added_channel


    def update_id(self):
        ''' Update the database if from the geom_station instance.
        '''
        if self.geom_station is not None:
            self.id = self.geom_station.id





class DbRecorder(Recorder):

    def __init__(self, parent_inventory, serial, type, description,
            author_uri, agency_uri, creation_time,
            id = None, geom_recorder = None):
        Recorder.__init__(self, id = id, serial = serial, type = type,
                         author_uri = author_uri, agency_uri = agency_uri, creation_time = creation_time,
                        parent_inventory = parent_inventory)

        if geom_recorder is None:
            # Create a new database recorder instance.
            geom_recorder_orm = self.parent_inventory.project.dbTables['geom_recorder']
            self.geom_recorder = geom_recorder_orm(serial = self.serial,
                                                   type = self.type,
                                                   agency_uri = self.agency_uri,
                                                   author_uri = self.author_uri,
                                                   creation_time = self.creation_time)
        else:
            self.geom_recorder = geom_recorder


    @classmethod
    def from_sqlalchemy_orm(cls, parent_inventory, recorder_orm):
        cur_recorder = cls(parent_inventory = parent_inventory,
                   id = recorder_orm.id,
                   serial = recorder_orm.serial,
                   type = recorder_orm.type,
                   description = recorder_orm.description,
                   author_uri = recorder_orm.author_uri,
                   agency_uri = recorder_orm.agency_uri,
                   creation_time = recorder_orm.creation_time,
                   geom_recorder = recorder_orm)

        for cur_stream in recorder_orm.streams:
            db_stream = DbRecorderStream.from_sqlalchemy_orm(cur_recorder, cur_stream)
            cur_recorder.streams.append(db_stream)

        return cur_recorder


    @classmethod
    def from_inventory_recorder(cls, parent_inventory, recorder):
        cur_recorder = cls(parent_inventory = parent_inventory,
                           serial = recorder.serial,
                           type = recorder.type,
                           author_uri = recorder.author_uri,
                           agency_uri = recorder.agency_uri,
                           creation_time = recorder.creation_time,
                           description = recorder.description)

        for cur_stream in recorder.streams:
            cur_recorder.add_stream(cur_stream)

        return cur_recorder


    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        attr_map = {};
        attr_map['serial'] = 'serial'
        attr_map['type'] = 'type'
        attr_map['description'] = 'description'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        if attr in attr_map.keys():
            self.__dict__[attr] = value
            if 'geom_recorder' in self.__dict__:
                setattr(self.geom_recorder, attr_map[attr], value)
        else:
            self.__dict__[attr] = value


    def add_stream(self, cur_stream):
        ''' Add a stream to the recorder.

        Parameters
        ----------
        cur_stream : :class:`DbRecorderStream`
            The stream to add to the recorder.
        '''
        if cur_stream.__class__ is RecorderStream:
            cur_stream = DbRecorderStream.from_inventory_stream(self, cur_stream)

        added_stream = Recorder.add_stream(self, cur_stream)
        if added_stream is not None:
            self.geom_recorder.streams.append(cur_stream.geom_rec_stream)

        return added_stream



    def update_id(self):
        ''' Update the database if from the geom_recorder instance.
        '''
        if self.geom_recorder is not None:
            self.id = self.geom_recorder.id



class DbRecorderStream(RecorderStream):

    def __init__(self, parent_recorder, name, label,
                 gain, bitweight, bitweight_units, agency_uri, author_uri,
                 creation_time, id = None, geom_rec_stream = None):
        RecorderStream.__init__(self,
                                id = id,
                                name = name,
                                label = label,
                                gain = gain,
                                bitweight = bitweight,
                                bitweight_units = bitweight_units,
                                agency_uri = agency_uri,
                                author_uri = author_uri,
                                creation_time = creation_time,
                                parent_recorder = parent_recorder)

        if geom_rec_stream is None:
            geom_rec_stream_orm = self.parent_inventory.project.dbTables['geom_rec_stream']
            self.geom_rec_stream = geom_rec_stream_orm(recorder_id = self.id,
                                            name = self.name,
                                            label = self.label,
                                            gain = self.gain,
                                            bitweight = self.bitweight,
                                            bitweight_units = self.bitweight_units,
                                            agency_uri = self.agency_uri,
                                            author_uri = self.author_uri,
                                            creation_time = self.creation_time)
        else:
            self.geom_rec_stream = geom_rec_stream


    @classmethod
    def from_sqlalchemy_orm(cls, parent_recorder, geom_rec_stream):
        cur_stream =  cls(parent_recorder = parent_recorder,
                          name = geom_rec_stream.name,
                          label = geom_rec_stream.label,
                          gain = geom_rec_stream.gain,
                          bitweight = geom_rec_stream.bitweight,
                          bitweight_units = geom_rec_stream.bitweight_units,
                          id = geom_rec_stream.id,
                          author_uri = geom_rec_stream.author_uri,
                          agency_uri = geom_rec_stream.agency_uri,
                          creation_time = geom_rec_stream.creation_time,
                          geom_rec_stream = geom_rec_stream)

        for cur_sensor_to_stream in geom_rec_stream.sensors:
            db_sensor = DbSensor.from_sqlalchemy_orm(cur_stream, cur_sensor_to_stream.sensor)
            cur_start_time = UTCDateTime(cur_sensor_to_stream.start_time)
            cur_end_time = UTCDateTime(cur_sensor_to_stream.end_time)
            cur_stream.sensors.append((db_sensor, cur_start_time, cur_end_time))
            db_sensor.set_parent_inventory(cur_stream.parent_inventory)

        return cur_stream


    @classmethod
    def from_inventory_stream(cls, parent_recorder, stream):
        cur_stream =  cls(parent_recorder = parent_recorder,
                          name = stream.name,
                          label = stream.label,
                          gain = stream.gain,
                          bitweight = stream.bitweight,
                          bitweight_units = stream.bitweight_units,
                          author_uri = stream.author_uri,
                          agency_uri = stream.agency_uri,
                          creation_time = stream.creation_time)

        for cur_sensor, cur_start_time, cur_end_time in stream.sensors:
            cur_stream.add_sensor(sensor = cur_sensor,
                                  start_time = cur_start_time,
                                  end_time = cur_end_time)
        return cur_stream


    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        attr_map = {};
        attr_map['name'] = 'name'
        attr_map['label'] = 'label'
        attr_map['gain'] = 'gain'
        attr_map['bitweight'] = 'bitweight'
        attr_map['bitweight_units'] = 'bitweight_units'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        if attr in attr_map.keys():
            self.__dict__[attr] = value
            if 'geom_rec_stream' in self.__dict__:
                setattr(self.geom_rec_stream, attr_map[attr], value)
        else:
            self.__dict__[attr] = value


    def add_sensor(self, sensor_serial, sensor_type, start_time, end_time):
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

        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time from which on the sensor has been operating at the station.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time up to which the sensor has been operating at the station. "None" if the station is still running.
        '''
        added_sensor = RecorderStream.add_sensor(self,
                                                 sensor_serial = sensor_serial,
                                                 sensor_type = sensor_type,
                                                 start_time = start_time,
                                                 end_time = end_time)
        if added_sensor is not None:
            # Add the sensor to the database orm.
            if start_time is not None:
                start_time_timestamp = start_time.timestamp
            else:
                start_time_timestamp = None

            if end_time is not None:
                end_time_timestamp = end_time.timestamp
            else:
                end_time_timestamp = None

            geom_sensor_to_stream_orm = self.parent_inventory.project.dbTables['geom_sensor_to_stream']
            geom_sensor_to_stream = geom_sensor_to_stream_orm(self.id,
                                                              added_sensor.id,
                                                              start_time_timestamp,
                                                              end_time_timestamp)
            geom_sensor_to_stream.sensor = added_sensor.geom_sensor
            self.geom_rec_stream.sensors.append(geom_sensor_to_stream)

        return added_sensor


    def change_sensor_start_time(self, sensor, start_time, end_time, new_start_time):
        ''' Change the sensor deployment start time

        Parameters
        ----------
        sensor : :class:`Sensor`
            The sensor which should be changed.

        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime or String
            A :class:`~obspy.core.utcdatetime.UTCDateTime` instance or a data-time string which can be used by :class:`~obspy.core.utcdatetime.UTCDateTime`.
        '''
        sensor_2_change = [(s, b, e, k) for k, (s, b, e) in enumerate(self.sensors) if s == sensor and b == start_time and e == end_time]

        if len(sensor_2_change) == 1:
            sensor_2_change = sensor_2_change[0]
            position = sensor_2_change[3]
        elif len(sensor_2_change) > 1:
            msg = 'More than one sensor found in the station.'
            return(start_time, msg)
        else:
            msg = 'The sensor can''t be found in the station.'
            return (start_time, msg)

        msg = ''    


        if not isinstance(new_start_time, UTCDateTime):
            try:
                new_start_time = UTCDateTime(new_start_time)
            except:
                new_start_time = sensor_2_change[2]
                msg = "The entered value is not a valid time."


        if not sensor_2_change[2] or (sensor_2_change[2] and new_start_time < sensor_2_change[2]):
            self.sensors[position] = (sensor_2_change[0], new_start_time, sensor_2_change[2])
            # Change the start-time in the ORM.
            cur_geom_sensor_time = [x for x in self.geom_station.sensors if x.child is sensor.geom_sensor and UTCDateTime(x.start_time) == start_time]
            if len(cur_geom_sensor_time) == 1:
                if new_start_time is not None:
                    cur_geom_sensor_time[0].start_time = new_start_time.timestamp
                else:
                    cur_geom_sensor_time[0].start_time = new_start_time
            elif len(cur_geom_sensor_time) > 1:
                self.logger.error('Found more than two sensor ORM children.')
        else:
            new_start_time = sensor_2_change[1]
            msg = "The end-time has to be larger than the begin time."

        return (new_start_time, msg)


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
            # Change the start-time in the ORM.
            cur_geom_sensor_time = [x for x in self.geom_station.sensors if x.child is sensor.geom_sensor]
            if len(cur_geom_sensor_time) == 1:
                    cur_geom_sensor_time[0].end_time = None
            elif len(cur_geom_sensor_time) > 1:
                self.logger.error('Found more than two sensor ORM children.')

        else:
            if not isinstance(end_time, UTCDateTime):
                try:
                    end_time = UTCDateTime(end_time)
                except:
                    end_time = sensor_2_change[2]
                    msg = "The entered value is not a valid time."


            if not sensor_2_change[1] or end_time > sensor_2_change[1]:
                self.sensors[position] = (sensor_2_change[0], sensor_2_change[1], end_time)
                # Change the start-time in the ORM.
                cur_geom_sensor_time = [x for x in self.geom_station.sensors if x.child is sensor.geom_sensor]
                if len(cur_geom_sensor_time) == 1:
                    if end_time is not None:
                        cur_geom_sensor_time[0].end_time = end_time.timestamp
                    else:
                        cur_geom_sensor_time[0].end_time = end_time
                elif len(cur_geom_sensor_time) > 1:
                    self.logger.error('Found more than two sensor ORM children.')
            else:
                end_time = sensor_2_change[2]
                msg = "The end-time has to be larger than the begin time."

        return (end_time, msg)


    def update_id(self):
        ''' Update the database if from the geom_sensor instance.
        '''
        if self.geom_rec_stream is not None:
            self.id = self.geom_rec_stream.id






class DbSensor(Sensor):

    def __init__(self, parent_inventory, serial, type,
                 label, author_uri, agency_uri, creation_time,
                 id = None, geom_sensor = None):
        Sensor.__init__(self, id = id, serial = serial, type = type,
                        label = label, author_uri = author_uri,
                        agency_uri = agency_uri, creation_time = creation_time,
                        parent_inventory = parent_inventory)

        if geom_sensor is None:
            geom_sensor_orm = self.parent_inventory.project.dbTables['geom_sensor']
            self.geom_sensor = geom_sensor_orm(self.label,
                                               self.serial,
                                               self.type,
                                               agency_uri = self.agency_uri,
                                               author_uri = self.author_uri,
                                               creation_time = self.creation_time)
        else:
            self.geom_sensor = geom_sensor


    @classmethod
    def from_sqlalchemy_orm(cls, parent_inventory, geom_sensor):
        cur_sensor =  cls(parent_inventory = parent_inventory,
                          serial = geom_sensor.serial,
                          type = geom_sensor.type,
                          label = geom_sensor.label,
                          id = geom_sensor.id,
                          author_uri = geom_sensor.author_uri,
                          agency_uri = geom_sensor.agency_uri,
                          creation_time = geom_sensor.creation_time,
                          geom_sensor = geom_sensor)

        for cur_param in geom_sensor.parameters:
            db_param = DbSensorParameter.from_sqlalchemy_orm(cur_sensor, cur_param)
            cur_sensor.parameters.append(db_param)

        return cur_sensor



    @classmethod
    def from_inventory_sensor(cls, parent_inventory, sensor):
        cur_sensor =  cls(parent_inventory = parent_inventory,
                          serial = sensor.serial,
                          type = sensor.type,
                          label = sensor.label,
                          author_uri = sensor.author_uri,
                          agency_uri = sensor.agency_uri,
                          creation_time = sensor.creation_time)

        for cur_parameter in sensor.parameters:
            cur_sensor.add_parameter(DbSensorParameter.from_inventory_sensor_parameter(cur_sensor, cur_parameter))
        return cur_sensor




    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        attr_map = {};
        attr_map['label'] = 'label'
        attr_map['serial'] = 'serial'
        attr_map['type'] = 'type'
        attr_map['rec_channel_name'] = 'rec_channel_name'
        attr_map['channel_name'] = 'channel_name'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        if attr in attr_map.keys():
            self.__dict__[attr] = value
            if 'geom_sensor' in self.__dict__:
                setattr(self.geom_sensor, attr_map[attr], value)
        else:
            self.__dict__[attr] = value


    def add_parameter(self, parameter):
        ''' Add a parameter to the sensor

        Parameters
        ----------
        parameter : :class:`DbSensorParameter`
            The parameter to add to the sensor.
        '''
        if parameter.__class__ is DbSensorParameter:
            self.parameters.append(parameter)
            self.geom_sensor.parameters.append(parameter.geom_sensor_parameter)

            # Add the tf poles and zeros to the database orm.
            geom_tfpz_orm = self.parent_inventory.project.dbTables['geom_tf_pz']
            for cur_pole in parameter.tf_poles:
                parameter.geom_sensor_parameter.tf_pz.append(geom_tfpz_orm(parameter.id, 1, cur_pole.real, cur_pole.imag))
            for cur_zero in parameter.tf_zeros:
                parameter.geom_sensor_parameter.tf_pz.append(geom_tfpz_orm(parameter.id, 0, cur_zero.real, cur_zero.imag))
        elif parameter.__class__ is SensorParameter:
            parameter = self.add_parameter(DbSensorParameter.from_inventory_sensor_parameter(self, parameter))
        else:
            parameter = None

        return parameter



    def update_id(self):
        ''' Update the database if from the geom_sensor instance.
        '''
        if self.geom_sensor is not None:
            self.id = self.geom_sensor.id



class DbSensorParameter(SensorParameter):

    def __init__(self, parent_sensor, sensitivity, sensitivity_units, tf_type,
                 tf_units, tf_normalization_factor, tf_normalization_frequency,
                 id, start_time, end_time, author_uri, agency_uri, creation_time,
                 tf_poles = [], tf_zeros = [],
                 geom_sensor_parameter = None):

        SensorParameter.__init__(self,
                                 parent_sensor = parent_sensor,
                                 sensitivity = sensitivity,
                                 sensitivity_units = sensitivity_units,
                                 start_time = start_time,
                                 end_time = end_time,
                                 tf_type = tf_type,
                                 tf_units = tf_units,
                                 tf_normalization_factor = tf_normalization_factor,
                                 tf_normalization_frequency = tf_normalization_frequency,
                                 author_uri = author_uri,
                                 agency_uri = agency_uri,
                                 creation_time = creation_time,
                                 tf_poles = tf_poles,
                                 tf_zeros = tf_zeros,
                                 id = id)

        if geom_sensor_parameter is None:
            geom_sensor_param_orm = self.parent_inventory.project.dbTables['geom_sensor_param']
            self.geom_sensor_parameter = geom_sensor_param_orm(sensor_id = parent_sensor.id,
                                                     start_time = self.start_time.timestamp,
                                                     end_time = None if self.end_time is None else self.end_time.timestamp,
                                                     tf_normalization_factor = self.tf_normalization_factor,
                                                     tf_normalization_frequency = self.tf_normalization_frequency,
                                                     tf_type = self.tf_type,
                                                     tf_units = self.tf_units,
                                                     sensitivity = self.sensitivity,
                                                     sensitivity_units = self.sensitivity_units,
                                                     agency_uri = self.agency_uri,
                                                     author_uri = self.author_uri,
                                                     creation_time = self.creation_time)
        else:
            self.geom_sensor_parameter = geom_sensor_parameter


    @classmethod
    def from_inventory_sensor_parameter(cls, parent_sensor, sensor_parameter):
        return cls(parent_sensor = parent_sensor,
                   start_time = sensor_parameter.start_time,
                   end_time = sensor_parameter.end_time,
                   tf_normalization_factor = sensor_parameter.tf_normalization_factor,
                   tf_normalization_frequency = sensor_parameter.tf_normalization_frequency,
                   tf_type = sensor_parameter.tf_type,
                   tf_units = sensor_parameter.tf_units,
                   tf_poles = sensor_parameter.tf_poles,
                   tf_zeros = sensor_parameter.tf_zeros,
                   sensitivity = sensor_parameter.sensitivity,
                   sensitivity_units = sensor_parameter.sensitivity_units,
                   author_uri = sensor_parameter.author_uri,
                   agency_uri = sensor_parameter.agency_uri,
                   creation_time = sensor_parameter.creation_time,
                   id = sensor_parameter.id)


    @classmethod
    def from_sqlalchemy_orm(cls, parent_sensor, geom_sensor_parameter):

        if geom_sensor_parameter.start_time is not None:
            start_time = UTCDateTime(geom_sensor_parameter.start_time)
        else:
            start_time = None

        if geom_sensor_parameter.end_time is not None:
            end_time = UTCDateTime(geom_sensor_parameter.end_time)
        else:
            end_time = None

        sensor = cls(parent_sensor = parent_sensor,
                   start_time = start_time,
                   end_time = end_time,
                   tf_normalization_factor = geom_sensor_parameter.tf_normalization_factor,
                   tf_normalization_frequency = geom_sensor_parameter.tf_normalization_frequency,
                   tf_type = geom_sensor_parameter.tf_type,
                   tf_units = geom_sensor_parameter.tf_units,
                   sensitivity = geom_sensor_parameter.sensitivity,
                   sensitivity_units = geom_sensor_parameter.sensitivity_units,
                   id = geom_sensor_parameter.id,
                   author_uri = geom_sensor_parameter.author_uri,
                   agency_uri = geom_sensor_parameter.agency_uri,
                   creation_time = geom_sensor_parameter.creation_time,
                   geom_sensor_parameter = geom_sensor_parameter)

        # Collect the poles and zeros of the transfer function.
        for cur_pz in geom_sensor_parameter.tf_pz:
            if cur_pz.type == 0:
                sensor.tf_zeros.append(complex(cur_pz.complex_real, cur_pz.complex_imag))
            elif cur_pz.type == 1:
                sensor.tf_poles.append(complex(cur_pz.complex_real, cur_pz.complex_imag))

        return sensor


    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        attr_map = {};
        attr_map['start_time'] = 'start_time'
        attr_map['end_time'] = 'end_time'
        attr_map['tf_normalization_factor'] = 'tf_normalization_factor'
        attr_map['tf_normalization_frequency'] = 'tf_normalization_frequency'
        attr_map['tf_type'] = 'tf_type'
        attr_map['tf_units'] = 'tf_units'
        attr_map['sensitivity'] = 'sensitivity'
        attr_map['sensitivity_units'] = 'sensitivity_units'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        if attr in attr_map.keys():
            self.__dict__[attr] = value
            if 'geom_sensor_parameter' in self.__dict__:
                if (attr == 'start_time') or (attr == 'end_time'):
                    setattr(self.geom_sensor_parameter, attr_map[attr], value.timestamp)
                else:
                    setattr(self.geom_sensor_parameter, attr_map[attr], value)
        else:
            self.__dict__[attr] = value


    def update_id(self):
        ''' Update the database if from the geom_sensor instance.
        '''
        if self.geom_sensor_parameter is not None:
            self.id = self.geom_sensor_parameter.id




class DbChannel(Channel):

    def __init__(self, parent_station, name, description, agency_uri,
                 author_uri, creation_time,
                 id = None, geom_channel = None):
        Channel.__init__(self,
                         id = id,
                         name = name,
                         description = description,
                         agency_uri = agency_uri,
                         author_uri = author_uri,
                         parent_station = parent_station)

        if geom_channel is None:
            geom_channel_orm = self.parent_inventory.project.dbTables['geom_channel']
            self.geom_channel = geom_channel_orm(name = self.name,
                                                description = self.description,
                                                agency_uri = self.agency_uri,
                                                author_uri = self.author_uri,
                                                creation_time = self.creation_time)
        else:
            self.geom_channel = geom_channel


    @classmethod
    def from_sqlalchemy_orm(cls, parent_station, geom_channel):
        channel =  cls(parent_station = parent_station,
                       id = geom_channel.id,
                       name = geom_channel.name,
                       description = geom_channel.description,
                       author_uri = geom_channel.author_uri,
                       agency_uri = geom_channel.agency_uri,
                       creation_time = geom_channel.creation_time,
                       geom_channel = geom_channel)

        for cur_stream_to_channel in geom_channel.streams:
            db_stream = DbRecorderStream.from_sqlalchemy_orm(channel, cur_stream_to_channel.stream)
            cur_start_time = UTCDateTime(cur_stream_to_channel.start_time)
            cur_end_time = UTCDateTime(cur_stream_to_channel.end_time)
            channel.streams.append((db_stream, cur_start_time, cur_end_time))
            db_stream.set_parent_inventory(channel.parent_inventory)

        return channel



    @classmethod
    def from_inventory_channel(cls, parent_station, channel):
        cur_channel =  cls(parent_station = parent_station,
                           name = channel.name,
                           description = channel.description,
                           author_uri = channel.author_uri,
                           agency_uri = channel.agency_uri,
                           creation_time = channel.creation_time)

        for cur_stream, cur_start_time, cur_end_time in channel.streams:
            cur_channel.add_stream(DbRecorderStream.from_inventory_stream(cur_channel, cur_stream),
                                   cur_start_time,
                                   cur_end_time)

        return cur_channel


    def __setattr__(self, attr, value):
        ''' Control the attribute assignements.
        '''
        attr_map = {};
        attr_map['name'] = 'name'
        attr_map['description'] = 'description'
        attr_map['author_uri'] = 'author_uri'
        attr_map['agency_uri'] = 'agency_uri'
        attr_map['creation_time'] = 'creation_time'

        if attr in attr_map.keys():
            self.__dict__[attr] = value
            if 'geom_channel' in self.__dict__:
                setattr(self.geom_channel, attr_map[attr], value)
        else:
            self.__dict__[attr] = value


    def add_stream(self, cur_stream, start_time, end_time):
        ''' Add a stream to the channel.

        '''
        if((cur_stream, start_time) in [(x[0], x[1]) for x in self.streams]):
            # The sensor is already assigned to the station for this timespan.
            return None

        self.streams.append((cur_stream, start_time, end_time))
        self.has_changed = True

        # Add the sensor the the database orm.
        if start_time is not None:
            start_time_timestamp = start_time.timestamp
        else:
            start_time_timestamp = None

        if end_time is not None:
            end_time_timestamp = end_time.timestamp
        else:
            end_time_timestamp = None

        geom_stream_to_channel_orm = self.parent_inventory.project.dbTables['geom_stream_to_channel']
        geom_stream_to_channel = geom_stream_to_channel_orm(channel_id = self.id,
                                        stream_id = cur_stream.id,
                                        start_time = start_time_timestamp,
                                        end_time = end_time_timestamp)
        geom_stream_to_channel.stream = cur_stream.geom_rec_stream
        self.geom_channel.streams.append(geom_stream_to_channel)

        return cur_stream



    def update_id(self):
        ''' Update the database if from the geom_sensor instance.
        '''
        if self.geom_channel is not None:
            self.id = self.geom_channel.id
