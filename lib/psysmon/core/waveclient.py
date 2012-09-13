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
import os
from obspy.core import read, Stream
from obspy.earthworm import Client

class WaveClient:
    '''The WaveClient class.


    Attributes
    ----------

    '''

    def __init__(self, name, mode): 
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

        # The name of the waveclient.
        self.name = name

        # The mode of the waveclient.
        self.mode = mode

        # The options of the waveclient.
        # The options can vary depending on the mode of the waveclient.
        # The options attribute is a dictionary with the option name as the key
        # and the option values as the value.
        self.options = {}

        # The available data of the waveclient. This includes the
        # currently displayed time period and the preloaded data in
        # front and behind the time period.
        self.stock = Stream()


    def get_from_stock(self, network, station, location, channel, start_time, end_time):
        ''' Get the data of the specified scnl from the stock data.
        
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

        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.

        Returns
        -------
        stream : :class:`obspy.core.Stream`
            The requested waveform data. All traces are packed into one stream.
        
        '''
        if location == '--':
            location = None

        curStream = self.stock.select(station = station,
                                      channel = channel,
                                      network = network,
                                      location = location)
        curStream = curStream.copy()
        curStream.trim(starttime = start_time, 
                       endtime = end_time)

        return curStream

                                       
    def add_to_stock(self, stream):
        ''' Add the passed stream to the stock data.

        '''
        self.stock += stream
        self.stock.merge(stream)



    def getWaveform(self, 
                    startTime,
                    endTime,
                    network = None, 
                    station = None, 
                    location = None, 
                    channel = None):
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

        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.

        Returns
        -------
        stream : :class:`obspy.core.Stream`
            The requested waveform data. All traces are packed into one stream.
        '''
        assert False, 'getWaveform must be defined'


class PsysmonDbWaveClient(WaveClient):
    ''' The pSysmon database waveclient.

    This class provides the connector to a pSysmon formatted SQL waveform 
    database. 
    '''

    def __init__(self, name, project):
        
        WaveClient.__init__(self, name=name, mode='psysmonDb')

        # The psysmon project owning the waveclient.
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

        # The senors database table.
        self.geomSensor = self.project.dbTables['geom_sensor']

        # The list of the associated waveform directories.
        self.waveformDirList = []


        # Initialize the waveformDirList from the database.
        self.loadWaveformDirList()



    def getWaveform(self, startTime, endTime, scnl):
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

        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.

        waveformDirList : List of Strings
            A list of waveform directories associated with the project.
            Each entry in the list is a dictionary with the fields id, dir, dirAlias and description.


        Returns
        -------
        stream : :class:`obspy.core.Stream`
            The requested waveform data. All traces are packed into one stream.
        '''

        self.logger.debug("Querying...")

        self.logger.debug('startTime: %s', startTime)
        self.logger.debug('endTime: %s', endTime)

        # Create the standard query.
        query = self.dbSession.query(self.traceheader.file_type,
                                     self.traceheader.filename, 
                                     self.waveformDirAlias.alias,
                                     self.geomStation.net_name,
                                     self.geomStation.name,
                                     self.geomStation.location,
                                     self.geomSensor.channel_name).\
                               filter(self.traceheader.wf_id ==self.waveformDir.id).\
                               filter(self.waveformDir.id == self.waveformDirAlias.wf_id, 
                                      self.waveformDirAlias.user == self.project.activeUser.name)

        # Add the startTime filter option.
        if startTime:
            query = query.filter(self.traceheader.begin_time + self.traceheader.numsamp * 1/self.traceheader.sps > startTime.getTimeStamp())

        # Add the endTime filter option.
        if endTime:
            query = query.filter(self.traceheader.begin_time < endTime.getTimeStamp())

        # Add the linkage between geometry ids.
        query = query.filter(self.traceheader.station_id == self.geomStation.id,
                             self.traceheader.sensor_id == self.geomSensor.id)

        stream = Stream()

        # Filter the SCNL selections.
        if scnl:
            for stat, chan, net, loc in scnl:
                curQuery = query.filter(self.geomStation.name == stat, 
                                        self.geomSensor.channel_name == chan,
                                        self.geomStation.net_name == net,
                                        self.geomStation.location == loc)
                for curHeader in curQuery:
                    filename = os.path.join(curHeader.alias, curHeader.filename)
                    self.logger.debug("Loading file: %s", filename)
                    curStream = read(pathname_or_url = filename,
                                     format = curHeader.file_type,
                                     starttime = startTime,
                                     endtime = endTime)

                    if not curStream:
                        continue

                    # Change the header values to the one loaded from the database.
                    for curTrace in curStream:
                        curTrace.stats.network = curHeader.net_name
                        curTrace.stats.station = curHeader.name
                        curTrace.stats.location = curHeader.location
                        curTrace.stats.channel = curHeader.channel_name

                    stream += curStream


        self.logger.debug("....finished.")

        return stream



    def loadWaveformDirList(self):
        '''Load the waveform directories from the database table.

        '''
        wfDir = self.waveformDir
        wfDirAlias = self.waveformDirAlias

        dbSession = self.dbSession
        self.waveformDirList = dbSession.query(wfDir.id, 
                                               wfDir.directory, 
                                               wfDirAlias.alias, 
                                               wfDir.description
                                              ).join(wfDirAlias, 
                                                     wfDir.id==wfDirAlias.wf_id
                                                    ).filter(wfDirAlias.user==self.project.activeUser.name).all()




