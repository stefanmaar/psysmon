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
''' Event binding.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
from __future__ import division
from builtins import object
from past.utils import old_div
import logging
import operator as op

import obspy.core.utcdatetime as utcdatetime
import obspy.geodetics as geodetics

import psysmon
import psysmon.packages.event.core as ev_core



class DetectionBinder(object):
    ''' Bind detections on various stations to an event.
    '''

    def __init__(self, event_catalog, stations, author_uri = None, agency_uri = None):
        ''' Initialize the instance.

        Parameters
        ----------
        stations : List of :class:`~psysmon.packages.geometry.inventory.Station`
            The stations for wich the search windows are computed.

        '''
        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        # The event catalog to which the events should be added.
        self.event_catalog = event_catalog

        # The stations used for binding the detections.
        self.stations = stations

        # The search windows for all combinations of stations.
        # This is a dictionary of dictionaries with the snl as keys.
        self.search_windows = {}

        # The epicentral distances bewteen the stations.
        self.epi_dist = {}

        self.author_uri = author_uri

        self.agency_uri = agency_uri

    def bind(self,
             catalog,
             channel_scnl,
             n_neighbors = 2,
             min_match_neighbors = 2,
             extend_ratio = 0.01,
             min_extend = 0.5,
             max_extend = 10):
        ''' Bind the detections to events.
        '''
        # Get the detections of the channels and sort them according to time.
        detections = {}
        for cur_scnl in channel_scnl:
            detections[cur_scnl] = catalog.get_detections(scnl = cur_scnl)
            detections[cur_scnl] = sorted(detections[cur_scnl],
                                          key = op.attrgetter('start_time'))

        # Get the earlies detection of each channel. Remove these detections
        # from the detections list.
        next_detections = [x[0] for x in list(detections.values()) if len(x) > 0]

        while len(next_detections) > 0:

            next_detections = sorted(next_detections,
                                     key = op.attrgetter('start_time'))
            first_detection = next_detections.pop(0)

            self.logger.debug('Processing detection %d, %s, %s.',
                              first_detection.db_id,
                              first_detection.start_time,
                              first_detection.snl)

            # Compute the search window extend based on the length
            # of the main detection.
            search_win_extend = first_detection.length * extend_ratio
            if search_win_extend < min_extend:
                search_win_extend = min_extend
            elif search_win_extend > max_extend:
                search_win_extend = max_extend

            self.logger.debug('main detection length: %f.', first_detection.length)
            self.logger.debug('search_win_extend: %f.', search_win_extend)

            # Get the search windows for the detection combinations.
            search_windows = self.get_search_window(first_detection,
                                                    next_detections)
            self.logger.debug('Search windows: %s', search_windows)
            ext_sw = [x + search_win_extend for x in search_windows]
            self.logger.debug('Extended search windows: %s', ext_sw)

            # Get the detections matching the search window.
            match_detections = [x for k, x in enumerate(next_detections) if x.start_time <= first_detection.start_time + ext_sw[k]]
            self.logger.debug('Matching detections: %s.', [(x.db_id, x.start_time, x.snl) for x in match_detections])

            # Check if there are matching detections on neighboring stations.
            # There have to be detections at at least min_match_neighbors.
            # If there are not enough matching detections, all matching
            # detections have to be on neighbor stations.

            #TODO: The neighbors should contain only stations which have been
            # selected for binding the detections.
            neighbors = self.epi_dist[first_detection.snl]
            if len(neighbors) > (n_neighbors + 1):
                neighbors = neighbors[1:n_neighbors + 1]
            #neighbors = [x for x in neighbors if x[1] <= max_neighbor_dist]
            neighbors_snl = [x[0] for x in neighbors]
            match_snl = [x.snl for x in match_detections]
            match_neighbors = [x for x in neighbors_snl if x in match_snl]

            self.logger.debug('neighbors_snl: %s', neighbors_snl)
            self.logger.debug('match_snl: %s', match_snl)

            # TODO: Add a check for detections on distant neighbors.
            # If there is a small number of detections on distant stations,
            # check for detections on stations with a similar epi distance. If
            # no detections are found on these similar stations, reject the
            # binding.

            if len(neighbors) < min_match_neighbors:
                raise RuntimeError("Not enough neighbors found for station %s. Detection ID: %d.", first_detection.snl, first_detection.db_id)

            # TODO: Maybe add the following option.
            # Add a dedicated option to check, if a
            # small number of neighbors have matching detections, they should
            # all be direct neighbors to the master station.
            if len(match_neighbors) < min_match_neighbors:
                # There are not enough detection on neigboring stations.
                # Reset the matched detections.
                self.logger.debug('Not enough detections on neighboring stations. Detection ID: %d. Start time: %s', first_detection.db_id, first_detection.start_time)
                match_detections = []
            else:
                # This is a valid event.
                # Add the first detection to the match detections.
                match_detections.append(first_detection)

            if match_detections:
                # Create an event using the matching detections.
                creation_time = utcdatetime.UTCDateTime()
                start_time = min([x.start_time for x in match_detections])
                end_time = max([x.end_time for x in match_detections])
                event = ev_core.Event(start_time = start_time,
                                      end_time = end_time,
                                      author_uri = self.author_uri,
                                      agency_uri = self.agency_uri,
                                      creation_time = creation_time,
                                      detections = match_detections)
                self.event_catalog.add_events([event, ])
                self.logger.debug('Added event %s to %s.',
                                  event.start_time,
                                  event.end_time)

                # Remove the matching detections from the detections list.
                for cur_detection in match_detections:
                    detections[cur_detection.scnl].remove(cur_detection)
            else:
                # Remove the first detection from the detections list.
                detections[first_detection.scnl].remove(first_detection)

            # Get the next earliest detection of each channel.
            next_detections = [x[0] for x in list(detections.values()) if len(x) > 0]


    def get_search_window(self, master, slaves):
        ''' Get the search time windows.
        '''
        search_windows = []
        for cur_slave in slaves:
            cur_win = self.search_windows[master.snl][cur_slave.snl]
            search_windows.append(cur_win)

        return search_windows


    def compute_search_windows(self, vel = 1000.):
        ''' Compute the search windows for the given stations.

        The length of the search windows is computed using a simple
        velocity model with constant velocity.
        The computed search window is saved in the search_windows attribute.

        Paramters
        ---------
        vel : float
            The velocity used to compute the search window [m/s].
            For the distance the great circle distance between a station pair 
            is used.

        '''
        # TODO: Make this a user preference.
        # The minimum length of the search window.
        min_search_win = 0.2

        # TODO: Use a standard earth model to compute the search windows. Use
        # the P and S phases to determine the window width.

        vel = float(vel)
        # Compute the search windows.
        for cur_station in self.stations:
            cur_search_win = {}
            cur_epi_dist = []
            src_lonlat = cur_station.get_lon_lat()
            for cur_dst in self.stations:
                dst_lonlat = cur_dst.get_lon_lat()
                dist, az1, az2 = geodetics.gps2dist_azimuth(lon1 = src_lonlat[0], lat1 = src_lonlat[1],
                                                            lon2 = dst_lonlat[0], lat2 = dst_lonlat[1])
                cur_tt = old_div(dist, vel)
                if cur_tt < min_search_win:
                    cur_tt = min_search_win
                cur_search_win[cur_dst.snl] = cur_tt
                cur_epi_dist.append((cur_dst.snl, dist))

            cur_epi_dist = sorted(cur_epi_dist, key = lambda x: x[1])
            self.search_windows[cur_station.snl] = cur_search_win
            self.epi_dist[cur_station.snl] = cur_epi_dist



