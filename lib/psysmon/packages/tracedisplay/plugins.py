# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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

import logging
import wx
from psysmon.core.plugins import PluginNode


class SelectStation(PluginNode):
    '''

    '''
    def __init__(self, name, mode, category, tags, nodeClass, parent=None, docEntryPoint=None):
        ''' The constructor

        '''

        PluginNode.__init__(self, 
                            name = name, 
                            mode = mode,
                            category = category,
                            tags = tags, 
                            nodeClass = nodeClass,
                            parent = parent,
                            docEntryPoint = docEntryPoint)

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)



    def buildMenu(self):
        self.logger.debug('Building the menu.')


    def buildFoldPanel(self, panelBar):
        self.logger.debug('Building the fold panel.')
        foldPanel = panelBar.AddFoldPanel(self.name, collapsed = False)


        #button1 = wx.Button(foldPanel, wx.ID_ANY, "Collapse Me")

        # Create a checkbox list holding the station names.
        #sampleList = ['ALBA', 'SITA', 'GILA']
        displayedStations = [x[0] for x in self.parent.displayOptions.showStations]
        stationList = sorted(list(set([x[0] for x in self.parent.displayOptions.availableStations])))
        lb = wx.CheckListBox(foldPanel, wx.ID_ANY, (80, 50), wx.DefaultSize, stationList)
        
        ind = [m for m,x in enumerate(stationList) if x in displayedStations]
        lb.SetChecked(ind)



        panelBar.AddFoldPanelWindow(foldPanel, lb)




