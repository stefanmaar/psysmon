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

import psysmon
from psysmon.core.plugins import OptionPlugin
import psysmon.core.preferences_manager as preferences_manager
from psysmon.artwork.icons import iconsBlack16 as icons
import wx




class SelectArray(OptionPlugin):
    '''
    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.
        '''
        OptionPlugin.__init__(self,
                              name = 'select array',
                              category = 'display',
                              tags = ['array', 'view', 'select'])
        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons._2x2_grid_icon_16

        self.lb = None


    def buildFoldPanel(self, parent):
        ''' Build the custom fold panel.
        '''
        fold_panel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.array_list = [x.name for x in sorted(self.parent.displayManager.availableArrays)]

        lb = wx.CheckListBox(parent = fold_panel,
                             id = wx.ID_ANY,
                             choices = self.array_list)

        shown_array_names = [x.name for x in self.parent.displayManager.showArrays]
        ind = [m for m, x in enumerate(self.array_list) if x in shown_array_names]
        lb.SetCheckedItems(ind)

        # Bind the events.
        lb.Bind(wx.EVT_CHECKLISTBOX, self.on_box_checked, lb)

        sizer.Add(lb, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        fold_panel.SetSizer(sizer)

        # Save the listbox as a class attribute.
        self.lb = lb

        fold_panel.SetMinSize(lb.GetBestSize())

        return fold_panel


    def on_box_checked(self, event):
        index = event.GetSelection()

        # Show the selected arrays and remove the unselected ones.
        if not self.lb.IsChecked(index):
            self.parent.displayManager.hideArray(self.array_list[index])
        else:
            self.parent.displayManager.showArray(self.array_list[index])


class SelectStation(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'select station',
                              category = 'display',
                              tags = ['station', 'view', 'select'])

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)
        
        self.icons['active'] = icons.pin_map_icon_16

        self.lb = None

        # Accelerators for shortcuts not bound to a menu item.
        handler = self.on_next_station
        self.shortcuts['next_station'] = {'accelerator_string': 'Down',
                                          'handler': handler}

        handler = self.on_prev_station
        self.shortcuts['prev_station'] = {'accelerator_string': 'Up',
                                          'handler': handler}


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

        ind = [m for m, x in enumerate(self.stationList) if x in displayedStations]
        lb.SetCheckedItems(ind)

        # Bind the events.
        lb.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, lb)

        sizer.Add(lb, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        foldPanel.SetSizer(sizer)

        # Save the listbox as a class attribute.
        self.lb = lb

        return foldPanel

    
    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}
        hooks['station_sort_order_changed'] = self.on_td_sort_order_changed

        return hooks


    def on_td_sort_order_changed(self):
        ''' Handle the station_sort_order_changed hook of tracedisplay.
        '''
        displayedStations = self.parent.displayManager.getSNL('show')

        # Create a unique list containing SNL. Preserve the sort order.
        self.stationList = self.parent.displayManager.getSNL('available')
        stationListString = [":".join(x) for x in self.stationList]
        
        self.lb.Clear()
        self.lb.Append(stationListString)
        ind = [m for m, x in enumerate(self.stationList) if x in displayedStations]
        self.lb.SetCheckedItems(ind)


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


    def on_next_station(self, evt):
        ''' Handle a shortcut press.
        '''
        self.next_station()

        
    def on_prev_station(self, evt):
        ''' Handle a shortcut press.
        '''
        self.prev_station()
        
            
    def next_station(self):
        ''' Display the next station.
        '''
        self.parent.displayManager.show_next_station()
        if self.lb is not None:
            displayedStations = self.parent.displayManager.getSNL('show')
            ind = [m for m, x in enumerate(self.stationList) if x in displayedStations]
            self.lb.SetCheckedItems(ind)


    def prev_station(self):
        ''' Display the next station.
        '''
        self.parent.displayManager.show_prev_station()
        if self.lb is not None:
            displayedStations = self.parent.displayManager.getSNL('show')
            ind = [m for m, x in enumerate(self.stationList) if x in displayedStations]
            self.lb.SetCheckedItems(ind)




class SelectChannel(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''

        OptionPlugin.__init__(self,
                              name = 'select channel',
                              category = 'display',
                              tags = ['channel', 'view', 'select'],)

        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

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

        ind = [m for m, x in enumerate(self.channelList) if x in self.parent.displayManager.showChannels]
        lb.SetCheckedItems(ind)

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

