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

import psysmon.core.packageNodes as package_nodes
import psysmon.core.gui_preference_dialog as gui_preference_dialog
from psysmon.core.preferences_manager import FloatSpinPrefItem
import psysmon.core.result as result
import psysmon.core.util as p_util
import numpy as np


class ComputeAmplitudeFeatures(package_nodes.LooperCollectionChildNode):
    ''' Apply a median filter to a timeseries.

    '''
    name = 'compute amplitude features'
    mode = 'looper child'
    category = 'Amplitude'
    tags = ['stable', 'looper child']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        pref_page = self.pref_manager.add_page('Preferences')
        w_group = pref_page.add_group('window')

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'noise_window_length',
                              label = 'noise window length',
                              value = 5,
                              limit = (0, 1000),
                              tool_tip = 'The length of the time-span used to compute the noise parameters [s].'
                             )
        w_group.add_item(item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()



    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Create a table result.
        columns = ['max_abs', 'peak_to_peak']
        table_result = result.TableResult(name = 'amplitude features',
                                          key_name = 'scnl',
                                          start_time = process_limits[0],
                                          end_time = process_limits[1],
                                          origin_name = self.name,
                                          origin_resource = origin_resource,
                                          column_names = columns)

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

            # Compute the maximum range of the trace.
            peak_to_peak = np.max(proc_trace.data) + np.abs(np.min(proc_trace.data))


            cur_scnl = p_util.traceid_to_scnl(tr.id)
            table_result.add_row(key = cur_scnl,
                                 max_abs = max_abs,
                                 peak_to_peak = peak_to_peak)


        self.result_bag.add(table_result)



