import wx
import wx.lib.colourdb
import container
from obspy.core import read
#import numpy as np
#from matplotlib.dates import DateFormatter, date2num, drange, num2date
#import datetime

# Read a standart miniseed file downloaded from obsby.
st = read('tests/data/RJOB_061005_072159.ehz.gse')
curTrace = st.traces[0]

# Read two data files containing gapped data.
#st1 = read('tests/data/gappedData01.msd');
#st2 = read('tests/data/gappedData02.msd');
#curTrace = st1.traces[0] + st2.traces[1];

app = wx.App(False)
frame = wx.Frame(None, wx.ID_ANY, "TraceDisplay Development")

sizer = wx.BoxSizer(wx.VERTICAL)

clrList = wx.lib.colourdb.getColourInfoList()
colorNames = ['TURQUOISE', 'CADETBLUE', 'SEAGREEN', 'GOLDENROD', 'SADDLEBROWN', 'VIOLETRED', 'BLUE4', 'LIGHTSKYBLUE4']
channelColors = [tuple(x[1:4]) for x in clrList if x[0] in colorNames]
channelLabels = ['channel 1', 'channel 2', 'channel 3']
stationLabels = ['station 1', 'station 2', 'station 3'] 


viewPort =  container.TdViewPort(parent=frame)


for n, curStation in enumerate(stationLabels):
    myStation = container.TdStation(frame, wx.ID_ANY, name=curStation, color='white')
    viewPort.addStation(myStation)

    #for m, curChannel in enumerate(channelLabels):
        #curColor = channelColors[m]
        #myChannel = container.TdChannel(myStation, wx.ID_ANY, name=curChannel, color=curColor)
        #myStation.addChannel(myChannel)

        #for k in range(0,1):
            #myView = container.TdSeismogramView(myChannel, wx.ID_ANY, name="view"+str(k), lineColor=curColor)
            #myView.plot(curTrace)
            #myChannel.addView(myView)

sizer.Add(viewPort, 1, flag=wx.EXPAND|wx.ALL, border=0)
frame.SetSize((300, 600))
frame.SetSizer(sizer)
frame.SetBackgroundColour("white")
frame.Show(True)
app.MainLoop()
