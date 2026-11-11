from __future__ import division
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

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from past.utils import old_div
import logging
from psysmon.core.processingStack import ProcessingNode
from psysmon.core.preferences_manager import SingleChoicePrefItem
from psysmon.core.preferences_manager import FloatSpinPrefItem
from psysmon.core.preferences_manager import IntegerSpinPrefItem
from psysmon.core.preferences_manager import CheckBoxPrefItem
import numpy as np
import scipy as sp

logger = logging.getLogger(__name__)


class Detrend(ProcessingNode):
    ''' Detrend a timeseries.

    This node uses the detrend method of the obspy stream class to remove the 
    trend from a timeseries. 
    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'detrend',
                                mode = 'editable',
                                category = 'test',
                                tags = ['remove', 'mean'],
                                **kwargs
                               )

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        # Add a single_choice field.
        item = SingleChoicePrefItem(name = 'detrend method',
                              #limit = ('simple', 'linear', 'constant'),
                              limit = ('constant',),
                              value = 'constant')
        gen_group.add_item(item)

    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        #stream = stream.split()
        #stream.detrend(type = self.pref_manager.get_value('detrend method'))
        #stream = stream.merge()

        for cur_trace in stream:
            cur_trace.data = cur_trace.data - np.nanmean(cur_trace.data)



class MedianFilter(ProcessingNode):
    ''' Apply a median filter to a timeseries.

    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'median filter',
                                mode = 'editable',
                                category = 'time domain filter',
                                tags = ['filter', 'median', 'time domain', 'de-spike', 'spike'],
                                **kwargs
                               )

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'samples', 
                              value = 3,
                              limit = (3, 100))
        gen_group.add_item(item)

    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for tr in stream.traces:
            tr.data = sp.signal.medfilt(tr.data, self.pref_manager.get_value('samples'))



class FilterBandPass(ProcessingNode):
    '''

    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = 'bandpass filter',
                                mode = 'editable',
                                category = 'frequency',
                                tags = ['filter', 'bandpass'],
                                **kwargs
                               )

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'min. frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1)
        gen_group.add_item(item)

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'max. frequ.', 
                              value = 15,
                              limit = (0, None),
                              digits = 1,
                              increment = 1)
        gen_group.add_item(item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30))
        gen_group.add_item(item)

        # Zero phase checkbox.
        item = CheckBoxPrefItem(name = 'zero_phase',
                                label = 'zero phase',
                                value = False,
                                tool_tip = 'Use a zero phase filtering.')
        gen_group.add_item(item)

        # Parallel Trace Threads
        item = IntegerSpinPrefItem(name = 'threads',
                                   label = 'Parallel Trace Threads',
                                   value = -1,
                                   limit = (-1, 64),
                                   tool_tip = '-1 = Auto (uses min(trace_count, cpu_cores, 4)).\n'
                                              '1 = Single-threaded (sequential loop, no thread pool).\n'
                                              '>1 = Use specific number of worker threads.')
        gen_group.add_item(item)

    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        freqmin = self.pref_manager.get_value('min. frequ.')
        freqmax = self.pref_manager.get_value('max. frequ.')
        corners = self.pref_manager.get_value('corners')
        zerophase = self.pref_manager.get_value('zero_phase')
        threads_pref = int(self.pref_manager.get_value('threads'))

        def _filter_trace(tr):
            tr.filter('bandpass',
                      freqmin = freqmin,
                      freqmax = freqmax,
                      corners = corners,
                      zerophase = zerophase)

        if threads_pref == 1:
            max_workers = 1
        elif threads_pref > 1:
            max_workers = min(len(stream.traces), threads_pref)
        else:  # -1 = Auto
            cpu_avail = os.cpu_count() or 4
            max_workers = min(len(stream.traces), cpu_avail, 4)

        if max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_filter_trace, stream.traces))
        else:
            for tr in stream.traces:
                _filter_trace(tr)



class FilterLowPass(ProcessingNode):
    '''

    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = 'lowpass filter',
                                mode = 'editable',
                                category = 'frequency',
                                tags = ['filter', 'lowpass'],
                                **kwargs
                               )

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1)
        gen_group.add_item(item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30))
        gen_group.add_item(item)

        # Zero phase checkbox.
        item = CheckBoxPrefItem(name = 'zero_phase',
                                label = 'zero phase',
                                value = False,
                                tool_tip = 'Use a zero phase filtering.')
        gen_group.add_item(item)





    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('lowpass',
                      freq = self.pref_manager.get_value('frequ.'),
                      zerophase = self.pref_manager.get_value('zero_phase')
                     )




