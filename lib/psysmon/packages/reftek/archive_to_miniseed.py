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
import os.path
import json
import logging

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
        self.create_output_prefs()

        self.scan_summary = {}


    def create_archive_prefs(self):
        ''' Create the archive input preference items.
        '''
        archive_page = self.pref_manager.add_page('scan archive')
        archive_group = archive_page.add_group('archive')

        select_page = self.pref_manager.add_page('select')
        tr_group = select_page.add_group('time range')
        us_group = select_page.add_group('unit selection')

        # The archive directory
        pref_item = psy_pm.DirBrowsePrefItem(name = 'archive_dir',
                                             label = 'archive directory',
                                             value = '',
                                             hooks = {'on_value_change': self.on_archive_dir_changed},
                                             tool_tip = 'The root directory of the Reftek raw data archive.'
                                            )
        archive_group.add_item(pref_item)

        # Scan archive button.
        pref_item = psy_pm.ActionItem(name = 'scan_archive',
                                      label = 'scan archive',
                                      mode = 'button',
                                      action = self.on_scan_archive,
                                      tool_tip = 'Scan the reftek raw data archive.')
        archive_group.add_item(pref_item)



        # The start time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                                      label = 'start time',
                                                      value = utcdatetime.UTCDateTime('2012-07-09T00:00:00'),
                                                      tool_tip = 'The start time of the interval to process.')
        tr_group.add_item(pref_item)

        # The end time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                                      label = 'end time',
                                                      value = utcdatetime.UTCDateTime('2012-07-09T00:00:00'),
                                                      tool_tip = 'The end time of the interval to process.')
        tr_group.add_item(pref_item)


        # The SCNL list
        pref_item = psy_pm.ListCtrlEditPrefItem(name = 'unit_list',
                                           label = 'units',
                                           value = [],
                                           column_labels = ['unit id', 'stream', 'first data', 'last data'],
                                           limit = [],
                                           tool_tip = 'Select the units to process.'
                                          )
        us_group.add_item(pref_item)


    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        out_page = self.pref_manager.add_page('output')
        out_group = out_page.add_group('output')

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the MiniSeed files.')
        out_group.add_item(item)


    def edit(self):
        ''' Create the edit dialog.
        '''
        # Initialize the archive controller.
        self.load_scan_summary()
        self.update_units_list()

        dlg = psysmon.core.gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prefNodeOutput = {}):
        '''
        '''
        archive_dir = self.pref_manager.get_value('archive_dir')
        archive_scan_file = os.path.join(archive_dir, 'psysmon_archive_scan.json')
        if os.path.isfile(archive_scan_file):
            try:
                fp = open(archive_scan_file)
                self.logger.info('Loading the archive scan result file: %s.', archive_scan_file)
                ac = json.load(fp = fp, cls = psysmon.packages.reftek.archive.ArchiveScanDecoder)
                ac.sort_raw_files()
            finally:
                fp.close()

            stream_list = self.pref_manager.get_value('unit_list')
            start_time = self.pref_manager.get_value('start_time')
            end_time = self.pref_manager.get_value('end_time')
            output_dir = self.pref_manager.get_value('output_dir')

            ac.output_directory = output_dir
            for cur_stream in stream_list:
                cur_start_time = start_time
                cur_end_time = end_time
                #self.logger.debug("Converting stream %s.", cur_stream)
                stream_start_time = utcdatetime.UTCDateTime(cur_stream[2])
                stream_end_time = utcdatetime.UTCDateTime(cur_stream[3])
                if stream_start_time > cur_start_time:
                    cur_start_time = stream_start_time
                if stream_end_time < cur_end_time:
                    cur_end_time = stream_end_time
                ac.archive_to_mseed(unit_id = cur_stream[0],
                                    stream = cur_stream[1],
                                    start_time = cur_start_time,
                                    end_time = cur_end_time)


    def load_scan_summary(self):
        '''
        '''
        archive_dir = self.pref_manager.get_value('archive_dir')
        archive_scan_file = os.path.join(archive_dir, 'psysmon_archive_scan_summary.json')
        if os.path.isfile(archive_scan_file):
            #self.logger.info('Found an archive scan summary file: %s. Using this file.', archive_scan_file)
            try:
                fp = open(archive_scan_file)
                self.scan_summary = json.load(fp)
            finally:
                fp.close()



    def update_units_list(self):
        '''
        '''
        if 'stream_list' in self.scan_summary:
            self.pref_manager.set_limit('unit_list', self.scan_summary['stream_list'])


    def on_archive_dir_changed(self):
        ''' Handle the changed archive_dir.
        '''
        self.load_scan_summary()
        self.update_units_list()


    def on_scan_archive(self, event):
        ''' Scan the reftek archive directory.

        Scan the archive and fill the units listcontrol.
        '''
        archive_dir = self.pref_manager.get_value('archive_dir')
        ac = psysmon.packages.reftek.archive.ArchiveController(archive = archive_dir)
        ac.scan()
        self.scan_summary = ac.summary
        self.update_units_list()
