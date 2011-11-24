import wx
import container




class TraceDisplay(wx.frame):
    '''
    The tracedisplay main window.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, size=(400, 600)):
        wx.Frame.__init__(self, parent=parent, id=id)
        self.SetMinSize=size
        
        # The stations to display.
        self.stations = []


    def buildGui(self):
        '''
        Create the GUI elements of the tracedisplay window.
        ''' 
