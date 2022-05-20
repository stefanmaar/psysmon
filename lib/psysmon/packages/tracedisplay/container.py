from __future__ import print_function
from __future__ import division
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

import numpy as np
from obspy.core import UTCDateTime
import wx
import wx.lib.graphics
from wx.adv import DatePickerCtrl
from wx.lib.masked import TextCtrl as MaskedTextCtrl
try:
    from agw import floatspin as floatspin
except ImportError:
    # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as floatspin

import psysmon
import psysmon.gui.util as gui_util


class ChannelAnnotationArea(wx.Panel):

    def __init__(self, parent = None,
                 id = wx.ID_ANY,
                 label = "channel name",
                 bgColor = "white",
                 color = "black",
                 penColor = "black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)
        
        self.SetMinSize((40, -1))

        self.bgColor = bgColor
        self.label = label
        self.color = color
        self.penColor = penColor

        self.SetBackgroundColour(self.bgColor)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)

        
    def onSetFocus(self, event):
        self.logger.debug("onSetFocus in channel annotation")
        event.ResumePropagation(30)
        event.Skip()


    def OnPaint(self, event):
        #print "OnPaint"
        event.Skip()
        dc = wx.PaintDC(self)
        gc = self.makeGC(dc)
        self.draw(gc)

    def makeGC(self, dc):
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.",
                        25, 25)
            return None
        return gc

    def draw(self, gc):
        #print "drawing"
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]

        # Define the drawing  pen.
        penSize = 2
        pen = wx.Pen(self.penColor, penSize)
        pen.SetJoin(wx.JOIN_ROUND)

        # Define the filling brush.
        brush = wx.Brush(self.color)

        # Define the font styles.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        color = wx.Colour('black')
        #font.SetWeight(wx.BOLD)
        gc.SetFont(font, color)

        path = gc.CreatePath()
        path.MoveToPoint(width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, penSize/2.0)
        path.MoveToPoint(3/4.0*width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, height-penSize/2.0)
        path.MoveToPoint(3/4.0*width, height-penSize/2.0)
        path.AddLineToPoint(width, height-penSize/2.0)
        path.CloseSubpath()

        path1 = gc.CreatePath()
        path1.AddRectangle(3/4.0*width, penSize/2.0, width/4.0, height-penSize/2.0)

        gc.SetPen(pen)
        gc.SetBrush(brush)
        gc.FillPath(path1)
        gc.DrawPath(path)

        newPos = height / 2

        #print winSize
        #print newPos
        gc.PushState()
        gc.Translate(width/4.0, newPos)
        gc.Rotate(np.radians(-90))
        w, h = gc.GetTextExtent(self.label)
        #print w
        gc.DrawText(self.label, -w/2.0, -h/2.0)
        #gc.DrawPath(path1)
        gc.PopState()


