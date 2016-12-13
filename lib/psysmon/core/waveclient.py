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
import threading
from obspy.core import read, Stream
from obspy.earthworm import Client
import numpy as np

class WaveClient(object):
    '''The WaveClient class.


    Attributes
    ----------

    '''

    def __init__(self, name, stock_window = 3600):
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

        # The available data of the waveclient. This includes the
        # currently displayed time period and the preloaded data in
        # front and behind the time period.
        self.stock = Stream()


        # The threading lock object for the stock stream.
        self.stock_lock = threading.Lock()

        # The threads used for preloading data.
        self.preload_threads = []

        # The time-window in seconds of the stock stream before and after the currently
        # displayed time-period. 
        self.stock_window = stock_window

    @property
    def mode(self):
        ''' The mode of the waveclient.

        '''
        return self.__class__.__name__

    @property
    def pickle_attributes(self):
        ''' The attributes which can be pickled.
        '''
        d = {}
        d['stock_window'] = self.stock_window
        return d


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
        self.stock_lock.acquire()
        curStream = self.stock.select(station = station,
                                      channel = channel,
                                      network = network,
                                      location = location)
        curStream = curStream.copy()
        self.stock_lock.release()
        self.logger.debug('Selected stream from stock: %s', curStream)
        curStream.trim(starttime = start_time,
                       endtime = end_time)
        self.logger.debug('Trimmed stream to: %s', curStream)

        return curStream


    def add_to_stock(self, stream):
        ''' Add the passed stream to the stock data.

        '''
        self.stock_lock.acquire()
        self.stock = self.stock + stream.copy()
        self.stock.merge(stream)
        self.stock_lock.release()


    def trim_stock(self, start_time, end_time):
        ''' Trim the stock streams.

        '''
        self.stock_lock.acquire()
        self.stock.trim(starttime = start_time - self.stock_window, endtime = end_time + self.stock_window)
        self.stock_lock.release()
        self.logger.debug('Trimmed stock stream to %s - %s.', start_time - self.stock_window, end_time + self.stock_window)
        self.logger.debug('stock: %s', self.stock)


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


