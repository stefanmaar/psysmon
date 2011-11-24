import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class AnnotationPanel(wx.Panel):

    def __init__(self, parent, color=None, maxSize=(200, 20)):
        wx.Panel.__init__(self, parent)
        self.SetMinSize((10,3))
        self.SetBackgroundColour(color)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, "annotation area", (20, 10))
        self.sizer.Add(label, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        # The maximum size of the annotation panel.
        self.maxSize = maxSize

        self.Resize()

    def Resize( self ):
        print "resizing annotationPanel"
        pixels = tuple(self.GetParent().GetClientSize())
        newSize = [pixels[0]/5.0, pixels[1]/4.0]  
        if newSize[0] > self.maxSize[0]:
            newSize[0] = self.maxSize[0]

        if newSize[1] > self.maxSize[1]:
            newSize[1] = self.maxSize[1]

        self.SetSize(tuple(newSize))
        self.SetPosition((pixels[0]-newSize[0], 0)) 


class PlotPanel(wx.Panel):
    """
    The PlotPanel has a Figure and a Canvas. OnSize events simply set a 
    flag, and the actual resizing of the figure is triggered by an Idle event.
    """
    def __init__( self, parent, color=None, dpi=None, **kwargs ):
        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__( self, parent, **kwargs )
        self.SetMinSize((40, 12))

        # initialize matplotlib stuff
        self.figure = Figure( None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.SetPosition((0,0))
        self.SetBackgroundColour('blue')

        #self.Resize()

        self.Bind(wx.EVT_SIZE, self.Resize())

    def SetColor( self, rgbtuple=None ):
        """Set figure and canvas colours to be the same."""
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        self.canvas.SetBackgroundColour( wx.Colour( *rgbtuple ) )

    def Resize(self):
        pixels = tuple(self.GetParent().GetClientSize())
        print "resizing PlotPanel"
        print pixels
        print self.GetParent()
        self.SetSize( pixels )
        self.canvas.SetSize( pixels )
        self.figure.set_size_inches( float( pixels[0] )/self.figure.get_dpi(),
                                    float( pixels[1] )/self.figure.get_dpi() )

class TdView(wx.Panel):
    '''
    The tracedisplay view container.
    '''
    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None):
        wx.Panel.__init__(self, parent) 
        self.SetBackgroundColour('green') 

        self.plotCanvas = PlotPanel(self, color=(255,255,255))
        self.annotationArea = AnnotationPanel(self, color=(255,0,0))
        self.plotCanvas.SetPosition((0,0))
        self.annotationArea.SetPosition((0,0))
        self.name = name
        #self.annotationArea2 = AnnotationPanel(parent, color=(0,0,255))

        self.parentViewport = parentViewport

        # Create the view data axes.
        self.dataAxes = self.plotCanvas.figure.add_axes([0.1,0.1,0.8,0.8])

        self.Bind(wx.EVT_SIZE, self._onSize)

    def _onSize( self, event ):
        event.Skip()
        print "view resize"
        print "view size: " + str(self.GetSize())
        print "view parent: " + str(self.GetParent())
        print "view parent size: " + str(self.GetParent().GetSize())
        self.annotationArea.Resize()
        self.plotCanvas.Resize()


class TdSeismogramView(TdView):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None):
        TdView.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        self.t0 = None

    def plot(self, trace):
        endTime = trace.stats.starttime + (trace.stats.npts * 1/trace.stats.sampling_rate)
        time = np.arange(trace.stats.starttime.timestamp, endTime.timestamp, 1/trace.stats.sampling_rate)

        # Check if the data is a ma.maskedarray
        if np.ma.count_masked(trace.data):
            time = np.ma.array(time[:-1], mask=trace.data.mask)

        self.t0 = time[0]
        self.dataAxes.plot(time-self.t0, trace.data)
        #self.dataAxes.plot(trace.data)


class TdAnnotationArea(wx.Panel):

    def __init__(self, parent=None, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent=parent, id=id)



class TdChannel(wx.Panel):
    '''
    The channel panel.

    The channel panel may hold 1 to more TdViews.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewPort=None):
        wx.Panel.__init__(self, parent=parent, id=id)

        self.parentViewPort = parentViewPort

        # A list containing the views of the channel.
        self.views = []

        self.annotationArea = TdAnnotationArea(self, id=wx.ID_ANY)
        self.sizer = wx.GridBagSizer(0,0)

        myView = TdSeismogramView(self, wx.ID_ANY, name="myView")
        self.sizer.Add(myView, pos=(0,0), flag=wx.ALL|wx.EXPAND, border=0)
        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(0)
        self.SetSizer(self.sizer)

        self.Bind(wx.EVT_SIZE, self._onSize)

    def _onSize(self, event):
        event.Skip()
        print ""
        print ""
        print "--------------------"
        print "resizing tdChannel"
        print "tdChannel size:" + str(self.GetSize())


