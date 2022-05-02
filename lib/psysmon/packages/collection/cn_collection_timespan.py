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
import psysmon.gui.dialog.pref_listbook as psy_lb


class CollectionTimespan(package_nodes.CollectionNode):
    ''' Set the runtime time-span of a collection.
    '''
    name = 'set collection time-span'
    mode = 'editable'
    category = 'collection'
    tags = ['collection', 'time', 'runtime']


    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.CollectionNode.__init__(self, **args)
        self.create_timespan_prefs()


    def create_timespan_prefs(self):
        ''' Create the time-span preference items.
        '''
        timespan_page = self.pref_manager.add_page('time-span')
        time_group = timespan_page.add_group('time-span')

        pref_item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                                label = 'start time',
                                                value = utcdatetime.UTCDateTime('2012-07-09T00:00:00'),
                                                tool_tip = 'The start time overriding the start time preference values of all collection nodes in the collection.')
        time_group.add_item(pref_item)

        pref_item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                                label = 'end time',
                                                value = utcdatetime.UTCDateTime('2012-07-09T00:00:00'),
                                                tool_tip = 'The end time overriding the start time preference values of all collection nodes in the collection.')
        time_group.add_item(pref_item)


    def edit(self):
        dlg = psy_lb.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        ''' Execute the looper collection node.

        '''
        self.parentCollection.runtime_att.start_time = self.pref_manager.get_value('start_time')
        self.parentCollection.runtime_att.end_time = self.pref_manager.get_value('end_time')


