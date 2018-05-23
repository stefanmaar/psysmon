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

import obspy.core.utcdatetime as utcdatetime

import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog as gui_preference_dialog


class CollectionLooper(package_nodes.CollectionNode):
    ''' Set the runtime time-span of a collection.
    '''
    name = 'loop the collection'
    mode = 'execute only'
    category = 'collection'
    tags = ['collection', 'loop', 'time', 'runtime']


    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.CollectionNode.__init__(self, **args)


    def edit(self):
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        ''' Execute the looper collection node.

        '''
        start_times = ['2018-03-07T12:30',
                       '2018-03-07T13:10',
                       '2018-03-08T14:50',
                       '2018-03-15T13:00',
                       '2018-03-21T12:50',
                       '2018-03-23T10:40',
                       '2018-03-28T13:20',
                       '2018-03-28T13:50',
                       '2018-03-29T13:50',
                       '2018-04-10T09:40',
                       '2018-04-18T10:00',
                       '2018-04-18T13:40',
                       '2018-04-27T09:40',
                       '2018-04-27T10:00',
                       '2018-05-02T14:20',
                       '2018-05-08T11:20',
                       '2018-05-08T11:40',
                       '2018-05-14T12:20',
                       '2018-05-22T13:00']

        start_times = [utcdatetime.UTCDateTime(x) for x in start_times]
        end_times = [x + 600 for x in start_times]

        self.parentCollection.runtime_att.start_time = start_times[0]
        self.parentCollection.runtime_att.end_time = end_times[0]
        self.parentCollection.runtime_att.loop_start_times = start_times[1:]
        self.parentCollection.runtime_att.loop_end_times = end_times[1:]


