import wx
import wx.lib.graphics
from wx.lib.stattext import GenStaticText as StaticText
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import wx.lib.scrolledpanel as scrolled
from matplotlib.figure import Figure
import numpy as np


class TdViewAnnotationPanel(wx.Panel):
    '''
    The view annotation area.

    This area can be used to plot anotations for the view. This might be 
    some statistic values (e.g. min, max), the axes limits or some 
    other custom info.
    '''
    def __init__(self, parent, size=(50,-1), color=None):
        wx.Panel.__init__(self, parent, size=size)
        self.SetBackgroundColour(color)


	# Create a test label.
        label = StaticText(self, wx.ID_ANY, "view annotation area", (20, 10))
        font = wx.Font(6, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        label.SetFont(font)

	# Add the label to the sizer.
	sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(label, 1, wx.EXPAND|wx.ALL, border=0)
	self.SetSizer(sizer)

        #print label.GetAlignment()


class PlotPanel(wx.Panel):
    """
    The PlotPanel
    """
    def __init__( self, parent, color=None, dpi=None, **kwargs ):
        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__( self, parent, **kwargs )
        self.SetMinSize((100, 40))

        # initialize matplotlib stuff
        self.figure = Figure( None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.SetMinSize((30, 10))
        self.SetBackgroundColour('blue')

	# Add the canvas to the sizer.
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

    def SetColor( self, rgbtuple=None ):
        """Set figure and canvas colours to be the same."""
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        self.canvas.SetBackgroundColour( wx.Colour( *rgbtuple ) )


class TdView(wx.Panel):
    '''
    The tracedisplay view container.
    '''
    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour('green')

        self.plotCanvas = PlotPanel(self, color=(255,255,255))
        self.annotationArea = TdViewAnnotationPanel(self, color='gray80')

        self.SetMinSize(self.plotCanvas.GetMinSize())

        sizer = wx.GridBagSizer(0,0)
        sizer.Add(self.plotCanvas, pos=(0,0), flag=wx.ALL|wx.EXPAND, border=0)
        sizer.Add(self.annotationArea, pos=(0,1), flag=wx.ALL|wx.EXPAND, border=1)
	sizer.AddGrowableRow(0)
	sizer.AddGrowableCol(0)
	self.SetSizer(sizer)

        self.name = name

        self.parentViewport = parentViewport

        # Create the view data axes.
        #self.dataAxes = self.plotCanvas.figure.add_axes([0.1,0.1,0.8,0.8])
        self.dataAxes = self.plotCanvas.figure.add_axes([0,0,1,1])

        #self.Bind(wx.EVT_SIZE, self._onSize)

    def _onSize( self, event ):
        event.Skip()
        #print "view resize"
        #print "view size: " + str(self.GetSize())
        #print "view parent: " + str(self.GetParent())
        #print "view parent size: " + str(self.GetParent().GetSize())
        #self.annotationArea.Resize()
        self.plotCanvas.Resize()


class TdSeismogramView(TdView):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        TdView.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        self.t0 = None
	self.lineColor = [x/255.0 for x in lineColor]

    def plot(self, trace):
        endTime = trace.stats.starttime + (trace.stats.npts * 1/trace.stats.sampling_rate)
        time = np.arange(trace.stats.starttime.timestamp, endTime.timestamp, 1/trace.stats.sampling_rate)

        # Check if the data is a ma.maskedarray
        if np.ma.count_masked(trace.data):
            time = np.ma.array(time[:-1], mask=trace.data.mask)

        self.t0 = time[0]
        self.dataAxes.plot(time-self.t0, trace.data, color=self.lineColor)
        self.dataAxes.set_frame_on(False)
        self.dataAxes.get_xaxis().set_visible(False)
        self.dataAxes.get_yaxis().set_visible(False)

class TdChannelAnnotationArea(wx.Panel):

    def __init__(self, parent=None, id=wx.ID_ANY, label="channel name", bgColor="white", color="indianred", penColor="black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((40, -1))

        self.bgColor = bgColor
        self.label = label
        self.color = color
        self.penColor = penColor

	self.SetBackgroundColour(self.bgColor)

        self.Bind(wx.EVT_PAINT, self.OnPaint)


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
        penSize = 2;
        pen = wx.Pen(self.penColor, penSize)
        pen.SetJoin(wx.JOIN_ROUND)

        # Define the filling brush.
        brush = wx.Brush(self.color)

        # Define the font styles.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        #font.SetWeight(wx.BOLD)
        gc.SetFont(font)

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

        newPos =  height/2

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

class TdChannel(wx.Panel):
    '''
    The channel panel.

    The channel panel may hold 1 to more TdViews.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewPort=None, name='channel name', color='black'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The viewPort containing the channel.
        self.parentViewPort = parentViewPort

        # The channel's name.
        self.name = name

        # The channel's color.
        self.color = color

        # A list containing the views of the channel.
        self.views = []

        self.SetBackgroundColour('white')

        self.annotationArea = TdChannelAnnotationArea(self, id=wx.ID_ANY, label=self.name, color=color)
        self.sizer = wx.GridBagSizer(0,0)
	self.sizer.Add(self.annotationArea, pos=(0,0), span=(1,1), flag=wx.ALL|wx.EXPAND, border=0)
        self.sizer.AddGrowableCol(1)
        self.SetSizer(self.sizer)

    def addView(self, view):
        view.Reparent(self)
        self.views.append(view)
	#print len(self.views)
	if self.views:
	    self.sizer.Add(view, pos=(len(self.views)-1,1), flag=wx.ALL|wx.EXPAND, border=0)
            self.sizer.AddGrowableRow(len(self.views)-1)
	    self.sizer.SetItemSpan(self.annotationArea, (len(self.views), 1))

            channelSize = self.views[0].GetMinSize()
            channelSize[1] = channelSize[1] * len(self.views) 
            self.SetMinSize(channelSize)
	self.SetSizer(self.sizer)



class TdStation(wx.Panel):
    '''
    The station panel.

    The station panel may hold 1 to more TdChannels.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewPort=None, name='channel name', color='black'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The viewPort containing the channel.
        self.parentViewPort = parentViewPort

        # The channel's name.
        self.name = name

        # The channel's color.
        self.color = color

        # A list containing the views of the channel.
        self.channels = []

        self.SetBackgroundColour('white')

        self.annotationArea = TdStationAnnotationArea(self, id=wx.ID_ANY, label=self.name, color=color)
        self.sizer = wx.GridBagSizer(0,0)
	self.sizer.Add(self.annotationArea, pos=(0,0), span=(1,1), flag=wx.ALL|wx.EXPAND, border=0)
        self.sizer.AddGrowableCol(1)
        self.SetSizer(self.sizer)

    def addChannel(self, channel):
        channel.Reparent(self)
        self.channels.append(channel)
	if self.channels:
	    self.sizer.Add(channel, pos=(len(self.channels)-1,1), flag=wx.TOP|wx.BOTTOM|wx.EXPAND, border=1)
            self.sizer.AddGrowableRow(len(self.channels)-1)
	    self.sizer.SetItemSpan(self.annotationArea, (len(self.channels), 1))

            stationSize = self.channels[0].GetMinSize()
            stationSize[1] = stationSize[1] * len(self.channels) 
            self.SetMinSize(stationSize)
	self.SetSizer(self.sizer)



class TdStationAnnotationArea(wx.Panel):

    def __init__(self, parent=None, id=wx.ID_ANY, label="station name", bgColor="white", color="indianred", penColor="black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((40, -1))

        self.bgColor = bgColor
        self.label = label
        self.color = color
        self.penColor = penColor

	self.SetBackgroundColour(self.bgColor)

        self.Bind(wx.EVT_PAINT, self.OnPaint)


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
        penSize = 2;
        pen = wx.Pen(self.penColor, penSize)
        pen.SetJoin(wx.JOIN_ROUND)

        # Define the filling brush.
        brush = wx.Brush(self.color)

        # Define the font styles.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        gc.SetFont(font)

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

        newPos =  height/2

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



class TdViewPort(scrolled.ScrolledPanel):
    '''
    The tracedisplay viewport.

    This panel holds the :class:`~psysmon.packages.tracedisplay.TdStation` objects.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.SetBackgroundColour('red')

        self.SetupScrolling()

        self.stations = []


    def addStation(self, station, position=None):
        '''
        Add a TdStation object to the viewport.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.tracedisplay.TdViewPort`
        :param station: The station to be added to the viewport.
        :type station: :class:TdStation
        :param position: The position where to add the station. If none, the station is added to the bottom.
        :type position: Integer
        '''
        station.Reparent(self)
        self.stations.append(station)

        self.sizer.Add(station, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
        viewPortSize = self.stations[0].GetMinSize()
        viewPortSize[1] = viewPortSize[1] * len(self.stations) + 100 
        #self.SetMinSize(viewPortSize)
        self.SetupScrolling()


