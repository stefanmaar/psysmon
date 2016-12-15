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

import copy

import psysmon.core.preferences_manager as preferences_manager
import psysmon.packages.tracedisplay.plugins_processingstack as plugins_processingstack
import psysmon.core.packageNodes as package_nodes
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.processingStack as ps


class ProcessingStackLooperChild(package_nodes.LooperCollectionChildNode):
    ''' The processing stack.

    '''
    name = 'processing stack'
    mode = 'looper child'
    category = 'Trace processing'
    tags = ['stable', 'looper child', 'processing']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_processing_stack_preferences()


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Initialize the available processing nodes.
        processing_nodes = self.project.getProcessingNodes(('common', ))
        if self.pref_manager.get_value('processing_stack') is None:
                detrend_node_template = [x for x in processing_nodes if x.name == 'detrend'][0]
                detrend_node = copy.deepcopy(detrend_node_template)
                self.pref_manager.set_value('processing_stack', [detrend_node, ])
        self.pref_manager.set_limit('processing_stack', processing_nodes)

        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()



    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        processing_stack = ps.ProcessingStack(name = 'pstack',
                                              project = self.project,
                                              nodes = self.pref_manager.get_value('processing_stack'))

        processing_stack.execute(stream = stream,
                                 process_limits = process_limits,
                                 origin_resource = origin_resource)



    def create_processing_stack_preferences(self):
        ''' Create the preference items of the processing stack section.
        '''
        ps_page = self.pref_manager.add_page('processing stack')
        ep_group = ps_page.add_group('processing stack')
        item = plugins_processingstack.ProcessingStackPrefItem(name = 'processing_stack',
                                                           label = 'processing stack',
                                                           value = None,
                                                           tool_tip = 'Edit the processing stack nodes.')
        ep_group.add_item(item)
