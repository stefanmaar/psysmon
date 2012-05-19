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
import time
import wx
import wx.lib.colourdb
import psysmon.core.gui as psygui
from psysmon.core.packageNodes import CollectionNode
from obspy.core.utcdatetime import UTCDateTime
import container


keyMap = {
    wx.WXK_BACK : "WXK_BACK",
    wx.WXK_TAB : "WXK_TAB",
    wx.WXK_RETURN : "WXK_RETURN",
    wx.WXK_ESCAPE : "WXK_ESCAPE",
    wx.WXK_SPACE : "WXK_SPACE",
    wx.WXK_DELETE : "WXK_DELETE",
    wx.WXK_START : "WXK_START",
    wx.WXK_LBUTTON : "WXK_LBUTTON",
    wx.WXK_RBUTTON : "WXK_RBUTTON",
    wx.WXK_CANCEL : "WXK_CANCEL",
    wx.WXK_MBUTTON : "WXK_MBUTTON",
    wx.WXK_CLEAR : "WXK_CLEAR",
    wx.WXK_SHIFT : "WXK_SHIFT",
    wx.WXK_ALT : "WXK_ALT",
    wx.WXK_CONTROL : "WXK_CONTROL",
    wx.WXK_MENU : "WXK_MENU",
    wx.WXK_PAUSE : "WXK_PAUSE",
    wx.WXK_CAPITAL : "WXK_CAPITAL",
    #wx.WXK_PRIOR : "WXK_PRIOR",
    #wx.WXK_NEXT : "WXK_NEXT",
    wx.WXK_END : "WXK_END",
    wx.WXK_HOME : "WXK_HOME",
    wx.WXK_LEFT : "WXK_LEFT",
    wx.WXK_UP : "WXK_UP",
    wx.WXK_RIGHT : "WXK_RIGHT",
    wx.WXK_DOWN : "WXK_DOWN",
    wx.WXK_SELECT : "WXK_SELECT",
    wx.WXK_PRINT : "WXK_PRINT",
    wx.WXK_EXECUTE : "WXK_EXECUTE",
    wx.WXK_SNAPSHOT : "WXK_SNAPSHOT",
    wx.WXK_INSERT : "WXK_INSERT",
    wx.WXK_HELP : "WXK_HELP",
    wx.WXK_NUMPAD0 : "WXK_NUMPAD0",
    wx.WXK_NUMPAD1 : "WXK_NUMPAD1",
    wx.WXK_NUMPAD2 : "WXK_NUMPAD2",
    wx.WXK_NUMPAD3 : "WXK_NUMPAD3",
    wx.WXK_NUMPAD4 : "WXK_NUMPAD4",
    wx.WXK_NUMPAD5 : "WXK_NUMPAD5",
    wx.WXK_NUMPAD6 : "WXK_NUMPAD6",
    wx.WXK_NUMPAD7 : "WXK_NUMPAD7",
    wx.WXK_NUMPAD8 : "WXK_NUMPAD8",
    wx.WXK_NUMPAD9 : "WXK_NUMPAD9",
    wx.WXK_MULTIPLY : "WXK_MULTIPLY",
    wx.WXK_ADD : "WXK_ADD",
    wx.WXK_SEPARATOR : "WXK_SEPARATOR",
    wx.WXK_SUBTRACT : "WXK_SUBTRACT",
    wx.WXK_DECIMAL : "WXK_DECIMAL",
    wx.WXK_DIVIDE : "WXK_DIVIDE",
    wx.WXK_F1 : "WXK_F1",
    wx.WXK_F2 : "WXK_F2",
    wx.WXK_F3 : "WXK_F3",
    wx.WXK_F4 : "WXK_F4",
    wx.WXK_F5 : "WXK_F5",
    wx.WXK_F6 : "WXK_F6",
    wx.WXK_F7 : "WXK_F7",
    wx.WXK_F8 : "WXK_F8",
    wx.WXK_F9 : "WXK_F9",
    wx.WXK_F10 : "WXK_F10",
    wx.WXK_F11 : "WXK_F11",
    wx.WXK_F12 : "WXK_F12",
    wx.WXK_F13 : "WXK_F13",
    wx.WXK_F14 : "WXK_F14",
    wx.WXK_F15 : "WXK_F15",
    wx.WXK_F16 : "WXK_F16",
    wx.WXK_F17 : "WXK_F17",
    wx.WXK_F18 : "WXK_F18",
    wx.WXK_F19 : "WXK_F19",
    wx.WXK_F20 : "WXK_F20",
    wx.WXK_F21 : "WXK_F21",
    wx.WXK_F22 : "WXK_F22",
    wx.WXK_F23 : "WXK_F23",
    wx.WXK_F24 : "WXK_F24",
    wx.WXK_NUMLOCK : "WXK_NUMLOCK",
    wx.WXK_SCROLL : "WXK_SCROLL",
    wx.WXK_PAGEUP : "WXK_PAGEUP",
    wx.WXK_PAGEDOWN : "WXK_PAGEDOWN",
    wx.WXK_NUMPAD_SPACE : "WXK_NUMPAD_SPACE",
    wx.WXK_NUMPAD_TAB : "WXK_NUMPAD_TAB",
    wx.WXK_NUMPAD_ENTER : "WXK_NUMPAD_ENTER",
    wx.WXK_NUMPAD_F1 : "WXK_NUMPAD_F1",
    wx.WXK_NUMPAD_F2 : "WXK_NUMPAD_F2",
    wx.WXK_NUMPAD_F3 : "WXK_NUMPAD_F3",
    wx.WXK_NUMPAD_F4 : "WXK_NUMPAD_F4",
    wx.WXK_NUMPAD_HOME : "WXK_NUMPAD_HOME",
    wx.WXK_NUMPAD_LEFT : "WXK_NUMPAD_LEFT",
    wx.WXK_NUMPAD_UP : "WXK_NUMPAD_UP",
    wx.WXK_NUMPAD_RIGHT : "WXK_NUMPAD_RIGHT",
    wx.WXK_NUMPAD_DOWN : "WXK_NUMPAD_DOWN",
    #wx.WXK_NUMPAD_PRIOR : "WXK_NUMPAD_PRIOR",
    wx.WXK_NUMPAD_PAGEUP : "WXK_NUMPAD_PAGEUP",
    #wx.WXK_NUMPAD_NEXT : "WXK_NUMPAD_NEXT",
    wx.WXK_NUMPAD_PAGEDOWN : "WXK_NUMPAD_PAGEDOWN",
    wx.WXK_NUMPAD_END : "WXK_NUMPAD_END",
    wx.WXK_NUMPAD_BEGIN : "WXK_NUMPAD_BEGIN",
    wx.WXK_NUMPAD_INSERT : "WXK_NUMPAD_INSERT",
    wx.WXK_NUMPAD_DELETE : "WXK_NUMPAD_DELETE",
    wx.WXK_NUMPAD_EQUAL : "WXK_NUMPAD_EQUAL",
    wx.WXK_NUMPAD_MULTIPLY : "WXK_NUMPAD_MULTIPLY",
    wx.WXK_NUMPAD_ADD : "WXK_NUMPAD_ADD",
    wx.WXK_NUMPAD_SEPARATOR : "WXK_NUMPAD_SEPARATOR",
    wx.WXK_NUMPAD_SUBTRACT : "WXK_NUMPAD_SUBTRACT",
    wx.WXK_NUMPAD_DECIMAL : "WXK_NUMPAD_DECIMAL",
    wx.WXK_NUMPAD_DIVIDE : "WXK_NUMPAD_DIVIDE",

    wx.WXK_WINDOWS_LEFT : "WXK_WINDOWS_LEFT",
    wx.WXK_WINDOWS_RIGHT : "WXK_WINDOWS_RIGHT",
    wx.WXK_WINDOWS_MENU : "WXK_WINDOWS_MENU",

    wx.WXK_COMMAND : "WXK_COMMAND",

    wx.WXK_SPECIAL1 : "WXK_SPECIAL1",
    wx.WXK_SPECIAL2 : "WXK_SPECIAL2",
    wx.WXK_SPECIAL3 : "WXK_SPECIAL3",
    wx.WXK_SPECIAL4 : "WXK_SPECIAL4",
    wx.WXK_SPECIAL5 : "WXK_SPECIAL5",
    wx.WXK_SPECIAL6 : "WXK_SPECIAL6",
    wx.WXK_SPECIAL7 : "WXK_SPECIAL7",
    wx.WXK_SPECIAL8 : "WXK_SPECIAL8",
    wx.WXK_SPECIAL9 : "WXK_SPECIAL9",
    wx.WXK_SPECIAL10 : "WXK_SPECIAL10",
    wx.WXK_SPECIAL11 : "WXK_SPECIAL11",
    wx.WXK_SPECIAL12 : "WXK_SPECIAL12",
    wx.WXK_SPECIAL13 : "WXK_SPECIAL13",
    wx.WXK_SPECIAL14 : "WXK_SPECIAL14",
    wx.WXK_SPECIAL15 : "WXK_SPECIAL15",
    wx.WXK_SPECIAL16 : "WXK_SPECIAL16",
    wx.WXK_SPECIAL17 : "WXK_SPECIAL17",
    wx.WXK_SPECIAL18 : "WXK_SPECIAL18",
    wx.WXK_SPECIAL19 : "WXK_SPECIAL19",
    wx.WXK_SPECIAL2 : "WXK_SPECIAL2",
}


