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

''' A collection of classes, that are currently not used in the code.
I kept them in case there is any need for them in the future.
'''
import logging

import wx

import wx.lib.platebtn as platebtn
import wx.lib.scrolledpanel as scrolled
from wx.lib.splitter import MultiSplitterWindow

import psysmon
from psysmon.artwork.icons import iconsBlack10


class FoldPanelBar(scrolled.ScrolledPanel):
    ''' pSysmon custom foldpanelbar class.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.sizer = wx.GridBagSizer(0, 0)
        self.sizer.AddGrowableCol(0)
        self.SetSizer(self.sizer)

        self.SetupScrolling()

        self.subPanels = []


    def addPanel(self, subPanel, icon):
        foldPanel = self.makeFoldPanel(subPanel, icon)
        curRow = len(self.subPanels)
        self.subPanels.append(foldPanel)
        best = foldPanel.GetBestSize()
        foldPanel.SetMinSize(best)
        foldPanel.SetSize(best)
        self.sizer.Add(foldPanel, pos=(curRow, 0), flag=wx.EXPAND|wx.ALL, border=0)
        self.sizer.AddGrowableRow(curRow)
        self.sizer.Layout()
        self.SetupScrolling()

        return foldPanel



    def hidePanel(self, subPanel):
        self.subPanels.remove(subPanel)
        self.sizer.Detach(subPanel)
        subPanel.Hide()
        self.rearrangePanels()
        
        if subPanel.minimizeButton.IsPressed():
            subPanel.minimizeButton.SetState(platebtn.PLATE_NORMAL)
            # The _pressed attribute is not reset when setting the
            # state. Do it explicitely.
            subPanel.minimizeButton._pressed = False



    def showPanel(self, subPanel):
        self.subPanels.append(subPanel)
        if subPanel.isMinimized:
            subPanel.toggleMinimize()
        self.rearrangePanels()


    def toggleMinimizePanel(self, subPanel):
        subPanel.toggleMinimize()
        self.rearrangePanels()


    def rearrangePanels(self):

        for curPanel in self.subPanels:
            self.sizer.Hide(curPanel)
            self.sizer.Detach(curPanel)

        for k, curPanel in enumerate(self.subPanels):
            self.sizer.Add(curPanel, pos=(k,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
            self.sizer.Show(curPanel)

        self.Layout()
        #self.SetupScrolling()


    def makeFoldPanel(self, panel, icon):
        foldPanel = FoldPanel(self, panel, icon)
        return foldPanel


    def onCloseButtonClick(self, event):
        self.hidePanel(event.GetEventObject().GetParent())


    def onMinimizeButtonClick(self, event):
        self.toggleMinimizePanel(event.GetEventObject().GetParent())



class FoldPanel(wx.Panel):

    def __init__(self, parent, contentPanel, icon):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.SetMinSize((50, 10))

        self.isMinimized = False

        self.icon = icon
        self.contentPanel = contentPanel

        contentPanel.Reparent(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        headerSizer = wx.GridBagSizer(0, 0)

        bmp = icon.GetBitmap()
        self.headerButton = wx.StaticBitmap(self, -1, bmp, (0, 0),
                                            (bmp.GetWidth(),
                                             bmp.GetHeight()),
                                            style=wx.NO_BORDER)
        headerSizer.Add(self.headerButton, pos=(0, 0), flag=wx.ALL, border=2)

        bmp = iconsBlack10.minus_icon_10.GetBitmap()
        #self.minimizeButton = wx.BitmapButton(self, -1, bmp, (0,0), 
        #                               style=wx.NO_BORDER)
        self.minimizeButton = platebtn.PlateButton(self, wx.ID_ANY, bmp=bmp,
                                                   style=platebtn.PB_STYLE_DEFAULT|platebtn.PB_STYLE_TOGGLE)
        self.minimizeButton.SetPressColor(wx.NamedColor('peachpuff4'))
        headerSizer.Add(self.minimizeButton, pos=(0, 2),
                        flag=wx.ALL|wx.ALIGN_RIGHT, border=0)

        bmp = iconsBlack10.delete_icon_10.GetBitmap()
        #self.closeButton = wx.BitmapButton(self, -1, bmp, (0,0), 
        #                               style=wx.NO_BORDER)
        self.closeButton = platebtn.PlateButton(self, wx.ID_ANY, bmp=bmp)
        self.closeButton.SetPressColor(wx.NamedColor('peachpuff4'))
        headerSizer.Add(self.closeButton, pos=(0 ,3),
                        flag=wx.ALL|wx.ALIGN_RIGHT, border=0)
        headerSizer.AddGrowableCol(1)

        sizer.Add(headerSizer, 0, flag=wx.EXPAND|wx.ALL, border=0)
        sizer.Add(self.contentPanel, 0, flag=wx.EXPAND|wx.ALL|wx.ALIGN_LEFT, border=0)
        self.SetSizer(sizer)
        self.sizer = sizer
        self.headerSizer = headerSizer

        self.Bind(wx.EVT_BUTTON, parent.onCloseButtonClick, self.closeButton)
        self.Bind(wx.EVT_TOGGLEBUTTON, parent.onMinimizeButtonClick, self.minimizeButton)


    def toggleMinimize(self):
        if self.contentPanel.IsShown():
            #self.sizer.Detach(self.contentPanel)
            self.contentPanel.Hide()
            self.SetMinSize(self.GetBestSize())
            self.SetSize(self.GetBestSize())
            self.sizer.Layout()
            self.isMinimized = True
            self.minimizeButton.SetPressColor(wx.NamedColor('darkolivegreen4'))
        else:
            #self.sizer.Add(self.contentPanel, 0, flag=wx.EXPAND|wx.ALL, border = 0)
            self.contentPanel.Show()
            self.SetMinSize(self.GetBestSize())
            self.SetSize(self.GetBestSize())
            self.sizer.Layout()
            self.isMinimized = False
            self.minimizeButton.SetPressColor(wx.NamedColor('peachpuff4'))


class FoldPanelBarSplitter(scrolled.ScrolledPanel):
    ''' pSysmon custom foldpanelbar class.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        #wx.ScrolledWindow.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.splitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetOrientation(wx.VERTICAL)

        self.sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.splitter.SetMinimumPaneSize(100)

        #self.EnableScrolling(True, True)
        self.SetupScrolling()

        self.subPanels = []

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSashChanged, self.splitter)


    def onSashChanged(self, event):
        print('Changed sash: %d; %s\n' % (event.GetSashIdx(), event.GetSashPosition()))


    def addPanel(self, subPanel):
        subPanel.Reparent(self.splitter)
        self.subPanels.append(subPanel)
        self.splitter.AppendWindow(subPanel, 200)
        self.SetupScrolling()

        
    def hidePanel(self, subPanel):
        self.subPanels.remove(subPanel)
        self.splitter.DetachWindow(subPanel)
        subPanel.Hide()

        
    def showPanel(self, subPanel):
        subPanel.Show()
        self.addPanel(subPanel)


    def rearrangePanels(self):
        for curPanel in self.subPanels:
            self.sizer.Hide(curPanel)
            self.sizer.Detach(curPanel)

        for curPanel in self.subPanels:
            self.sizer.Add(curPanel, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
