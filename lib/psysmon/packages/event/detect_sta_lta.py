# -*- coding: utf-8 -*-
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
''' STA/LTA event detection.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import psysmon
from psysmon.core.packageNodes import CollectionNode
import psysmon.core.preferences_manager as psy_pm
from obspy.core.utcdatetime import UTCDateTime

from psysmon.core.gui_preference_dialog import ListbookPrefDialog



class StaLtaDetection(CollectionNode):
    ''' Do a STA/LTA event detection.

    '''
    name = 'STA/LTA event detection'
    mode = 'editable'
    category = 'Event'
    tags = ['stable', 'event', 'STA/LTA', 'detect']


    def __init__(self, **args):
        CollectionNode.__init__(self, **args)

        # Setup the pages of the preference manager.
        self.pref_manager.add_page('General')
        self.pref_manager.add_page('STA/LTA')

        # The start_time.
        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The end time.
        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The stations to process.
        item = psy_pm.MultiChoicePrefItem(name = 'stations',
                                          label = 'stations',
                                          group = 'components to process',
                                          limit = ('value 1', 'value 2', 'value 3', 'value 4', 'value 5'),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the detection.')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The channels to process.
        item = psy_pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          group = 'components to process',
                                          limit = ('value 1', 'value 2', 'value 3', 'value 4', 'value 5'),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the detection.')
        self.pref_manager.add_item(pagename = 'General',
                                   item = item)

        # The STA/LTA parameters
        item = psy_pm.SingleChoicePrefItem(name = 'cf_type',
                                           label = 'characteristic function',
                                           group = 'detection',
                                           limit = ('abs', 'square'),
                                           value = 'square',
                                           tool_tip = 'The type of the characteristic function used to compute the STA and LTA.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'sta_len',
                                        label = 'STA length [s]',
                                        group = 'detection',
                                        value = 1,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The length of the STA in seconds.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'lta_len',
                                        label = 'LTA length [s]',
                                        group = 'detection',
                                        value = 10,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The length of the LTA in seconds.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'thr',
                                        label = 'threshold',
                                        group = 'detection',
                                        value = 3,
                                        limit = (0, 1000),
                                        digits = 1,
                                        tool_tip = 'The threshold of STA/LTA when to trigger an event.')
        self.pref_manager.add_item(pagename = 'STA/LTA',
                                   item = item)



    def edit(self):
        stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
        self.pref_manager.set_limit('stations', stations)

        channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
        self.pref_manager.set_limit('channels', channels)

        dlg = ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self):
        pass