class TdDatetimeInfo(wx.Panel):
    def __init__(self, parent=None, id=wx.ID_ANY, bgColor="ghostwhite",
                 penColor="black"):
        wx.Panel.__init__(self,
                          parent=parent,
                          id=id,
                          style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((-1, 30))
        self.SetMaxSize((-1, 150))

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.startTime = None
        self.endTime = None
        self.scale = None

        sizer = wx.GridBagSizer(vgap = 0,
                                hgap = 5)

        self.dummy10 = wx.StaticText(self, wx.ID_ANY, '', size=(10, -1))
        self.dummy80 = wx.StaticText(self, wx.ID_ANY, '', size=(80, -1))
        self.dummy100 = wx.StaticText(self, wx.ID_ANY, '', size=(100, -1))

        style = wx.adv.DP_DEFAULT | wx.adv.DP_SHOWCENTURY
        self.startDatePicker = DatePickerCtrl(self,
                                              id = wx.ID_ANY,
                                              style = style)


        self.startTimePicker = MaskedTextCtrl(self, wx.ID_ANY, '',
                                              mask = '##:##:##.######',
                                              excludeChars = '',
                                              formatcodes = 'F!',
                                              includeChars = '',
                                              size = (-1, -1))


        size = self.startTimePicker.GetSize()
        self.startTimeGoButton = wx.Button(self,
                                           id = wx.ID_ANY,
                                           label = "go",
                                           size = (-1, size[1]))


        fs = floatspin.FloatSpin(self,
                                 wx.ID_ANY,
                                 min_val = 0,
                                 max_val = None,
                                 increment = 1,
                                 value = 60,
                                 agwStyle = floatspin.FS_RIGHT,
                                 size = (-1, -1))
        self.durationFloatSpin = fs
        self.durationFloatSpin.SetDigits(3)
        self.durationFloatSpin.SetFormat('%f')
        self.durationFloatSpin.SetRange(min_val=0.1,
                                        max_val=None)
        self.durationFloatSpin.SetMinSize((150, -1))

        sizer.Add(self.dummy80,
                  pos = (0, 0),
                  flag = wx.ALL,
                  border = 0)
        sizer.Add(self.startDatePicker, pos=(0, 1),
                  flag = wx.ALL | wx.ALIGN_BOTTOM | wx.EXPAND,
                  border=0)
        sizer.Add(self.startTimePicker,
                  pos = (0, 2),
                  flag = wx.ALL | wx.ALIGN_BOTTOM | wx.EXPAND,
                  border = 0)
        sizer.Add(self.startTimeGoButton,
                  pos = (0, 3),
                  flag = wx.ALL | wx.ALIGN_BOTTOM | wx.EXPAND,
                  border = 0)
        sizer.Add(self.durationFloatSpin,
                  pos = (0, 5),
                  flag = wx.ALL | wx.ALIGN_BOTTOM | wx.EXPAND,
                  border = 0)
        sizer.Add(self.dummy10,
                  pos = (0, 6),
                  flag = wx.ALL,
                  border = 0)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(4)

        print("Sizes: ")
        print(self.durationFloatSpin.GetMinSize())
        print(self.durationFloatSpin.GetBestSize())
        print(self.durationFloatSpin.DoGetBestClientSize())

        self.SetSizerAndFit(sizer)

        self.SetBackgroundColour(bgColor)

        self.Bind(floatspin.EVT_FLOATSPIN,
                  self.onDurationFloatSpin,
                  self.durationFloatSpin)
        self.Bind(wx.EVT_BUTTON, self.onStartTimeGo, self.startTimeGoButton)
        

    def onStartTimePicker(self, event):
        self.logger.debug('onStartTimePicker')

    def onStartTimeGo(self, event):
        self.logger.debug('GO startTime GO')
        curDate = gui_util.wxdate2pydate(self.startDatePicker.GetValue())
        if self.startTimePicker.IsValid():
            curTime = self.startTimePicker.GetValue().replace('.', ':').split(':')
            curDateTime = UTCDateTime(curDate.year, curDate.month, curDate.day,
                                      int(curTime[0]), int(curTime[1]),
                                      int(curTime[2]), int(curTime[3]))
            self.logger.debug('startTime: %s', curDateTime)
            self.GetParent().GetParent().setStartTime(curDateTime)


    def onDurationFloatSpin(self, event):
        #dlg = wx.TextEntryDialog(
        #        self, 'Duration:',
        #        'Enter new duration')

        #dlg.SetValue(str(self.endTime - self.startTime))

        #if dlg.ShowModal() == wx.ID_OK:
        #    self.logger.debug('New duration: %f', float(dlg.GetValue()))
        #    self.logger.debug('Parent: %s', self.GetParent().GetParent())
        #    self.GetParent().GetParent().setDuration(float(dlg.GetValue()))
        floatSpin = event.GetEventObject()
        value = floatSpin.GetValue()
        self.logger.debug('New duration: %f', value)
        self.GetParent().GetParent().setDuration(value)



    def onPaint(self, event):
        #print "OnPaint"
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]
        btnSize = self.durationButton.GetSize()
        pos = (width - 100 - btnSize[1], height / 2)
        self.durationButton.SetPosition(pos)
        event.Skip()
        #dc = wx.PaintDC(self)
        #gc = self.makeGC(dc)
        #self.draw(gc)


    def makeGC(self, dc):
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.",
                        25, 25)
            return None
        return gc

    def draw(self, gc):
        self.logger.debug('Draw datetime')
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        color = wx.Colour('black')
        font.SetWeight(wx.BOLD)
        gc.SetFont(font, color)
        if self.startTime:
            gc.PushState()
            gc.Translate(80, height/2.0)

            spanText = str(self.endTime - self.startTime) + ' s'
            text = str(self.startTime) + '      length: ' + spanText
            gc.DrawText(text, 0, 0)

            #gc.PopState()
            #gc.PushState()
            #text = str(self.endTime - self.startTime) + ' s'
            #(textWidth, textHeight) = gc.GetTextExtent(text)
            #gc.Translate(width - 100 - textWidth, height/2.0)
            #gc.DrawText(text, 0, 0)

            #gc.PopState()

            #gc.Translate(width/2.0, height/2.0)
            #penSize = 2
            #pen = wx.Pen('black', penSize)
            #pen.SetJoin(wx.JOIN_ROUND)
            #path = gc.CreatePath()
            #scalebarLength = 10
            #path.MoveToPoint(0, 0)
            #path.AddLineToPoint(scalebarLength * self.scale, 0)
            #path.CloseSubpath()

            #gc.Translate(width/2.0, height/2.0)
            #gc.SetPen(pen)
            #gc.DrawPath(path)

            #gc.PopState()


    def setTime(self, startTime, endTime, scale):

        # TODO: Add a check for the correct data type.
        self.startTime = startTime
        self.endTime = endTime
        self.scale = scale

        # Set the datePicker value.
        self.startDatePicker.SetValue(gui_util.pydate2wxdate(self.startTime))
        self.startTimePicker.SetValue(self.startTime.strftime('%H%M%S%f'))

        #self.startTimeButton.SetLabel(str(self.startTime))
        #self.startTimeButton.SetSize(self.startTimeButton.DoGetBestSize())

        #self.durationButton.SetLabel(str(self.endTime - self.startTime) + ' s')
        #self.durationButton.SetSize(self.durationButton.DoGetBestSize())
        self.durationFloatSpin.SetValue(self.endTime - self.startTime)




