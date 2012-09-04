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
    def __init__(self, name, mode, category, tags, options,  docEntryPoint=None, parentStack = None):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = name,
                                mode = mode,
                                category = category,
                                tags = tags,
                                options = options,
                                docEntryPoint = docEntryPoint,
                                parentStack = parentStack)

        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def getEditPanel(self, parent):

        fieldSize = (250, 30)
        editPanel = OptionsEditPanel(property = self.options,
                                     parent = parent
                                    )
        editPanel.addPage('detrend')

        container = StaticBoxContainer(label = 'detrend parameters',
                                       parent = editPanel)
        editPanel.addContainer(container, 'detrend')

        choices = ['simple', 'linear', 'constant']
        curField = SingleChoiceField(parent = editPanel,
                                     name = 'detrend method',
                                     propertyKey = 'method',
                                     size = fieldSize,
                                     choices = choices)
        editPanel.addField(curField, container)

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
    def __init__(self, name, mode, category, tags, options,  docEntryPoint=None, parentStack = None):
        ''' The constructor

        '''

        ProcessingNode.__init__(self,
                                name = name,
                                mode = mode,
                                category = category,
                                tags = tags,
                                options = options,
                                docEntryPoint = docEntryPoint,
                                parentStack = parentStack)

        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def getEditPanel(self, parent):

        fieldSize = (250, 30)
        editPanel = OptionsEditPanel(property = self.options,
                                     parent = parent
                                    )
        editPanel.addPage('bandpass filter')

        container = StaticBoxContainer(label = 'filter parameters',
                                       parent = editPanel)
        editPanel.addContainer(container, 'bandpass filter')

        curField = FloatSpinField(parent = editPanel,
                                  name = 'min. frequency',
                                  propertyKey = 'freqmin',
                                  size = fieldSize
                                 )
        editPanel.addField(curField, container)

        curField = FloatSpinField(parent = editPanel,
                                  name = 'max. frequency',
                                  propertyKey = 'freqmax',
                                  size = fieldSize
                                 )
        editPanel.addField(curField, container)

        curField = IntegerCtrlField(parent = editPanel,
                                    name = 'corners',
                                    propertyKey = 'corners',
                                    size = fieldSize
                                   )
        editPanel.addField(curField, container)
        
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
