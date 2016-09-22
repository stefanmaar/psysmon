import ipdb
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
The importWaveform module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classes of the importWaveform dialog window.
'''

import os
import copy
import logging
import psysmon
import psysmon.core.packageNodes as package_nodes
import obspy.core
from obspy.core.utcdatetime import UTCDateTime
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.packages.tracedisplay.plugins_processingstack import PStackEditField
from psysmon.core.processingStack import ProcessingStack
from psysmon.core.processingStack import ResultBag



## Documentation for class WindowProcessorNode
# 
# 
class TimeWindowLooperNode(package_nodes.LooperCollectionNode):

    name = 'time window looper'
    mode = 'editable'
    category = 'Looper'
    tags = ['stable', 'looper']

    def __init__(self, **args):
        package_nodes.LooperCollectionNode.__init__(self, **args)

        #self.create_selector_preferences()
        self.create_component_selector_preferences()
        self.create_output_preferences()


    def edit(self):
        # Initialize the components.
        # TODO: Make the station selection SNL coded.
        if self.project.geometry_inventory:
            stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
            self.pref_manager.set_limit('stations', stations)

            channels = sorted(list(set([x.name for x in self.project.geometry_inventory.get_channel()])))
            self.pref_manager.set_limit('channels', channels)

        # Create the edit dialog.
        dlg = ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput={}):
        # Get the output directory from the pref_manager. If no directory is
        # specified create one based on the node resource id.
        ipdb.set_trace() ############################## Breakpoint ##############################
        output_dir = self.pref_manager.get_value('output_dir')
        if not output_dir:
            output_dir = self.project.dataDir

        # TODO: Loop through the children nodes and execute each node. Maybe do
        # this in a separate class. Take the Sliding Window Processor. The
        # processed stream has to be passed from one node to the other like in
        # the processing stack. The input parameters of the execute node should
        # be the same as for the current processing nodes.



    def create_component_selector_preferences(self):
        ''' Create the preference items of the component selection section.

        '''
        self.pref_manager.add_page('components')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'process time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).',
                                           position = 1)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                           label = 'end time',
                                           group = 'process time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The end time of the selection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).',
                                           position = 2)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        item = psy_pm.IntegerSpinPrefItem(name = 'window_length',
                                          label = 'window length [s]',
                                          group = 'process time span',
                                          value = 300,
                                          limit = [0, 86400],
                                          tool_tip = 'The sliding window length in seconds.',
                                          position = 3)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        item = psy_pm.IntegerSpinPrefItem(name = 'window_overlap',
                                          label = 'window overlap [%]',
                                          group = 'process time span',
                                          value = 50,
                                          limit = [0, 99],
                                          tool_tip = 'The overlap of two successive sliding windows in percent.',
                                          position = 4)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)


        # The stations to process.
        item = psy_pm.MultiChoicePrefItem(name = 'stations',
                                          label = 'stations',
                                          group = 'components to process',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The stations which should be used for the processing.',
                                          position = 1)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)

        # The channels to process.
        item = psy_pm.MultiChoicePrefItem(name = 'channels',
                                          label = 'channels',
                                          group = 'components to process',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The channels which should be used for the processing.',
                                          position = 2)
        self.pref_manager.add_item(pagename = 'components',
                                   item = item)


    def create_processing_stack_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        self.pref_manager.add_page('processing stack')

        item = psy_pm.CustomPrefItem(name = 'processing_stack',
                                     label = 'processing stack',
                                     group = 'time window processing',
                                     value = None,
                                     gui_class = PStackEditField,
                                     tool_tip = 'Edit the processing stack nodes.')
        self.pref_manager.add_item(pagename = 'processing stack',
                                   item = item)


    def create_output_preferences(self):
        ''' Create the preference items of the output section.

        '''
        self.pref_manager.add_page('output')

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        group = 'output',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the processing results.'
                                       )
        self.pref_manager.add_item(pagename = 'output',
                                   item = item)

        item = psy_pm.SingleChoicePrefItem(name = 'output_interval',
                                          label = 'output interval',
                                          group = 'output',
                                          limit = ('daily', 'weekly', 'monthly'),
                                          value = 'monthly',
                                          tool_tip = 'The interval for which to save the results.')
        self.pref_manager.add_item(pagename = 'output',
                                   item = item)



