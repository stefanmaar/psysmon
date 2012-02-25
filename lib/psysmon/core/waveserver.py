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
Module for providing the waveform data from various sources.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import logging
import string
from obspy.core import read, Trace, Stream

class WaveServer:
    '''The waveserver class.


    Attributes
    ----------

    '''

    def __init__(self, source, project, wsUrl=None): 
        '''The constructor.

        Create an instance of the Project class.

        Parameters
        ----------
        source : String
            The waveform source.

            - sqlDB (A pSymson formatted SQL database)
            - earthworm (A earthworm waverserver)
            - css (A CSS formatted flat file database)
        '''
        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The project name.
        self.source = source

        # The waveform resource connector.
        self.connector = None

        if string.lower(self.source) == 'sqldb':
            self.connector = SqlConnector(project)
        else:
            self.logger.error('The required source "%s" is not supported.', self.source)


    def getWaveform(self, 
                    network = None, 
                    station = None, 
                    location = None, 
                    channel = None, 
                    beginTime = None, 
                    endTime = None):
        ''' Get the waveform data for the specified parameters.

        Parameters
        ----------
        network : String
            The network name.

        station : String
            The station name.

        location : String
            The location specifier.

        channel : String
            The channel name.

        beginTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.
        '''
        self.connector.getWaveform(network,
                                   station,
                                   location,
                                   channel,
                                   beginTime,
                                   endTime)

class SqlConnector:
    ''' The SQL database waveserver connector.

    This class provides the connector to a pSysmon formatted SQL waveform 
    database. 
    '''

    def __init__(self, project):

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The current psysmon project.
        self.project = project

        # The current database session.
        self.dbSession = project.getDbSession()

        # The traceheader database table.
        self.traceheader = self.project.dbTables['traceheader']

        # The waveform directory table.
        self.waveformDir = self.project.dbTables['waveform_dir']

        # The waveform directory alias table.
        self.waveformDirAlias = self.project.dbTables['waveform_dir_alias']

        # The station database table.
        self.geomStation = self.project.dbTables['geom_station']


    def getWaveform(self, 
                    network = None, 
                    station = None, 
                    location = None, 
                    channel = None, 
                    beginTime = None, 
                    endTime = None):
        ''' Get the waveform data for the specified parameters.

        Parameters
        ----------
        network : String
            The network name.

        station : String
            The station name.

        location : String
            The location specifier.

        channel : String
            The channel name.

        beginTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.
        '''

        self.logger.debug("Querying...")

        # Create the standard query.
        query = self.dbSession.query(self.traceheader.filename, 
                                     self.waveformDirAlias.alias).\
                               filter(self.traceheader.wf_id ==self.waveformDir.id).\
                               filter(self.waveformDir.id == self.waveformDirAlias.wf_id, 
                                      self.waveformDirAlias.user == self.project.activeUser.name)

        # Check for station filter option.
        if station:
            query = query.filter(self.traceheader.station_id == self.geomStation.id, 
                                 self.geomStation.name.in_(station))

        for curHeader in query:
            self.logger.debug("%s", curHeader)


        self.logger.debug("....finished.")



