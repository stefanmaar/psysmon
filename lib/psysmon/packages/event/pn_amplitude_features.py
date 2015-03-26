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
from psysmon.core.preferences_manager import IntegerSpinPrefItem
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
            abs_max = np.max(tr.data)
            cur_scnl = p_util.traceid_to_scnl(tr.id)
            self.add_result(name = 'abs_max',
                            scnl = cur_scnl,
                            value = abs_max)

            mean = np.mean(tr.data)
            self.add_result(name = 'mean',
                            scnl = cur_scnl,
                            value = mean)



