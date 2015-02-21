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

name = "geometry"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The geometry package."
website = "http://www.stefanmertl.com"

# Specify the module(s) where to search for collection node classes.
collection_node_modules = ['applyGeometry',
                           'editGeometry']


def databaseFactory(base):
    from sqlalchemy import Column, Integer, String, Float
    from sqlalchemy import ForeignKey, UniqueConstraint
    from sqlalchemy.orm import relationship

    tables = []

    # Create the geom_recorder table mapper class.
    class GeomRecorder(base):
        __tablename__ = 'geom_recorder'
        __table_args__ = (
                          UniqueConstraint('serial', 'type'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key=True, autoincrement=True)
        serial = Column(String(45), nullable=False)
        type = Column(String(255), nullable=False)
        description = Column(String(255), nullable=True)
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        streams = relationship('GeomRecorderStream',
                               cascade = 'all',
                               backref = 'parent')


        def __init__(self, serial, type,
                agency_uri, author_uri, creation_time):
            self.serial = serial
            self.type = type
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

        def __repr__(self):
            return "Recorder\nid: %d\nserial: %s\ntype: %s\n" % (self.id, self.serial, self.type)

    tables.append(GeomRecorder)



    class GeomRecorderStream(base):
        __tablename__ = 'geom_rec_stream'
        __table_args__ = (
                          UniqueConstraint('recorder_id', 'name'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key=True, autoincrement=True)
        recorder_id = Column(Integer,
                             ForeignKey('geom_recorder.id',
                                        onupdate='cascade',
                                        ondelete='set null'),
                             nullable=True)
        name = Column(String(20), nullable = False)
        label = Column(String(20), nullable = False)
        gain = Column(Float)
        bitweight = Column(Float(53))
        bitweight_units = Column(String(15))
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        sensors = relationship('GeomSensorToStream',
                               backref = 'parent')

        def __init__(self, recorder_id, name, label,
                gain, bitweight, bitweight_units,
                agency_uri, author_uri, creation_time):
            self.recorder_id = recorder_id
            self.name = name
            self.label = label
            self.gain = gain
            self.bitweight = bitweight
            self.bitweight_units = bitweight_units
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time


        def __repr__(self):
            return "GeomRecorderStream\id: %d\nrecorder_id: %d\nname: %s\nlabel: %s\nagency_uri: %s\nauthor_uri: %s\ncreation_time: %s\n" % (self.id,
                        self.recorder_id, self.name, self.label, self.agency_uri, self.author_uri, self.creation_time)

    tables.append(GeomRecorderStream)


    class GeomSensorToStream(base):
        __tablename__ = 'geom_sensor_to_stream'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        stream_id = Column(Integer, ForeignKey('geom_rec_stream.id', onupdate='cascade'), primary_key=True, nullable=False)
        sensor_id = Column(Integer, ForeignKey('geom_sensor.id', onupdate='cascade'), primary_key=True, nullable=False)
        start_time = Column(Float(53), nullable=False)
        end_time = Column(Float(53))

        sensor = relationship('GeomSensor')

        def __init__(self, stream_id, sensor_id, start_time, end_time):
            self.stream_id = stream_id
            self.sensor_id = sensor_id
            self.start_time = start_time
            self.end_time = end_time


    tables.append(GeomSensorToStream)






    # Create the geom_sensor table mapper class.
    class GeomSensor(base):
        __tablename__ = 'geom_sensor'
        __table_args__ = (
                          UniqueConstraint('serial', 'type'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key=True, autoincrement=True)
        serial = Column(String(45), nullable=False)
        component = Column(String(45), nullable=False)
        type = Column(String(255), nullable=False)
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        parameters = relationship('GeomSensorParam', 
                                  cascade = 'all',
                                  backref = 'parent')


        def __init__(self, serial, type, component,
                agency_uri, author_uri, creation_time):
            self.serial = serial
            self.type = type
            self.component = component
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

        def __repr__(self):
            return "id: %s\nserial: %s\ntype: %s\ncomponent: %s\n" % (str(self.id),
                                                                  self.serial,
                                                                  self.type,
                                                                  self.component
                                                                  )


    tables.append(GeomSensor)


    # Create the geom_sensor_param table mapper.
    class GeomSensorParam(base):
        __tablename__ = 'geom_sensor_param'
        __table_args__ = (
                          UniqueConstraint('sensor_id', 'start_time', 'end_time'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key=True, autoincrement=True)
        sensor_id = Column(Integer, ForeignKey('geom_sensor.id', onupdate='cascade'), nullable=True, default=-1)
        start_time = Column(Float(53))
        end_time = Column(Float(53))
        tf_normalization_factor = Column(Float)
        tf_normalization_frequency = Column(Float)
        tf_type = Column(String(150))
        tf_units = Column(String(20))
        sensitivity = Column(Float(53))
        sensitivity_units = Column(String(30))
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        tf_pz = relationship('GeomTfPz', cascade='all')


        def __init__(self, sensor_id, start_time, end_time, tf_normalization_factor,
                     tf_normalization_frequency, tf_type, tf_units, sensitivity,
                     sensitivity_units, agency_uri, author_uri, creation_time):
            self.sensor_id = sensor_id
            self.start_time = start_time
            self.end_time = end_time
            self.tf_normalization_factor = tf_normalization_factor
            self.tf_normalization_frequency = tf_normalization_frequency
            self.tf_type = tf_type
            self.tf_units = tf_units
            self.sensitivity = sensitivity
            self.sensitivity_units = sensitivity_units
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time


    tables.append(GeomSensorParam)


    # Create the geom_tf_pz table mapper.
    class GeomTfPz(base):
        __tablename__ = 'geom_tf_pz'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer, primary_key=True, autoincrement=True)
        param_id = Column(Integer, ForeignKey('geom_sensor_param.id', onupdate='cascade'), nullable=False)
        type = Column(Integer, nullable=False, default=1)
        complex_real = Column(Float, nullable=False)
        complex_imag = Column(Float, nullable=False)


        def __init__(self, param_id, type, complex_real, complex_imag):
            self.param_id = param_id
            self.type = type
            self.complex_real = complex_real
            self.complex_imag = complex_imag

    tables.append(GeomTfPz)



    # Create the geom_network table mapper.
    class GeomNetwork(base):
        __tablename__ = 'geom_network'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        name = Column(String(10), primary_key=True, nullable=False)
        description = Column(String(255))
        type = Column(String(255))
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        stations = relationship('GeomStation', 
                                cascade = 'all', 
                                backref = 'parent')


        def __init__(self, name, description, type,
                agency_uri, author_uri, creation_time):
            self.name = name
            self.description = description
            self.type = type
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time


    tables.append(GeomNetwork)


    # Create the geom_station table mapper class.
    class GeomStation(base):
        __tablename__ = 'geom_station'
        __table_args__ = (
                          UniqueConstraint('network', 'name', 'location'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key=True, autoincrement=True)
        network = Column(String(10), ForeignKey('geom_network.name', onupdate='cascade'), nullable=True)
        name = Column(String(20), nullable=False)
        location = Column(String(3), nullable=False)
        x = Column(Float(53), nullable=False)
        y = Column(Float(53), nullable=False)
        z = Column(Float(53), nullable=False)
        coord_system = Column(String(50), nullable=False)
        description = Column(String(255))
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        channels = relationship('GeomChannel')


        def __init__(self, network, name, location, x, y, z, coord_system,
                     description, agency_uri, author_uri, creation_time):
            self.network = network
            self.name = name
            self.location = location
            self.x = x
            self.y = y
            self.z = z
            self.coord_system = coord_system
            self.description = description
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time


        def __repr__(self):
            return "Station\nname: %s\nlocation: %s\nx: %f\ny: %f\nz: %f\ncoord_system: %s\ndescription: %s\n" % (self.name, self.location, self.x, self.y, self.z, self.coord_system, self.description)

    tables.append(GeomStation)


    class GeomChannel(base):
        __tablename__ = 'geom_channel'
        __table_args__ = (
                          UniqueConstraint('name'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key=True, autoincrement=True)
        station_id = Column(Integer, ForeignKey('geom_station.id', onupdate='cascade'), primary_key=True, nullable=False)
        name = Column(String(20))
        description = Column(String(255))
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        streams = relationship('GeomStreamToChannel')


        def __init__(self, name, description, agency_uri,
                     author_uri, creation_time):
            self.name = name
            self.description = description
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(GeomChannel)




    class GeomStreamToChannel(base):
        __tablename__ = 'geom_stream_to_channel'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer, primary_key=True, autoincrement=True)
        channel_id = Column(Integer, ForeignKey('geom_channel.id', onupdate='cascade'), primary_key=True, nullable=False)
        stream_id = Column(Integer, ForeignKey('geom_rec_stream.id', onupdate='cascade'), primary_key=True, nullable=False)
        start_time = Column(Float(53), nullable=False)
        end_time = Column(Float(53))

        stream = relationship('GeomRecorderStream')

        def __init__(self, channel_id, stream_id, start_time, end_time):
            self.channel_id = channel_id
            self.stream_id = stream_id
            self.start_time = start_time
            self.end_time = end_time


    tables.append(GeomStreamToChannel)


    return tables
