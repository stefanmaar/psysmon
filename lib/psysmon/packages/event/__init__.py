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
    # AUTHOR_INFO table mapper class
    class QmlAuthorInfo(base):
        __tablename__ = 'qml_author_info'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        agency_id = Column(String(64), nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author = Column(String(128), nullable = True)
        author_uri = Column(String(255), nullable = True)


    tables.append(QmlAuthorInfo)


    ###########################################################################
    # COMMENT table mapper class
    class QmlComment(base):
        __tablename__ = 'qml_comment'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key = True, autoincrement = True)
        parent_rid = Column(String(255), nullable = False)
        author_info_id = Column(Integer(10),
                                ForeignKey('qml_author_info.id',
                                           onupdate = 'cascade',
                                           ondelete = 'set null'),
                                nullable = True)
        text = Column(Text, nullable = True)
        resource_id = Column(String(255), nullable = True)
        creation_time = Column(DateTime(), nullable = True)
        version = Column(String(30), nullable = True)

    tables.append(QmlComment)


    ###########################################################################
    # EVENT_PARAMETERS table mapper class
    class QmlEventParameters(base):
        __tablename__  = 'qml_event_parameters'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key = True, autoincrement = True)
        public_id = Column(String(255), nullable = False)
        description = Column(Text, nullable = True)
        creation_time = Column(DateTime(), nullable = True)
        version = Column(String(30), nullable = True)
        UniqueConstraint('public_id')

    tables.append(QmlEventParameters)


    ###########################################################################
    # EVENT_PARAMETERS table mapper class
    class QmlEvent(base):
        __tablename__  = 'qml_event'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer(10), primary_key = True, autoincrement = True)
        ev_param_id = Column(Integer(10), 
                             ForeignKey('qml_event_parameters.id',
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

    tables.append(QmlEvent)


    ###########################################################################
    # DETECTION table mapper class
    class QmlDetection(base):
        __tablename__  = 'qml_detection'
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

    tables.append(QmlEvent)


    return tables




def nodeFactory():
    from collection_nodes import EventExample

    nodeTemplates = []

    myTemplate = EventExample(name = 'event example node',
                              mode = 'uneditable',
                              category = 'Example',
                              tags = ['stable', 'example'],
                              options = None,
                              requires = None, 
                              provides = ('exp2InputData', )
                             )
    nodeTemplates.append(myTemplate)

    return nodeTemplates





