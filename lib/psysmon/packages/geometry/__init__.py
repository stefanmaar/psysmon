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

name = "geometry"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The geometry package."
website = "http://www.stefanmertl.com"


def nodeFactory():
    from applyGeometry import ApplyGeometry
    from editGeometry import EditGeometry

    nodeTemplates = []

    # Create a pSysmon collection node template and add it to the package.
    options = {}
    myNodeTemplate = EditGeometry(name = 'edit geometry',
                                  mode = 'standalone',
                                  category = 'Geometry',
                                  tags = ['stable'],
                                  options = options
                                  )
    nodeTemplates.append(myNodeTemplate) 

    # Create a pSysmon collection node template and add it to the package.
    options = {}
    myNodeTemplate = ApplyGeometry(name = 'apply geometry',
                                   mode = 'uneditable',
                                   category = 'Geometry',
                                   tags = ['stable'],
                                   options = options
                                   )
    nodeTemplates.append(myNodeTemplate)

    return nodeTemplates



def databaseFactory(base):
    from sqlalchemy import Column, Integer, String, Float
    from sqlalchemy import ForeignKey, UniqueConstraint
    from sqlalchemy.orm import relationship

    tables = []

    # Create the geom_recorder table mapper class.
    class GeomRecorder(base):
        __tablename__ = 'geom_recorder'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        serial = Column(String(45), nullable=False)
        type = Column(String(255), nullable=False)
        UniqueConstraint('serial', 'type')

        sensors = relationship('GeomSensor', cascade='all, delete-orphan')

        
        def __init__(self, serial, type):
            self.serial = serial
            self.type = type


    tables.append(GeomRecorder)


    # Create the geom_sensor table mapper class.
    class GeomSensor(base):
        __tablename__ = 'geom_sensor'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        recorder_id = Column(Integer(10), ForeignKey('geom_recorder.id', onupdate='cascade'), nullable=False)
        label = Column(String(255), nullable=False)
        serial = Column(String(45), nullable=False)
        type = Column(String(255), nullable=False)
        rec_channel_name = Column(String(10), nullable=False)
        channel_name = Column(String(10), nullable=False)
        UniqueConstraint('recorder_id', 'serial', 'type', 'rec_channel_name', 'channel_name')

        parameters = relationship('GeomSensorParam', cascade='all, delete-orphan')

        
        def __init__(self, recorder_id, label, serial, type, rec_channel_name, channel_name):
            self.recorder_id = recorder_id
            self.label = label
            self.serial = serial
            self.type = type
            self.rec_channel_name = rec_channel_name
            self.channel_name = channel_name


    tables.append(GeomSensor)


    # Create the geom_sensor_param table mapper.
    class GeomSensorParam(base):
        __tablename__ = 'geom_sensor_param'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        sensor_id = Column(Integer(10), ForeignKey('geom_sensor.id', onupdate='cascade'), nullable=False, default=-1)
        start_time = Column(Float(53))
        end_time = Column(Float(53))
        normalization_factor = Column(Float)
        normalization_frequency = Column(Float)
        type = Column(String(150))
        tf_units = Column(String(20))
        gain = Column(Float)
        sensitivity = Column(Float(53))
        sensitivity_units = Column(String(30))
        bitweight = Column(Float(53))
        bitweight_units = Column(String(15))
        UniqueConstraint = ('sensor_id', 'start_time', 'end_time')

        tfPz = relationship('GeomTfPz', cascade='all, delete-orphan')


        def __init__(self, sensor_id, start_time, end_time, normalization_factor, 
                     normalization_frequency, type, tf_units, gain, sensitivity, 
                     bitweight, bitweight_units):
            self.sensor_id = sensor_id
            self.start_time = start_time
            self.end_time = end_time
            self.normalization_factor = normalization_factor
            self.normalization_frequency = normalization_frequency
            self.type = type
            self.tf_units = tf_units
            self.gain = gain
            self.sensitivity = sensitivity
            self.bitweight = bitweight
            self.bitweight_units = bitweight_units


    tables.append(GeomSensorParam)


    # Create the geom_tf_pz table mapper.
    class GeomTfPz(base):
        __tablename__ = 'geom_tf_pz'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        param_id = Column(Integer(10), ForeignKey('geom_sensor_param.id', onupdate='cascade'), nullable=False)
        type = Column(Integer(2), nullable=False, default=1)
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

        stations = relationship('GeomStation', cascade='all, delete-orphan')


        def __init__(self, name, description, type):
            self.name = name
            self.description = description
            self.type = type

    tables.append(GeomNetwork)


    # Create the geom_station table mapper class.
    class GeomStation(base):
        __tablename__ = 'geom_station'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        net_name = Column(String(10), ForeignKey('geom_network.name', onupdate='cascade'), nullable=False)
        name = Column(String(10), nullable=False)
        location = Column(String(3), nullable=False)
        X = Column(Float(53), nullable=False)
        Y = Column(Float(53), nullable=False)
        Z = Column(Float(53), nullable=False)
        coord_system = Column(String(50), nullable=False)
        description = Column(String(255))
        UniqueConstraint('net_name', 'name', 'location')

        sensors = relationship('GeomSensorTime')


        def __init__(self, net_name, name, location, X, Y, Z, coord_system, 
                     description):
            self.net_name = net_name
            self.name = name
            self.location = location
            self.X = X
            self.Y = Y
            self.Z = Z
            self.coord_system = coord_system
            self.description = description

    tables.append(GeomStation)


    # Create the geom_sensor_time table mapper class.
    class GeomSensorTime(base):
        __tablename__ = 'geom_sensor_time'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        stat_id = Column(Integer(10), ForeignKey('geom_station.id', onupdate='cascade'), primary_key=True, nullable=False)
        sensor_id = Column(Integer(10), ForeignKey('geom_sensor.id', onupdate='cascade'), primary_key=True, nullable=False)
        start_time = Column(Float(53), primary_key=True, nullable=False)
        end_time = Column(Float(53))

        child = relationship('GeomSensor')

        def __init__(self, stat_id, sensor_id, start_time, end_time):
            self.stat_id = stat_id
            self.sensor_id = sensor_id
            self.start_time = start_time
            self.end_time = end_time


    tables.append(GeomSensorTime)


    return tables