class TraceDisplay(CollectionNode):
    '''

    '''

    def edit(self):
        pass


    def execute(self, prevNodeOutput={}):

        self.logger.debug('Executing TraceDisplay')


        app = psygui.PSysmonApp()

        tdDlg = TraceDisplayDlg(project = self.project,
                                parent = None,
                                id = wx.ID_ANY,
                                title = "TraceDisplay Development")

        app.MainLoop()


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

        # Create the display option.
        self.displayOptions = DisplayOptions()

        # Create the shortcut options.
        self.shortCutOptions = ShortCutOptions()

        # Initialize the user interface.
        self.initUI()
        self.initKeyEvents()

        # Display the data.
        self.updateDisplay()

        # Show the frame. 
        self.Show(True)


    def initUI(self):
        ''' Build the userinterface.

        '''
        self.logger.debug('Initializing the GUI')
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.viewPort =  container.TdViewPort(parent = self)
        self.sizer.Add(self.viewPort, 1, flag = wx.EXPAND|wx.ALL, border = 0)
        self.SetSizer(self.sizer)
        self.SetBackgroundColour('white')
        self.viewPort.SetFocus()


    def initKeyEvents(self):
        ''' Initialize the key event bindings.

        '''
        self.logger.debug('Binding key events.')
        self.viewPort.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

        self.shortCutOptions.addAction(('WXK_RIGHT',), self.advanceTime)
        self.shortCutOptions.addAction(('WXK_LEFT',), self.decreaseTime)
        

    def advanceTime(self):
        ''' Advance the display time by one step. 
        '''
        self.displayOptions.advanceTime()
        self.updateDisplay()


    def decreaseTime(self):
        ''' Decrease the display time by one step.
        '''
        self.displayOptions.decreaseTime()
        self.updateDisplay()


    def onKeyDown(self, event):
        ''' Handle a key down event.

        '''
        keyCode = event.GetKeyCode()
        keyName = keyMap.get(keyCode, None)

        if keyName is None:
            if keyCode < 256:
                if keyCode == 0:
                    keyName = "NUL"
                elif keyCode < 27:
                    keyName = "Ctrl-%s" % chr(ord('A') + keyCode-1)
                else:
                    keyName = "\"%s\"" % chr(keyCode)
            else:
                keyName = "(%s)" % keyCode
        
        
        # Process the modifiers.
        pressedKey = []
        modString = ""
        for mod, ch in [(event.ControlDown(), 'CTRL'),
                        (event.AltDown(),     'ALT'),
                        (event.ShiftDown(),   'SHIFT'),
                        (event.MetaDown(),    'META')]:
            if mod:
                pressedKey.append(ch)
                modString += ch + " + "

        pressedKey.append(keyName)
        pressedKeyString = modString + keyName
        self.logger.debug('Pressed key: %s - %s', keyCode, pressedKeyString)
        action = self.shortCutOptions.getAction(tuple(pressedKey))
        
        if action:
            action()


    def onSetFocus(self, event):
        ''' Handle a key down event.

        '''
        self.logger.debug('Setting focus.')
    
    
    def updateDisplay(self):
        ''' Update the display.

        '''

        channels2Load = list(itertools.chain(*self.displayOptions.channel.values()))
        stream = self.project.waveclient['main client'].\
                              getWaveform(startTime = self.displayOptions.startTime,
                                          endTime = self.displayOptions.endTime,
                                          station = self.displayOptions.station,
                                          channel = channels2Load)
        print dir(stream)
        stream.detrend(type = 'constant')

        self.logger.debug("Finished loading data.")
        for curStation in self.displayOptions.station:
            myStation = self.viewPort.hasStation(curStation)
            if not myStation:
                # The station doesn't exist, create a new one.
                myStation = container.TdStation(parent=self.viewPort, id=wx.ID_ANY, name=curStation, color='white')
                self.viewPort.addStation(myStation)
                myStation.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)

            for m, curChannel in enumerate(self.displayOptions.channel[curStation]):
                myChannel = myStation.hasChannel(curChannel)
                if not myChannel:
                    curColor = self.displayOptions.channelColors[m]
                    myChannel = container.TdChannel(myStation, wx.ID_ANY, name=curChannel, color=curColor)
                    myStation.addChannel(myChannel)

                self.logger.debug("station: %s", curStation)
                self.logger.debug("channel: %s", curChannel)
                curStream = stream.select(station = curStation,
                                          channel = curChannel)

                myView = myChannel.hasView(myChannel)
                if not myView:
                    myView = container.TdSeismogramView(myChannel, wx.ID_ANY, name=myChannel, lineColor=curColor)

                    for curTrace in curStream:
                        self.logger.debug("Plotting trace:\n%s", curTrace)
                        start = time.clock()
                        myView.plot(curTrace)
                        myView.setXLimits(left = self.displayOptions.startTime.timestamp,
                                          right = self.displayOptions.endTime.timestamp)
                        myView.draw()
                        stop = time.clock()
                        self.logger.debug("Plotted data (%.5fs).", stop - start)
                    myChannel.addView(myView)

                    myChannel.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
                else:
                    for curTrace in curStream:
                        self.logger.debug("Plotting trace:\n%s", curTrace)
                        try:
                            myView.plot(curTrace)
                            myView.setXLimits(left = self.displayOptions.startTime.timestamp,
                                              right = self.displayOptions.endTime.timestamp)
                            myView.draw()
                        except Exception, err:
                            print err
                            pass




