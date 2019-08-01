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

import psysmon
import os
import os.path
import logging
import re
import operator as op
import json

import numpy as np

from obspy.core.utcdatetime import UTCDateTime

import obspy.core.stream
import obspy.core.trace

import RT_130_h


class RawFile(object):
    ''' A Reftek raw file.
    '''

    def __init__(self, full_filename, parent = None):
        ''' Initialization of the instance.

        It is supposed, that the reftek archive has the follwing directory structure:
            YYYYDDD
                UNIT_ID
                    STREAM
                        data_files

        Parameters
        ----------
        full_filename : String
            The absolute path to the reftek raw data file.

        parent : :class:`Stream`
            The parent stream holding the raw file.
        '''
        # The parent stream.
        self.parent = parent

        # The path and filename.
        self.path, self.filename = os.path.split(full_filename)

        tmp = self.path.split(os.sep)

        # The stream number
        self.stream_num = int(tmp[-1])

        # The recorder unit id.
        self.unit_id = tmp[-2]

        year = int(tmp[-3][0:4])
        doy = int(tmp[-3][4:])
        hour = int(self.filename[0:2])
        minute = int(self.filename[2:4])
        second = int(self.filename[4:6])
        millisecond = int(self.filename[6:9])
        length = float.fromhex(self.filename[10:]) / 1000.

        # The start time of the file.
        self.start_time = UTCDateTime(year = year,
                                      julday = doy,
                                      hour = hour,
                                      minute = minute,
                                      second = second,
                                      microsecond = millisecond * 1000)

        # The end time of the file.
        self.end_time = self.start_time + length


    @property
    def abs_filename(self):
        ''' The absolute path to the file.
        '''
        if self.parent:
            return os.path.join(self.parent_archive.archive, self.path, self.filename)
        else:
            return os.path.join(self.path, self.filename)


    @property
    def parent_archive(self):
        ''' The archive holding the raw file.
        '''
        if self.parent:
            return self.parent.parent_archive
        else:
            return None




