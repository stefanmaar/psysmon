# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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


class Detrend(ProcessingNode):
    ''' Detrend a timeseries.

    This node uses the detrend method of the obspy stream class to remove the 
    trend from a timeseries. 
    '''
    nodeClass = 'common'

    def __init__(self):
        ''' The constructor

        '''
        ProcessingNode.__init__(self,
                                name = 'detrend',
                                mode = 'editable',
                                category = 'test',
                                tags = ['remove', 'mean']
                               )

        # Add a single_choice field.
        item = SingleChoicePrefItem(name = 'detrend method',
                              limit = ('simple', 'linear', 'constant'),
                              value = 'constant',
                             )
        self.pref.add_item(item = item)


    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.detrend(type = self.pref.get_value('detrend method'))




class FilterBandPass(ProcessingNode):
    '''

    '''
    nodeClass = 'common'

    def __init__(self):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = 'bandpass filter',
                                mode = 'editable',
                                category = 'frequency',
                                tags = ['filter', 'bandpass']
                               )

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'min. frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref.add_item(item = item)

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'max. frequ.', 
                              value = 15,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref.add_item(item = item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30)
                             )
        self.pref.add_item(item = item)

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
                      freqmin = self.pref.get_value('min. frequ.'),
                      freqmax = self.pref.get_value('max. frequ.'),
                      corners = self.pref.get_value('corners')
                     )



class FilterLowPass(ProcessingNode):
    '''

    '''
    nodeClass = 'common'

    def __init__(self):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = 'lowpass filter',
                                mode = 'editable',
                                category = 'frequency',
                                tags = ['filter', 'lowpass'],
                               )

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref.add_item(item = item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30)
                             )
        self.pref.add_item(item = item)


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
                      freq = self.pref.get_value('frequ.')
                     )




class FilterHighPass(ProcessingNode):
    '''

    '''
    nodeClass = 'common'

    def __init__(self):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = 'highpass filter',
                                mode = 'editable',
                                category = 'frequency',
                                tags = ['filter', 'highpass']
                               )

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'frequ.', 
                              value = 1,
                              limit = (0, None),
                              digits = 1,
                              increment = 1
                             )
        self.pref.add_item(item = item)

        # Add an float_spin field.
        item = IntegerSpinPrefItem(name = 'corners', 
                              value = 4,
                              limit = (1, 30)
                             )
        self.pref.add_item(item = item)

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
                      freq = self.pref.get_value('frequ.')
                     )
