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
import logging
import os
import pickle

import matplotlib as mpl
import matplotlib.pyplot as plt
import wx

import psysmon
import psysmon.core.plugins as plugins
import psysmon.artwork.icons as icons
import psysmon.core.preferences_manager as preferences_manager



class ExportImage(plugins.CommandPlugin):
    ''' Export the visible axes to an image.

    '''
    nodeClass = 'TraceDisplay'


    def __init__(self):
        ''' Initialize the instance.

        '''
        plugins.CommandPlugin.__init__(self,
                                       name = 'export image',
                                       category = 'export',
                                       tags = ['export', 'image', 'png']
                                       )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.photo_icon_16


        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        out_group = pref_page.add_group('output')

        item = preferences_manager.DirBrowsePrefItem(name = 'output_dir',
                                                     label = 'output directory',
                                                     value = '',
                                                     tool_tip = 'The directory where to save the image file.')
        out_group.add_item(item)


    def run(self):
        ''' Export the visible data to the project server.
        '''
        export_dir = self.pref_manager.get_value('export_dir')

        if export_dir == '':
            # Get the export directory from the user.
            dlg = wx.DirDialog(self.parent, "Choose an export directory:",
                               style = wx.DD_DEFAULT_STYLE
                               | wx.DD_DIR_MUST_EXIST)

            if dlg.ShowModal() == wx.ID_OK:
                export_dir = dlg.GetPath()
                self.pref_manager.set_value('export_dir', export_dir)
            else:
                return

        views = self.parent.viewport.get_node(node_type = 'view')

        view_height = 3         # The height of the view in cm
        view_width = 10         # The width of the view in cm
        dpi = 300

        cm_per_inch = 2.54
        fig_width = view_width / cm_per_inch
        fig_height = view_height * len(views)

        fig = plt.figure(figsize = (fig_width, fig_height))


        for k, cur_view in enumerate(views):
            cur_axes = fig.add_subplot(len(views), 1, k + 1)
            view_axes = cur_view.axes
            for cur_line in view_axes.lines:
                copy_line = mpl.lines.Line2D(*cur_line.get_data())
                cur_axes.add_line(copy_line)

            cur_axes.set_xlim(view_axes.get_xlim())
            cur_axes.set_ylim(view_axes.get_ylim())

        plt.show()


