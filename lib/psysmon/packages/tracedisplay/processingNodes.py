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


class Detrend(ProcessingNode):
    '''

    '''
    def __init__(self, name, mode, category, tags, options, docEntryPoint=None, parentStack = None):
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
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)



    def edit(self):
        pass


    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        self.logger.debug('Executing the processing node.')
        stream.detrend(type = 'constant')

