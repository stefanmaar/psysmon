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
import logging
import numpy as np
import scipy.signal

import psysmon
import psysmon.core.lib_signal as lib_signal



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
        self.thrf = np.empty((0,0))
        self.sta = np.empty((0,0))
        self.lta = np.empty((0,0))


    def set_data(self, data):
        ''' Set the data array an clear all related features.
        '''
        self.data = data

        self.cf = np.empty((0,0))
        self.thrf = np.empty((0,0))
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

        # Compute the threshold function.
        self.thrf = self.sta / self.lta

        if mode == 'valid':
            self.thrf = self.thrf[self.n_lta:]
            self.sta = self.sta[self.n_lta:]
            self.lta = self.lta[self.n_lta:]


    def compute_event_limits(self, stop_delay = 10):
        ''' Compute the event start and end times based on the detection functions.

        '''
        event_marker = []

        # Find the event begins indicated by exceeding the threshold value.
        event_on = np.zeros(self.thrf.shape)
        event_on[self.thrf >= self.thr] = 1
        event_start = np.zeros(self.thrf.shape)
        event_start[1:] = np.diff(event_on)

        # Get the stop values from the sta function.
        event_start_ind = np.flatnonzero(event_start == 1)
        stop_values = self.sta[np.flatnonzero(event_start == 1) - stop_delay]

        # TODO: Implement Allen's event stop criteria computation.
        # Slightly increase the stop value with time when searching for the
        # STA below the stop value.
        # Don't immediately stop the event but use some stop-wait criteria like
        # Allen does with the counting of the zero-crossings (S) and peaks (L).

        # TODO: Exclude the timespans already declared as events from the LTA
        # used for detecting new event starts. This could help to detect
        # consecutive events where the second event is not detected because the
        # LTA is still influenced by the prior event.
        # This would require a recomputation of the LTA and STA after each
        # detected event. The sample in the timeseries between the event limits
        # would have to be resed to the general noise level.
        # Another way would be to compute the cumulative LTA value of the event
        # and substract it from the LTA time window after the event.

        # Find the event end values.
        go_on = True
        self.logger.debug("Computing the event limits.")
        #for k, cur_event_start in enumerate(event_start_ind):
        if len(event_start_ind) > 0:
            while go_on:
                cur_event_start = event_start_ind[0]
                cur_stop_value = stop_values[0]
                if self.sta[cur_event_start] <= cur_stop_value:
                    cur_stop_value = self.sta[cur_event_start]
                try:
                    next_end_ind = np.flatnonzero(self.sta[cur_event_start:] < cur_stop_value)[0]
                    cur_event_end = cur_event_start + next_end_ind
                    # Remove all start indices which are larger than the currend
                    # event end.
                    new_ind = np.argwhere(event_start_ind > cur_event_end).flatten()
                    if len(new_ind) > 0:
                        new_ind = new_ind[0]
                        self.logger.debug("new_ind: %d", new_ind)
                        if new_ind == 0:
                            self.logger.error("The current event start STA is lower than the stop value. Using the next event_start to avoid infinite loop.")
                            new_ind = 1

                        event_start_ind = event_start_ind[new_ind:]
                        stop_values = stop_values[new_ind:]
                        self.logger.debug("event_start_ind[0]: %d", event_start_ind[0])
                    else:
                        self.logger.debug("len(new_ind): %d", len(new_ind))
                        go_on = False
                except:
                    self.logger.debug("in exception")
                    cur_event_end = len(self.thrf)-1
                    go_on = False


                # Compute the cumulative LTA value created by the event and
                # substract it from the LTA window influenced by the event.
                # TODO: Compute the lta moving average for the time window influenced by the
                # event timespan and substract it from the LTA. Teh cumulative
                # LTA is not working well.
                cum_lta = self.lta[cur_event_end] - self.lta[cur_event_start]
                lta_replace_start = cur_event_start
                lta_replace_end = cur_event_end
                if lta_replace_end - lta_replace_start < self.n_lta:
                    lta_replace_end = lta_replace_start + +self.n_sta + self.n_lta
                #self.lta[lta_replace_start:lta_replace_end] -= self.lta[lta_replace_start:lta_replace_end] - self.lta[lta_replace_start]
                lta_mod = self.lta[lta_replace_start:lta_replace_end] - cum_lta
                lta_mod[lta_mod < self.lta[cur_event_start]] = self.lta[cur_event_start]
                #self.lta[lta_replace_start:lta_replace_end] = lta_mod


                event_marker.append((cur_event_start, cur_event_end))

        self.logger.debug("Finished the event limits computation.")
        return event_marker
