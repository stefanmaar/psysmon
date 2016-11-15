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

import logging
import wx
from psysmon.core.plugins import OptionPlugin
from psysmon.artwork.icons import iconsBlack16 as icons



class SelectStation(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'select station',
                              category = 'view',
                              tags = ['station', 'view', 'select']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.pin_map_icon_16

        self.lb = None


    def register_keyboard_shortcuts(self):
        ''' Register the keyboard shortcuts.
        '''
        #self.parent.shortcutManager.addAction(('WXK_DOWN',), self.next_station)
        #self.parent.shortcutManager.addAction(('WXK_UP', ), self.prev_station)
        pass

    def buildFoldPanel(self, parent):
        self.logger.debug('Building the fold panel.')

        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)


        #button1 = wx.Button(foldPanel, wx.ID_ANY, "Collapse Me")

        # Create a checkbox list holding the station names.
        #sampleList = ['ALBA', 'SITA', 'GILA']
        displayedStations = self.parent.displayManager.getSNL('show')

        # Create a unique list containing SNL. Preserve the sort order.
        self.stationList = self.parent.displayManager.getSNL('available')

        stationListString = [":".join(x) for x in self.stationList]
        lb = wx.CheckListBox(parent = foldPanel,
                             id = wx.ID_ANY,
                             choices = stationListString)

        ind = [m for m,x in enumerate(self.stationList) if x in displayedStations]
        lb.SetChecked(ind)

        # Bind the events.
        lb.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, lb)

        sizer.Add(lb, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        foldPanel.SetSizer(sizer)

        # Save the listbox as a class attribute.
        self.lb = lb

        return foldPanel


    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.lb.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)
        self.logger.debug('stationList[%d]: %s', index, self.stationList[index])

        # Remove all entries with the selected station from the
        # showStations.
        if not self.lb.IsChecked(index):
            self.parent.displayManager.hideStation(self.stationList[index])
        else:
            self.parent.displayManager.showStation(self.stationList[index])


    def next_station(self):
        ''' Display the next station.
        '''
        self.parent.displayManager.show_next_station()
        if self.lb is not None:
            displayedStations = self.parent.displayManager.getSNL('show')
            ind = [m for m,x in enumerate(self.stationList) if x in displayedStations]
            self.lb.SetChecked(ind)



    def prev_station(self):
        ''' Display the next station.
        '''
        self.parent.displayManager.show_prev_station()
        if self.lb is not None:
            displayedStations = self.parent.displayManager.getSNL('show')
            ind = [m for m,x in enumerate(self.stationList) if x in displayedStations]
            self.lb.SetChecked(ind)




class SelectChannel(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''

        OptionPlugin.__init__(self,
                              name = 'select channel',
                              category = 'view',
                              tags = ['channel', 'view', 'select'],
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.pin_sq_right_icon_16



    def buildMenu(self):
        pass


    def buildFoldPanel(self, parent):
        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.channelList = sorted(self.parent.displayManager.availableChannels)

        lb = wx.CheckListBox(parent = foldPanel,
                             id = wx.ID_ANY,
                             choices = self.channelList)

        ind = [m for m,x in enumerate(self.channelList) if x in self.parent.displayManager.showChannels]
        lb.SetChecked(ind)

        # Bind the events.
        lb.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, lb)

        sizer.Add(lb, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        foldPanel.SetSizer(sizer)

        # Save the listbox as a class attribute.
        self.lb = lb

        foldPanel.SetMinSize(lb.GetBestSize())

        return foldPanel





    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.lb.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)
        self.logger.debug('channelList[%d]: %s', index, self.channelList[index])

        # Remove all entries with the selected station from the
        # showStations.
        if not self.lb.IsChecked(index):
            self.parent.displayManager.hideChannel(self.channelList[index])
        else:
            self.parent.displayManager.showChannel(self.channelList[index])