class PasscalRecordingFormatParser(object):
    ''' A parser for the Passcal Recording Format used by the Reftek-130 data logger.
    '''
    def __init__(self):
        ''' Initialization of the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The size of the data packets.
        self.packet_size = 1024

        # The methods for the individual packet types.
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

        # The active event found in the raw data files.
        self.events = {}

        # The parsed sample data.
        self.traces = {}

        # The start times of the traces.
        self.start_time = {}



    def parse(self, filename, start_time = None, end_time = None):
        ''' Parse the pakets of a reftek raw data file.

        Parameters
        ----------
        filename : String
            The absolute path to a reftek raw data file.
        '''
        self.parse_start_time = start_time
        self.parse_end_time = end_time
        self.traces = {}
        self.start_time = {}
        self.stream = obspy.core.stream.Stream()

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
            self.stream.append(tr)

        # Clear the traces and the corresponding start times.
        self.traces = {}
        self.start_time = {}

        return self.stream.copy()


    def parse_packet(self, packet_buffer):
        ''' Parse a Reftek 130 packet.

        Parameters
        ----------
        packet_buffer : List
            The binary data of a packet read from the reftek raw data file.
        '''
        packet_header =  RT_130_h.PacketHeader().decode(packet_buffer)
        if packet_header.type != 'DT':
            self.logger.debug("Found a packet: %s.", packet_header.type)

        if packet_header.type in self.packet_parser.iterkeys():
            self.packet_parser[packet_header.type](packet_header, packet_buffer)
        else:
            self.logger.error("Unknown data packet: %s.", packet_header.type)


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

        # Get the sampling rate from the event header.
        if packet_header.unit in self.events.iterkeys() and data_packet.event in self.events[packet_header.unit].keys():
            cur_event = self.events[packet_header.unit][data_packet.event]
            sampling_rate = float(cur_event.SampleRate)
        elif packet_header.unit in self.events.iterkeys():
            # TODO: Add a user flag to select the guessing of the sampling
            # rate.
            keys = np.array(self.events[packet_header.unit].keys())
            min_ind = np.argmin(np.abs(keys - data_packet.event))
            cur_event = self.events[packet_header.unit][keys[min_ind]]
            sampling_rate = float(cur_event.SampleRate)
            self.logger.debug("No matching event found for the data packet event: %s - %d. Guessing the sampling from past events to: %f.", packet_header.unit, data_packet.event, sampling_rate)
        else:
            # TODO: Add an option to override the sampling rate if no event is
            # found.
            self.logger.error("No event found for the data packet event: %s - %d. Can't determine sampling rate.", packet_header.unit, data_packet.event)
            return

        # Check if the data packet is inside the requested time span.
        start_time = UTCDateTime(year = packet_header.year,
                                 julday = packet_header.doy,
                                 hour = packet_header.hr,
                                 minute = packet_header.mn,
                                 second = packet_header.sc,
                                 microsecond = packet_header.ms * 1000)

        end_time = start_time + 1562. / sampling_rate        # In a highliy compressed data packet, max. 1561 data samples can be stored.

        if self.parse_start_time and self.parse_end_time:
            if not (start_time <= self.parse_end_time and end_time >= self.parse_start_time):
                # The data is not inside the requested interval. Ignore it.
                return


        station = packet_header.unit
        channel = str(data_packet.channel + 1)          # The channel is zero-based, add 1.
        location = str(data_packet.data_stream + 1)     # The streeam is zero-based, add 1.

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
                self.logger.debug("dt (%f) doesn't match. Starting a new trace for %s.", dt, cur_key)
                tr = obspy.core.trace.Trace()
                tr.stats.station = cur_key[0]
                tr.stats.channel = cur_key[1]
                tr.stats.location = cur_key[2]
                tr.stats.sampling_rate = cur_key[3]
                tr.stats.starttime = self.start_time[cur_key]
                tr.data = np.array(self.traces[cur_key], dtype = np.dtype(np.int32))
                self.stream.append(tr)
                self.traces.pop(cur_key)
                self.start_time.pop(cur_key)



    def parse_eh_packet(self, packet_header, packet_buffer):
        ''' Parse an event header packet.
        '''
        event_header = RT_130_h.EH().decode(packet_buffer)
        if packet_header.unit not in self.events.iterkeys():
            self.events[packet_header.unit] = {}
        self.events[packet_header.unit][event_header.EventNumber] = event_header
        self.logger.debug("Added event of unit %s: %d.", packet_header.unit, event_header.EventNumber)


    def parse_et_packet(self, packet_header, packet_buffer):
        ''' Parse an event trailer packet.
        '''
        event_trailer = RT_130_h.EH().decode(packet_buffer)
        #if packet_header.unit in self.active_event.iterkeys():
        #    if event_trailer.EventNumber == self.active_event[packet_header.unit].EventNumber:
        #        self.active_event.pop(packet_header.unit)
        #        self.logger.debug("Closed active event of %s: %d.", packet_header.unit, event_trailer.EventNumber)
        #    else:
        #        self.logger.error("The active event %d doesn't match the event to close. Closed active event of %s: %d.", self.active_event[packet_header.unit].EventNumber, packet_header.unit, event_trailer.EventNumber)
        #        self.active_event.pop(packet_header.unit)





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

    def __init__(self, unit_id, parent_archive = None):
        ''' Initialize the instance.

        Parameters
        ----------
        unit_id : String
            The unit ID of a reftek recorder.

        parent_archive : :class:`ArchiveController`
            The parent archive holding the unit.
        '''
        self.parent_archive = parent_archive

        self.unit_id = unit_id

        self.streams = {}


    def add_raw_file(self, raw_file):
        ''' Add a reftek raw data file to the unit.

        Parameters
        ----------
        raw_file : :class:`RawFile`
            The RawFile instance representing a reftek raw data file.
        '''
        if raw_file.stream_num not in self.streams.iterkeys():
            self.streams[raw_file.stream_num] = Stream(raw_file.stream_num, parent_unit = self)

        self.streams[raw_file.stream_num].add_raw_file(raw_file)


    def sort_raw_files(self):
        ''' Sort the raw data files according to their start time.
        '''
        for cur_stream in self.streams.itervalues():
            cur_stream.sort_raw_files()




class Stream(object):
    ''' A Reftek recorder stream.
    '''

    def __init__(self, number, parent_unit = None):
        ''' Initialize the instance.

        Parameters
        ----------
        number : Integer
            The number of the stream.

        parent_unit : :class:`Unit`
            The parent unit holding the stream.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.parent_unit = parent_unit

        self.number = number

        self.raw_files = []

        self.parser = PasscalRecordingFormatParser()


    @property
    def parent_archive(self):
        '''
        '''
        if self.parent_unit:
            return self.parent_unit.parent_archive
        else:
            return None


    @property
    def first_data_time(self):
        '''
        '''
        if self.raw_files:
            self.sort_raw_files()
            return self.raw_files[0].start_time


    @property
    def last_data_time(self):
        '''
        '''
        if self.raw_files:
            self.sort_raw_files()
            return self.raw_files[-1].end_time


    def add_raw_file(self, raw_file):
        ''' Add a reftek raw data file to the stream.

        raw_file : :class:`RawFile`
            The RawFile instance representing a reftek raw data file.
        '''
        if raw_file.stream_num == self.number:
            raw_file.parent = self
            self.raw_files.append(raw_file)


    def sort_raw_files(self):
        ''' Sort the raw data files according to the start time.
        '''
        self.raw_files = sorted(self.raw_files, key = op.attrgetter('start_time'))


    def parse(self, raw_file):
        ''' Parse a reftek raw data file.

        Parameters
        ----------
        raw_file : :class:`RawFile`
            The raw data file to parse.

        Returns
        -------
        st : :class:`~obspy.core.stream.Stream`
            The data parsed from the file.
        '''
        st = self.parser.parse(os.path.join(raw_file.path, raw_file.filename))
        # TODO: return a copy of the stream.
        return st


    def get_data(self, start_time, end_time, trim = False):
        ''' Get the data of the stream.

        Parameters
        ----------
        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The start time of the time span for which to load the data.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The end time of the time span for which to load the data.

        trim : Boolean
            If true, the returned data stream is trimmed to the specified time limits.
            If false, the data stream is returned as loaded from the raw data files.
        '''
        raw_files = [x for x in self.raw_files if x.start_time < end_time and x.end_time > start_time]
        st = obspy.core.stream.Stream()
        for cur_raw_file in raw_files:
            self.logger.debug("Parsing file %s.", cur_raw_file.abs_filename)
            st += self.parser.parse(cur_raw_file.abs_filename,
                                    start_time = start_time,
                                    end_time = end_time)
        try:
            st.merge()
        except:
            self.logger.exception("Couldn't merge the stream\n %s.\nTry to go on with an unmerged stream.", st)

        if trim:
            st.trim(start_time, end_time)
        return st




