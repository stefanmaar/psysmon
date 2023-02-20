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


import numpy as np
import scipy as sp

import psysmon.core.packageNodes as package_nodes
from psysmon.core.preferences_manager import FloatSpinPrefItem
import psysmon.core.result as result
import psysmon.core.util as p_util


class ComputeTimedomainFeatures(package_nodes.LooperCollectionChildNode):
    ''' Apply a median filter to a timeseries.

    '''
    name = 'compute timedomain features'
    mode = 'looper child'
    category = 'Amplitude'
    tags = ['stable', 'looper child']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        # The gap between the noise end and the event begin for SNR
        # computation [s].
        self.noise_gap = 0.1

        pref_page = self.pref_manager.add_page('Preferences')
        w_group = pref_page.add_group('window')

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'noise_window_length',
                                 label = 'noise window length',
                                 value = 5,
                                 limit = (0, 1000),
                                 tool_tip = 'The length of the time-span used to compute the noise parameters [s].')
        w_group.add_item(item)


    @property
    def pre_stream_length(self):
        ''' The time-span needed for correct processing prior to the start time
        of the stream passed to the execute method [s].
        '''
        return self.pref_manager.get_value('noise_window_length') + self.noise_gap


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Import the module in the function to avoid import errors
        # in headless mode, when not wxPython library is installed.
        import psysmon.gui.dialog.pref_listbook as psy_lb
        
        # Create the edit dialog.
        dlg = psy_lb.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()



    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Create a table result.
        columns = ['max_abs', 'peak_to_peak', 'mean_abs', 'std_abs',
                   'median_abs', 'snr', 'snr_max_mean', 'snr_max_max',
                   'max_env', 'acf_tr_fz', 'acf_tr_npeaks',
                   'acf_env_npeaks', 'skew', 'kurt', 'hist_ratio',
                   'eb_10', 'eb_25', 'eb_50', 'eb_75', 'eb_90',
                   'max_env_peak_time', 'fwd_peak_cnt', 'rvs_peak_cnt']
        table_result = result.TableResult(name='amplitude features',
                                          key_name='scnl',
                                          start_time=process_limits[0],
                                          end_time=process_limits[1],
                                          origin_name=self.name,
                                          origin_resource=origin_resource,
                                          column_names=columns,
                                          sub_directory = ("{0:04d}".format(process_limits[0].year),
                                                           "{0:03d}".format(process_limits[0].julday)))

        for tr in stream.traces:
            if process_limits is not None:
                proc_trace = tr.slice(starttime = process_limits[0],
                                      endtime = process_limits[1])
            else:
                proc_trace = tr

            if len(proc_trace) == 0:
                continue
            
            self.logger.debug('proc_trace: %s', proc_trace)

            # The absolute values of the trace amplitudes.
            abs_trace = np.abs(proc_trace.data)
            
            # Absolute maximum value of the trace.
            max_abs = np.max(abs_trace)

            # Maximum of the envelope of the trace.
            comp_trace = sp.signal.hilbert(proc_trace.data)
            trace_envelope = np.sqrt(np.real(comp_trace)**2 + np.imag(comp_trace)**2)
            max_env = np.max(trace_envelope)

            # Autocorrelation parameters of the trace
            acf_max_length = 5
            sps = proc_trace.stats.sampling_rate
            max_lag = int(acf_max_length * sps)
            first_zero, n_peaks = self.compute_acf_features(data = proc_trace.data,
                                                            sps = sps,
                                                            max_lag = max_lag)
            acf_tr_first_zero = first_zero
            acf_tr_npeaks = n_peaks
            

            # Autocorrelation parameters of the envelope
            max_lag = int(acf_max_length * sps)
            first_zero, n_peaks = self.compute_acf_features(data = trace_envelope,
                                                            sps = sps,
                                                            max_lag = max_lag)
            acf_env_npeaks = n_peaks

            # Compute the maximum range of the trace.
            peak_to_peak = np.max(proc_trace.data) - np.min(proc_trace.data)

            # Compute the mean value of the trace absolute values.
            mean_abs = np.mean(abs_trace)

            # Compute the standard deviation of the trace.
            std_abs = np.std(abs_trace)

            # Compute the median of the trace.
            median_abs = np.median(abs_trace)

            # Skewness of the data.
            skew = sp.stats.skew(proc_trace.data)

            # Kurtosis of the data.
            kurt = sp.stats.kurtosis(proc_trace.data)

            # Histogram area ratio.
            hist_ratio = self.compute_histogram_features(proc_trace.data,
                                                         nbins = 50)

            # Energy buildup.
            eb = self.compute_energy_buildup(proc_trace.data,
                                             sps = sps)

            # Envelope peaks.
            res = self.compute_envelope_peaks(proc_trace.data,
                                              sps = sps,
                                              prominence = 0.05)
            max_env_peak_time = res['max_peak_time']
            fwd_peak_cnt = res['fwd_peak_cnt']
            rvs_peak_cnt = res['rvs_peak_cnt']

            #Compute the signal to noise ratio.
            if process_limits is None:
                snr = np.NaN
                snr_max_mean = np.NaN
                snr_max_max = np.NaN
            else:
                noise_window_length = self.pref_manager.get_value('noise_window_length')
                noise_start_time = process_limits[0] - noise_window_length - self.noise_gap
                if noise_start_time < tr.stats.starttime:
                    noise_start_time = tr.stats.starttime
                noise_trace = tr.slice(starttime = noise_start_time,
                                       endtime = noise_start_time + noise_window_length)
                signal_rms = np.sqrt(np.mean(proc_trace.data**2))
                noise_rms = np.sqrt(np.mean(noise_trace.data**2))
                noise_mean = np.mean(np.abs(noise_trace.data))
                noise_max_abs = np.max(np.abs(noise_trace.data))
                snr = signal_rms / noise_rms
                snr_max_mean = max_abs / noise_mean
                snr_max_max = max_abs / noise_max_abs

            cur_scnl = p_util.traceid_to_scnl(tr.id)
            table_result.add_row(key = ':'.join(cur_scnl),
                                 max_abs = max_abs,
                                 peak_to_peak = peak_to_peak,
                                 mean_abs = mean_abs,
                                 std_abs = std_abs,
                                 median_abs = median_abs,
                                 snr = round(snr, 2),
                                 snr_max_mean = round(snr_max_mean, 2),
                                 snr_max_max = round(snr_max_max, 2),
                                 max_env = max_env,
                                 acf_tr_fz = acf_tr_first_zero,
                                 acf_tr_npeaks = acf_tr_npeaks,
                                 acf_env_npeaks = acf_env_npeaks,
                                 skew = skew,
                                 kurt = kurt,
                                 hist_ratio = hist_ratio,
                                 eb_10 = eb['eb_10'],
                                 eb_25 = eb['eb_25'],
                                 eb_50 = eb['eb_50'],
                                 eb_75 = eb['eb_75'],
                                 eb_90 = eb['eb_90'],
                                 max_env_peak_time = max_env_peak_time,
                                 fwd_peak_cnt = fwd_peak_cnt,
                                 rvs_peak_cnt = rvs_peak_cnt)

        self.result_bag.add(table_result)


    def compute_acf_features(self, data, sps, max_lag):
        ''' Compute the autocorrelation features.

        '''
        acf = sp.signal.correlate(data,
                                  data)
        lags = sp.signal.correlation_lags(len(data),
                                          len(data))
        pos_mask = lags >= 0
        acf = acf[pos_mask][:max_lag]
        lags = lags[pos_mask]

        # Normalize the acf
        acf = acf / np.max(np.abs(acf))

        # Get the first zero crossing.
        if np.any(acf <= 0):
            first_zero = np.where(acf <= 0)[0][0]
            first_zero_time = first_zero / sps
        else:
            first_zero_time = None

        # Find the peaks.
        peaks = sp.signal.find_peaks(acf,
                                     prominence = 0.1)
        peaks = peaks[0]

        return (first_zero_time, len(peaks))


    def compute_histogram_features(self, data, nbins = 50):
        ''' Compute the hisotram features.
        '''
        data = np.abs(data)
        perc10 = np.percentile(data, 10)
        perc95 = np.percentile(data, 95)
        noise_mask = data <= perc10
        outlier_mask = data > perc95
        data = data[~(noise_mask | outlier_mask)]
        data = data / np.max(np.abs(data))
        data = np.sort(data)

        hist, bin_edges = np.histogram(data,
                                       bins = nbins,
                                       range = [0, np.max(data)],
                                       density = True)
        cumsum = np.cumsum(hist * np.diff(bin_edges))
        bin_right = bin_edges[:-1] + np.diff(bin_edges)
        a_below = np.trapz(cumsum, bin_right)
        a_above = np.trapz(1 - cumsum, bin_right)

        return a_above / a_below


    def compute_energy_buildup(self, data, sps):
        ''' Compute the energy buildup features.
        '''
        energy = data**2
        energy = energy / np.sum(energy)
        en_cumsum = np.cumsum(energy)
        percentiles = [10, 25, 50, 75, 90]
        eb = {}
        for cur_perc in percentiles:
            cur_key = 'eb_{:.0f}'.format(np.floor(cur_perc))
            cur_ind = np.argwhere(en_cumsum > (cur_perc / 100))[0][0]
            eb[cur_key] = cur_ind / sps

        return eb


    def compute_envelope_peaks(self, data, sps, prominence = 0.1):
        comp_trace = sp.signal.hilbert(data)
        tr_env = np.sqrt(np.real(comp_trace)**2 + np.imag(comp_trace)**2)

        # Normalize the envelope.
        max_env = np.max(tr_env)
        tr_env = tr_env / max_env

        # Find the peaks.
        peaks = sp.signal.find_peaks(tr_env,
                                     prominence = prominence)
        peaks = peaks[0]

        # Compute the time of the max peak.
        max_ind = np.argmax(tr_env[peaks])
        max_peak_time = peaks[max_ind] / sps

        # Count the peaks that form a new maximum in forward direction.
        fwd_peak_cnt = 0
        max_peak = 0
        for cur_peak in peaks:
            cur_amp = tr_env[cur_peak]
            if cur_amp > max_peak:
                fwd_peak_cnt += 1
                max_peak = cur_amp

        # Count the peaks, that form a new maximum in reverse direction.
        rvs_peak_cnt = 0
        max_peak = 0
        for cur_peak in peaks[::-1]:
            cur_amp = tr_env[cur_peak]
            if cur_amp > max_peak:
                rvs_peak_cnt += 1
                max_peak = cur_amp

        res = {'max_peak_time': max_peak_time,
               'fwd_peak_cnt': fwd_peak_cnt,
               'rvs_peak_cnt': rvs_peak_cnt}
        return res
