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

name = "pick"                                 # The package name.
version = "0.0.1"                               # The package version.
author = "Stefan Mertl"                         # The package author.
minPsysmonVersion = "0.0.1"                     # The minimum pSysmon version required.
description = "Handle traveltime and amplitude picks."            # The package description.
website = "http://psysmon.mertl-research.at"    # The package website.

# Specify the module(s) where to search for collection node classes.
collection_node_modules = []

# Specify the module(s) where to search for plugin classes.
plugin_modules = []

# Specify the module(s) where to search for processing node classes.
processing_node_modules = []


def databaseFactory(base):
    from sqlalchemy import Column
    from sqlalchemy import Integer
    from sqlalchemy import String
    from sqlalchemy import Text
    from sqlalchemy import Float
    from sqlalchemy import ForeignKey
    from sqlalchemy import UniqueConstraint
    from sqlalchemy.orm import relationship

    tables = []


    ###########################################################################
    # PICK_CATALOG database table mapper class.
    class PickCatalogOrm(base):
        __tablename__  = 'pick_catalog'
        __table_args__ = (
                          UniqueConstraint('name'),
                          {'mysql_engine': 'InnoDB'}
                         )

        id = Column(Integer, primary_key = True, autoincrement = True)
        name = Column(String(255), nullable = False)
        mode = Column(String(255), nullable = False)
        description = Column(Text, nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)

        events = relationship('PickOrm',
                               cascade = 'all',
                               backref = 'parent',
                               lazy = 'select')

        def __init__(self, name, mode, description,
                     agency_uri, author_uri, creation_time):
            self.name = name
            self.mode = mode
            self.description = description
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(PickCatalogOrm)


    class PickOrm(base):
        __tablename__ = 'pick'
        __table_args__ = (
                          {'mysql_engine': 'InnoDb'}
                         )

        id = Column(Integer, primary_key = True, autoincrement = True)
        catalog_id = Column(Integer,
                            ForeignKey('pick_catalog.id',
                                       onupdate = 'cascade',
                                       ondelete = 'set null'),
                            nullable = True)
        channel_id = Column(Integer,
                            ForeignKey('geom_channel.id',
                                       onupdate = 'cascade',
                                       ondelete = 'set null'),
                            nullable = True)
        stream_id = Column(Integer,
                           ForeignKey('geom_rec_stream.id',
                                      onupdate = 'cascade',
                                      ondelete = 'set null'),
                           nullable = True)
        label = Column(String(255), nullable = False)
        time = Column(Float(53), nullable = False)
        amp1 = Column(Float, nullable = False)
        amp2 = Column(Float, nullable = True)
        first_motion = Column(Integer, nullable = True)
        error = Column(Float, nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)


        def __init__(self, catalog_id, channel_id, stream_id,
                     label, time, amp1, amp2,
                     first_motion, error, agency_uri, author_uri,
                     creation_time):
            self.catalog_id = catalog_id
            self.channel_id = channel_id
            self.stream_id = stream_id
            self.label = label
            self.time = time
            self.amp1 = amp1
            self.amp2 = amp2
            self.first_motion = first_motion
            self.error = error
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(PickOrm)


    return tables