class ArchiveController(object):
    ''' Archive Reftek raw data files.

    '''

    def __init__(self, archive, output_directory = None, last_scan = None):
        ''' Initialize the instance.

        Parameters
        ----------
        archive : String
            The path to the Reftek raw data file archive.

        output_directory : String
            The path to the directory where to save any converted data files.

        last_scan : :class:`obspy.core.utcdatetime.UTCDateTime`
            The time of the last scan of the archive.

        '''
        # The logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The archive directory.
        self.archive = archive

        # The directory to handle.
        self.output_directory = output_directory

        # The available units.
        self.units = {}

        # The time of the last archive scan.
        self.last_scan = last_scan


    @property
    def summary(self):
        '''
        '''
        summary = {}
        summary['scan_time'] = self.last_scan.isoformat()
        stream_list = []
        for cur_unit in self.units.itervalues():
            cur_stream = [(cur_unit.unit_id, x.number, x.first_data_time.isoformat(), x.last_data_time.isoformat()) for x in cur_unit.streams.itervalues()]
            stream_list.extend(cur_stream)
        summary['stream_list'] = stream_list
        return summary


    def add_raw_file(self, filename):
        ''' Add a Reftek raw data file.

        It is supposed, that the reftek archive has the follwing directory structure:
            YYYYDDD
                UNIT_ID
                    STREAM
                        data_files

        Parameters
        ----------
        filename : String
            The absolute path to the reftek raw data file.
        '''

        if not filename.startswith(self.archive):
            self.logger.error("The file %s is not located in the archive %s.", filename, self.archive)
            return

        filename = filename.replace(self.archive, '')

        if filename.startswith(os.sep):
            filename = filename[1:]

        cur_raw_file = RawFile(filename)

        if cur_raw_file.unit_id not in self.units.iterkeys():
            self.units[cur_raw_file.unit_id] = Unit(cur_raw_file.unit_id, parent_archive = self)

        self.units[cur_raw_file.unit_id].add_raw_file(cur_raw_file)


    def sort_raw_files(self):
        ''' Sort the raw data files according to their start time.
        '''
        for cur_unit in self.units.itervalues():
            cur_unit.sort_raw_files()


    def scan(self):
        ''' Scan the data directory for reftek raw data files.

        '''
        if not os.path.isdir(self.archive):
            self.logger.error("The reftek archive directory %s doesn't exist.", self.archive)
            return

        self.logger.info("Scanning the archive directory %s.", self.archive)

        re_raw = re.compile (".*\w{9}_\w{8}$")

        for root, dirs, files in os.walk(self.archive):
            dirs.sort()
            for cur_file in files:
                if re_raw.match(cur_file):
                    self.logger.debug('Adding file %s.', os.path.join(root, cur_file))
                    self.add_raw_file(os.path.join(root, cur_file))

        self.last_scan = UTCDateTime()

        self.sort_raw_files()

        # Save the scan results in the archive directory.
        try:
            result_file = os.path.join(self.archive, 'psysmon_archive_scan.json')
            fp = open(result_file, mode = 'w')
            json.dump(self, fp = fp, cls = ArchiveScanEncoder)
            self.logger.info("Saved the scan result in the file %s.", result_file)
            fp.close()

            result_file = os.path.join(self.archive, 'psysmon_archive_scan_summary.json')
            fp = open(result_file, mode = 'w')
            json.dump(self.summary, fp = fp)
            self.logger.info("Saved the scan result summary in the file %s.", result_file)
        finally:
            fp.close()



    def get_stream(self, unit_id, stream):
        ''' Get an existing stream.

        Parameters
        ----------
        unit_id : String
            The unit ID of the reftek recorder.

        stream : Integer
            The number of the stream.
        '''
        try:
            return self.units[unit_id].streams[stream]
        except:
            return None


    def archive_to_mseed(self, unit_id, stream, start_time, end_time, interval = 3600):
        ''' Convert the raw data to miniseed files.

        Read Reftek raw data files from the archive and convert them to MiniSeed
        files using the obspy miniseed support. The data of the specified time span
        is converted to miniseed files with a specified length (interval).

        Parameters
        ----------
        unit_id : String
            The unit ID of the reftek recorder.

        stream : Integer
            The number of the stream.

        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The start time of the time span to convert.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The end time of the time span to convert.

        interval : Float
            The length in seconds of the converted miniseed files.
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

            if not st:
                self.logger.warning("No data found.")
                continue

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
                    cur_outdir = os.path.join(self.output_directory, "%04d" % stats.starttime.year)
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




class ArchiveScanEncoder(json.JSONEncoder):
    ''' A JSON encoder for the reftek archive scan file.
    '''
    def __init__(self, **kwargs):
        json.JSONEncoder.__init__(self, **kwargs)
        self.indent = 4
        self.sort_keys = True

    def default(self, obj):
        ''' Convert reftek archive objects to a dictionary.
        '''
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]

        if obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        elif obj_class == 'Stream':
            d = self.encode_stream(obj)
        else:
            d = self.object_to_dict(obj, ignore = ['logger', 'parent', 'parent_unit', 'parent_archive',
                                                   'parser'])

        # Add the class and module information to the dictionary.
        tmp = {'__baseclass__': base_class,
               '__class__': obj_class,
               '__module__': obj.__module__}
        d.update(tmp)

        return d


    def convert_utcdatetime(self, obj):
        return {'isoformat': obj.isoformat()}


    def encode_stream(self, obj):
        attr = ['number', ]
        d = self.object_to_dict(obj, attr = attr)
        d['raw_files'] = [x.abs_filename for x in obj.raw_files]
        return d


    def object_to_dict(self, obj, attr = None, ignore = None):
        ''' Copy selected attributes of object to a dictionary.
        '''
        def hint_tuples(item):
            if isinstance(item, tuple):
                return {'__tuple__': True, 'items': item}
            if isinstance(item, list):
                return [hint_tuples(e) for e in item]
            else:
                return item

        if not attr:
            attr = obj.__dict__.keys()

        if ignore:
            attr = [x for x in attr if x not in ignore]

        d = {}
        for cur_attr in attr:
            d[cur_attr] = hint_tuples(getattr(obj, cur_attr))

        return d


class ArchiveScanDecoder(json.JSONDecoder):
    ''' A JSON decoder for the reftek archive scan file.
    '''

    def __init__(self, **kwargs):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)


    def convert_object(self, d):
        if '__class__' in d:
            class_name = d.pop('__class__')
            module_name = d.pop('__module__')
            base_class = d.pop('__baseclass__')

            if class_name == 'ArchiveController':
                inst = self.decode_archive_controller(d)
            elif class_name == 'Unit':
                inst = self.decode_unit(d)
            elif class_name == 'Stream':
                inst = self.decode_stream(d)
            elif class_name == 'RawFile':
                inst = self.decode_raw_file(d)
            elif class_name == 'UTCDateTime':
                inst = self.decode_utcdatetime(d)
            else:
                inst = {'ERROR': 'MISSING DECODER'}
        else:
            inst = d

        return inst


    def decode_hinted_tuple(self, item):
        if isinstance(item, dict):
            if '__tuple__' in item:
                return tuple(item['items'])
        elif isinstance(item, list):
                return [self.decode_hinted_tuple(x) for x in item]
        else:
            return item


    def decode_archive_controller(self, d):
        '''
        '''
        inst = psysmon.packages.reftek.archive.ArchiveController(archive = d['archive'],
                                                                 output_directory = d['output_directory'],
                                                                 last_scan = d['last_scan'])

        inst.units = d['units']
        for cur_unit in inst.units.itervalues():
            cur_unit.parent_archive = inst

        return inst


    def decode_unit(self, d):
        '''
        '''
        inst = psysmon.packages.reftek.archive.Unit(unit_id = d['unit_id'])

        # JSON only supports strings as keys of dictionaries.
        # Restore the streams dictionary with integers as keys.
        for cur_key, cur_item in d['streams'].iteritems():
            cur_item.parent_unit = inst
            inst.streams[int(cur_key)] = cur_item

        return inst


    def decode_stream(self, d):
        '''
        '''
        inst = psysmon.packages.reftek.archive.Stream(number = d['number'])

        for cur_filename in d['raw_files']:
            inst.add_raw_file(RawFile(cur_filename))

        return inst


    def decode_raw_file(self, d):
        '''
        '''
        inst = psysmon.packages.reftek.archive.RawFile(filename = os.path.join(d['path'], d['filename']))

        return inst


    def decode_utcdatetime(self, d):
        inst = UTCDateTime(d['isoformat'])
        return inst
