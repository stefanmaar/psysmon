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
import wx.lib.colourdb
from psysmon.core.packageNodes import CollectionNode
from obspy.core.utcdatetime import UTCDateTime
import container


class TraceDisplay(CollectionNode):
    '''

    '''

    def edit(self):
        pass


    def execute(self, prevNodeOutput={}):
        
        # Create the logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.logger.debug('Executing TraceDisplay')

        startTime = UTCDateTime('2010-08-31 07:59:00')
        endTime = UTCDateTime('2010-08-31 08:02:00')
        #station = ['ALBA', 'BISA', 'GILA', 'GUWA', 'G_ALLA', 'G_GRUA',
        #           'G_JOAA', 'G_NAWA', 'G_PITA', 'G_RETA', 'G_SIGA', 
        #           'G_VEIA', 'G_VELA', 'G_WISA', 'MARA', 'SITA']
        station = ['GILA', 'GUWA', 'G_ALLA', 'G_GRUA']
        channel = ['HHZ', 'HHN', 'HHE']
        
        clrList = wx.lib.colourdb.getColourInfoList()
        colorNames = ['TURQUOISE', 'CADETBLUE', 'SEAGREEN', 'GOLDENROD', 'SADDLEBROWN', 'VIOLETRED', 'BLUE4', 'LIGHTSKYBLUE4']
        channelColors = [tuple(x[1:4]) for x in clrList if x[0] in colorNames]

        stream = self.project.waveserver['psysmon database'].\
                              getWaveform(startTime = startTime,
                                          endTime = endTime,
                                          station = station,
                                          channel = channel)


        frame = wx.Frame(None, wx.ID_ANY, "TraceDisplay Development")
        sizer = wx.BoxSizer(wx.VERTICAL)
        viewPort =  container.TdViewPort(parent=frame)

        for curStation in station:
            myStation = container.TdStation(frame, wx.ID_ANY, name=curStation, color='white')
            viewPort.addStation(myStation)
    
            for m, curChannel in enumerate(channel):
                curColor = channelColors[m]
                myChannel = container.TdChannel(myStation, wx.ID_ANY, name=curChannel, color=curColor)
                myStation.addChannel(myChannel)

                self.logger.debug("station: %s", curStation)
                self.logger.debug("channel: %s", curChannel)
                curStream = stream.select(station = curStation,
                                          channel = curChannel)

                myView = container.TdSeismogramView(myChannel, wx.ID_ANY, name=myChannel, lineColor=curColor)
                
                for curTrace in curStream:
                    self.logger.debug("Plotting trace:\n%s", curTrace)
                    myView.plot(curTrace)
                myChannel.addView(myView)
            

        sizer.Add(viewPort, 1, flag=wx.EXPAND|wx.ALL, border=0)
        frame.SetSize((800, 600))
        frame.SetSizer(sizer)
        frame.SetBackgroundColour("white")
        frame.Show(True)
        
