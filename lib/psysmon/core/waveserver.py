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

import string

class WaveServer:
    '''The waveserver class.


    Attributes
    ----------
    activeUser : String
        The currently active user.

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

        # The project name.
        self.source = source

        # The waveform resource connector.
        self.connector = None

        if string.lower(self.source) == 'sqldb':
            self.connector = SqlConnector(project.getDbSession(), 
                                          project.dbTables['traceheader'])


    def getWaveform(self, network, station, location, channel, beginTime, endTime):
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

    def __init__(self, dbSession, traceheaderTable):

        # The current database session.
        self.dbSession = dbSession

        # The traceheader database table.
        self.table = traceheaderTable


    def getWaveform(self, network, station, location, channel, beginTime, endTime):
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

        for val in self.dbSession.query(self.table):
            print "Querying..."
            print val



