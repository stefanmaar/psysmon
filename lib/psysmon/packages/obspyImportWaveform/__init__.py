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

name = "obspyImportWaveform"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The obspyImportWaveform packages"
website = "http://www.stefanmertl.com"


def nodeFactory():
    from importWaveform import ImportWaveform

    nodeTemplates = []

    # Create a pSysmon collection node template and add it to the package.
    options = {}
    options['inputFiles'] = []                     # The files to import.
    options['lastDir'] = ""                        # The last used directory.
    myNodeTemplate = ImportWaveform(name = 'import waveform',
                                    mode = 'editable',
                                    category = 'Data Import',
                                    tags = ['stable'],
                                    options = options
                                    )
    nodeTemplates.append(myNodeTemplate)

    return nodeTemplates



def databaseFactory(base):
    from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey
    from sqlalchemy.orm import relationship
    
    tables = []

    # Create the traceheader table mapper class.
    class Traceheader(base):
        __tablename__ = 'traceheader'

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        file_type = Column(String(10), nullable=False)
        wf_id = Column(Integer(10), nullable=False, default=-1)
        filename = Column(String(255), nullable=False)
        orig_path = Column(Text, nullable=False)
        network = Column(String(10), nullable=False, default='')
        recorder_serial = Column(String(45), nullable=False)
        channel = Column(String(45), nullable=False)
        location = Column(String(3), nullable=False)
        sps = Column(Integer(10), nullable=False)
        numsamp = Column(Integer(10), nullable=False)
        begin_date = Column(String(26), nullable=False)
        begin_time = Column(Float(53), nullable=False)
        station_id = Column(Integer(10), nullable=False, default=-1)
        recorder_id = Column(Integer(10), nullable=False, default=-1)
        sensor_id = Column(Integer(10), nullable=False, default=-1)


    tables.append(Traceheader)


    # Create the waveformdir table mapper class.
    class WaveformDir(base):
        __tablename__ = 'waveformDir'

        id = Column(Integer(10), primary_key=True, autoincrement=True)
        directory = Column(String(255), nullable=False, unique=True)
        description = Column(String(255), nullable=False)
        aliases = relationship("WaveformDirAlias", cascade="all, delete, delete-orphan")

        def __init__(self, directory, description):
            self.directory = directory
            self.description = description

    tables.append(WaveformDir)


    # Create the waveformdiralias database table.
    class WaveformDirAlias(base):
        __tablename__ = 'waveformDirAlias'

        wf_id = Column(Integer(10), 
                       ForeignKey('waveformDir.id', onupdate="cascade"), 
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


