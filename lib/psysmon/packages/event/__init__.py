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

name = "events"                                 # The package name.
version = "0.0.1"                               # The package version.
author = "Stefan Mertl"                         # The package author.
minPsysmonVersion = "0.0.1"                     # The minimum pSysmon version required.
description = "The events core package"            # The package description.
website = "http://www.stefanmertl.com"          # The package website.


def databaseFactory(base):
    from sqlalchemy import Column
    from sqlalchemy import Integer
    from sqlalchemy import String
    from sqlalchemy import Text
    from sqlalchemy import Float
    from sqlalchemy import DateTime
    from sqlalchemy import ForeignKey
    from sqlalchemy import UniqueConstraint
    from sqlalchemy.orm import relationship

    tables = []

    ###########################################################################
    # EVENT_SET table mapper class
    class EventSetDb(base):
        __tablename__  = 'event_set'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key = True, autoincrement = True)
        public_id = Column(String(255), nullable = False)
        description = Column(Text, nullable = True)
        creation_time = Column(DateTime(), nullable = True)
        version = Column(String(30), nullable = True)
        UniqueConstraint('public_id')

    tables.append(EventSetDb)


    ###########################################################################
    # EVENT table mapper class
    class EventDb(base):
        __tablename__  = 'event'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key = True, autoincrement = True)
        ev_param_id = Column(Integer(10), 
                             ForeignKey('event_set.id',
                                        onupdate = 'cascade', 
                                        ondelete = 'set null'),
                             nullable = True)
        public_id = Column(String(255), nullable = False)
        pref_origin_id = Column(String(255), nullable = True)
        pref_magnitude_id = Column(String(255), nullable = True)
        pref_focmec_id = Column(String(255), nullable = True)
        ev_type = Column(String(50), nullable = True)
        ev_type_certainty = Column(String(50), nullable = True)
        creation_time = Column(DateTime(), nullable = True)
        version = Column(String(30), nullable = True)
        UniqueConstraint('public_id')

    tables.append(EventDb)


    ###########################################################################
    # DETECTION table mapper class
    class DetectionDb(base):
        __tablename__  = 'detection'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key = True, autoincrement = True)
        public_id = Column(String(255), nullable = False)
        sensor_id = Column(Integer(10), 
                           ForeignKey('geom_sensor.id',
                                      onupdate = 'cascade',
                                      ondelete = 'set null'),
                           nullable = True)
        start_time = Column(Float(53), nullable = False)
        end_time = Column(Float(53), nullable = False)
        creation_time = Column(DateTime(), nullable = True)
        version = Column(String(30), nullable = True)
        UniqueConstraint('public_id')

    tables.append(DetectionDb)


    return tables




def nodeFactory():
    from collection_nodes import EventExample

    nodeTemplates = [EventExample, ]

    return nodeTemplates





