# -*- coding: utf-8 -*-
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
Handle earthquake bulletins.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

'''
import os
import psysmon
import logging
import re
import csv
import gzip

import obspy.core.utcdatetime as utcdatetime

import psysmon.packages.event.core as ev_core


class ImsParser(object):
    ''' Parse bulletins in IMS format.
    '''


    def __init__(self):
        # the logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        logger_name = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

        # The bulletin file handle.
        self.b_file = None

        # The bulletin title.
        self.bulletin_title = None

        # The dictionary holding the currently parsed event.
        self.event_dict = {}

        # The events parsed from the bulletin file. A list of dictionaries.
        self.events = []

        self.parser = {}
        self.parser['ims1.0:short'] = self.parse_ims1_0_short


    def parse(self, filename, zipped = False):
        ''' Parse a text file in IMS format.
        '''
        if not os.path.exists(filename):
            self.logger.error("The filename %s doesn't exist.", filename)
            return False

        self.events = []
        self.event_dict = {}

        bulletin_format = None
        try:
            if zipped:
                self.b_file = gzip.open(filename, 'rb')
            else:
                self.b_file = open(filename, 'r')
            for cur_line in self.b_file:
                cur_line = cur_line.rstrip()
                if bulletin_format is None:
                    # Waiting for the data_type line.
                    if cur_line.lower().startswith('data_type'):
                        tmp = cur_line.split(' ')
                        if tmp[1].lower() == 'bulletin':
                            bulletin_format = tmp[2].lower()
                        elif tmp[1].lower() == 'event':
                            bulletin_format = tmp[2].lower()

                        if bulletin_format == 'ims1.0':
                            bulletin_format = 'ims1.0:short'

                        bulletin_parsed = self.parser[bulletin_format]()

            self.b_file.close()

            if bulletin_parsed is True:
                self.logger.debug('Bulletin parsed successfully.')
            else:
                self.logger.debug('Bulletin was not parsed completely.')

        finally:
            self.b_file.close()

        return bulletin_parsed


    def get_catalog(self, name = 'ims1_short_parsed', agency_uri = None, author_uri = None):
        ''' Get a catalog instance of the parsed bulletin.
        '''
        catalog = ev_core.Catalog(name = name, agency_uri = agency_uri)

        for cur_event_dict in self.events:
            if len(cur_event_dict['origins']) == 0:
                self.logger.error("No origins found for event %s. Can't compute the start time.", cur_event_dict['event_id'])

            orig_start_time = min([x['starttime'] for x in cur_event_dict['origins']])
            start_time = min([utcdatetime.UTCDateTime(orig_start_time.year, orig_start_time.month, orig_start_time.day,
                            x['arrival_time']['hour'], x['arrival_time']['minute'],
                            int(x['arrival_time']['second']),
                            int(round((x['arrival_time']['second'] - int(x['arrival_time']['second'])) * 1000000))) for x in cur_event_dict['phases']])
            end_time = max([utcdatetime.UTCDateTime(orig_start_time.year, orig_start_time.month, orig_start_time.day,
                            x['arrival_time']['hour'], x['arrival_time']['minute'],
                            int(x['arrival_time']['second']),
                            int(round((x['arrival_time']['second'] - int(x['arrival_time']['second'])) * 1000000))) for x in cur_event_dict['phases']])

            if start_time == end_time:
                end_time = start_time + 1;

            # TODO: The event type should be an instance of an event_type class
            # which is related to the event_type database table.
            cur_event = ev_core.Event(start_time = start_time,
                                   end_time = end_time,
                                   public_id = cur_event_dict['event_id'],
                                   #event_type = cur_event_dict['origins'][0]['event_type'],
                                   description = cur_event_dict['location'],
                                   agency_uri = cur_event_dict['origins'][0]['author'])

            catalog.add_events([cur_event,])

        return catalog


    def parse_ims1_0_short(self):
        ''' Parse an IMS1.0:short bulletin.
        '''
        block_parser = {}
        block_parser['event'] = self.parse_event_title_block
        block_parser['origin'] = self.parse_origin_block
        block_parser['magnitude'] = self.parse_magnitude_block
        block_parser['phase'] = self.parse_phase_block
        block_parser['isf_comment'] = self.parse_isf_comment

        cur_block = None

        for cur_line in self.b_file:
            cur_line = cur_line.rstrip()
            self.logger.debug(cur_line)

            if cur_line.lower().startswith('event'):
                # Parse the event title block.
                cur_block = 'event'
            elif cur_line.lstrip().lower().startswith('date'):
                # Parse the origin block.
                cur_block = 'origin'
                cur_line = self.b_file.next().rstrip()
                self.logger.debug(cur_line)
            elif cur_line.lstrip().lower().startswith('magnitude'):
                # Parse the magnitude sub-block.
                cur_block = 'magnitude'
                cur_line = self.b_file.next().rstrip()
                self.logger.debug(cur_line)
            elif cur_line.lower().startswith('sta'):
                # Parse the phase block.
                cur_block = 'phase'
                cur_line = self.b_file.next().rstrip()
                self.logger.debug(cur_line)
            elif self.bulletin_title is None:
                # Read the bulletin title string.
                self.logger.debug('Reading the bulletin title.')
                self.bulletin_title = cur_line
            elif cur_line.startswith('#'):
                # Lines starting with a hashtag are comments.
                cur_block = 'comment'
            elif cur_line.startswith(' (#') and cur_line.endswith(')'):
                # Lines starting with a blank, open paranthesis and a hashtag
                # ar ISF comments.
                cur_block = 'isf_comment'
            elif cur_line.lower().startswith('stop'):
                # The end of the bulletin is reached. Save the last event and 
                # stop parsing.
                if len(self.event_dict) != 0:
                    self.events.append(self.event_dict.copy())
                return True

            # Check for empty lines.
            if len(cur_line.strip()) == 0:
                continue

            # Check for comment lines.
            if cur_line.startswith(' ') and cur_line[1] == '(' and cur_line.endswith(')'):
                if cur_block != 'isf_comment':
                    continue

            if cur_block in block_parser.iterkeys():
                block_parser[cur_block](cur_line)

        return False



    def parse_event_title_block(self, cur_line):
        ''' Parse the IMS1.0 event title block.
        '''
        self.logger.debug('Parsing the event title block.')
        if len(self.event_dict) != 0:
            # Save an already parsed event to the list.
            self.events.append(self.event_dict.copy())

        self.event_dict = {}
        self.event_dict['origins'] = []
        self.event_dict['magnitudes'] = []
        self.event_dict['phases'] = []
        self.event_dict['event_id'] = cur_line[6:14].strip()
        self.event_dict['location'] = cur_line[15:80].strip()


    def parse_origin_block(self, cur_line):
        ''' Parse the IMS1.0 origin block.
        '''
        self.logger.debug('Parsing the origin block.')
        if len(cur_line) < 136:
            self.logger.warn("The length of the origin block line is too small. Skipping this line: %s", cur_line)
            return

        cur_origin = {}
        cur_date = cur_line[0:10].strip()
        [cur_year, cur_month, cur_day] = cur_date.split('/')
        cur_time = cur_line[11:22].strip()
        time_split = re.split('[:\.]', cur_time)
        cur_hour = time_split[0]
        cur_min = time_split[1]
        cur_sec = time_split[2]
        if len(time_split) == 4:
            cur_ms = time_split[3]
        else:
            cur_ms = 0

        cur_origin['starttime'] = utcdatetime.UTCDateTime(year = int(cur_year),
                                                          month = int(cur_month),
                                                          day = int(cur_day),
                                                          hour = int(cur_hour),
                                                          minute = int(cur_min),
                                                          second = int(cur_sec),
                                                          microsecond = int(cur_ms)*1000)
        cur_origin['fixed_ot_flag'] = cur_line[22]

        try:
            cur_origin['origin_time_error'] = float(cur_line[24:29].strip())
        except:
            cur_origin['origin_time_error'] = None

        try:
            cur_origin['rms_residuals'] = float(cur_line[30:35].strip())
        except:
            cur_origin['rms_residuals'] = None

        try:
            cur_origin['latitude'] = float(cur_line[36:44].strip())
        except:
            cur_origin['latitude'] = None

        try:
            cur_origin['longitude'] = float(cur_line[45:54].strip())
        except:
            cur_origin['longitude'] = None

        cur_origin['fixed_epi_flag'] = cur_line[54].strip()

        try:
            cur_origin['ellips_semi_major_axis'] = float(cur_line[56:60].strip())
        except:
            cur_origin['ellips_semi_major_axis'] = None

        try:
            cur_origin['ellips_semi_minor_axis'] = float(cur_line[61:66].strip())
        except:
            cur_origin['ellips_semi_minor_axis'] = None

        try:
            cur_origin['ellips_strike'] = int(cur_line[67:70].strip())
        except:
            cur_origin['ellips_strike'] = None

        try:
            cur_origin['depth'] = float(cur_line[71:76].strip())
        except:
            cur_origin['depth'] = None

        cur_origin['fixed_depth_flag'] = cur_line[76].strip()

        try:
            cur_origin['depth_error'] = float(cur_line[24:29].strip())
        except:
            cur_origin['depth_error'] = None

        try:
            cur_origin['num_def_phases'] = int(cur_line[83:87].strip())
        except:
            cur_origin['num_def_phases'] = None

        try:
            cur_origin['num_def_stations'] = int(cur_line[88:92].strip())
        except:
            cur_origin['num_def_stations'] = None

        try:
            cur_origin['gap'] = int(cur_line[93:96].strip())
        except:
            cur_origin['gap'] = None

        try:
            cur_origin['dist_closest_station'] = float(cur_line[97:103].strip())
        except:
            cur_origin['dist_closest_station'] = None

        try:
            cur_origin['dist_furthest_station'] = float(cur_line[104:110].strip())
        except:
            cur_origin['dist_furthest_station'] = None

        cur_origin['analysis_type'] = cur_line[111].strip()
        cur_origin['location_method'] = cur_line[113].strip()
        cur_origin['event_type'] = cur_line[115:117].strip()
        cur_origin['author'] = cur_line[118:127].strip()
        cur_origin['origin_id'] = cur_line[128:136].strip()

        self.event_dict['origins'].append(cur_origin)


    def parse_magnitude_block(self, cur_line):
        ''' Parser the IMS1.0 magnitude block.
        '''
        self.logger.debug('Parsing the magnitude sub-block.')
        cur_mag = {}
        cur_mag['magnitude_type'] = cur_line[0:5].strip()
        cur_mag['min_max'] = cur_line[5]
        try:
            cur_mag['magnitude_value'] = float(cur_line[6:10].strip())
        except:
            cur_mag['magnitude_value'] = None

        try:
            cur_mag['std_magnitude_error'] = float(cur_line[11:14].strip())
        except:
            cur_mag['std_magnitude_error'] = None

        try:
            cur_mag['num_stations'] = int(cur_line[15:19].strip())
        except:
            cur_mag['num_stations'] = None

        cur_mag['author'] = cur_line[20:29].strip()

        try:
            cur_mag['orig_id'] = int(cur_line[30:38].strip())
        except:
            cur_mag['orig_id'] = None


        self.event_dict['magnitudes'].append(cur_mag)



    def parse_phase_block(self, cur_line):
        ''' Parser the IMS1.0 phase block.
        '''
        self.logger.debug('Parsing the phase block.')
        cur_phase = {}

        cur_phase['station_code'] = cur_line[0:5].strip()
        try:
            cur_phase['station_to_event_dist'] = float(cur_line[6:12].strip())
        except:
            cur_phase['station_to_event_dist'] = None

        try:
            cur_phase['event_to_station_azimuth'] = float(cur_line[13:18].strip())
        except:
            cur_phase['event_to_station_azimuth'] = None

        cur_phase['phase_code'] = cur_line[19:27].strip()

        cur_phase['arrival_time'] = {}
        cur_phase['arrival_time']['hour'] = int(cur_line[28:30])
        cur_phase['arrival_time']['minute'] = int(cur_line[31:33])
        cur_phase['arrival_time']['second'] = float(cur_line[34:40])

        try:
            cur_phase['time_residual'] = float(cur_line[41:46])
        except:
            cur_phase['time_residual'] = None

        try:
            cur_phase['observed_azimuth'] = float(cur_line[47:52])
        except:
            cur_phase['observed_azimuth'] = None

        try:
            cur_phase['azimuth_residual'] = float(cur_line[53:58])
        except:
            cur_phase['azimuth_residual'] = None

        try:
            cur_phase['observed_slowness'] = float(cur_line[59:65])
        except:
            cur_phase['observed_slowness'] = None

        try:
            cur_phase['slowness_residual'] = float(cur_line[66:72])
        except:
            cur_phase['slowness_residual'] = None

        cur_phase['t_flag'] = cur_line[73]
        cur_phase['a_flag'] = cur_line[74]
        cur_phase['s_flag'] = cur_line[75]

        try:
            cur_phase['snr'] = float(cur_line[77:82])
        except:
            cur_phase['snr'] = None

        try:
            cur_phase['amplitude'] = float(cur_line[83:92])
        except:
            cur_phase['amplitude'] = None

        try:
            cur_phase['period'] = float(cur_line[93:98])
        except:
            cur_phase['period'] = None

        cur_phase['pick_type'] = cur_line[99]
        cur_phase['direction_sp_motion'] = cur_line[100]
        cur_phase['onset_quality'] = cur_line[101]
        cur_phase['magnitude_type'] = cur_line[103:108].strip()
        cur_phase['min_max'] = cur_line[108]

        try:
            cur_phase['magnitude_value'] = float(cur_line[109:113])
        except:
            cur_phase['magnitude_value'] = None

        cur_phase['arrival_identification'] = cur_line[114:122].strip()

        self.event_dict['phases'].append(cur_phase)


    def parse_isf_comment(self, cur_line):
        ''' Parse an ISF comment.
        '''
        cur_comment_line = cur_line[3:-1]
        keyword = cur_comment_line.split(' ')[0]
        if keyword.lower() == 'prime':
            self.event_dict['pref_origin'] = self.event_dict['origins'][-1]







class CsvParser(object):
    ''' Parse a CSV event file.
    '''

    def __init__(self):
        # the logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        logger_name = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

        self.events = []


    def parse(self, filename):
        ''' Parse a text file in CSV format.

        First row is a header line.
        The following lines contain the data.

        public_id, start_time, end_time, description, author_uri, agency_uri
        event_1,2015-01-01T01:00:00.000000,2015-01-01T01:00:10.000000,example event 1,sm,mr
        event_2,2015-01-02T01:00:00.000000,2015-01-02T01:00:10.000000,example event 1,sm,mr

        If the author_uri AND the agency uri is empty, the URIs of the current psysmon user will be used.

        Parameters
        ----------
        filename : String
            The CSV file to parse.
        '''
        if not os.path.exists(filename):
            self.logger.error("The filename %s doesn't exist.", filename)
            return False

        with open(filename, 'rb') as event_file:
            csv_reader = csv.reader(event_file, delimiter = ',', quotechar = '"')
            header_line = csv_reader.next()
            for cur_row in csv_reader:
                if cur_row:
                    cur_event = ev_core.Event(public_id = cur_row[0],
                                              start_time = utcdatetime.UTCDateTime(cur_row[1]),
                                              end_time = utcdatetime.UTCDateTime(cur_row[2]),
                                              description = cur_row[3],
                                              author_uri = cur_row[4],
                                              agency_uri = cur_row[5])
                    self.events.append(cur_event)

        return True


    def get_catalog(self, name = 'csv_parsed', author_uri = None, agency_uri = None):
        ''' Get a catalog instance of the parsed csv file.
        '''
        catalog = ev_core.Catalog(name = name, agency_uri = agency_uri,
                                  author_uri = author_uri)

        # Adjust the URIs of the events.
        if author_uri or agency_uri:
            for cur_event in self.events:
                if not cur_event.author_uri and not cur_event.agency_uri:
                    cur_event.author_uri = author_uri
                    cur_event.agency_uri = agency_uri
        catalog.add_events(self.events)

        return catalog