class FilterHighPass(ProcessingNode):
    '''

    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = 'highpass filter',
                                mode = 'editable',
                                category = 'frequency',
                                tags = ['filter', 'highpass'],
                                **kwargs
                               )


        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'frequ.',
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1)
        gen_group.add_item(item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners',
                              value = 4,
                              limit = (1, 30))
        gen_group.add_item(item)

        # Zero phase checkbox.
        item = CheckBoxPrefItem(name = 'zero_phase',
                                label = 'zero phase',
                                value = False,
                                tool_tip = 'Use a zero phase filtering.')
        gen_group.add_item(item)


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('highpass',
                      freq = self.pref_manager.get_value('frequ.'),
                      zerophase = self.pref_manager.get_value('zero_phase')
                     )


class ConvertToSensorUnits(ProcessingNode):
    ''' Detrend a timeseries.

    This node uses the detrend method of the obspy stream class to remove the 
    trend from a timeseries. 
    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'convert to sensor units',
                                mode = 'uneditable',
                                category = 'test',
                                tags = ['convert', 'unit', 'physical'],
                                **kwargs
                               )


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for tr in stream.traces:
            station = self.parentStack.project.geometry_inventory.get_station(network = tr.stats.network,
                                                                              name = tr.stats.station,
                                                                              location = tr.stats.location)
            # Fallback for virtual beams from array stacking
            if not station and hasattr(tr.stats, 'source_station'):
                station = self.parentStack.project.geometry_inventory.get_station(
                    network = getattr(tr.stats, 'source_network', tr.stats.network),
                    name = tr.stats.source_station,
                    location = getattr(tr.stats, 'source_location', '')
                )
                if not station:
                    station = self.parentStack.project.geometry_inventory.get_station(
                        network = getattr(tr.stats, 'source_network', tr.stats.network),
                        name = tr.stats.source_station
                    )
            if not station:
                logger.warning('ConvertToSensorUnits: No station found for trace %s in inventory.', tr.id)
                continue
            if len(station) > 1:
                raise ValueError('There are more than one stations. This is not yet supported.')
            station = station[0]

            channel = station.get_channel(name = tr.stats.channel)
            if not channel and hasattr(tr.stats, 'source_channel'):
                channel = station.get_channel(name = tr.stats.source_channel)
            if not channel:
                logger.warning('ConvertToSensorUnits: No channel found for trace %s in inventory.', tr.id)
                continue
            if len(channel) > 1:
                raise ValueError('There are more than one channels. This is not yet supported.')
            channel = channel[0]

            stream_tb = channel.get_stream(start_time = tr.stats.starttime,
                                           end_time = tr.stats.endtime)
            if not stream_tb:
                logger.warning('ConvertToSensorUnits: No recorder stream found for trace %s.', tr.id)
                continue
            if len(stream_tb) > 1:
                raise ValueError('There are more than one recorder streams. This is not yet supported.')
            rec_stream = stream_tb[0].item

            rec_stream_param = rec_stream.get_parameter(start_time = tr.stats.starttime,
                                                        end_time = tr.stats.endtime)
            if not rec_stream_param:
                logger.warning('ConvertToSensorUnits: No recorder stream parameters found for trace %s.', tr.id)
                continue
            if len(rec_stream_param) > 1:
                raise ValueError('There are more than one recorder stream parameters. This is not yet supported.')
            rec_stream_param = rec_stream_param[0]

            components_tb = rec_stream.get_component(start_time = tr.stats.starttime,
                                                     end_time = tr.stats.endtime)
            if not components_tb:
                logger.warning('ConvertToSensorUnits: No sensor component found for trace %s.', tr.id)
                continue
            if len(components_tb) > 1:
                raise ValueError('There are more than one components. This is not yet supported.')
            component = components_tb[0].item

            comp_param = component.get_parameter(start_time = tr.stats.starttime,
                                                 end_time = tr.stats.endtime)
            if not comp_param:
                logger.warning('ConvertToSensorUnits: No sensor component parameters found for trace %s.', tr.id)
                continue
            if len(comp_param) > 1:
                raise ValueError('There are more than one parameters for this component. This is not yet supported.')
            comp_param = comp_param[0]

            scale_factor = old_div(rec_stream_param.bitweight, (rec_stream_param.gain * comp_param.sensitivity))
            tr.data = tr.data * scale_factor
            tr.stats.unit = component.output_unit.strip()


