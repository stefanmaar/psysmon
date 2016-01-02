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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The convert reftek archive to miniseed module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog

import psysmon.packages.reftek.archive

import obspy.core.utcdatetime as utcdatetime


class ConvertArchiveToMiniseed(psysmon.core.packageNodes.CollectionNode):
    '''
    '''
    name = 'reftek archive to miniseed'
    mode = 'editable'
    category = 'Reftek utilities'
    tags = ['development', ]


    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        self.create_archive_prefs()

        self.ac = None


    def create_archive_prefs(self):
        ''' Create the archive input preference items.
        '''
        pagename = '1 archive'
        self.pref_manager.add_page(pagename)

        # The archive directory
        pref_item = psy_pm.DirBrowsePrefItem(name = 'archive_dir',
                                             label = 'archive directory',
                                             group = 'archive',
                                             value = '',
                                             hooks = {'on_value_change': self.on_archive_dir_changed},
                                             tool_tip = 'The root directory of the Reftek raw data archive.'
                                            )
        self.pref_manager.add_item(pagename = pagename, item = pref_item)

        # Scan archive button.
        item = psy_pm.ActionItem(name = 'acan_archive',
                                 label = 'scan archive',
                                 group = 'archive',
                                 mode = 'button',
                                 action = self.on_scan_archive,
                                 tool_tip = 'Scan the reftek raw data archive.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = item)

        # The start time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                                      label = 'start time',
                                                      value = utcdatetime.UTCDateTime('2012-07-09T00:00:00'),
                                                      group = 'time range',
                                                      tool_tip = 'The start time of the interval to process.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        # The end time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                                      label = 'end time',
                                                      value = utcdatetime.UTCDateTime('2012-07-09T00:00:00'),
                                                      group = 'time range',
                                                      tool_tip = 'The end time of the interval to process.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        # The SCNL list
        pref_item = psy_pm.ListCtrlEditPrefItem(name = 'unit_list',
                                           label = 'units',
                                           value = [],
                                           column_labels = ['unit id', 'stream', 'first data', 'last data'],
                                           limit = [],
                                           group = 'unit selection',
                                           tool_tip = 'Select the units to process.'
                                          )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


    def edit(self):
        ''' Create the edit dialog.
        '''
        # Initialize the archive controller.
        archive_dir = self.pref_manager.get_value('archive_dir')
        self.ac = psysmon.packages.reftek.archive.ArchiveController(archive = archive_dir)
        # TODO: If available, load the last scan from the json file.

        dlg = psysmon.core.gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def on_archive_dir_changed(self):
        ''' Handle the changed archive_dir.
        '''
        if self.ac:
            self.ac.archive = self.pref_manager.get_value('archive_dir')
            self.units = {}
            self.last_scan = None


    def on_scan_archive(self, event):
        ''' Scan the reftek archive directory.

        Scan the archive and fill the units listcontrol.
        '''
        self.ac.scan()
        stream_list = []
        for cur_unit in self.ac.units.itervalues():
            cur_stream = [(cur_unit.unit_id, x.number, x.first_data_time.isoformat(), x.last_data_time.isoformat()) for x in cur_unit.streams.itervalues()]
            stream_list.extend(cur_stream)

        self.pref_manager.set_limit('unit_list', stream_list)