class PreloadThread(threading.Thread):
    ''' The waveclient preload thread.

    This thread is used to preload the data of a waveclient.
    '''

    def __init__(self, start_time, end_time, scnl, group=None, target=None, name=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.start_time = start_time

        self.end_time = end_time

        self.scnl = scnl

        self.target = target

    def run(self):
        self.target(self.start_time, self.end_time, self.scnl)


class PsysmonDbWaveClient(WaveClient):
    ''' The pSysmon database waveclient.

    This class provides the connector to a pSysmon formatted SQL waveform
    database.
    '''

    def __init__(self, name = 'psysmon db waveclient', project = None, **kwargs):

        WaveClient.__init__(self, name=name, **kwargs)

        # The psysmon project owning the waveclient.
        self.project = project

        # The list of the associated waveform directories.
        self.waveformDirList = []

        # Initialize the waveformDirList from the database.
        self.loadWaveformDirList()


    @property
    def traceheader(self):
        # The traceheader database table.
        if self.project is not None:
            return self.project.dbTables['traceheader']
        else:
            return None

    @property
    def waveformDir(self):
        # The waveform directory table.
        if self.project is not None:
            return self.project.dbTables['waveform_dir']
        else:
            return None

    @property
    def waveformDirAlias(self):
        # The waveform directory alias table.
        if self.project is not None:
            return self.project.dbTables['waveform_dir_alias']
        else:
            return None


    @property
    def geomStation(self):
        # The station database table.
        if self.project is not None:
            return self.project.dbTables['geom_station']
        else:
            return None

    @property
    def geomChannel(self):
        # The channels database table.
        if self.project is not None:
            return self.project.dbTables['geom_channel']
        else:
            return None

    @property
    def geomRecorderStream(self):
        # The recorder stream database table.
        if self.project is not None:
            return self.project.dbTables['geom_recorder_stream']
        else:
            return None





    def getWaveform(self, startTime, endTime, scnl):
        ''' Get the waveform data for the specified parameters.

        Parameters
        ----------
        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.

        scnl : List of Tuples (STATION, CHANNEL, NETWORK, LOCATION)
            The channels for which to get the waveform data.

        Returns
        -------
        stream : :class:`obspy.core.Stream`
            The requested waveform data. All traces are packed into one stream.
        '''
        self.logger.debug("Getting the waveform...")

        new_data = False
        stream = Stream()

        # Trim the stock stream to new limits.
        self.trim_stock(start_time = startTime, end_time = endTime)

        # Filter the SCNL selections.
        if scnl:
            for stat, chan, net, loc in scnl:
                stock_stream = self.get_from_stock(station = stat,
                                                   channel = chan,
                                                   network = net,
                                                   location = loc,
                                                   start_time = startTime,
                                                   end_time = endTime)

                if len(stock_stream) > 0:
                    self.logger.debug('Found data in stock....\n%s', stock_stream)
                    stock_stream.merge()
                    cur_trace = stock_stream.traces[0]
                    cur_start_time = cur_trace.stats.starttime
                    cur_end_time = cur_trace.stats.starttime + cur_trace.stats.npts / cur_trace.stats.sampling_rate

                    stream += stock_stream.split()

                    if (cur_start_time - startTime) > 1/cur_trace.stats.sampling_rate:
                        self.logger.debug('Get missing data in front...')
                        self.logger.debug('Loading data from %s to %s.', startTime, cur_start_time)
                        curStream = self.load_from_file(station = stat,
                                                        channel = chan,
                                                        network = net,
                                                        location = loc,
                                                        start_time = startTime,
                                                        end_time = cur_start_time)
                        stream += curStream
                        new_data = True

                    if (endTime - cur_end_time) > 1/cur_trace.stats.sampling_rate:
                        self.logger.debug('Get missing data in back...')
                        self.logger.debug('Loading data from %s to %s.', cur_end_time, endTime)
                        curStream = self.load_from_file(station = stat,
                                                        channel = chan,
                                                        network = net,
                                                        location = loc,
                                                        start_time = cur_end_time,
                                                        end_time = endTime)
                        stream += curStream
                        new_data = True

                    if isinstance(stock_stream.traces[0].data, np.ma.masked_array):
                        # Try to fill the data gaps.
                        self.logger.debug('There are gaps in the stock stream. Try to fill them...')
                        stock_stream = stock_stream.split()
                        gaps = stock_stream.getGaps()
                        for cur_gap in gaps:
                            self.logger.debug('Loading data for gap %s.', cur_gap)
                            curStream = self.load_from_file(station = stat,
                                                            channel = chan,
                                                            network = net,
                                                            location = loc,
                                                            start_time = cur_gap[4],
                                                            end_time = cur_gap[5])
                            stream += curStream
                            new_data = True


                else:
                    self.logger.debug('No stock data available...')
                    self.logger.debug('Loading data from %s to %s.', startTime, endTime)
                    curStream = self.load_from_file(station = stat,
                                                    channel = chan,
                                                    network = net,
                                                    location = loc,
                                                    start_time = startTime,
                                                    end_time = endTime)

                    stream += curStream
                    new_data = True

                stream.merge()
        if new_data:
            self.add_to_stock(stream)
            #self.trim_stock(start_time = startTime, end_time = endTime)

        self.logger.debug("....finished getting the waveform.")

        return stream



    def load_from_file(self, station, channel, network, location, start_time, end_time):
        ''' Load the data from file.

        Select all files containing data from the database.
        Load the data of the given time priod from the files and add it
        to a stream which is returned.

        Attributes
        ----------


        Returns
        -------
        stream : :class:`~obspy.core.Stream`
            The data of the specified SCNL and time period loaded from the files.
        '''
        data_stream = Stream()

        # Get the channel from the inventory. It's expected, that only one
        # channel is returned. If more than one channels are returned, then
        # there is an error in the geometry inventory.
        cur_channel = self.project.geometry_inventory.get_channel(network = network,
                                                                  station = station,
                                                                  location = location,
                                                                  name = channel)

        if cur_channel:
            if len(cur_channel) > 1:
                raise RuntimeError('More than 1 channel returned for SCNL: %s:%s:%s:%s. Checkk the geometry inventory for duplicate entries.' % (station, channel, network, location))

            cur_channel = cur_channel[0]

            dbSession = self.project.getDbSession()

            # Select the file type, filename and waveform directory.
            query = dbSession.query(self.traceheader.file_type,
                                    self.traceheader.filename,
                                    self.waveformDirAlias.alias).\
                                    filter(self.traceheader.wf_id ==self.waveformDir.id).\
                                    filter(self.waveformDir.id == self.waveformDirAlias.wf_id).\
                                    filter(self.waveformDirAlias.user == self.project.activeUser.name)

            # Add the startTime filter option.
            if start_time:
                query = query.filter(self.traceheader.begin_time + self.traceheader.numsamp * 1/self.traceheader.sps > start_time.timestamp)

            # Add the endTime filter option.
            if end_time:
                query = query.filter(self.traceheader.begin_time < end_time.timestamp)

            # Get the streams assigned to the channel for the requested
            # time-span.
            assigned_streams = cur_channel.get_stream(start_time = start_time,
                                                      end_time = end_time)
            for cur_timebox in assigned_streams:
                cur_rec_stream = cur_timebox.item

                # Create a new query with filters for the serial and stream
                # name.
                cur_query = query.filter(self.traceheader.recorder_serial == cur_rec_stream.serial).\
                                  filter(self.traceheader.stream == cur_rec_stream.name)

                # Process the results of the query.
                for curHeader in cur_query:
                    filename = os.path.join(curHeader.alias, curHeader.filename)
                    self.logger.debug("Loading file: %s", filename)
                    cur_data_stream = read(pathname_or_url = filename,
                                           format = curHeader.file_type,
                                           starttime = start_time,
                                           endtime = end_time,
                                           dtype = 'float64')

                    if not cur_data_stream:
                        continue

                    # Change the header values to the ones stored in the geometry inventory.
                    for curTrace in cur_data_stream:
                        curTrace.stats.network = network
                        curTrace.stats.station = station
                        curTrace.stats.location = location
                        curTrace.stats.channel = channel
                        curTrace.stats.unit = 'counts'

                    data_stream += cur_data_stream

            dbSession.close()

        return data_stream

    def loadWaveformDirList(self):
        '''Load the waveform directories from the database table.

        '''
        wfDir = self.waveformDir
        wfDirAlias = self.waveformDirAlias

        # Check if the waveform_dir database tables exist.
        if wfDir is None or wfDirAlias is None:
            return

        # TODO: make the waveform dir list a dynamic property.
        dbSession = self.project.getDbSession()
        self.waveformDirList = dbSession.query(wfDir.id,
                                               wfDir.directory,
                                               wfDirAlias.alias,
                                               wfDir.description
                                              ).join(wfDirAlias,
                                                     wfDir.id==wfDirAlias.wf_id
                                                    ).filter(wfDirAlias.user==self.project.activeUser.name).all()

        dbSession.close()



class EarthwormWaveclient(WaveClient):
    ''' The earthworm waveserver client.

    This class provides the connector to a Earthworm waveserver.
    The client uses the :class:`obspy.earthworm.Client` class.
    '''

    def __init__(self, name = 'earthworm waveserver client', host='localhost', port=16022, **kwargs):
        WaveClient.__init__(self, name=name, **kwargs)

        # The Earthworm waveserver host to which the client should connect.
        self.host = host

        # The port on which the Eartworm waveserver is running on host.
        self.port = port

        # The obspy earthworm waveserver client instance.
        self.client = Client(self.host,
                             self.port,
                             timeout=2)

    @property
    def pickle_attributes(self):
        ''' The attributes which can be pickled.
        '''
        d = super(EarthwormWaveclient, self).pickle_attributes
        d['host'] = self.host
        d['port'] = self.port
        return d


    def getWaveform(self,
                    startTime,
                    endTime,
                    scnl):
        ''' Get the waveform data for the specified parameters.

        Parameters
        ----------
        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.

        scnl : List of tuples
            The SCNL codes of the data to request.


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
            for cur_trace in stream:
                cur_trace.stats.unit = 'counts'
            self.logger.debug('got waveform: %s', stream)
            self.logger.debug('leave try')
        except Exception as e:
            self.logger.exception("Error connecting to waveserver: %s", e)

        return stream



    def preload(self, start_time, end_time, scnl):
        ''' Preload the data for the given timespan and the scnl.

        Preloading is done as a thread.
        '''
        t = PreloadThread(name = 'daemon',
                          start_time = start_time,
                          end_time = end_time,
                          scnl = scnl,
                          target = self.getWaveform
                         )
        t.setDaemon(True)
        t.start()
        self.preload_threads.append(t)
        return t







