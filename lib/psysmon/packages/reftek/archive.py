# LICENSE
#
# This file is part of psysmomat.
#
# If you use psysmomat in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# psysmomat is free software: you can redistribute it and/or modify
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


import os
import os.path
import glob
import subprocess
import logging
import shutil
import re
import tempfile
import operator as op

import numpy as np

from obspy.core.utcdatetime import UTCDateTime
from obspy.core import read

import obspy.core.stream
import obspy.core.trace

import RT_130_h


class RawFile(object):
    ''' A Reftek raw file.
    '''

    def __init__(self, filename):
        '''
        It is supposed, that the reftek archive has the follwing directory structure:
            YYYYDDD
                UNIT_ID
                    STREAM
                        data_files
        '''
        self.path, self.filename = os.path.split(filename)

        tmp = self.path.split(os.sep)
        self.stream_num = int(tmp[-1])
        self.unit_id = tmp[-2]
        year = int(tmp[-3][0:4])
        doy = int(tmp[-3][4:])
        hour = int(self.filename[0:2])
        minute = int(self.filename[2:4])
        second = int(self.filename[4:6])
        millisecond = int(self.filename[6:9])
        length = float.fromhex(self.filename[10:]) / 1000.

        self.start_time = UTCDateTime(year = year,
                                      julday = doy,
                                      hour = hour,
                                      minute = minute,
                                      second = second,
                                      microsecond = millisecond * 1000)

        self.end_time = self.start_time + length


    @property
    def abs_filename(self):
        '''
        '''
        return os.path.join(self.path, self.filename)





class PasscalRecordingFormatParser(object):
    '''
    '''
    def __init__(self):
        '''
        '''
        self.packet_size = 1024

        self.packets = {}

        self.packet_parser = {}
        self.packet_parser['AD'] = self.parse_ad_packet
        self.packet_parser['CD'] = self.parse_cd_packet
        self.packet_parser['DS'] = self.parse_ds_packet
        self.packet_parser['DT'] = self.parse_dt_packet
        self.packet_parser['EH'] = self.parse_eh_packet
        self.packet_parser['ET'] = self.parse_et_packet
        self.packet_parser['OM'] = self.parse_om_packet
        self.packet_parser['SH'] = self.parse_sh_packet
        self.packet_parser['SC'] = self.parse_sc_packet

        self.events = {}

        self.traces = {}
        self.start_time = {}



    def parse(self, filename):
        ''' Parse the pakets of the file.
        '''
        stream = obspy.core.stream.Stream()

        fh = open(filename, 'rb')

        try:
            while 1:
                buf = fh.read(self.packet_size)
                if not buf:
                    break;
                else:
                    self.parse_packet(buf)
        finally:
            fh.close()


        # Convert the remaining trace data to obspy traces and add them to the
        # stream.
        for cur_key, cur_data in self.traces.iteritems():
            tr = obspy.core.trace.Trace()
            tr.stats.station = cur_key[0]
            tr.stats.channel = cur_key[1]
            tr.stats.location = cur_key[2]
            tr.stats.sampling_rate = cur_key[3]
            tr.stats.starttime = self.start_time[cur_key]
            tr.data = np.array(cur_data, dtype = np.dtype(np.int32))
            stream.append(tr)

        # Clear the traces and the corresponding start times.
        self.traces = {}
        self.start_time = {}

        return stream


    def parse_packet(self, packet_buffer):
        ''' Parse a Reftek 130 packet.
        '''
        packet_header =  RT_130_h.PacketHeader().decode(packet_buffer)
        if packet_header.type != 'DT':
            print "Found a packet: %s." % packet_header.type
        if packet_header.type in self.packet_parser.keys():
            self.packet_parser[packet_header.type](packet_header, packet_buffer)
        else:
            print "Unknown data packet: %s." % packet_header.type


    def parse_ad_packet(self, packet_header, packet_buffer):
        ''' Parse an auxiliary data parameter packet.
        '''
        pass


    def parse_cd_packet(self, packet_header, packet_buffer):
        ''' Parse a calibration parameter packet.
        '''
        pass


    def parse_ds_packet(self, packet_header, packet_buffer):
        ''' Parse a data stream parameter packet.
        '''
        pass


    def parse_dt_packet(self, packet_header, packet_buffer):
        ''' Parse a data packet.
        '''
        data_packet = RT_130_h.DT().decode(packet_buffer)
        if data_packet.event in self.events.keys():
            cur_event = self.events[data_packet.event]
            start_time = UTCDateTime(year = packet_header.year,
                                     julday = packet_header.doy,
                                     hour = packet_header.hr,
                                     minute = packet_header.mn,
                                     second = packet_header.sc,
                                     microsecond = packet_header.ms * 1000)
            sampling_rate = float(cur_event.SampleRate)
            station = packet_header.unit
            channel = str(data_packet.channel)
            location = str(data_packet.data_stream)

            #   If data is steim1 or steim2 then x0 is in 2nd to last data sample
            #   and xn is in the last data sample
            if data_packet.data_format == 0xc0 or data_packet.data_format == 0xc2 :
                del data_packet.data[-2:]

            cur_key = (station, channel, location, sampling_rate)
            if cur_key not in self.traces:
                self.traces[cur_key] = data_packet.data
                self.start_time[cur_key] = start_time
            else:
                # Check if the data time.
                end_time = self.start_time[cur_key] + (len(self.traces[cur_key]) - 1) / sampling_rate
                dt = start_time - end_time
                if dt > 0 and np.abs(dt - 1/sampling_rate) <= 1/(10*sampling_rate):
                    self.traces[cur_key].extend(data_packet.data)
                else:
                    # Write the trace data to the stream and clear the trace
                    # data.
                    # Start a new trace data.
                    print "dt doesn't match: %f" % dt
        else:
            print "No event found for the data packet event: %d." % data_packet.event



    def parse_eh_packet(self, packet_header, packet_buffer):
        ''' Parse an event header packet.
        '''
        event_header = RT_130_h.EH().decode(packet_buffer)
        self.events[event_header.EventNumber] = event_header
        print "event: %d " % event_header.EventNumber


    def parse_et_packet(self, packet_header, packet_buffer):
        ''' Parse an event trailer packet.
        '''
        event_trailer = RT_130_h.EH().decode(packet_buffer)


    def parse_om_packet(self, packet_header, packet_buffer):
        ''' Parse an operation moder parameter packet.
        '''
        pass


    def parse_sh_packet(self, packet_header, packet_buffer):
        ''' Parse a state-of-health packet.
        '''
        pass


    def parse_sc_packet(self, packet_header, packet_buffer):
        ''' Parse a station/channel parameter packet.
        '''
        pass





