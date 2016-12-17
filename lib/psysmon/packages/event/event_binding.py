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
import operator as op

import obspy.core.utcdatetime as utcdatetime
import obspy.geodetics as geodetics

import psysmon.packages.event.core as ev_core



class EventBinder(object):
    ''' Bind detections on various stations to an event.
    '''

    def __init__(self, event_catalog, author_uri = None, agency_uri = None):
        ''' Initialize the instance.
        '''
        # The event catalog to which the events should be added.
        self.event_catalog = event_catalog

        # The search windows for all combinations of stations.
        # This is a dictionary of dictionaries with the snl as keys.
        self.search_windows = {}

        self.author_uri = author_uri

        self.agency_uri = agency_uri

    def bind(self, catalog, channel_scnl):
        ''' Bind the detections to events.
        '''
        # Get the detections of the channels and sort them according to time.
        detections = {}
        for cur_scnl in channel_scnl:
            detections[cur_scnl] = catalog.get_detections(scnl = cur_scnl)
            detections[cur_scnl] = sorted(detections[cur_scnl], key = op.attrgetter('start_time'))

        # Get the earlies detection of each channel. Remove these detections
        # from the detections list.
        next_detections = [x[0] for x in detections.values() if len(x) > 0]

        while len(next_detections) > 0:
            next_detections = sorted(next_detections, key = op.attrgetter('start_time'))
            first_detection = next_detections.pop(0)

            # Get the search windows for the detection combinations.
            search_windows = self.get_search_window(first_detection, next_detections)

            # Get the detections matching the search window.
            match_detections = [x for k,x in enumerate(next_detections) if x.start_time <= first_detection.start_time + search_windows[k]]
            match_detections.append(first_detection)

            # Create an event using the matching detections.
            event = ev_core.Event(start_time = min([x.start_time for x in match_detections]),
                                  end_time = max([x.end_time for x in match_detections]),
                                  author_uri = self.author_uri,
                                  agency_uri = self.agency_uri,
                                  creation_time = utcdatetime.UTCDateTime(),
                                  detections = match_detections)
            self.event_catalog.add_events([event, ])

            # Remove the matching detections from the detections list.
            for cur_detection in match_detections:
                detections[cur_detection.scnl].remove(cur_detection)

            # Get the next earliest detection of each channel.
            next_detections = [x[0] for x in detections.values() if len(x) > 0]


    def get_search_window(self, master, slaves):
        ''' Get the search time windows.
        '''
        search_windows = []
        for cur_slave in slaves:
            cur_win = self.search_windows[master.snl][cur_slave.snl]
            search_windows.append(cur_win)

        return search_windows


    def compute_search_windows(self, stations, vel = 1000.):
        ''' Compute the search windows for the given stations.

        The length of the search windows is computed using a simple
        velocity model with constant velocity.
        The computed search window is saved in the search_windows attribute.

        Paramters
        ---------
        stations : List of :class:`~psysmon.packages.geometry.inventory.Station`
            The stations for wich the search windows are computed.

        vel : float
            The velocity used to compute the search window [m/s].
            For the distance the great circle distance between a station pair 
            is used.

        '''
        vel = float(vel)
        # Compute the search windows.
        for cur_station in stations:
            cur_search_win = {}
            for cur_dst in stations:
                src_lonlat = cur_station.get_lon_lat()
                dst_lonlat = cur_dst.get_lon_lat()
                dist, az1, az2 = geodetics.gps2dist_azimuth(src_lonlat[0], src_lonlat[1],
                                                            dst_lonlat[0], src_lonlat[1])
                cur_search_win[cur_dst.snl] = dist / vel

            self.search_windows[cur_station.snl] = cur_search_win