class StationAnnotationArea(wx.Panel):

    def __init__(self, parent=None, id=wx.ID_ANY, label="station name", bgColor="white", color="black", penColor="black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((40, -1))

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.bgColor = bgColor
        self.label = label
        self.color = color
        self.penColor = penColor

        self.SetBackgroundColour(self.bgColor)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        #self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

    def OnPaint(self, event):
        #print "OnPaint"
        event.Skip()
        dc = wx.PaintDC(self)
        gc = self.makeGC(dc)
        self.draw(gc)

    def onSetFocus(self, event):
        self.logger.debug("onSetFocus in station annotation")
        event.ResumePropagation(30)
        event.Skip()


    def onKeyDown(self, event):
        print("onKeyDown in station annotation")
        event.ResumePropagation(1)
        event.Skip()

    def makeGC(self, dc):
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.",
                        25, 25)
            return None
        return gc

    def draw(self, gc):
        #print "drawing"
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]

        # Define the drawing  pen.
        penSize = 2;
        pen = wx.Pen(self.penColor, penSize)
        pen.SetJoin(wx.JOIN_ROUND)

        # Define the filling brush.
        brush = wx.Brush(self.color)

        # Define the font styles.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        color = wx.Colour('black')
        font.SetWeight(wx.BOLD)
        gc.SetFont(font, color)

        path = gc.CreatePath()
        path.MoveToPoint(width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, penSize/2.0)
        path.MoveToPoint(3/4.0*width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, height-penSize/2.0)
        path.MoveToPoint(3/4.0*width, height-penSize/2.0)
        path.AddLineToPoint(width, height-penSize/2.0)
        path.CloseSubpath()

        path1 = gc.CreatePath()
        path1.AddRectangle(3/4.0*width, penSize/2.0, width/4.0, height-penSize/2.0)

        gc.SetPen(pen)
        gc.SetBrush(brush)
        gc.FillPath(path1)
        gc.DrawPath(path)

        newPos =  height / 2

        #print winSize
        #print newPos
        gc.PushState()
        gc.Translate(width/4.0, newPos)
        gc.Rotate(np.radians(-90))
        w, h = gc.GetTextExtent(self.label)
        #print w
        gc.DrawText(self.label, -w/2.0, -h/2.0)
        #gc.DrawPath(path1)
        gc.PopState()