class Unit(object):
    ''' A Reftek recorder unit.
    '''

    def __init__(self, unit_id):
        '''
        '''
        self.unit_id = unit_id

        self.streams = {}


    def add_raw_file(self, raw_file):
        '''
        '''
        if raw_file.stream_num not in self.streams.keys():
            self.streams[raw_file.stream_num] = Stream(raw_file.stream_num)

        self.streams[raw_file.stream_num].add_raw_file(raw_file)



class Stream(object):
    ''' A Reftek recorder stream.
    '''

    def __init__(self, number):
        '''
        '''
        self.number = number

        self.raw_files = []

        self.parser = PasscalRecordingFormatParser()


    def add_raw_file(self, raw_file):
        '''
        '''
        if raw_file.stream_num == self.number:
            self.raw_files.append(raw_file)


    def sort_raw_files(self):
        '''
        '''
        self.raw_files = sorted(self.raw_files, key = op.attrgetter('start_time'))


    def parse(self, raw_file):
        '''
        '''
        st = self.parser.parse(os.path.join(raw_file.path, raw_file.filename))
        # TODO: return a copy of the stream.
        return st


    def get_data(self, start_time, end_time, trim = False):
        ''' Get the data of the stream.
        '''
        raw_files = [x for x in self.raw_files if x.start_time < end_time and x.end_time > start_time]
        st = obspy.core.stream.Stream()
        for cur_raw_file in raw_files:
            # TODO: Add the possibility to define a timespan for the data to
            # parse. Don't read the whole raw_data, but only the desired
            # timespan.
            st += self.parser.parse(cur_raw_file.abs_filename)
        st.merge()
        if trim:
            st.trim(start_time, end_time)
        return st




