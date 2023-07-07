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


import matplotlib.mlab as mlab
import numpy as np
import scipy as sp

import psysmon
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.result as result
import psysmon.core.util as p_util

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.gui.dialog.pref_listbook as psy_lb


class ComputeFreqdomainFeatures(package_nodes.LooperCollectionChildNode):
    ''' Compute the frequency domain features.

    '''
    name = 'compute frequencydomain features'
    mode = 'looper child'
    category = 'Frequency'
    tags = ['stable', 'looper child']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)
        pref_page = self.pref_manager.add_page('Preferences')
        psd_group = pref_page.add_group('PSD')

        tool_tip = 'The length of the fft window [samples].'
        pref_item = psy_pm.IntegerSpinPrefItem(name = 'psd_nfft',
                                               label = 'nfft',
                                               value = 8192,
                                               limit = [0, 1000000],
                                               tool_tip = tool_tip)
        psd_group.add_item(pref_item)

        tool_tip = 'The overlap of the fft windows [%].'
        pref_item = psy_pm.IntegerSpinPrefItem(name = 'psd_overlap',
                                               label = 'fft overlap [%]',
                                               value = 50,
                                               limit = [0, 99],
                                               tool_tip = tool_tip)
        psd_group.add_item(pref_item)

        tool_tip = ('The maximum frequency used for the computation. '
                    'Data above this value is ignores.')
        pref_item = psy_pm.IntegerSpinPrefItem(name = 'max_frequ',
                                               label = 'max. frequency [Hz]',
                                               value = 100,
                                               limit = [1, 100000],
                                               tool_tip = tool_tip)
        psd_group.add_item(pref_item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = psy_lb.ListbookPrefDialog(preferences = self.pref_manager)

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None,
                origin_resource = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Get the user preferences.
        psd_nfft = self.pref_manager.get_value('psd_nfft')
        psd_overlap = self.pref_manager.get_value('psd_overlap')
        f_max = self.pref_manager.get_value('max_frequ')

        # Create a table result.
        columns = ['fft_max_peak_frequ', 'fft_mean', 'fft_med', 'fft_skew',
                   'fft_kurt', 'fft_centroid', 'fft_spec_bw',
                   'fft_n_peaks', 'fft_peaks_mean', 'fft_peaks_med',
                   'fft_peaks_mean_df', 'fft_peaks_med_df', 'fft_peaks_std_df',
                   'fft_peaks_min', 'fft_peaks_max']
        sub_dir = ("{0:04d}".format(process_limits[0].year),
                   "{0:03d}".format(process_limits[0].julday))
        table_result = result.TableResult(name='frequency features',
                                          key_name='scnl',
                                          start_time=process_limits[0],
                                          end_time=process_limits[1],
                                          origin_name=self.name,
                                          origin_resource=origin_resource,
                                          column_names=columns,
                                          sub_directory = sub_dir)

        for tr in stream.traces:
            if process_limits is not None:
                proc_trace = tr.slice(starttime = process_limits[0],
                                      endtime = process_limits[1])
            else:
                proc_trace = tr

            if len(proc_trace) == 0:
                continue

            self.logger.debug('proc_trace: %s', proc_trace)

            # Compute the PSD of the trace.
            sps = proc_trace.stats.sampling_rate        
            P, frequ = self.compute_psd(proc_trace.data,
                                        sps = sps,
                                        nfft = psd_nfft,
                                        overlap = psd_overlap)

            # Limit the PSD to the max frequency.
            mask = frequ <= f_max
            P = P[mask]
            frequ = frequ[mask]

            # Create a normalized version.
            P_norm = P / np.max(P)

            # Find the peaks in the spectrum.
            peaks = sp.signal.find_peaks(P_norm,
                                         prominence = 0.05)
            peaks = peaks[0]

            # Compute statistical parameters of the peaks.
            try:
                fft_max_peak_frequ = np.max(frequ[peaks])
            except Exception:
                fft_max_peak_frequ = np.nan
            fft_mean = np.mean(P_norm)
            fft_med = np.median(P_norm)
            fft_skew = sp.stats.skew(P_norm)
            fft_kurt = sp.stats.kurtosis(P_norm)

            # Compute centroid and bandwidth.
            f_c, f_bw = self.compute_cent_bw(P_norm, frequ, p = 2)

            # Compute the bandwidth of the peaks.
            try:
                peaks_bw = [np.min(frequ[peaks]),
                            np.max(frequ[peaks])]
            except Exception:
                peaks_bw = [np.nan,
                            np.nan]

            # Compute the statistical parameters of the peaks distribution.
            n_peaks = len(peaks)
            peak_frequ = frequ[peaks]
            peaks_mean = np.mean(peak_frequ)
            peaks_med = np.median(peak_frequ)
            peaks_diff = np.diff(peak_frequ)
            peaks_mean_delta = np.mean(peaks_diff)
            peaks_med_delta = np.median(peaks_diff)
            peaks_std_delta = np.std(peaks_diff)
            
            cur_scnl = p_util.traceid_to_scnl(tr.id)
            table_result.add_row(key = ':'.join(cur_scnl),
                                 fft_max_peak_frequ = fft_max_peak_frequ,
                                 fft_mean = fft_mean,
                                 fft_med = fft_med,
                                 fft_skew = fft_skew,
                                 fft_kurt = fft_kurt,
                                 fft_centroid = f_c,
                                 fft_spec_bw = f_bw,
                                 fft_n_peaks = n_peaks,
                                 fft_peaks_mean = peaks_mean,
                                 fft_peaks_med = peaks_med,
                                 fft_peaks_mean_df = peaks_mean_delta,
                                 fft_peaks_med_df = peaks_med_delta,
                                 fft_peaks_std_df = peaks_std_delta,
                                 fft_peaks_min = peaks_bw[0],
                                 fft_peaks_max = peaks_bw[1],)

        self.result_bag.add(table_result)


    def compute_psd(self, data, sps, nfft, overlap):
        ''' Compute the PSD of the trace.
        '''
        # Compute the PSD using matplotlib.mlab.psd
        pad_to = None
        if len(data) < nfft:
            nfft = np.floor(len(data) / 4)
            # Get the next lower power of two.
            nfft = int(np.power(2, np.floor(np.log2(nfft))))
            pad_to = nfft

        n_overlap = np.floor(nfft * overlap / 100)

        (P, frequ) = mlab.psd(data,
                              Fs = sps,
                              NFFT = nfft,
                              noverlap = n_overlap,
                              detrend = 'constant',
                              scale_by_freq = True,
                              pad_to = pad_to)

        if P.ndim == 2:
            P = P.squeeze()

        return (P, frequ)


    def compute_cent_bw(self, P, frequ, p = 2):
        ''' Compute the centroid and spectral bandwidth.
        '''
        f_c = np.sum(P * frequ) / np.sum(P)
        f_bw = np.sum(P * (frequ - f_c)**p)**(1/p)

        return (f_c, f_bw)
