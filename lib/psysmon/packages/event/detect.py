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
''' Event detection.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
from profilehooks import profile

import logging
import numpy as np
import scipy.signal

import psysmon
import psysmon.core.lib_signal as lib_signal
import psysmon.packages.event.lib_detect_sta_lta as lib_detect_sta_lta



class StaLtaDetector:
    ''' Run a standard STA/LTA Detection.
    '''

    def __init__(self, data = None, cf_type = 'square', n_sta = 2,
                 n_lta = 10, thr = 3):
        ''' Initialize the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The type of the characteristic function.
        self.allowed_cf_type = ['abs', 'square', 'envelope', 'envelope^2']
        if cf_type not in self.allowed_cf_type:
            raise ValueError("Wrong value for cf_type. Allowed are: %s." % self.allowed_cf_type)
        self.cf_type = cf_type

        # The length of the STA in samples.
        self.n_sta = n_sta

        # The length of the LTA in samples.
        self.n_lta = n_lta

        # The threshold of the STA/LTA ratio when to declare the begin of an
        # event.
        self.thr = thr

        # The data array.
        if data is None:
            self.data = np.empty((0,0))
        else:
            self.data = data

        # The computed STA/LTA data.
        self.cf = np.empty((0,0))
        self.sta = np.empty((0,0))
        self.lta = np.empty((0,0))


    def set_data(self, data):
        ''' Set the data array an clear all related features.
        '''
        self.data = data

        self.cf = np.empty((0,0))
        self.sta = np.empty((0,0))
        self.lta = np.empty((0,0))



    def compute_cf(self):
        ''' Compute the characteristic function.
        '''
        if self.cf_type not in self.allowed_cf_type:
            raise ValueError("Wrong value for cf_type. Allowed are: %s." % self.allowed_cf_type)

        if self.cf_type == 'abs':
            self.cf = np.abs(self.data)
        elif self.cf_type == 'square':
            self.cf = self.data**2
        elif self.cf_type == 'envelope':
            data_comp = scipy.signal.hilbert(self.data)
            self.cf = np.sqrt(np.real(data_comp)**2 + np.imag(data_comp)**2)
        elif self.cf_type == 'envelope^2':
            data_comp = scipy.signal.hilbert(self.data)
            self.cf = np.sqrt(np.real(data_comp)**2 + np.imag(data_comp)**2)
            self.cf = self.cf ** 2


    def compute_thrf(self, mode = 'valid'):
        ''' Compute the THRF, STA and LTA function.

        Parameters
        ----------
        cf : NumpyArray
            The characteristic function computed from the timeseries.

        mode : String (valid, full)
            How to return the computed time series.
                valid: Return only the valid values without the LTA buildup effect.
                full: Return the full length of the computed time series.
        '''
        clib_signal = lib_signal.clib_signal

        # The old version using np.correlate. This was way too slow. Switched
        # to the implementation of the moving average in C. Keep this part of
        # the code for future reference.
        #sta_filt_op = np.ones(n_sta) / float(n_sta)
        #lta_filt_op = np.ones(n_lta) / float(n_lta)
        #sta_corr = np.correlate(cf, sta_filt_op, 'valid')
        #lta_corr = np.correlate(cf, lta_filt_op, 'valid')
        #sta_corr = np.concatenate([np.zeros(n_sta - 1), sta_corr])
        #lta_corr = np.concatenate([np.zeros(n_lta - 1), lta_corr])

        n_cf = len(self.cf)
        cf = np.ascontiguousarray(self.cf, dtype = np.float64)
        self.sta = np.empty(n_cf, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_cf, self.n_sta, cf, self.sta)
        self.lta = np.empty(n_cf, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_cf, self.n_lta, cf, self.lta)

        # Use non-overlapping STA and LTA windows. The LTA is computed using
        # samples prior to the STA window.
        self.lta[self.n_sta:] = self.lta[:-self.n_sta]

        # Trim the sta and lta arrays to the valid length. The last n_sta
        # values are not valid because no shifted LTA is available.
        self.sta = self.sta[:-self.n_sta]
        self.lta = self.lta[:-self.n_sta]

        if mode == 'valid':
            self.sta = self.sta[self.n_lta:]
            self.lta = self.lta[self.n_lta:]


    @profile
    def compute_event_limits(self, stop_delay = 10):
        ''' Compute the event start and end times based on the detection functions.

        '''
        self.stop_crit = np.zeros(self.sta.shape)
        self.replace_limits = []
        event_marker = []
        self.lta_orig = self.lta.copy()

        # Find the event begins indicated by exceeding the threshold value.
        event_start, stop_value = self.compute_start_stop_values(0, stop_delay)

        # Find the event end values.
        self.logger.debug("Computing the event limits.")
        #for k, cur_event_start in enumerate(event_start_ind):

        # TODO: Put the whole detection into a c function. This prevents using
        # multiple loops through the data and the complicated removal of the
        # event influence onto the LTA.

        while event_start < (len(self.sta) - 1):
            self.logger.debug("Processing the next event. event_start_ind: %d", event_start)
            if self.sta[event_start] <= stop_value:
                stop_value = self.sta[event_start]

            # Start the search for the event end one sample after the event
            # start to avoid eventual problems with identical event_start
            # and event end.
            cur_search_start = event_start + 1

            # TODO: Use a loop in a C function do compute the event stop.
            # Using the complete array is not efficient when processing
            # long arrays.
            clib_detect = lib_detect_sta_lta.clib_detect_sta_lta
            cur_sta = np.ascontiguousarray(self.sta[cur_search_start:], dtype = np.float64)
            cur_lta = np.ascontiguousarray(self.lta[cur_search_start:], dtype = np.float64)
            cur_lta = cur_lta * self.thr
            n_cur_sta = len(cur_sta)
            n_cur_lta = len(cur_lta)
            cur_stop_crit = np.empty(n_cur_sta, dtype = np.float64)
            next_end_ind = clib_detect.compute_event_end(n_cur_sta, cur_sta, n_cur_lta, cur_lta, stop_value, cur_stop_crit)

            # Compute the stop criterium. 
            #stop_crit = self.compute_stop_criterium(cur_search_start, stop_value)

            # Compute the event end.
            #next_end_ind = self.compute_event_end(cur_search_start, stop_crit)
            cur_event_end = cur_search_start + next_end_ind

            # Remove all start indices which are smaller than the currend
            # event end.
            #new_ind = np.argwhere(event_start_ind > cur_event_end).flatten()
            #if len(new_ind) > 0:
            #    new_ind = new_ind[0]
            #    self.logger.debug("new_ind: %d", new_ind)
            #    if new_ind == 0:
            #        raise RuntimeError("The current event start STA is lower than the stop value. Using the next event_start to avoid infinite loop.")
            #
            #    event_start_ind = event_start_ind[new_ind:]
            #    stop_values = stop_values[new_ind:]
            #    self.logger.debug("event_start_ind[0]: %d", event_start_ind[0])

            # Copy the event stop criterium to the overall stop criterium array.
            self.stop_crit[cur_search_start:cur_event_end] = cur_stop_crit[:next_end_ind]

            # Remove the influence of the detected event from the LTA
            # timeseries.
            self.remove_event_influence(event_start - 50, cur_event_end)

            # Add the event marker.
            # TODO: add the lta length to the event limits. Adapt the
            # tracedisplay view accordingly.
            event_marker.append((event_start, cur_event_end))

            # Recompute the next event start indices.
            event_start, stop_value = self.compute_start_stop_values(cur_event_end, stop_delay)

        self.logger.debug("Finished the event limits computation.")
        return event_marker


    def compute_stop_criterium(self, event_start, stop_value):
        ''' Compute the stop criterium.
        '''
        # Use the detection function from the current event start on.
        cur_sta = self.sta[event_start:]
        cur_lta = self.lta[event_start:]
        stop_crit = np.ones(cur_sta.shape) * stop_value

        # Find the points where the sta is below the lta.
        sta_below_required = 10
        sta_below_lta_mask = cur_sta < (cur_lta * self.thr)
        sta_below_lta = np.zeros(sta_below_lta_mask.shape)
        sta_below_lta[sta_below_lta_mask] = 1
        sta_below_limits = np.zeros(sta_below_lta.shape)
        sta_below_limits[1:] = np.diff(sta_below_lta)
        sta_below_start_ind = np.flatnonzero(sta_below_limits == 1)
        sta_below_end_ind = np.flatnonzero(sta_below_limits == -1)
        if len(sta_below_end_ind) < len(sta_below_start_ind):
            sta_below_end_ind = np.hstack((sta_below_end_ind, [len(sta_below_lta)]))
        sta_below_duration = sta_below_end_ind - sta_below_start_ind
        sta_below_lta_long_enough = np.flatnonzero(sta_below_duration > sta_below_required)
        sta_below_lta_long_enough = sta_below_start_ind[sta_below_lta_long_enough]

        # Increase the stop criterium from the time when the sta falls
        # the last time before the prelim_event_end below the lta.
        if len(sta_below_lta_long_enough) > 0:
            start_grow = sta_below_lta_long_enough[0]
            stop_crit[start_grow:] += np.arange(len(stop_crit) - start_grow) * (stop_value * 0.001)

        return stop_crit


    def compute_event_end(self, event_start, stop_crit):
        ''' Compute the event end.
        '''
        cur_sta = self.sta[event_start:]

        sta_below_required = 100
        sta_below_stop_mask = cur_sta < stop_crit
        sta_below_stop = np.zeros(sta_below_stop_mask.shape)
        sta_below_stop[sta_below_stop_mask] = 1
        sta_below_limits = np.zeros(sta_below_stop.shape)
        sta_below_limits[0] = sta_below_stop[0]
        sta_below_limits[1:] = np.diff(sta_below_stop)
        sta_below_start_ind = np.flatnonzero(sta_below_limits == 1)
        sta_below_end_ind = np.flatnonzero(sta_below_limits == -1)
        if len(sta_below_end_ind) < len(sta_below_start_ind):
            sta_below_end_ind = np.hstack((sta_below_end_ind, [len(sta_below_stop)]))
        sta_below_duration = sta_below_end_ind - sta_below_start_ind
        sta_below_stop_long_enough = np.flatnonzero(sta_below_duration > sta_below_required)
        sta_below_stop_long_enough = sta_below_start_ind[sta_below_stop_long_enough]

        if len(sta_below_stop_long_enough) == 0:
            self.logger.warning("There is no STA value below the current stop value before the end of the data. Use the end of the data as the event end.")
            next_end_ind = len(stop_crit)
        else:
            next_end_ind = sta_below_stop_long_enough[0]

        return next_end_ind


    def remove_event_influence(self, event_start, event_end):
        ''' Remove the influence of the detected event from the LTA.
        '''
        event_lta = self.compute_replace_lta(event_start, event_end)

        # Remove the event lta from the LTA timeseries.
        event_length = event_end - event_start
        lta_replace_start = event_start + self.n_sta
        lta_replace_end = lta_replace_start + event_length + self.n_lta
        if lta_replace_start < len(self.lta):
            if lta_replace_end > len(self.lta):
                lta_replace_end = len(self.lta)
                event_lta = event_lta[:lta_replace_end - lta_replace_start]
            self.lta[lta_replace_start:lta_replace_end] -= event_lta
            self.replace_limits.append((lta_replace_start, lta_replace_end))
        else:
            self.logger.warning("The LTA replacement start is after the trace length. Didn't change the LTA.")


    def compute_replace_lta(self, event_start, event_end):
        ''' Compute the moving average used to remove the event influence on the LTA.
        '''
        # Compute the LTA moving average of the event cf only.
        event_length = event_end - event_start
        event_cf = np.zeros(2*self.n_lta + event_length)
        event_cf[self.n_lta:self.n_lta + event_length] = self.cf[event_start + self.n_lta:event_end + self.n_lta]
        c_event_cf = np.ascontiguousarray(event_cf, dtype = np.float64)
        n_event_cf = len(event_cf)
        event_lta = np.empty(n_event_cf, dtype = np.float64)
        ret_val = lib_signal.clib_signal.moving_average(n_event_cf, self.n_lta, c_event_cf, event_lta)
        noise_cf = np.zeros(event_cf.shape)
        noise_cf[self.n_lta:self.n_lta + event_length] = self.lta[event_start]
        c_noise_cf = np.ascontiguousarray(noise_cf, dtype = np.float64)
        n_noise_cf = len(noise_cf)
        noise_lta = np.empty(n_event_cf, dtype = np.float64)
        ret_val = lib_signal.clib_signal.moving_average(n_noise_cf, self.n_lta, c_noise_cf, noise_lta)
        event_lta = event_lta[self.n_lta:] - noise_lta[self.n_lta:]

        return event_lta


    def compute_start_stop_values(self, crop_start, stop_delay):
        ''' Compute the event start indices and the stop values.
        '''
        clib_detect = lib_detect_sta_lta.clib_detect_sta_lta

        thrf = np.ascontiguousarray(self.sta[crop_start:]/self.lta[crop_start:], dtype = np.float64)
        event_start = clib_detect.compute_event_start(len(thrf), thrf, self.thr)

        event_start_ind = crop_start + event_start
        stop_value = self.sta[event_start_ind - stop_delay]

        return event_start_ind, stop_value



