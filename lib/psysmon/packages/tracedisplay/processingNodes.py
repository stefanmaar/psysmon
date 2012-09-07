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

import logging
from psysmon.core.processingStack import ProcessingNode
from psysmon.core.guiBricks import OptionsEditPanel, StaticBoxContainer, SingleChoiceField, IntegerCtrlField, FloatSpinField


class Detrend(ProcessingNode):
    '''

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

        self.options['method'] = 'constant'


        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def getEditPanel(self, parent):

        fieldSize = (250, 30)
        editPanel = OptionsEditPanel(options = self.options,
                                     parent = parent
                                    )
        editPanel.addPage('detrend')

        container = StaticBoxContainer(label = 'detrend parameters',
                                       parent = editPanel)
        editPanel.addContainer(container, 'detrend')

        choices = ['simple', 'linear', 'constant']
        curField = SingleChoiceField(parent = editPanel,
                                     name = 'detrend method',
                                     optionsKey = 'method',
                                     size = fieldSize,
                                     choices = choices)
        container.addField(curField)


        return editPanel




    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.detrend(type = self.options['method'])




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

        self.options['freqmin'] = 1
        self.options['freqmax'] = 15
        self.options['zerophase'] = False
        self.options['corners'] = 4

        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def getEditPanel(self, parent):

        fieldSize = (250, 30)
        editPanel = OptionsEditPanel(options = self.options,
                                     parent = parent
                                    )
        editPanel.addPage('bandpass filter')

        container = StaticBoxContainer(label = 'filter parameters',
                                       parent = editPanel)
        editPanel.addContainer(container, 'bandpass filter')

        curField = FloatSpinField(parent = editPanel,
                                  name = 'min. frequency',
                                  optionsKey = 'freqmin',
                                  size = fieldSize,
                                  digits = 2,
                                  min_val = 0
                                 )
        container.addField(curField)

        curField = FloatSpinField(parent = editPanel,
                                  name = 'max. frequency',
                                  optionsKey = 'freqmax',
                                  size = fieldSize,
                                  digits = 2,
                                  min_val = 0
                                 )
        container.addField(curField)

        curField = IntegerCtrlField(parent = editPanel,
                                    name = 'corners',
                                    optionsKey = 'corners',
                                    size = fieldSize
                                   )
        container.addField(curField)


        return editPanel




    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('bandpass',
                      freqmin = self.options['freqmin'],
                      freqmax = self.options['freqmax']
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
    
        self.options['freq'] = 10
        self.options['zerophase'] = False
        self.options['corners'] = 4
        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def getEditPanel(self, parent):

        fieldSize = (250, 30)
        editPanel = OptionsEditPanel(options = self.options,
                                     parent = parent
                                    )
        editPanel.addPage('lowpass filter')

        container = StaticBoxContainer(label = 'filter parameters',
                                       parent = editPanel)
        editPanel.addContainer(container, 'lowpass filter')

        curField = FloatSpinField(parent = editPanel,
                                  name = 'cutoff frequency',
                                  optionsKey = 'freq',
                                  size = fieldSize,
                                  digits = 2,
                                  min_val = 0
                                 )
        container.addField(curField)

        curField = IntegerCtrlField(parent = editPanel,
                                    name = 'corners',
                                    optionsKey = 'corners',
                                    size = fieldSize
                                   )
        container.addField(curField)


        return editPanel




    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('lowpass',
                      freq = self.options['freq']
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
    
        self.options['freq'] = 10
        self.options['zerophase'] = False
        self.options['corners'] = 4
        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def getEditPanel(self, parent):

        fieldSize = (250, 30)
        editPanel = OptionsEditPanel(options = self.options,
                                     parent = parent
                                    )
        editPanel.addPage('highpass filter')

        container = StaticBoxContainer(label = 'filter parameters',
                                       parent = editPanel)
        editPanel.addContainer(container, 'highpass filter')

        curField = FloatSpinField(parent = editPanel,
                                  name = 'cutoff frequency',
                                  optionsKey = 'freq',
                                  size = fieldSize,
                                  digits = 2,
                                  min_val = 0
                                 )
        container.addField(curField)

        curField = IntegerCtrlField(parent = editPanel,
                                    name = 'corners',
                                    optionsKey = 'corners',
                                    size = fieldSize
                                   )
        container.addField(curField)


        return editPanel




    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        #self.logger.debug('Executing the processing node.')
        stream.filter('highpass',
                      freq = self.options['freq']
                     )
