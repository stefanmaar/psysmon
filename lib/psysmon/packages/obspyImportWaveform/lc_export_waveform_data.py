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

import obspy.core.util.base


import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog as gui_preference_dialog


class ExportWaveformData(package_nodes.LooperCollectionChildNode):
    ''' Export waveform data to a file.

    '''
    name = 'export waveform data'
    mode = 'looper child'
    category = 'export'
    tags = ['waveform', 'data', 'export']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_output_preferences()

        # TODO: Add format preferences for selected output formats.



    def create_output_preferences(self):
        ''' Create the output preferences.
        '''
        output_page = self.pref_manager.add_page('Output')
        format_group = output_page.add_group('format')

        obspy_formats = obspy.core.util.base.ENTRY_POINTS['waveform'].keys()
        obspy_formats = sorted(obspy_formats)
        item = psy_pm.SingleChoicePrefItem(name = 'file_format',
                                           label = 'file format',
                                           limit = obspy_formats,
                                           value = 'MSEED',
                                           tool_tip = 'The export file format supported by obspy.')
        format_group.add_item(item)



    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        dlg.ShowModal()
        dlg.Destroy()



    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the looper child node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        print stream

