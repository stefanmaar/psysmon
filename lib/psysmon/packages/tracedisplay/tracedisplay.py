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
import itertools
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




        tdDlg = TraceDisplayDlg(project = self.project,
                                parent = None,
                                id = wx.ID_ANY,
                                title = "TraceDisplay Development")
        return



class TraceDisplayDlg(wx.Frame):
    ''' The TraceDisplay main window.
    

    Attributes
    ----------
    logger : :class:`logging.logger`
        The logger used for debug, status and similiar messages.


    '''

    def __init__(self, project, parent = None, id = wx.ID_ANY, title = "tracedisplay", 
                 size=(1000, 600)):
        ''' The constructor.

        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.project = project

        # Initialize the user interface.
        self.initUI()

        # Create the display options.
        self.displayOptions = DisplayOptions()

        # Display the data.
        self.updateDisplay()
       
        # Show the frame. 
        self.Show(True)


    def initUI(self):
        ''' Build the userinterface.

        '''
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.viewPort =  container.TdViewPort(parent = self)
        self.sizer.Add(self.viewPort, 1, flag = wx.EXPAND|wx.ALL, border = 0)
        self.SetSizer(self.sizer)
        self.SetBackgroundColour('white')


    def updateDisplay(self):
        ''' Update the display.

        '''

        channels2Load = list(itertools.chain(*self.displayOptions.channel.values()))
        stream = self.project.waveserver['psysmon database'].\
                              getWaveform(startTime = self.displayOptions.startTime,
                                          endTime = self.displayOptions.endTime,
                                          station = self.displayOptions.station,
                                          channel = channels2Load)


        for curStation in self.displayOptions.station:
            myStation = container.TdStation(parent=self.viewPort, id=wx.ID_ANY, name=curStation, color='white')
            self.viewPort.addStation(myStation)
    
            for m, curChannel in enumerate(self.displayOptions.channel[curStation]):
                curColor = self.displayOptions.channelColors[m]
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
        



class DisplayOptions:


    def __init__(self):
        # The timespan to show.
        self.startTime = UTCDateTime('2010-08-31 07:59:00')
        self.endTime = UTCDateTime('2010-08-31 08:02:00')

        # The stations to show.
        #self.station = ['ALBA', 'BISA', 'GILA', 'GUWA', 'G_ALLA', 'G_GRUA',
        #           'G_JOAA', 'G_NAWA', 'G_PITA', 'G_RETA', 'G_SIGA', 
        #           'G_VEIA', 'G_VELA', 'G_WISA', 'MARA', 'SITA']
        self.station = ['GILA', 'GUWA', 'G_ALLA', 'G_GRUA', 'SITA', 'ALBA', 'G_NAWA']
        #self.station = ['ALBA', 'SITA', 'GILA', 'GUWA', 'G_ALLA', 'G_GRUA']
        
        # The channels to show.
        self.channel = {}
        #self.channel['GILA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['GUWA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['G_ALLA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['G_GRUA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['ALBA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['SITA'] = ['HHZ', 'HHN', 'HHE']
        
        # Fill the channel automatically. 
        # This has to be changed to a user selectable value.
        for curStation in self.station:
            self.channel[curStation] = ['HHZ', 'HHN', 'HHE']
        
        # The trace color settings.
        clrList = wx.lib.colourdb.getColourInfoList()
        colorNames = ['TURQUOISE', 'CADETBLUE', 'SEAGREEN', 'GOLDENROD', 'SADDLEBROWN', 'VIOLETRED', 'BLUE4', 'LIGHTSKYBLUE4']
        self.channelColors = [tuple(x[1:4]) for x in clrList if x[0] in colorNames]
        


