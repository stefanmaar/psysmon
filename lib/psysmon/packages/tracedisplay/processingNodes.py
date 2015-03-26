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
from psysmon.core.preferences_manager import SingleChoicePrefItem
from psysmon.core.preferences_manager import FloatSpinPrefItem
from psysmon.core.preferences_manager import IntegerSpinPrefItem
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

        # Add a single_choice field.
        item = SingleChoicePrefItem(name = 'detrend method',
                              limit = ('simple', 'linear', 'constant'),
                              value = 'constant',
                             )
        self.pref_manager.add_item(item = item)


    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.detrend(type = self.pref_manager.get_value('detrend method'))
        


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

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'samples', 
                              value = 3,
                              limit = (3, 100)
                             )
        self.pref_manager.add_item(item = item)


    def execute(self, stream):
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

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'min. frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref_manager.add_item(item = item)

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'max. frequ.', 
                              value = 15,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref_manager.add_item(item = item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30)
                             )
        self.pref_manager.add_item(item = item)

        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def execute(self, stream):
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
                      corners = self.pref_manager.get_value('corners')
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

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref_manager.add_item(item = item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30)
                             )
        self.pref_manager.add_item(item = item)


        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)





    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('lowpass',
                      freq = self.pref_manager.get_value('frequ.')
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

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref_manager.add_item(item = item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30)
                             )
        self.pref_manager.add_item(item = item)

        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)


    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('highpass',
                      freq = self.pref_manager.get_value('frequ.')
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


    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for tr in stream.traces:
            station = self.parentStack.inventory.get_station(network = tr.stats.network,
                                                             name = tr.stats.station,
                                                             location = tr.stats.location)
            if len(station) > 1:
                raise ValueError('There are more than one stations. This is not yet supported.')
            station = station[0]
            sensor = station.get_sensor(channel_name = tr.stats.channel,
                                        start_time = tr.stats.starttime,
                                        end_time = tr.stats.endtime)
            if len(sensor) > 1:
                raise ValueError('There are more than one sensors. This is not yet supported.')
            sensor = sensor[0]
            param = sensor[0].get_parameter(start_time = tr.stats.starttime,
                                            end_time = tr.stats.endtime)

            if len(param) > 1:
                raise ValueError('There are more than one parameters. This is not yet supported.')

            param = param[0]

            tr.data = tr.data * param.bitweight / (param.gain * param.sensitivity)


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


    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for tr in stream.traces:
            tr.data = np.sign(tr.data) * np.log10(np.abs(tr.data))