class ScaleLog10(ProcessingNode):
    ''' Apply a log10 scaling.

    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'scale log10',
                                mode = 'uneditable',
                                category = 'test',
                                tags = ['convert', 'unit', 'physical'],
                                **kwargs
                               )


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for tr in stream.traces:
            tr.data = np.sign(tr.data) * np.log10(np.abs(tr.data))


class Resample(ProcessingNode):
    ''' Resample a timeseries.

    This node uses the resample method of the obspy trace to resample
    the trace data to the desired sampling rate.
    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'resample',
                                mode = 'editable',
                                category = 'sampling',
                                tags = ['resample', 'sps'],
                                **kwargs
                               )

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')
        # Add a single_choice field.
        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'sps',
                              value = 100,
                              limit = (1e-3, 100000))
        gen_group.add_item(item)

    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for cur_trace in stream:
            resamp_trace = cur_trace.resample(self.pref_manager.get_value('sps'))
            cur_trace.data = resamp_trace.data
            cur_trace.stats.sampling_rate = resamp_trace.stats.sampling_rate


class IntegerDecimation(ProcessingNode):
    ''' Decimate a timeseries to a target sampling rate (sps) by integer factor.

    Provides ultra-fast downsampling for pre-filtered seismic signals.
    When 'apply_low_pass_filter' is False (default), uses zero-overhead contiguous
    strided slicing, achieving up to 160x faster performance than Fourier sinc resampling.
    '''
    nodeClass = 'common'

    def __init__(self, **kwargs):
        ''' The constructor
        '''
        ProcessingNode.__init__(self,
                                name = 'integer decimation',
                                mode = 'editable',
                                category = 'sampling',
                                tags = ['decimate', 'downsample', 'sampling', 'integer', 'sps', 'stride'],
                                **kwargs
                               )

        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('General')

        item = FloatSpinPrefItem(
            name = 'sps',
            label = 'target sampling rate (sps)',
            value = 100.0,
            limit = (1e-3, 100000.0),
            digits = 1,
            increment = 10.0,
            tool_tip = 'Desired sampling rate in samples per second (must divide the input sampling rate by an integer factor).'
        )
        gen_group.add_item(item)

        item = CheckBoxPrefItem(
            name = 'apply_low_pass_filter',
            label = 'apply low-pass filter',
            value = False,
            tool_tip = 'Apply Chebyshev Type II low-pass anti-aliasing filter before downsampling.\n'
                       'When unchecked (False, default), downsamples via ultra-fast contiguous strided slicing.\n'
                       'Recommended to keep unchecked when an upstream bandpass filter already band-limits the signal below Nyquist.'
        )
        gen_group.add_item(item)

    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the integer decimation node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        target_sps = float(self.pref_manager.get_value('sps'))
        apply_filt = bool(self.pref_manager.get_value('apply_low_pass_filter'))
        if target_sps <= 0:
            return

        for cur_trace in stream:
            cur_sps = float(cur_trace.stats.sampling_rate)
            factor = cur_sps / target_sps
            int_factor = int(round(factor))

            if int_factor <= 1:
                continue

            # Check if factor is an integer within small numerical tolerance
            if abs(factor - int_factor) < 1e-4:
                if not apply_filt:
                    # Ultra-fast contiguous strided slicing (0.054 s vs 8.82 s)
                    cur_trace.data = np.ascontiguousarray(cur_trace.data[::int_factor])
                    cur_trace.stats.sampling_rate = cur_sps / int_factor
                else:
                    cur_trace.decimate(factor=int_factor, no_filter=False)
            else:
                logger.warning(
                    "IntegerDecimation: Current sampling rate %s is not an integer multiple of target %s (factor=%.4f). "
                    "Falling back to Fourier resample.",
                    cur_sps, target_sps, factor
                )
                resamp_trace = cur_trace.resample(target_sps)
                cur_trace.data = resamp_trace.data
                cur_trace.stats.sampling_rate = resamp_trace.stats.sampling_rate


