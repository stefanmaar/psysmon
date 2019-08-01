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

from past.utils import old_div
from psysmon.core.processingStack import ProcessingNode
from psysmon.core.preferences_manager import SingleChoicePrefItem
from psysmon.core.preferences_manager import FloatSpinPrefItem
from psysmon.core.preferences_manager import IntegerSpinPrefItem
from psysmon.core.preferences_manager import CheckBoxPrefItem
import numpy as np
import scipy as sp


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




    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('bandpass',
                      freqmin = self.pref_manager.get_value('min. frequ.'),
                      freqmax = self.pref_manager.get_value('max. frequ.'),
                      corners = self.pref_manager.get_value('corners'),
                      zerophase = self.pref_manager.get_value('zero_phase')
                     )



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
            if len(station) > 1:
                raise ValueError('There are more than one stations. This is not yet supported.')
            station = station[0]

            channel = station.get_channel(name = tr.stats.channel)

            if len(channel) > 1:
                raise ValueError('There are more than one channels. This is not yet supported.')
            channel = channel[0]

            stream_tb = channel.get_stream(start_time = tr.stats.starttime,
                                           end_time = tr.stats.endtime)

            if len(stream_tb) > 1:
                raise ValueError('There are more than one recorder streams. This is not yet supported.')
            rec_stream = stream_tb[0].item

            rec_stream_param = rec_stream.get_parameter(start_time = tr.stats.starttime,
                                                        end_time = tr.stats.endtime)
            if len(rec_stream_param) > 1:
                raise ValueError('There are more than one recorder stream parameters. This is not yet supported.')
            rec_stream_param = rec_stream_param[0]


            components_tb = rec_stream.get_component(start_time = tr.stats.starttime,
                                                     end_time = tr.stats.endtime)

            if len(components_tb) > 1:
                raise ValueError('There are more than one components. This is not yet supported.')
            component = components_tb[0].item
            comp_param = component.get_parameter(start_time = tr.stats.starttime,
                                                 end_time = tr.stats.endtime)

            if len(comp_param) > 1:
                raise ValueError('There are more than one parameters for this component. This is not yet supported.')

            comp_param = comp_param[0]

            tr.data = old_div(tr.data * rec_stream_param.bitweight, (rec_stream_param.gain * comp_param.sensitivity))
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
