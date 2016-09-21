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

from psysmon.core.processingStack import ProcessingNode
from psysmon.core.preferences_manager import FloatSpinPrefItem
import psysmon.core.util as p_util
import numpy as np
import scipy as sp


class ComputeAmplitudeFeatures(ProcessingNode):
    ''' Apply a median filter to a timeseries.

    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'compute amplitude features',
                                mode = 'editable',
                                category = 'amplitude',
                                tags = ['amplitude', 'maximal', 'minimal'],
                                **kwargs
                               )

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'noise_window_length',
                              label = 'noise window length',
                              value = 5,
                              limit = (0, 1000),
                              tool_tip = 'The length of the time-span used to compute the noise parameters [s].'
                             )
        self.pref_manager.add_item(item = item)


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for tr in stream.traces:
            if process_limits is not None:
                proc_trace = tr.slice(starttime = process_limits[0],
                                      endtime = process_limits[1])
            else:
                proc_trace = tr

            if len(proc_trace) == 0:
                continue

            # Compute the absolute maximum value of the trace.
            max_abs = np.max(np.abs(proc_trace.data))
            cur_scnl = p_util.traceid_to_scnl(tr.id)
            self.add_result(name = 'max_abs',
                            scnl = cur_scnl,
                            value = max_abs)


            # Compute the maximum range of the trace.
            peak_to_peak = np.max(proc_trace.data) + np.abs(np.min(proc_trace.data))
            self.add_result(name = 'peak_to_peak',
                            scnl = cur_scnl,
                            value = peak_to_peak)


            # Compute the mean value of the trace.
            mean = np.mean(proc_trace.data)
            self.add_result(name = 'mean',
                            scnl = cur_scnl,
                            value = mean)

            # Compute the standard deviation of the trace.
            mean = np.std(proc_trace.data)
            self.add_result(name = 'std',
                            scnl = cur_scnl,
                            value = mean)

            # Compute the median of the trace.
            mean = np.median(proc_trace.data)
            self.add_result(name = 'std',
                            scnl = cur_scnl,
                            value = mean)

            # Compute the signal to noise ratio.
            if process_limits is None:
                snr = np.NaN
            else:
                noise_window_length = self.pref_manager.get_value('noise_window_length')
                noise_start_time = process_limits[0] - noise_window_length - 1
                if noise_start_time < tr.stats.starttime:
                    noise_start_time = tr.stats.starttime
                noise_trace = tr.slice(starttime = noise_start_time,
                                      endtime = noise_start_time + noise_window_length)
                signal_rms = np.sqrt(np.mean(proc_trace.data**2))
                noise_rms = np.sqrt(np.mean(noise_trace.data**2))
                noise_mean = np.mean(np.abs(noise_trace.data))
                noise_max_abs = np.max(np.abs(noise_trace.data))
                snr = signal_rms/noise_rms
                snr_max_mean = max_abs / noise_mean
                snr_max_max = max_abs / noise_max_abs

            self.add_result(name = 'snr',
                            scnl = cur_scnl,
                            value = snr)

            self.add_result(name = 'snr_max_mean',
                            scnl = cur_scnl,
                            value = snr_max_mean)

            self.add_result(name = 'snr_max_max',
                            scnl = cur_scnl,
                            value = snr_max_max)