_PAZ_CACHE = {}
_PAZ_CACHE_LOCK = threading.Lock()


class RemoveResponsePAZ(ProcessingNode):
    ''' Remove instrument response using Poles and Zeros (PAZ) deconvolution.

    Queries the pSysmon geometry_inventory for sensor PAZ and datalogger
    gain/bitweight, and deconvolves the instrument response using ObsPy.
    '''
    nodeClass = 'common'

    @property
    def _paz_cache(self):
        return _PAZ_CACHE

    @property
    def _cache_lock(self):
        return _PAZ_CACHE_LOCK

    def __init__(self, **kwargs):
        ''' The constructor
        '''
        ProcessingNode.__init__(self,
                                name = 'remove response (paz)',
                                mode = 'editable',
                                category = 'instrument',
                                tags = ['response', 'paz', 'deconvolution', 'instrument'],
                                **kwargs
                               )

        # General Page
        page_gen = self.pref_manager.add_page('General')
        gen_group = page_gen.add_group('Deconvolution Settings')
        item = SingleChoicePrefItem(name = 'output quantity',
                                    limit = ('velocity', 'displacement', 'acceleration'),
                                    value = 'velocity',
                                    tool_tip = 'Physical quantity of the output data.')
        gen_group.add_item(item)

        item = FloatSpinPrefItem(name = 'water level (dB)',
                                 value = 60.0,
                                 limit = (0.0, 300.0),
                                 digits = 1,
                                 increment = 5.0,
                                 tool_tip = 'Water level in dB to prevent dividing by small numbers.')
        gen_group.add_item(item)

        item = CheckBoxPrefItem(name = 'taper ends',
                                label = 'taper ends',
                                value = True,
                                tool_tip = 'Apply cosine taper to trace ends before FFT.')
        gen_group.add_item(item)

        item = FloatSpinPrefItem(name = 'taper fraction',
                                 value = 0.05,
                                 limit = (0.0, 0.5),
                                 digits = 3,
                                 increment = 0.01,
                                 tool_tip = 'Fraction of trace length to taper at each end.')
        gen_group.add_item(item)

        # Pre-filter Page
        page_filt = self.pref_manager.add_page('Pre-filter')
        filt_group = page_filt.add_group('Frequency Pre-filter')
        item = CheckBoxPrefItem(name = 'use pre-filter',
                                label = 'enable pre-filter',
                                value = True,
                                tool_tip = 'Apply 4-corner cosine bandpass filter to prevent noise blowup.')
        filt_group.add_item(item)

        item = FloatSpinPrefItem(name = 'f1 (low stop, Hz)',
                                 value = 2.0,
                                 limit = (0.0, None),
                                 digits = 2,
                                 increment = 0.5,
                                 tool_tip = 'Lower stop-band frequency in Hz (gain = 0).')
        filt_group.add_item(item)

        item = FloatSpinPrefItem(name = 'f2 (low pass, Hz)',
                                 value = 4.0,
                                 limit = (0.0, None),
                                 digits = 2,
                                 increment = 0.5,
                                 tool_tip = 'Lower pass-band frequency in Hz (gain = 1).')
        filt_group.add_item(item)

        item = FloatSpinPrefItem(name = 'f3 (high pass, Hz)',
                                 value = 40.0,
                                 limit = (0.0, None),
                                 digits = 1,
                                 increment = 1.0,
                                 tool_tip = 'Upper pass-band frequency in Hz (gain = 1).')
        filt_group.add_item(item)

        item = FloatSpinPrefItem(name = 'f4 (high stop, Hz)',
                                 value = 48.0,
                                 limit = (0.0, None),
                                 digits = 1,
                                 increment = 1.0,
                                 tool_tip = 'Upper stop-band frequency in Hz (gain = 0).')
        filt_group.add_item(item)

        # Performance Page
        page_perf = self.pref_manager.add_page('Performance')
        perf_group = page_perf.add_group('Optimization & Parallelization')

        item = CheckBoxPrefItem(
            name = 'paz_vector_caching',
            label = 'PAZ Vector Caching for identical sensors',
            value = True,
            tool_tip = 'Pre-evaluate and cache the complex inverted transfer function vector H_inv(f) '
                       'across identical sensors, avoiding repeated high-order polynomial evaluations.'
        )
        perf_group.add_item(item)

        item = IntegerSpinPrefItem(
            name = 'threads',
            label = 'Parallel Trace Threads',
            value = -1,
            limit = (-1, 64),
            tool_tip = '-1 = Auto (uses min(trace_count, cpu_cores, 4)).\n'
                       '1 = Single-threaded (sequential loop, no thread pool).\n'
                       '>1 = Use specific number of worker threads.'
        )
        perf_group.add_item(item)

    def _compute_inv_transfer(self, paz, samp_rate, nfft, pre_filt, water_level):
        ''' Compute inverted transfer function vector in frequency domain. '''
        from obspy.signal.invsim import paz_to_freq_resp, invert_spectrum, cosine_taper
        delta = 1.0 / samp_rate
        freq_response, freqs = paz_to_freq_resp(
            paz['poles'], paz['zeros'], paz['gain'],
            delta, nfft, freq=True
        )
        invert_spectrum(freq_response, water_level)
        if pre_filt:
            fl1, fl2, fl3, fl4 = pre_filt
            cos_win = cosine_taper(freqs.size, freqs=freqs, flimit=(fl1, fl2, fl3, fl4))
            freq_response *= cos_win
        return freq_response / paz['sensitivity']

    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the response removal node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        output_type = self.pref_manager.get_value('output quantity')
        use_pre_filt = self.pref_manager.get_value('use pre-filter')
        if use_pre_filt:
            pre_filt = (
                self.pref_manager.get_value('f1 (low stop, Hz)'),
                self.pref_manager.get_value('f2 (low pass, Hz)'),
                self.pref_manager.get_value('f3 (high pass, Hz)'),
                self.pref_manager.get_value('f4 (high stop, Hz)')
            )
        else:
            pre_filt = None

        water_level = self.pref_manager.get_value('water level (dB)')
        taper = self.pref_manager.get_value('taper ends')
        taper_fraction = self.pref_manager.get_value('taper fraction')
        use_paz_cache = bool(self.pref_manager.get_value('paz_vector_caching'))
        threads_pref = int(self.pref_manager.get_value('threads'))

        def _process_trace(tr):
            # 1. Lookup station in geometry_inventory
            station = self.parentStack.project.geometry_inventory.get_station(
                network = tr.stats.network,
                name = tr.stats.station,
                location = tr.stats.location
            )
            # Fallback for virtual beams from array stacking
            if not station and hasattr(tr.stats, 'source_station'):
                station = self.parentStack.project.geometry_inventory.get_station(
                    network = getattr(tr.stats, 'source_network', tr.stats.network),
                    name = tr.stats.source_station,
                    location = getattr(tr.stats, 'source_location', '')
                )
                if not station:
                    station = self.parentStack.project.geometry_inventory.get_station(
                        network = getattr(tr.stats, 'source_network', tr.stats.network),
                        name = tr.stats.source_station
                    )
            if not station:
                logger.warning('No station found for trace %s in inventory.', tr.id)
                return

            channel = station[0].get_channel(name = tr.stats.channel)
            if not channel and hasattr(tr.stats, 'source_channel'):
                channel = station[0].get_channel(name = tr.stats.source_channel)
            if not channel:
                logger.warning('No channel found for trace %s in inventory.', tr.id)
                return

            # 2. Extract recorder stream (gain, bitweight)
            stream_tb = channel[0].get_stream(start_time = tr.stats.starttime, end_time = tr.stats.endtime)
            if not stream_tb:
                logger.warning('No recorder stream found for trace %s.', tr.id)
                return
            rec_stream = stream_tb[0].item
            rec_params = rec_stream.get_parameter(start_time = tr.stats.starttime, end_time = tr.stats.endtime)
            if not rec_params:
                logger.warning('No recorder stream parameters found for trace %s.', tr.id)
                return
            rec_param = rec_params[0]

            # 3. Extract sensor component (poles, zeros, sensitivity)
            comp_tb = rec_stream.get_component(start_time = tr.stats.starttime, end_time = tr.stats.endtime)
            if not comp_tb:
                logger.warning('No sensor component found for trace %s.', tr.id)
                return
            component = comp_tb[0].item
            comp_params = component.get_parameter(start_time = tr.stats.starttime, end_time = tr.stats.endtime)
            if not comp_params:
                logger.warning('No sensor component parameters found for trace %s.', tr.id)
                return
            comp_param = comp_params[0]

            # 4. Construct total sensitivity & PAZ dictionary
            # logger_gain in counts/V = Gain / Bitweight
            logger_gain = old_div(rec_param.gain, rec_param.bitweight)
            total_sensitivity = comp_param.sensitivity * logger_gain

            # Adjust zeros according to desired physical unit:
            # The geophone transfer function has 2 zeros (displacement -> Volt).
            # To deconvolve to displacement: keep [0j, 0j] -> unit 'm'
            # To deconvolve to velocity: drop one zero -> [0j] -> unit 'm/s'
            # To deconvolve to acceleration: drop two zeros -> [] -> unit 'm/s^2'
            if output_type == 'displacement':
                zeros = [0j, 0j]
                unit_str = 'm'
            elif output_type == 'velocity':
                zeros = [0j]
                unit_str = 'm/s'
            elif output_type == 'acceleration':
                zeros = []
                unit_str = 'm/s^2'
            else:
                zeros = [0j]
                unit_str = 'm/s'

            paz = {
                'poles': comp_param.tf_poles,
                'zeros': zeros,
                'gain': comp_param.tf_normalization_factor,
                'sensitivity': total_sensitivity
            }

            # 5. Execute deconvolution using PAZ cache or ObsPy simulate
            if use_paz_cache:
                from obspy.signal.util import _npts2nfft
                from obspy.signal.invsim import cosine_taper
                ndat = len(tr.data)
                nfft = _npts2nfft(ndat)
                cache_key = (
                    tuple(comp_param.tf_poles),
                    tuple(zeros),
                    float(comp_param.tf_normalization_factor),
                    float(total_sensitivity),
                    pre_filt,
                    float(water_level),
                    float(tr.stats.sampling_rate),
                    nfft
                )
                with self._cache_lock:
                    if cache_key not in self._paz_cache:
                        self._paz_cache[cache_key] = self._compute_inv_transfer(
                            paz, tr.stats.sampling_rate, nfft, pre_filt, water_level
                        )
                    inv_tf = self._paz_cache[cache_key]

                data = tr.data.astype(np.float64)
                data -= data.mean()
                if taper:
                    data *= cosine_taper(ndat, taper_fraction)
                data = np.fft.rfft(data, n=nfft)
                data *= inv_tf
                data[-1] = abs(data[-1]) + 0.0j
                data = np.fft.irfft(data)[:ndat]
                from obspy.signal.detrend import simple as simple_detrend
                tr.data = simple_detrend(data)
            else:
                tr.simulate(
                    paz_remove = paz,
                    pre_filt = pre_filt,
                    water_level = water_level,
                    zero_mean = True,
                    taper = taper,
                    taper_fraction = taper_fraction
                )
            tr.stats.unit = unit_str

        if threads_pref == 1:
            max_workers = 1
        elif threads_pref > 1:
            max_workers = min(len(stream.traces), threads_pref)
        else:  # -1 = Auto
            cpu_avail = os.cpu_count() or 4
            max_workers = min(len(stream.traces), cpu_avail, 4)

        if max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_process_trace, stream.traces))
        else:
            for tr in stream.traces:
                _process_trace(tr)


