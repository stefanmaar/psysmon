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

name = "obspyImportWaveform"
version = "0.0.4"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The obspyImportWaveform packages"
website = "http://www.stefanmertl.com"

# Specify the module(s) where to search for collection node classes.
collection_node_modules = ['importWaveform', 'import_filesystem_data']

'''
Database change history.
version 0.0.2 - 2016-01-27
Removed the location field. The location and channel values in the obspy
trace header is used to build the stream name LOCATION:CHANNEL.
version 0.0.3 - 2017-10-03
Added the file_ext, first_import and last_scan columns to the waveformDir
table.
version 0.0.4 - 2017-10-03
Added a unique constraint to the traceheader table (wf_id, filename).

'''

def databaseFactory(base):
    from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
    from sqlalchemy.orm import relationship
    from sqlalchemy import UniqueConstraint

    tables = []

    # Create the datafile table mapper class.
    class Datafile(base):
        ''' The datafile database table mapper.

        History
        -------
        1.0.0 - 2017-11-24
        Creation of the table.

        1.0.1 - 2017-11-25
        Changed the ondelete of wf_id to cascade.
        '''
        # TODO: Add the begin_time or date to the unique constraint. One file
        # can hold multiple traces. Currently these files can't be imported.
        __tablename__ = 'datafile'
        __table_args__ = (
                          UniqueConstraint('wf_id', 'filename'),
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '1.0.1'

        id = Column(Integer, primary_key=True, autoincrement=True)
        wf_id = Column(Integer,
                       ForeignKey('waveform_dir.id',
                                  onupdate = 'cascade',
                                  ondelete = 'cascade'),
                       nullable=True)
        filename = Column(String(255), nullable=False)
        filesize = Column(Float, nullable=False)
        file_type = Column(String(10), nullable=False)
        orig_path = Column(Text, nullable=False)
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))

        traceheaders = relationship('Traceheader',
                                    backref = 'datafile')


    tables.append(Datafile)


    # Create the traceheader table mapper class.
    class Traceheader(base):
        ''' The traceheader database table mapper.

        History
        -------
        1.1.0 - 2017-11-23
        Added the filesize column.

        2.0.0 - 2017-11-24
        Removed the columns which have been moved to the datafile table.
        Added the datafile_id column referencing the datafile.id column.

        2.0.1 - 2017-11-25
        Changed the ondelte of datafile_id to cascade.

        '''
        # TODO: Add the begin_time or date to the unique constraint. One file
        # can hold multiple traces. Currently these files can't be imported.
        __tablename__ = 'traceheader'
        __table_args__ = (
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '2.0.1'

        id = Column(Integer, primary_key=True, autoincrement=True)
        datafile_id = Column(Integer,
                             ForeignKey('datafile.id',
                                        onupdate = 'cascade',
                                        ondelete = 'cascade'),
                             nullable=True)
        recorder_serial = Column(String(45), nullable=False)
        stream = Column(String(45), nullable=False)
        network = Column(String(10), nullable=False, default='')
        sps = Column(Float(53), nullable=False)
        numsamp = Column(Integer, nullable=False)
        begin_date = Column(String(26), nullable=False)
        begin_time = Column(Float(53), nullable=False)
        agency_uri = Column(String(20))
        author_uri = Column(String(20))
        creation_time = Column(String(30))


    tables.append(Traceheader)

    # Create the waveformdir table mapper class.
    class WaveformDir(base):
        __tablename__ = 'waveform_dir'
        __table_args__ = {'mysql_engine': 'InnoDB'}
        _version = '1.0.0'

        id = Column(Integer, primary_key=True, autoincrement=True)
        directory = Column(String(255), nullable=False, unique=True)
        description = Column(String(255), nullable=False)
        file_ext = Column(String(255), nullable=False)
        first_import = Column(String(30), nullable = True)
        last_scan = Column(String(30), nullable = True)

        aliases = relationship("WaveformDirAlias", cascade="all, delete-orphan")

        def __init__(self, directory, description, file_ext,
                     first_import, last_scan):
            self.directory = directory
            self.description = description
            self.file_ext = file_ext
            self.first_import = first_import
            self.last_scan = last_scan

    tables.append(WaveformDir)


    # Create the waveformdiralias database table.
    class WaveformDirAlias(base):
        __tablename__ = 'waveform_dir_alias'
        __table_args__ = {'mysql_engine': 'InnoDB'}
        _version = '1.0.0'

        wf_id = Column(Integer,
                       ForeignKey('waveform_dir.id', onupdate="cascade"),
                       nullable=False, 
                       autoincrement=False, 
                       primary_key=True)
        user = Column(String(45), nullable=False, primary_key=True)
        alias = Column(String(255), nullable=False)


        def __init__(self, user, alias):
            self.user = user
            self.alias = alias

    tables.append(WaveformDirAlias)

    return tables


