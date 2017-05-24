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
'''
The plugin for the localization using the circle method.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import logging

import psysmon


class ClearMap(psysmon.core.plugins.CommandPlugin):
    ''' Clear the map view.

    '''
    nodeClass = 'GraphicLocalizationNode'


    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.CommandPlugin.__init__(self,
                                                    name = 'clear map',
                                                    category = 'visualize',
                                                    tags = ['map']
                                                    )

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = psysmon.artwork.icons.iconsBlack16.delete_icon_16




    def run(self):
        ''' Run the circle method localization.
        '''
        self.logger.info("Localizing using the circle method.")

        # Get all map views.
        map_view_name = self.rid[:self.rid.rfind('/') + 1] + 'map_view'
        map_view = self.parent.viewport.get_node(name = map_view_name)

        for cur_view in map_view:
            cur_view.axes.lines = []
            cur_view.axes.patches = []
            cur_view.draw()

