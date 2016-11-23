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
import wx


import matplotlib as mpl
try:
    from matplotlib.backends.backend_wxagg import FigureCanvas
except:
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

import psysmon.core.plugins
import psysmon.artwork.icons as icons

class ParticleMotion(psysmon.core.plugins.InteractivePlugin):
    '''
    '''

    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        psysmon.core.plugins.InteractivePlugin.__init__(self,
                                                        name = 'particle motion',
                                                        category = 'analyze',
                                                        tags = None)

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.iconsBlack16.emotion_smile_icon_16
        self.cursor = wx.CURSOR_CROSS

        self.figure = None
        self.axes = {}
        self.start_time = None
        self.end_time = None


    def activate(self):
        ''' Activate the plugin.
        '''
        psysmon.core.plugins.InteractivePlugin.activate(self)
        # Create a frame holding the plot panel. A simple figure is not
        # working.
        self.frame = ParticleMotionFrame()
        self.frame.Show()

    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        psysmon.core.plugins.InteractivePlugin.deactivate(self)
        self.cleanup()


    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        self.frame.Destroy()


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.on_button_press
        #hooks['button_release_event'] = self.on_button_release

        return hooks


    def on_button_press(self, event, parent = None):
        ''' Handle the button press events.
        '''
        if event.inaxes is None:
            return

        viewport = parent

        cur_view = event.canvas.GetGrandParent()
        self.view = cur_view

        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # Skipt the right mouse button.
            return
        else:
            # Check for the required 3-component traces.
            pass

            # Call the plot_particle_motion method.

            # Register the motion_notify_event.
            #hook = {}
            #hook['motion_notify_event'] = self.plot_particle_motion
            #cur_view.set_mpl_event_callbacks(hook, parent = parent)


    def plot_particle_motion(self, event, parent):
        ''' Update the particle motion plot.
        '''
        pass




class ParticleMotionFrame(wx.Frame):
    '''
    '''

    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = 'particle motion', size = (600, 600), dpi = 300):
        ''' Initialize the instance.
        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # initialize matplotlib stuff
        self.figure = mpl.figure.Figure(None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.canvas.SetMinSize((30, 10))
        self.SetBackgroundColour('white')

	# Add the canvas to the sizer.
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
