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
import psysmon.core.preferences_manager as preferences_manager


class LocalizeCircle(psysmon.core.plugins.CommandPlugin):
    ''' Run a localization using the circle method.

    '''
    nodeClass = 'GraphicLocalizationNode'


    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.CommandPlugin.__init__(self,
                                                    name = 'circle method',
                                                    category = 'localize',
                                                    tags = ['localize', 'circle']
                                                    )

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = psysmon.artwork.icons.iconsBlack16.localize_graphical_icon_16

        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'p_velocity',
                                                       label = 'P velocity [m/s]',
                                                       value = 5000,
                                                       limit = (1, 100000),
                                                       tool_tip = 'The P-wave velocity in m/s.'
                                                      )
        self.pref_manager.add_item(item = item)


    def run(self):
        ''' Run the circle method localization.
        '''
        self.logger.info("Localizing using the circle method.")
