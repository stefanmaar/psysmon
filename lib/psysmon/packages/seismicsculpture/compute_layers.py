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

import itertools
import os
import csv

import psysmon.core.packageNodes as package_nodes
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.preferences_manager as pm
import psysmon.core.result as result
import psysmon.packages.sourcemap as sourcemap

import numpy as np


class ComputeLayers(package_nodes.LooperCollectionChildNode):
    ''' Compute the sourcemap for a given time window.

    '''
    name = 'compute sculpture layers'
    mode = 'looper child'
    category = 'Seismic Sculpture'
    tags = ['stable', 'looper child', 'seismic sculpture']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        item = pm.FileBrowsePrefItem(name = 'img_filename',
                                    value = '',
                                    filemask = 'Portable Network Graphic (*.png)|*.png|' \
                                                'all files (*)|*',
                                    tool_tip = 'Specify the image file.')
        self.pref_manager.add_item(item = item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the looper child collection node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Try to load the image file.
        img_filename = self.pref_manager.get_value('img_filename')

        # Compute the pixel histogram. This can be done only once at the first
        # execution of the node. Save the result in a node attribute.

        # Get the circle agents from the node. If this is the first execution,
        # create a new set of circle agents.

        # Compute the envelope.

        # TODO: Add preference items to specify the length of the processing
        # window and the overlap.

        # Loop through the processing windows.

            # Get the envelope of the processing window.

            # Compute the spectrum of the processing window.

            # Compute the polarity of the processing window.

            # Modify the agents using the above parameters.

