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
import psysmon.core.icons as icons


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

        self.icons['active'] = icons.pin_map_icon_16


    def buildMenu(self):
        self.logger.debug('Building the menu.')


    def buildFoldPanel(self, parent):
        self.logger.debug('Building the fold panel.')

        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)


        #button1 = wx.Button(foldPanel, wx.ID_ANY, "Collapse Me")

        # Create a checkbox list holding the station names.
        #sampleList = ['ALBA', 'SITA', 'GILA']
        displayedStations = [(x[0],x[2],x[3]) for x in self.parent.displayOptions.getSCNL('show')]

        # Create a unique list containing SNL. Preserve the sort order.
        self.stationList = self.parent.displayOptions.getSNL('available')

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
            self.parent.displayOptions.hideStation(self.stationList[index])
        else:
            self.parent.displayOptions.showStation(self.stationList[index])





class SelectChannel(PluginNode):
    '''

    '''
    def __init__(self, name, mode, category, tags, nodeClass, parent=None, docEntryPoint=None):
        ''' The constructor.

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

        self.icons['active'] = icons.pin_sq_right_icon_16



    def buildMenu(self):
        pass


    def buildFoldPanel(self, parent):
        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.channelList = sorted(self.parent.displayOptions.availableChannels)

        lb = wx.CheckListBox(parent = foldPanel,
                             id = wx.ID_ANY,
                             choices = self.channelList)

        ind = [m for m,x in enumerate(self.channelList) if x in self.parent.displayOptions.showChannels]
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
            self.parent.displayOptions.hideChannel(self.channelList[index])
        else:
            self.parent.displayOptions.showChannel(self.channelList[index])



class SeismogramPlotter(PluginNode):
    '''

    '''
    def __init__(self, name, category, tags, nodeClass, parent=None, docEntryPoint=None):
        ''' The constructor.

        '''
        PluginNode.__init__(self,
                            name = name,
                            mode = 'addon',
                            category = category,
                            tags = tags,
                            nodeClass = nodeClass,
                            parent = parent,
                            docEntryPoint = docEntryPoint)

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)


    def plot(self, displayManager, dataManager, scnl=None):
        stream = dataManager.procStream


        if not scnl:
            # No SCNL code is specified. Plot all the stations.
            for curStation in displayManager.showStations:
                for curChannel in curStation.channels:
                    curView = displayManager.getViewContainer(curChannel.getSCNL(), 'seismogram')
                    curStream = stream.select(station = curStation.name,
                                             channel = curChannel.name,
                                             network = curStation.network,
                                             location = curStation.location)
                    if curStream:
                        curView.plot(curStream)
                    curView.setXLimits(left = displayManager.startTime.timestamp,
                                       right = displayManager.endTime.timestamp)
                    curView.draw()

        else:
            # Plot only the selected SCNL codes.
            for curScnl in scnl:
                curView = displayManager.getViewContainer(curScnl, 'seismogram')
                curStream = stream.select(station = curScnl[0],
                                          channel = curScnl[1],
                                          network = curScnl[2],
                                          location = curScnl[3])
                if curStream:
                    curView.plot(curStream)
                curView.setXLimits(left = displayManager.startTime.timestamp,
                                   right = displayManager.endTime.timestamp)                





class Zoom(PluginNode):
    '''

    '''
    def __init__(self, name, mode, category, tags, nodeClass, parent=None, docEntryPoint=None):
        ''' The constructor.

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

        self.icons['active'] = icons.zoom_icon_16



    def buildMenu(self):
        pass


    def buildFoldPanel(self, panelBar):
        pass


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.onButtonPress

        return hooks


    def buildToolbarButton(self):
        return 'Hallo hier spricht Zoom Plugin.'


    def onButtonPress(self, event):
        self.logger.debug('Mouse click catched.')