class EarthwormWaveclient(WaveClient):
    ''' The earthworm waveserver client.

    This class provides the connector to a Earthworm waveserver.
    The client uses the :class:`obspy.earthworm.Client` class.
    '''

    def __init__(self, name, host='localhost', port=16022):
        WaveClient.__init__(self, name=name, mode='earthworm')


        # The Earthworm waveserver host to which the client should connect.
        self.options['host'] = host

        # The port on which the Eartworm waveserver is running on host.
        self.options['port'] = port

        # The obspy earthworm waveserver client instance.
        self.client = Client(self.options['host'], 
                             self.options['port'], 
                             timeout=2)


    def getWaveform(self,
                    startTime,
                    endTime, 
                    scnl):
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

        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.


        Returns
        -------
        stream : :class:`obspy.core.Stream`
            The requested waveform data. All traces are packed into one stream.
        '''
        from obspy.core import Stream

        self.logger.debug("Querying...")
        self.logger.debug('startTime: %s', startTime)
        self.logger.debug('endTime: %s', endTime)
        self.logger.debug("%s", scnl)

        stream = Stream() 
        for curScnl in scnl:
            curStation = curScnl[0]
            curChannel = curScnl[1]
            curNetwork = curScnl[2]
            curLocation = curScnl[3]

            stock_stream = self.get_from_stock(station = curStation,
                                               channel = curChannel,
                                               network = curNetwork,
                                               location = curLocation,
                                               start_time = startTime,
                                               end_time = endTime)

            if len(stock_stream) > 0:
                cur_trace = stock_stream.traces[0]
                cur_start_time = cur_trace.stats.starttime
                cur_end_time = cur_trace.stats.starttime + cur_trace.stats.npts / cur_trace.stats.sampling_rate
                
                stream += stock_stream

                if startTime < cur_start_time:
                    curStream = self.request_from_server(station = curStation,
                                                         channel = curChannel,
                                                         network = curNetwork,
                                                         location = curLocation,
                                                         start_time = startTime,
                                                         end_time = cur_start_time)
                    stream += curStream

                if cur_end_time < endTime:
                    curStream = self.request_from_server(station = curStation,
                                                         channel = curChannel,
                                                         network = curNetwork,
                                                         location = curLocation,
                                                         start_time = cur_end_time,
                                                         end_time = endTime)
                    stream += curStream
                    
            else:
                curStream = self.request_from_server(station = curStation,
                                                     channel = curChannel,
                                                     network = curNetwork,
                                                     location = curLocation,
                                                     start_time = startTime,
                                                     end_time = endTime)
                stream += curStream
                                        
            stream.merge()

        self.add_to_stock(stream)

        return stream


    def request_from_server(self, station, network, channel, location, start_time, end_time):

        stream = Stream()

        try:
            self.logger.debug('Before getWaveform....')
            stream = self.client.getWaveform(network,
                                             station,
                                             location,
                                             channel,
                                             start_time,
                                             end_time)
            self.logger.debug('got waveform: %s', stream)
            self.logger.debug('leave try')
        except:
            self.logger.debug("Error connecting to waveserver.")

        return stream