class ArchiveController(object):
    ''' Archive Reftek raw data files.

    '''

    def __init__(self, archive, data_directory = None):
        ''' The constructor.

        '''
        # The logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The archive directory.
        self.archive = archive

        # The directory to handle.
        self.data_directory = data_directory

        # The available units.
        self.units = {}


    def add_raw_file(self, filename):
        ''' Add a Reftek raw data file.

        It is supposed, that the reftek archive has the follwing directory structure:
            YYYYDDD
                UNIT_ID
                    STREAM
                        data_files
        '''

        cur_raw_file = RawFile(filename)

        if cur_raw_file.unit_id not in self.units.keys():
            self.units[cur_raw_file.unit_id] = Unit(cur_raw_file.unit_id)

        self.units[cur_raw_file.unit_id].add_raw_file(cur_raw_file)



    def scan(self):
        ''' Scan the data directory for files.

        '''
        re_raw = re.compile (".*\w{9}_\w{8}$")

        for root, dirs, files in os.walk(self.archive):
            for cur_file in files:
                if re_raw.match(cur_file):
                    self.add_raw_file(os.path.join(root, cur_file))



    def get_stream(self, unit_id, stream):
        ''' Get an existing stream.
        '''
        try:
            return self.units[unit_id].streams[stream]
        except:
            return None


    def archive_to_mseed(self, out_dir, unit_id, stream, start_time, end_time, interval = 3600):
        ''' Convert the raw data to miniseed files.
        '''
        interval = float(interval)
        # Convert the timespan into year, day, hour lists.
        start_day = UTCDateTime(year = start_time.year,
                                month = start_time.month,
                                day = start_time.day,
                                hour = start_time.hour)
        end_day = UTCDateTime(year = end_time.year,
                              month = end_time.month,
                              day = end_time.day,
                              hour = end_time.hour)
        intervals_between = int((end_day - start_day)/interval)
        chunk_list = [start_day + x * interval for x in range(intervals_between)]

        # Get the required stream.
        cur_raw_stream = self.get_stream(unit_id = unit_id,
                                         stream = stream)
        if not cur_raw_stream:
            self.logger.error("No stream %d found for unit %s.", stream, unit_id)
            return

        for cur_chunk in chunk_list:
            cur_chunk_end_time = cur_chunk + interval - 1e-6
            self.logger.info("Processing unit_id %s, stream %d for timespan %s to %s.", unit_id, stream, cur_chunk.isoformat(), cur_chunk_end_time.isoformat())
            # Fetch the data for the time span from the archive.
            st = cur_raw_stream.get_data(start_time = cur_chunk,
                                         end_time = cur_chunk_end_time)

            # Trim the stream.
            self.logger.debug('Trimming file.')
            st.trim(starttime = cur_chunk, endtime = cur_chunk_end_time)

            # Write the stream to MiniSeed format file.
            for cur_trace in st:
                if np.ma.isMaskedArray(cur_trace.data):
                    split_stream = cur_trace.split()
                    export_traces = split_stream.traces
                else:
                    export_traces = [cur_trace, ]

                for cur_export_trace in export_traces:
                    stats = cur_export_trace.stats
                    trace_length = int((cur_export_trace.stats.endtime - cur_export_trace.stats.starttime) * 1000)
                    filename = '%04d%03d_%02d%02d%02d%03d_%d_%s_%s_%s.msd' % (stats.starttime.year, stats.starttime.julday, 
                        stats.starttime.hour, stats.starttime.minute, stats.starttime.second, int(stats.starttime.microsecond/1000),
                        trace_length, stats.station, stats.location, stats.channel)

                    # Check and prepare the BUD directory structure.
                    cur_outdir = os.path.join(out_dir, "%04d" % stats.starttime.year)
                    if not os.path.exists(cur_outdir):
                        os.mkdir(cur_outdir)

                    cur_outdir = os.path.join(cur_outdir, "%03d" % stats.starttime.julday)
                    if not os.path.exists(cur_outdir):
                        os.mkdir(cur_outdir)

                    cur_outdir = os.path.join(cur_outdir, "%s" % stats.station)
                    if not os.path.exists(cur_outdir):
                        os.mkdir(cur_outdir)

                    out_file = os.path.join(cur_outdir, filename)

                    try:
                        self.logger.debug('Writing miniseed file.')
                        cur_export_trace.write(out_file, format = 'MSEED', reclen=512, encoding='STEIM2')
                        self.logger.info('Wrote miniseed file %s containing the trace %s.', out_file, cur_export_trace)
                    except:
                        self.logger.exception('Error writing miniseed file %s using obspy.', out_file)



