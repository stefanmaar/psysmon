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
''' STA/LTA event detection.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
import logging
import copy
import numpy as np
import matplotlib.pyplot as plt

import psysmon
from psysmon.core.packageNodes import CollectionNode
import psysmon.core.preferences_manager as psy_pm
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.lib_signal as lib_signal

from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack



class StaLtaDetectionNode(CollectionNode):
    ''' Do a STA/LTA event detection.

    '''
    name = 'STA/LTA event detection'
    mode = 'editable'
    category = 'Event'
    tags = ['stable', 'event', 'STA/LTA', 'detect']


    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

        # Setup the pages of the preference manager.
        self.pref_manager.add_page('General')
        self.pref_manager.add_page('STA/LTA')
        self.pref_manager.add_page('Processing')

        # The start_time.
        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The end time.
        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The stations to process.
        item = psy_pm.MultiChoicePrefItem(name = 'stations',
                                          label = 'stations',
                                          group = 'components to process',
                                          limit = ('value 1', 'value 2', 'value 3', 'value 4', 'value 5'),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the detection.')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The channels to process.
        item = psy_pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          group = 'components to process',
                                          limit = ('value 1', 'value 2', 'value 3', 'value 4', 'value 5'),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the detection.')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The STA/LTA parameters
        item = psy_pm.SingleChoicePrefItem(name = 'cf_type',
                                           label = 'characteristic function',
                                           group = 'detection',
                                           limit = ('abs', 'square'),
                                           value = 'square',
                                           tool_tip = 'The type of the characteristic function used to compute the STA and LTA.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'sta_len',
                                        label = 'STA length [s]',
                                        group = 'detection',
                                        value = 1,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The length of the STA in seconds.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'lta_len',
                                        label = 'LTA length [s]',
                                        group = 'detection',
                                        value = 10,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The length of the LTA in seconds.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'thr',
                                        label = 'threshold',
                                        group = 'detection',
                                        value = 3,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The threshold of STA/LTA when to trigger an event.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'pre_et',
                                        label = 'pre-event time [s]',
                                        group = 'detection',
                                        value = 1,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The time window to add before the detected event start [s].')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'post_et',
                                        label = 'post-event time [s]',
                                        group = 'detection',
                                        value = 1,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The time window to add after the detected event end [s].')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.CustomPrefItem(name = 'processing_stack',
                                     label = 'processing stack',
                                     group = 'signal processing',
                                     value = None,
                                     gui_class = PStackEditField,
                                     tool_tip = 'Edit the processing stack nodes.')
        self.pref_manager.add_item(pagename = 'Processing',
                                   item = item)


    def edit(self):
        if self.project.geometry_inventory:
            stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
            self.pref_manager.set_limit('stations', stations)

            channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
            self.pref_manager.set_limit('channels', channels)

        processing_nodes = self.project.getProcessingNodes(('common', ))
        if self.pref_manager.get_value('processing_stack') is None:
                detrend_node_template = [x for x in processing_nodes if x.name == 'detrend'][0]
                detrend_node = copy.deepcopy(detrend_node_template)
                self.pref_manager.set_value('processing_stack', [detrend_node, ])

        self.pref_manager.set_limit('processing_stack', processing_nodes)

        dlg = ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        processing_stack = ProcessingStack(name = 'pstack',
                                           project = self.project,
                                           nodes = self.pref_manager.get_value('processing_stack'))
        detector = StaLtaDetector(cf_type = self.pref_manager.get_value('cf_type'),
                                  sta_len = self.pref_manager.get_value('sta_len'),
                                  lta_len = self.pref_manager.get_value('lta_len'),
                                  thr = self.pref_manager.get_value('thr'),
                                  project = self.project,
                                  processing_stack = processing_stack)

        detector.detect(start_time = self.pref_manager.get_value('start_time'),
                        end_time = self.pref_manager.get_value('end_time'),
                        stations = self.pref_manager.get_value('stations'),
                        channels = self.pref_manager.get_value('channels'))


 

class StaLtaDetector(object):

    def __init__(self, cf_type = 'square', sta_len = 2,
                 lta_len = 10, thr = 3, project = None,
                 processing_stack = None):

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The type of the characteristic function.
        self.cf_type = cf_type


        # The length of the STA in seconds.
        self.sta_len = sta_len

        # The length of the LTA in seconds.
        self.lta_len = lta_len

        # The threshold of the STA/LTA ratio when to declare the begin of an
        # event.
        self.thr = thr

        # The psysmon project.
        self.project = project

        # The processing stack used for signal processing before running the
        # detection.
        self.processing_stack = processing_stack


    def detect(self, start_time, end_time, stations, channels, interval = 3600.):
        ''' Start the detection.

        Parameters
        ----------
        start_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The start time of the timespan for which to detect the events.

        end_time : :class:`~obspy.core.utcdatetime.UTCDateTime`
            The end time of the timespan for which to detect the events.

        stations : list of Strings
            The names of the stations to process.

        channels : list of Strings
            The names of the channels to process.

        interval : float
            The interval into which the time span is split to run successive detections.

        '''
        interval = float(interval)

        n_intervals = (end_time - start_time) / interval
        interval_list = [start_time + x*interval for x in range(0, int(n_intervals))]

        if not interval_list:
            interval_list.append(start_time)

        scnl = []
        for cur_station_name in stations:
            for cur_channel_name in channels:
                cur_channel = self.project.geometry_inventory.get_channel(station = cur_station_name,
                                                                          name = cur_channel_name)
                if len(cur_channel) > 1:
                    raise RuntimeError("More than one channel returned. Expected 0 or 1. There seems to be a problem in the geometry inventory.")
                if cur_channel:
                    scnl.append(cur_channel[0].scnl)


        data_sources = self.get_data_sources(scnl)

        for cur_start_time in interval_list:
            cur_end_time = cur_start_time + interval
            self.logger.info("Processing timespan %s to %s.", cur_start_time.isoformat(),
                              cur_end_time.isoformat())

            for cur_scnl in scnl:
                try:
                    cur_channel = self.project.geometry_inventory.get_channel(station = cur_scnl[0], name = cur_scnl[1], network = cur_scnl[2])[0]
                    cur_timebox = cur_channel.get_stream(start_time = cur_start_time, end_time = cur_end_time)[0]
                    cur_stream_id = cur_timebox.item.id
                except:
                    cur_stream_id = None

                cur_waveclient = self.project.waveclient[data_sources[cur_scnl]]
                # Request data with a preceding window of length lta_len to
                # eliminate the lta buildup effects at the start of the time
                # window.
                cur_stream = cur_waveclient.getWaveform(startTime = cur_start_time - self.lta_len,
                                                        endTime = cur_end_time,
                                                        scnl = [cur_scnl, ])
                cur_stream = cur_stream.copy()

                if cur_stream:
                    self.logger.info("Processing stream %s.", cur_stream)
                    try:
                        cur_stream = cur_stream.split()
                        self.processing_stack.execute(cur_stream)
                        #cur_stream.detrend(type = 'constant')
                        #cur_stream.filter('bandpass', freqmin = 1.0, freqmax = 100.0)
                    except Exception as e:
                        self.logger.error('Error when processing the stream %s:\n%s', str(cur_stream), e)
                        continue

                    db_data = []
                    for cur_trace in cur_stream.traces:
                        cf = self.compute_cf(cur_trace.data)
                        cur_sps = cur_trace.stats.sampling_rate
                        thrf, sta, lta = self.compute_thrf(cf, cur_sps)
                        n_lta = int(self.lta_len * cur_sps)
                        event_marker = self.compute_event_limits(cur_trace.data[n_lta:],
                                                                 thrf, sta, lta)
                        detection_table = self.project.dbTables['detection']
                        event_table = self.project.dbTables['event']
                        for det_start_ind, det_end_ind in event_marker:
                            det_start_time = cur_trace.stats.starttime + (n_lta + det_start_ind) / cur_sps
                            det_end_time = det_start_time + (det_end_ind - det_start_ind) / cur_sps
                            cur_orm = detection_table(catalog_id = None,
                                                      rec_stream_id = cur_stream_id,
                                                      start_time = det_start_time.timestamp,
                                                      end_time = det_end_time.timestamp,
                                                      method = 'STA/LTA',
                                                      agency_uri = self.project.activeUser.agency_uri,
                                                      author_uri = self.project.activeUser.author_uri,
                                                      creation_time = UTCDateTime().isoformat())
                            db_data.append(cur_orm)

                            # TODO: Remove this export to the events database
                            # when the event binding is working.
                            # Add the events detected on station AP01 and
                            # channel HHZ to the events database.
                            # This is used as a workaround because of a missing
                            # event binding.
                            if cur_scnl == ('AP01', 'HHZ', 'APO', '00'):
                                comment_string = 'Detected on SCNL %s.' % str(cur_scnl)
                                #comment_string = 'delete me'
                                cur_orm = event_table(ev_catalog_id = None,
                                                      start_time = det_start_time.timestamp,
                                                      end_time = det_end_time.timestamp,
                                                      comment = comment_string,
                                                      agency_uri = self.project.activeUser.agency_uri,
                                                      author_uri = self.project.activeUser.author_uri,
                                                      creation_time = UTCDateTime().isoformat())
                                db_data.append(cur_orm)

                if db_data:
                    db_session = self.project.getDbSession()
                    db_session.add_all(db_data)
                    db_session.commit()
                    db_session.close()







    def get_data_sources(self, scnl):
        ''' Get the datasource for a given SCNL.

        Parameters
        ----------
        scnl : List of Tuple (STATION, CHANNEL, NETWORK, LOCATION)
            The SCNL for which to get the according waveclient.
        '''
        data_sources = {}
        for cur_scnl in scnl:
            if cur_scnl in self.project.scnlDataSources.keys():
                data_sources[cur_scnl] = self.project.scnlDataSources[cur_scnl]
            else:
                data_sources[cur_scnl] = self.project.defaultWaveclient

        return data_sources


    def compute_cf(self, data):
        ''' Compute the characteristic function.
        '''

        if self.cf_type == 'abs':
            return np.abs(data)
        elif self.cf_type == 'square':
            return data**2
        else:
            return data


    def compute_thrf(self, cf, sps, mode = 'valid'):
        ''' Compute the THRF, STA and LTA function.

        Parameters
        ----------
        cf : NumpyArray
            The characteristic function computed from the timeseries.

        sps : float
            The samples per second of the characteristic function.

        mode : String (valid, full)
            How to return the computed time series.
                valid: Return only the valid values without the LTA buildup effect.
                full: Return the full length of the computed time series.
        '''
        clib_signal = lib_signal.clib_signal

        n_sta = int(self.sta_len * sps)
        n_lta = int(self.lta_len * sps)

        # The old version using np.correlate. This was way too slow. Switched
        # to the implementation of the moving average in C. Keep this part of
        # the code for future reference.
        #sta_filt_op = np.ones(n_sta) / float(n_sta)
        #lta_filt_op = np.ones(n_lta) / float(n_lta)
        #sta_corr = np.correlate(cf, sta_filt_op, 'valid')
        #lta_corr = np.correlate(cf, lta_filt_op, 'valid')
        #sta_corr = np.concatenate([np.zeros(n_sta - 1), sta_corr])
        #lta_corr = np.concatenate([np.zeros(n_lta - 1), lta_corr])

        n_cf = len(cf)
        cf = np.ascontiguousarray(cf, dtype = np.float64)
        sta = np.empty(n_cf, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_cf, n_sta, cf, sta)
        lta = np.empty(n_cf, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_cf, n_lta, cf, lta)


        #sta[0:n_lta] = 0
        #lta[0:n_lta] = 1
        thrf = sta / lta

        if mode == 'valid':
            thrf = thrf[n_lta:]
            sta = sta[n_lta:]
            lta = lta[n_lta:]

        return (thrf, sta, lta)


    def compute_event_limits(self, data, thrf, sta, lta, stop_delay = 10):
        ''' Compute the event start and end times based on the detection functions.

        '''
        event_marker = []

        # Find the event begins indicated by exceeding the threshold value.
        event_on = np.zeros(thrf.shape)
        event_on[thrf >= self.thr] = 1
        event_start = np.zeros(thrf.shape)
        event_start[1:] = np.diff(event_on)

        # Find the event ends.
        event_start_ind = np.flatnonzero(event_start == 1)
        stop_values = sta[np.flatnonzero(event_start == 1) - stop_delay]

        for k, cur_event_start in enumerate(event_start_ind):
            try:
                next_end_ind = np.flatnonzero(sta[cur_event_start:] < stop_values[k])[0]
                cur_event_end = cur_event_start + next_end_ind
            except:
                cur_event_end = len(thrf)-1
            event_marker.append((cur_event_start, cur_event_end))

#        plt.plot(sta, 'r')
#        plt.plot(self.thr * lta, 'g')
#        plt.plot(data, 'k')
#        for event_begin, event_end in event_marker:
#            plt.axvline(event_begin, color = 'm')
#            plt.axvline(event_end, color = 'b')
#        plt.show()


        return event_marker