class ShortCutOptions:


    def __init__(self):
        ''' The constructor

        '''
        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)
        
        # A dictionary holding the actions bound to a certain key combination.
        # The key of the dictionary is a tuple of none or more modifiers keys 
        # and the pressed key.
        self.actions = {}


    def addAction(self, keyCombination, action):
        ''' Add an action to the shortcut options.

        Parameters
        ----------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        action : Method
            The method which should be executed when the key is pressed.

        '''
        self.actions[keyCombination] = action


    def getAction(self, keyCombination):
        ''' Get the action bound to the keyCombination.
        
        Paramters
        ---------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')
        
        Returns
        -------
        action : Method
            The method which should be executed when the key is pressed.
            None if no action is found.
        '''
        self.logger.debug("Searching for: %s", keyCombination)
        self.logger.debug("Available actions: %s", self.actions)
        return self.actions.get(keyCombination, None)


class DisplayOptions:


    def __init__(self):
        # The timespan to show.
        self.startTime = UTCDateTime('2010-08-31 07:57:00')
        self.endTime = UTCDateTime('2010-08-31 07:58:00')
        #self.endTime = UTCDateTime('2010-08-31 08:05:00')

        # The stations to show.
        #self.station = ['ALBA', 'BISA', 'GILA', 'GUWA', 'G_ALLA', 'G_GRUA',
        #           'G_JOAA', 'G_NAWA', 'G_PITA', 'G_RETA', 'G_SIGA', 
        #           'G_VEIA', 'G_VELA', 'G_WISA', 'MARA', 'SITA']
        self.station = ['ALBA', 'GILA', 'GUWA', 'G_ALLA', 'G_GRUA', 'G_JOAA', 'MARA', 'SITA', 'ALBA', 'G_NAWA']
        #self.station = ['ALBA', 'SITA', 'GILA']

        # The channels to show.
        self.channel = {}
        #self.channel['GILA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['GUWA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['G_ALLA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['G_GRUA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['ALBA'] = ['HHZ', 'HHN', 'HHE']
        #self.channel['SITA'] = ['HHZ', 'HHN', 'HHE']

        # Fill the channel automatically. 
        # This is just for testing.
        # This has to be changed to a user selectable value.
        for curStation in self.station:
            self.channel[curStation] = ['HHZ', 'HHN', 'HHE']

        # The trace color settings.
        clrList = wx.lib.colourdb.getColourInfoList()
        colorNames = ['TURQUOISE', 'CADETBLUE', 'SEAGREEN', 'GOLDENROD', 'SADDLEBROWN', 'VIOLETRED', 'BLUE4', 'LIGHTSKYBLUE4']
        self.channelColors = [tuple(x[1:4]) for x in clrList if x[0] in colorNames]


    def advanceTime(self):
        ''' Advance the time by one step.

        '''
        interval = self.endTime - self.startTime
        self.startTime = self.endTime
        self.endTime = self.startTime + interval


    def decreaseTime(self):
        ''' Decrease the time by one step.

        '''
        interval = self.endTime - self.startTime
        self.endTime = self.startTime
        self.startTime = self.startTime - interval

