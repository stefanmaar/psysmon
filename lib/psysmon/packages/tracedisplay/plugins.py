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
import time
import numpy as np
from matplotlib.patches import Rectangle
from psysmon.core.plugins import OptionPlugin, AddonPlugin, InteractivePlugin, CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
from container import View
from obspy.core import UTCDateTime
import wx.lib.mixins.listctrl as listmix
from psysmon.core.gui import psyContextMenu
import psysmon.core.guiBricks as guiBricks
from obspy.imaging.spectrogram import spectrogram
import psysmon.core.preferences_manager as preferences_manager
import pyo64 as pyo
import threading



class SonificationPyoControl(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'pyo control',
                              group = 'sonification',
                              category = 'pyo',
                              tags = ['sonify', 'pyo', 'play', 'sound']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.cogs_icon_16

        # The pyo server mode.
        pref_item = preferences_manager.SingleChoicePrefItem(name = 'server_mode', label = 'mode', value = 'jack', limit = ['portaudio', 'jack', 'coreaudio', 'offline', 'offline_nb'])
        self.pref_manager.add_item(item = pref_item)
        self.dev_names, self.dev_indexes = pyo.pa_get_output_devices()
        dev_default = pyo.pa_get_default_output()
        pref_item = preferences_manager.SingleChoicePrefItem(name = 'audio_device', label = 'audio devices', value = self.dev_names[self.dev_indexes.index(dev_default)], limit = self.dev_names)
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.TextEditPrefItem(name = 'rec_wav_file', label = 'rec. filename', value = '')
        self.pref_manager.add_item(item = pref_item)

        self.pyo_server = None

        self.pyo_server_started = False

        self.is_recording = False



    def start_pyo_server(self):
        audio = self.pref_manager.get_value('server_mode')

        if self.pyo_server is None and not pyo.serverCreated():
            self.pyo_server = pyo.Server(audio = audio, duplex = 0)
            self.pyo_server.setVerbosity(15)
        else:
            self.pyo_server.stop()
            self.pyo_server.reinit(audio = audio)

        output_device = self.pref_manager.get_value('audio_device')
        output_index = self.dev_indexes[self.dev_names.index(output_device)]
        self.pyo_server.setInOutDevice(output_index)

        if audio == 'offline':
            self.pyo_server.recordOptions(dur=10)
        else:
            if not pyo.serverBooted():
                self.pyo_server.boot()
            self.pyo_server.start()
            self.pyo_server._server.setAmpCallable(self.vu_meter)

        # TODO: Change the icon to indicate that the server is running.

        #snd = pyo.SNDS_PATH + "/transparent.aif"
        #sf = pyo.SfPlayer(filename).mix(2).out()
        #a = pyo.Sine(mul=0.1).mix(2).out()
        #count = 0
        #while sf.isOutputting() and count < 10:
        #    self.logger.debug('isOutputting: %s; isPlaying: %s', sf.isOutputting(), sf.isPlaying())
        #    time.sleep(0.2)
        #    count += 1

        #time.sleep(2)

    def stop_pyo_server(self):
        ''' Stop the pyo server.

        '''
        self.pyo_server.stop()
        self.logger.debug('Stopped the pyo server.')


    def start_record_pyo_server(self):
        ''' Start the recording of the pyo server.
        '''
        if self.rec_wav_file == '':
            filename = None
        else:
            filename = self.rec_wav_file

        self.pyo_server.recordOptions(sampletype = 3)
        self.pyo_server.recstart(filename)
        self.is_recording = True



    def stop_record_pyo_server(self):
        ''' Start the recording of the pyo server.
        '''
        self.pyo_server.recstop()
        self.is_recording = False



    def buildFoldPanel(self, panel_bar):
        ''' Create the foldpanel GUI.

        '''
        import pyolib._wxwidgets

        fold_panel = wx.Panel(parent = panel_bar, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)
        pref_panel = guiBricks.PrefEditPanel(pref = self.pref_manager,
                                       parent = fold_panel)
        sizer.Add(pref_panel, 0, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_button = wx.Button(fold_panel, wx.ID_ANY, 'start server')
        button_sizer.Add(self.start_button, 0, flag = wx.EXPAND, border = 0)
        self.shutdown_button = wx.Button(fold_panel, wx.ID_ANY, 'shutdown server')
        button_sizer.Add(self.shutdown_button, 0, flag = wx.EXPAND, border = 0)
        self.record_button = wx.Button(fold_panel, wx.ID_ANY, 'rec. start')
        button_sizer.Add(self.record_button, 0, flag = wx.EXPAND, border = 0)
        sizer.Add(button_sizer, 0, flag =wx.TOP|wx.LEFT, border = 5)

        self.vu_meter = pyolib._wxwidgets.VuMeter(parent = fold_panel)
        sizer.Add(self.vu_meter, 0, flag = wx.TOP|wx.LEFT, border = 5)

        #server_gui = pyolib._wxwidgets.ServerGUI(parent = fold_panel)
        #sizer.Add(server_gui, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)

        fold_panel.Bind(wx.EVT_BUTTON, self.start_server_callback, self.start_button)
        fold_panel.Bind(wx.EVT_BUTTON, self.shutdown_server_callback, self.shutdown_button)
        fold_panel.Bind(wx.EVT_BUTTON, self.record_callback, self.record_button)

        fold_panel.SetSizer(sizer)

        return fold_panel


    def start_server_callback(self, evt):
        if self.pyo_server_started == False:
            #self.t = multiprocessing.Process(target = self.start_pyo_server)
            #self.t.start()
            self.start_pyo_server()
            self.pyo_server_started = True
            self.start_button.SetLabel('stop server')
            self.shutdown_button.Disable()
        else:
            self.stop_pyo_server()
            self.pyo_server_started = False
            self.start_button.SetLabel('start server')
            self.shutdown_button.Enable()


    def shutdown_server_callback(self, evt):
        if self.pyo_server.getIsStarted() == 1:
            self.stop_pyo_server()
            time.sleep(0.25)
        self.pyo_server.shutdown()


    def record_callback(self, evt):
        if self.is_recording == False:
            self.start_record_pyo_server()
            self.record_button.SetLabel('rec. stop')
        else:
            self.stop_record_pyo_server()
            self.record_button.SetLabel('rec. start')



class SonificationPlayPhaseVocoder(CommandPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        CommandPlugin.__init__(self,
                              name = 'phase vocoder',
                              group = 'sonification',
                              category = 'single',
                              tags = ['sonify', 'pyo', 'play', 'sound', 'vocoder']
                             )


        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.playback_play_icon_16

        # The pyo SfPlayer
        self.sf = None

        # The pyo output object.
        self.out = None

        # The pyo server mode.
        pref_item = preferences_manager.IntegerSpinPrefItem(name = 'pva_fft_size', label = 'fft size', value = 1024, limit = [4, 100000])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'pvs_shift', label = 'freq. shift', value = 0, limit = [-10000, 10000])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_thr', label = 'comp. thr', value = -24, limit = [-100, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_ratio', label = 'comp. ratio', value = 2, limit = [-100, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_mul', label = 'comp. makeup gain', value = 1, limit = [-100, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_knee', label = 'comp. knee', value = 0, limit = [0, 1])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_risetime', label = 'comp. rise-time', value = 0.01, limit = [0, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_falltime', label = 'comp. fall-time', value = 0.1, limit = [0, 100])
        self.pref_manager.add_item(item = pref_item)


    def run(self):
        import pyo64 as pyo
        import os

        pyo_control_plugin = [x for x in self.parent.plugins if x.name == 'pyo control']
        if len(pyo_control_plugin) == 1:
            pyo_control_plugin = pyo_control_plugin[0]
        else:
            return

        project = self.parent.project

        stream = self.parent.dataManager.procStream
        if len(stream.traces) != 1:
            self.logger.error('Only streams with 1 traces are supported.')
            return
        sps = stream.traces[0].stats.sampling_rate
        filename = os.path.join(project.tmpDir, 'test.wav')
        #stream.traces[0].data = stream.traces[0].data / np.log10(np.abs(stream.traces[0].data))
        stream.write(filename, format = 'WAV', framerate = sps, rescale = True)

        if pyo_control_plugin.server_mode == 'offline':
            pyo_server = pyo_control_plugin.pyo_server
            fileinfo = pyo.sndinfo(filename)
            length = fileinfo[1]
            pyo_server.recordOptions(dur = length)
            pyo_server.boot()

        #self.sine = pyo.Sine(440, mul=0.1).mix(2).out()
        if pyo.serverBooted():
            #self.snd = pyo.SfPlayer(pyo.SNDS_PATH + '/transparent.aif', loop = False).mix(2).out()
            self.sf = pyo.SfPlayer(filename, interp = 2)
            #log_comp = pyo.Log10(self.sf)
            pva = pyo.PVAnal(self.sf, self.pva_fft_size)
            pvt = pyo.PVShift(pva, self.pvs_shift)
            pvs = pyo.PVSynth(pvt)
            comp = pyo.Compress(pvs, thresh = self.comp_thr, ratio = self.comp_ratio,
                                mul = self.comp_mul, knee = self.comp_knee,
                                risetime = self.comp_risetime, falltime = self.comp_falltime)
            clip = pyo.Clip(comp)
            self.out = clip.mix(2).out()
        else:
            self.logger.error('No booted pyo server found.')

        if pyo_control_plugin.server_mode == 'offline':
            pyo_server.start()


class SonificationPlayTimeCompress(CommandPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        CommandPlugin.__init__(self,
                              name = 'play time compress',
                              group = 'sonification',
                              category = 'single',
                              tags = ['sonify', 'pyo', 'play', 'sound', 'loop']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.playback_stop_icon_16

        # The pyo SfPlayer
        self.sf = None

        # The pyo input fader (used for crossfading).
        self.fader = None

        # The pyo output object.
        self.out_loop = None
        self.out_single = None

        self.ind = 0

        # The compression factor
        pref_item = preferences_manager.IntegerSpinPrefItem(name = 'comp_factor', label = 'time comp.', value = 20, limit = (1, 1000))
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.CheckBoxPrefItem(name = 'loop_sound', label = 'loop', value = True)
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'fade_time', label = 'fade time [s]', value = 5, limit = (0, 1000))
        self.pref_manager.add_item(item = pref_item)


    def run(self):
        if self.loop_sound is True:
            self.play_loop()
        else:
            self.play_single()


    def play_loop(self):
        ''' Play the wav file in a loop using a soundtable.
        '''
        import os
        pyo_control_plugin = [x for x in self.parent.plugins if x.name == 'pyo control']
        if len(pyo_control_plugin) == 1:
            pyo_control_plugin = pyo_control_plugin[0]
        else:
            return

        project = self.parent.project

        stream = self.parent.dataManager.procStream
        if len(stream.traces) != 1:
            self.logger.error('Only streams with 1 traces are supported.')
            return
        sps = stream.traces[0].stats.sampling_rate
        filename = os.path.join(project.tmpDir, 'sptc_wav_%02d.wav' % self.ind)
        framerate = self.comp_factor * sps
        stream.write(filename, format = 'WAV', framerate = framerate, rescale = True)

        if pyo_control_plugin.server_mode == 'offline':
            pyo_server = pyo_control_plugin.pyo_server
            fileinfo = pyo.sndinfo(filename)
            length = fileinfo[1]
            pyo_server.recordOptions(dur = length)
            pyo_server.boot()

        if pyo.serverBooted():
            if self.ind == 0:
                self.file_table = pyo.SndTable(filename)
                self.file_osc = pyo.Osc(self.file_table, freq = -self.file_table.getRate())
                self.comp = pyo.Compress(self.file_osc, thresh = -30, ratio = 6, mul = 2, knee = 0.2, risetime = 0.1, falltime = 0.1)
                self.ind = 1
            else:
                self.file_table1 = pyo.SndTable(filename)
                self.file_osc1 = pyo.Osc(self.file_table1, freq = -self.file_table1.getRate())
                self.comp1 = pyo.Compress(self.file_osc1, thresh = -30, ratio = 6, mul = 2, knee = 0.2, risetime = 0.1, falltime = 0.1)
                self.ind = 0

            if self.fader is None:
                self.fader = pyo.InputFader(self.comp)
            else:
                self.logger.debug('Fading')
                if self.ind == 1:
                    self.fader.setInput(self.comp, fadetime = self.fade_time)
                else:
                    self.fader.setInput(self.comp1, fadetime = self.fade_time)

            if self.out_loop is None:
                self.out_loop = self.fader.mix(2).out()
        else:
            self.logger.error('No booted pyo server found.')

        if pyo_control_plugin.server_mode == 'offline':
            pyo_server.start()


    def play_single(self):
        ''' Play the sound file one time using sfplayer.
        '''
        import os

        pyo_control_plugin = [x for x in self.parent.plugins if x.name == 'pyo control']
        if len(pyo_control_plugin) == 1:
            pyo_control_plugin = pyo_control_plugin[0]
        else:
            return

        project = self.parent.project

        # Stop the output.
        if self.out_loop is not None:
            self.out_loop.stop()
        if self.out_single is not None:
            self.out_single.stop()

        stream = self.parent.dataManager.procStream
        if len(stream.traces) != 1:
            self.logger.error('Only streams with 1 traces are supported.')
            return
        sps = stream.traces[0].stats.sampling_rate
        filename = os.path.join(project.tmpDir, 'sptc_wav_%02d.wav' % self.ind)
        framerate = self.comp_factor * sps
        stream.write(filename, format = 'WAV', framerate = framerate, rescale = True)

        if pyo_control_plugin.server_mode == 'offline':
            pyo_server = pyo_control_plugin.pyo_server
            fileinfo = pyo.sndinfo(filename)
            length = fileinfo[1]
            pyo_server.recordOptions(dur = length)
            pyo_server.boot()

        if pyo.serverBooted():
            self.sf = pyo.SfPlayer(filename, interp = 2, loop = False)
            comp = pyo.Compress(self.sf, thresh = -30, ratio = 6, mul = 2, knee = 0.2, risetime = 0.1, falltime = 0.1)
            self.out_single = comp.mix(2).out()
        else:
            self.logger.error('No booted pyo server found.')

        if pyo_control_plugin.server_mode == 'offline':
            pyo_server.start()


class SonificationLooperTimeCompress(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'loop time compress',
                              group = 'sonification',
                              category = 'single',
                              tags = ['sonify', 'pyo', 'play', 'sound', 'loop']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.playback_next_icon_16

        # The pyo output object.
        self.out_loop = None

        # The pyo loopers.
        self.looper = [None, None]

        # The pyo compressor objects.
        #self.comp = [None, None]
        self.comp = None

        # The pyo input fader.
        self.fader = None

        # Indicate the runtime status of the looper.
        self.looper_started = False

        # The current looper index.
        self.looper_ind = 0

        # The compression factor
        pref_item = preferences_manager.IntegerSpinPrefItem(name = 'comp_factor', label = 'time comp.', value = 20, limit = (1, 1000))
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.SingleChoicePrefItem(name = 'loop_mode', label = 'loop mode', value = 'forward', limit = ['no loop', 'forward', 'backward', 'back-and-forth'])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'fade_time', label = 'fade time [s]', value = 5, limit = (0, 1000))
        self.pref_manager.add_item(item = pref_item)

        # The loop_mode translation.
        self.loop_mode_val = {'no loop': 0, 'forward': 1, 'backward': 2, 'back-and-forth': 3}


    def buildFoldPanel(self, panel_bar):
        ''' Create the foldpanel GUI.

        '''
        import pyolib._wxwidgets

        fold_panel = wx.Panel(parent = panel_bar, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)
        pref_panel = guiBricks.PrefEditPanel(pref = self.pref_manager,
                                       parent = fold_panel)
        sizer.Add(pref_panel, 0, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_looper_button = wx.Button(fold_panel, wx.ID_ANY, 'start')
        button_sizer.Add(self.start_looper_button, 0, flag = wx.EXPAND, border = 0)
        self.grab_sound_button = wx.Button(fold_panel, wx.ID_ANY, 'grab sound')
        button_sizer.Add(self.grab_sound_button, 0, flag = wx.EXPAND, border = 0)
        sizer.Add(button_sizer, 0, flag =wx.TOP|wx.LEFT, border = 5)
        self.grab_sound_button.Disable()

        self.vu_meter = pyolib._wxwidgets.VuMeter(parent = fold_panel)
        sizer.Add(self.vu_meter, 0, flag = wx.TOP|wx.LEFT, border = 5)


        fold_panel.Bind(wx.EVT_BUTTON, self.grab_sound_callback, self.grab_sound_button)
        fold_panel.Bind(wx.EVT_BUTTON, self.start_looper_callback, self.start_looper_button)

        fold_panel.SetSizer(sizer)

        return fold_panel


    def start_looper_callback(self, evt):
        if self.looper_started == False:
            self.start_looper()
            self.start_looper_button.SetLabel('stop')
            self.grab_sound_button.Enable()
        else:
            self.stop_looper()
            self.looper_started = False
            self.start_looper_button.SetLabel('start')
            self.grab_sound_button.Disable()


    def grab_sound_callback(self, evt):
        #self.load_sound()
        self.start_looper()


    def start_looper(self):
        ''' Play the wav file in a loop using a soundtable.
        '''
        if pyo.serverBooted():
            filename = self.seismo_to_wav()
            fileinfo = pyo.sndinfo(filename)
            dur = fileinfo[1]
            self.file_table = pyo.SndTable(filename)
            self.looper[self.looper_ind] = pyo.Looper(self.file_table, dur = dur, mode = self.loop_mode_val[self.loop_mode])
            #self.comp[self.looper_ind] = pyo.Compress(self.looper[self.looper_ind], thresh = -30, ratio = 6, mul = 2, knee = 0.2, risetime = 0.1, falltime = 0.1)
            if self.looper_started is False:
                #self.fader = pyo.InputFader(self.comp[self.looper_ind])
                self.comp = pyo.Compress(self.looper[self.looper_ind], thresh = -30, ratio = 6, mul = 2, knee = 0.2, risetime = 0.1, falltime = 0.1)
                self.out_loop = self.comp.mix(2).out()
            else:
                #self.fader.setInput(self.comp[self.looper_ind], fadetime = self.fade_time)
                self.comp.setInput(self.looper[self.looper_ind], fadetime = self.fade_time)

            if self.looper_ind == 0:
                self.looper_ind = 1
            else:
                self.looper_ind = 0
            self.looper_started = True
        else:
            self.logger.error('No booted pyo server found.')
            self.looper_started = False


    def seismo_to_wav(self):
        import os
        pyo_control_plugin = [x for x in self.parent.plugins if x.name == 'pyo control']
        if len(pyo_control_plugin) == 1:
            pyo_control_plugin = pyo_control_plugin[0]
        else:
            return

        project = self.parent.project

        stream = self.parent.dataManager.procStream
        if len(stream.traces) != 1:
            self.logger.error('Only streams with 1 traces are supported.')
            return
        sps = stream.traces[0].stats.sampling_rate
        filename = os.path.join(project.tmpDir, 'sltc_loop.wav')
        framerate = self.comp_factor * sps
        stream.write(filename, format = 'WAV', framerate = framerate, rescale = True)

        return filename


    def stop_looper(self):
        self.out_loop.stop()



class PyoServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def end(self):
        self._terminated = True

    def run(self):
        import pyo64 as pyo
        import time

        s = pyo.Server().boot()
        s.start()
        snd = pyo.SNDS_PATH + "/transparent.aif"
        sf = pyo.SfPlayer(snd)
        out = sf.mix(2).out() 
        tf = pyo.TrigFunc(sf['trig'], self.end)



class SonificationPlayParameterMapping(CommandPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        CommandPlugin.__init__(self,
                              name = 'play parameter mapping',
                              group = 'sonification',
                              category = 'single',
                              tags = ['sonify', 'pyo', 'play', 'parameter mapping']
                             )


        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.playback_prev_icon_16

        # The pyo SfPlayer
        self.noise = None

        # The pyo output object.
        self.out = None

        # The pyo server mode.
        #pref_item = preferences_manager.SingleChoicePrefItem(name = 'server_mode', label = 'mode', value = 'portaudio', limit = ['portaudio', 'jack'])
        #self.pref_manager.add_item(item = pref_item)


    def run(self):
        import pyo64 as pyo

        pyo_control_plugin = [x for x in self.parent.plugins if x.name == 'pyo control']
        if len(pyo_control_plugin) == 1:
            pyo_control_plugin = pyo_control_plugin[0]
        else:
            return

        project = self.parent.project

        stream = self.parent.dataManager.procStream
        if len(stream.traces) != 1:
            self.logger.error('Only streams with 1 traces are supported.')
            return
        sps = stream.traces[0].stats.sampling_rate

        if pyo.serverBooted():
            tr = stream.traces[0]
            noise_level = np.median(np.abs(tr.data))
            noise_level = noise_level / 1.0e-6
            if noise_level > 1:
                noise_level = 1

            self.logger.debug('noise_level: %s', noise_level)

            if self.noise is None:
                self.noise = pyo.BrownNoise(noise_level)
                self.out = self.noise.mix(2).out()
            else:
                self.noise.setMul(noise_level)

            fourier = np.fft.fft(tr.data)
            n = tr.data.size
            dt = 1/sps
            freq = np.fft.fftfreq(n, d = dt)
            abs_fourier = np.abs(fourier)
            f_max = freq(abs_fourier == np.max(abs_fourier))[0]
            self.logger.debug('f_max: %s', f_max)

        else:
            self.logger.error('No booted pyo server found.')



class AutoPlay(CommandPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        CommandPlugin.__init__(self,
                              name = 'autoplay',
                              group = 'sonification',
                              category = 'continuous',
                              tags = ['sonify', 'pyo', 'play', 'parameter mapping']
                             )


        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.playback_play_icon_16

        # Start and stop the plugin.
        self.keep_running = False

        # The pyo server mode.
        #pref_item = preferences_manager.SingleChoicePrefItem(name = 'server_mode', label = 'mode', value = 'portaudio', limit = ['portaudio', 'jack'])
        #self.pref_manager.add_item(item = pref_item)


    def run(self):
        if self.keep_running is False:
            self.t = threading.Thread(target = self.advance_time)
            self.t.start()
        else:
            self.keep_running = False


    def advance_time(self):
        import time

        audio_plugin = [x for x in self.parent.plugins if x.name == 'loop time compress']
        if len(audio_plugin) == 1:
            audio_plugin = audio_plugin[0]
        else:
            return

        audio_plugin.start_looper_button.SetLabel('stop')
        audio_plugin.grab_sound_button.Disable()

        self.keep_running = True
        audio_plugin.start_looper()
        interval = self.parent.displayManager.endTime - self.parent.displayManager.startTime
        time.sleep(interval)
        while self.keep_running:
            wx.CallAfter(self.parent.advanceTime)
            wx.CallAfter(audio_plugin.start_looper)
            interval = self.parent.displayManager.endTime - self.parent.displayManager.startTime
            self.logger.debug('waiting %f seconds ....', interval)
            time.sleep(interval)



class RealTimeAutoPlay(CommandPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        CommandPlugin.__init__(self,
                              name = 'realtime autoplay',
                              group = 'sonification',
                              category = 'continuous',
                              tags = ['sonify', 'pyo', 'play', 'parameter mapping']
                             )


        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The ribbonbar icon.
        self.icons['active'] = icons.playback_play_icon_16

        self.snd_table = None

        self.pos = 0

        self.last_sample = 0

        self.counter = 1

        # The period to display.
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'display_time', label = 'display time', value = 10, limit = [1, 300])
        self.pref_manager.add_item(item = pref_item)

        # The period to preload.
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'preload_time', label = 'preload time', value = 1, limit = [1, 300])
        self.pref_manager.add_item(item = pref_item)

        pref_item = preferences_manager.FloatSpinPrefItem(name = 'norm_factor', label = 'norm. factor', value = 1e-6, limit = [0, 100])
        self.pref_manager.add_item(item = pref_item)

        pref_item = preferences_manager.IntegerSpinPrefItem(name = 'pva_fft_size', label = 'fft size', value = 1024, limit = [4, 100000])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'pvs_shift', label = 'freq. shift', value = 100, limit = [-10000, 10000])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_thr', label = 'comp. thr', value = -24, limit = [-100, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_ratio', label = 'comp. ratio', value = 2, limit = [-100, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_mul', label = 'comp. makeup gain', value = 1, limit = [-100, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_knee', label = 'comp. knee', value = 0, limit = [0, 1])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_risetime', label = 'comp. rise-time', value = 0.01, limit = [0, 100])
        self.pref_manager.add_item(item = pref_item)
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_falltime', label = 'comp. fall-time', value = 0.1, limit = [0, 100])
        self.pref_manager.add_item(item = pref_item)



    def run(self):
        self.init_display()
        print "##### after init_display"
        self.init_sound_table()
        print "##### after init_sound_table"
        self.play()
        print '---- end of run'

    def init_display(self):
        self.parent.setDuration(self.display_time)


    def init_sound_table(self):
        stream = self.get_stream()
        filename = self.seismo_to_wav()
        self.snd_table = pyo.SndTable(filename)
        data = stream.traces[0].data / self.norm_factor
        for k,x in enumerate(data):
            self.snd_table.put(x, self.pos + k)


    def seismo_to_wav(self, time_span = None):
        import os
        pyo_control_plugin = [x for x in self.parent.plugins if x.name == 'pyo control']
        if len(pyo_control_plugin) == 1:
            pyo_control_plugin = pyo_control_plugin[0]
        else:
            return

        project = self.parent.project

        stream = self.get_stream(time_span = time_span)
        sps = stream.traces[0].stats.sampling_rate
        filename = os.path.join(project.tmpDir, 'srtap_soundfile.wav')
        framerate = sps
        print '#### seismo_to_wav'
        print stream.traces[0].data
        stream.traces[0].data = stream.traces[0].data / self.norm_factor
        print stream.traces[0].data
        self.last_sample = stream.traces[0].data[-1]
        stream.write(filename, format = 'WAV', framerate = framerate, rescale = False)

        return filename


    def get_stream(self, time_span = None):
        stream = self.parent.dataManager.procStream.copy()
        if len(stream.traces) != 1:
            self.logger.error('Only streams with 1 traces are supported.')
            return

        if time_span is not None:
            stream.trim(starttime = stream.traces[0].stats.endtime - self.preload_time)

        if stream.traces[0].stats.endtime == self.parent.displayManager.endTime:
            stream.traces[0].data = stream.traces[0].data[:-1]

        return stream


    def play(self):
        if pyo.serverBooted():
            self.osc = pyo.Osc(self.snd_table, freq = self.snd_table.getRate(), interp = 3)
            self.metro = pyo.Metro(time = self.preload_time)
            pva = pyo.PVAnal(self.osc, self.pva_fft_size)
            pvt = pyo.PVShift(pva, self.pvs_shift)
            pvs = pyo.PVSynth(pvt)
            self.comp = pyo.Compress(pvs, thresh = self.comp_thr, ratio = self.comp_ratio,
                                mul = self.comp_mul, knee = self.comp_knee,
                                risetime = self.comp_risetime, falltime = self.comp_falltime)
            self.clip = pyo.Clip(self.comp)
            #self.out = self.osc.mix(2).out()
            self.out = self.clip.mix(2).out()
            self.metro.play()
            # Wait a little bit to ignore the first metro trigger.
            time.sleep(0.1)
            self.trig_func = pyo.TrigFunc(self.metro, self.advance_time)
        else:
            self.logger.error('No booted pyo server found.')

    def advance_time(self):
        print '#### in advance_time'
        wx.CallAfter(self.parent.advanceTime, self.preload_time)
        wx.CallAfter(self.preload_data)
        print '#### leaving advance_time'

    def preload_data(self):
        print '#### in preload_data'
        #filename = self.seismo_to_wav()
        #self.snd_table.insert(filename, pos = self.pos)
        stream = self.get_stream(time_span = self.preload_time)
        print stream.traces[0].data
        data = stream.traces[0].data / self.norm_factor
        print data
        # data = data / np.max(np.abs(data))

        # Shift the data to match the last sample.
        print '#### last_sample: %f' % self.last_sample
        print '#### diff: %f' % (data[0] - self.last_sample)
        #data = data + (data[0] - self.last_sample)
        #self.last_sample = stream.traces[0].data[-1]

        self.logger.debug('data length: %d', len(data))
        for k,x in enumerate(data):
            self.snd_table.put(x, self.pos + k)

        self.pos = self.pos + len(data)
        if self.pos >= self.snd_table.getSize():
            self.pos = 0

        #self.snd_table.save('/home/stefan/tmp/test_'+str(self.counter)+'.wav', sampletype = 2)
        self.counter += 1
        self.logger.debug('table insert position: %f', self.pos)
        print "tablesize: %d" % self.snd_table.getSize()
        print "table dur: %d" % self.snd_table.getDur()
        print "osc freq: %f" % self.osc.freq
        print "snd_table rate: %f" % self.snd_table.getRate()
        print '#### leaving preload_data'



class SelectStation(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'select station',
                              category = 'view',
                              tags = ['station', 'view', 'select']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.pin_map_icon_16



    def buildFoldPanel(self, parent):
        self.logger.debug('Building the fold panel.')

        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)


        #button1 = wx.Button(foldPanel, wx.ID_ANY, "Collapse Me")

        # Create a checkbox list holding the station names.
        #sampleList = ['ALBA', 'SITA', 'GILA']
        displayedStations = [(x[0],x[2],x[3]) for x in self.parent.displayManager.getSCNL('show')]

        # Create a unique list containing SNL. Preserve the sort order.
        self.stationList = self.parent.displayManager.getSNL('available')

        stationListString = [":".join(x) for x in self.stationList]
        lb = wx.CheckListBox(parent = foldPanel,
                             id = wx.ID_ANY,
                             choices = stationListString)

        ind = [m for m,x in enumerate(self.stationList) if x in displayedStations]
        lb.SetChecked(ind)

        # Bind the events.
        lb.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, lb)

        sizer.Add(lb, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        foldPanel.SetSizer(sizer)

        # Save the listbox as a class attribute.
        self.lb = lb

        return foldPanel


    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.lb.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)
        self.logger.debug('stationList[%d]: %s', index, self.stationList[index])

        # Remove all entries with the selected station from the
        # showStations.
        if not self.lb.IsChecked(index):
            self.parent.displayManager.hideStation(self.stationList[index])
        else:
            self.parent.displayManager.showStation(self.stationList[index])





class SelectChannel(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''

        OptionPlugin.__init__(self,
                              name = 'select channel',
                              category = 'view',
                              tags = ['channel', 'view', 'select'],
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.pin_sq_right_icon_16



    def buildMenu(self):
        pass


    def buildFoldPanel(self, parent):
        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.channelList = sorted(self.parent.displayManager.availableChannels)

        lb = wx.CheckListBox(parent = foldPanel,
                             id = wx.ID_ANY,
                             choices = self.channelList)

        ind = [m for m,x in enumerate(self.channelList) if x in self.parent.displayManager.showChannels]
        lb.SetChecked(ind)

        # Bind the events.
        lb.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, lb)

        sizer.Add(lb, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        foldPanel.SetSizer(sizer)

        # Save the listbox as a class attribute.
        self.lb = lb

        foldPanel.SetMinSize(lb.GetBestSize())

        return foldPanel





    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.lb.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)
        self.logger.debug('channelList[%d]: %s', index, self.channelList[index])

        # Remove all entries with the selected station from the
        # showStations.
        if not self.lb.IsChecked(index):
            self.parent.displayManager.hideChannel(self.channelList[index])
        else:
            self.parent.displayManager.showChannel(self.channelList[index])



class ProcessingStack(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor

        '''

        OptionPlugin.__init__(self,
                              name = 'processing stack',
                              category = 'proc',
                              tags = ['process', 'data']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.layers_1_icon_16



    def buildFoldPanel(self, parent):
        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        self.processingStack = self.parent.dataManager.processingStack

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # Create the buttons to control the stack.
        addButton = wx.Button(foldPanel, wx.ID_ANY, "add")
        #font = addButton.GetFont()
        #font.SetPointSize(10)
        #addButton.SetFont(font)
        removeButton = wx.Button(foldPanel, wx.ID_ANY, "remove")
        #removeButton.SetFont(font)
        runButton = wx.Button(foldPanel, wx.ID_ANY, "run")
        #runButton.SetFont(font)

        # Fill the button sizer.
        buttonSizer.Add(addButton, 0, wx.ALL)
        buttonSizer.Add(removeButton, 0, wx.ALL)
        buttonSizer.Add(runButton, 0, wx.ALL)

        # Fill the nodes list with the nodes in the processing stack.
        nodeNames = [x.name for x in self.processingStack.nodes]
        isActive = [m for m,x in enumerate(self.processingStack) if x.isEnabled() == True]

        self.nodeListBox = wx.CheckListBox(parent = foldPanel,
                                           id = wx.ID_ANY,
                                           choices = nodeNames,
                                           size = (100, -1))
        self.nodeListBox.SetChecked(isActive)
        
        # By default select the first processing node.
        self.nodeListBox.SetSelection(0)
        self.nodeOptions = self.processingStack[0].getEditPanel(foldPanel)

        # Add the elements to the main sizer.
        sizer.Add(self.nodeListBox, pos=(0,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Add(buttonSizer, pos=(0,1), flag=wx.TOP|wx.BOTTOM, border=1)
        sizer.Add(self.nodeOptions, pos=(1,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)

        # Bind the events.
        foldPanel.Bind(wx.EVT_BUTTON, self.onRun, runButton)
        foldPanel.Bind(wx.EVT_BUTTON, self.onAdd, addButton)
        foldPanel.Bind(wx.EVT_LISTBOX, self.onNodeSelected, self.nodeListBox)
        foldPanel.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, self.nodeListBox)

        foldPanel.SetSizer(sizer)
       
        self.foldPanel = foldPanel

        return foldPanel


    def updateNodeList(self):
        self.nodeListBox.Clear()
        nodeNames = [x.name for x in self.processingStack.nodes]
        isActive = [m for m,x in enumerate(self.processingStack) if x.isEnabled() == True]
        self.nodeListBox.AppendItems(nodeNames)
        self.nodeListBox.SetChecked(isActive)



    def onRun(self, event):
        ''' Re-run the processing stack.
        '''
        self.parent.updateDisplay()


    def onAdd(self, event):
        ''' Add a processing node to the stack.

        Open a dialog field to select from the available processing nodes.
        '''
        dlg = PStackAddNodeDialog(parent = self.foldPanel, availableNodes = self.parent.processingNodes)
        val = dlg.ShowModal()

        if val == wx.ID_OK:
            node2Add = dlg.getSelection()
            self.processingStack.addNode(node2Add, self.nodeListBox.GetSelection()+1) 
            self.updateNodeList()

        dlg.Destroy()


    def onNodeSelected(self, event):
        index = event.GetSelection()
        #selectedNode = event.GetString()
        sizer = self.foldPanel.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()
        self.nodeOptions = self.processingStack[index].getEditPanel(self.foldPanel)
        sizer.Add(self.nodeOptions, pos=(1,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Layout() 



    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.nodeListBox.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)

        self.processingStack[index].toggleEnabled()





class SeismogramPlotter(AddonPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self): 
        ''' The constructor.

        '''
        AddonPlugin.__init__(self,
                             name = 'plot seismogram',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.waveform_icon_16


    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            curView = displayManager.getViewContainer(curChannel.getSCNL(), self.name)
            if stream:
                if curChannel.parent.location == '--':
                    cur_location = None
                else:
                    cur_location = curChannel.parent.location

                curStream = stream.select(station = curChannel.parent.name,
                                         channel = curChannel.name,
                                         network = curChannel.parent.network,
                                         location = cur_location)
            else:
                curStream = None

            if curStream:
                lineColor = [x/255.0 for x in curChannel.container.color]
                curView.plot(curStream, lineColor)

            curView.setXLimits(left = displayManager.startTime.timestamp,
                               right = displayManager.endTime.timestamp)
            curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return SeismogramView



class SeismogramView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.t0 = None
	self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None

        self.line = None



    def plot(self, stream, color):

        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray / trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                timeArray = np.ma.array(timeArray, mask=trace.data.mask)

            self.t0 = trace.stats.starttime

            if not self.line:
                self.line, = self.dataAxes.plot(timeArray, trace.data, color = color)
            else:
                self.line.set_xdata(timeArray)
                self.line.set_ydata(trace.data)

            self.dataAxes.set_frame_on(False)
            self.dataAxes.get_xaxis().set_visible(False)
            self.dataAxes.get_yaxis().set_visible(False)
            yLim = np.max(np.abs(trace.data))
            self.dataAxes.set_ylim(bottom = -yLim, top = yLim)
            self.logger.debug('yLim: %s', yLim)

        # Add the time scale bar.
        scaleLength = 10
        unitsPerPixel = (2*yLim) / self.dataAxes.get_window_extent().height
        scaleHeight = 3 * unitsPerPixel
        if self.scaleBar:
            self.scaleBar.remove()
        self.scaleBar = Rectangle((timeArray[-1] - scaleLength,
                                  -yLim+scaleHeight/2.0),
                                  width=scaleLength,
                                  height=scaleHeight,
                                  edgecolor = 'none',
                                  facecolor = '0.75')
        self.dataAxes.add_patch(self.scaleBar)
        #self.dataAxes.axvspan(timeArray[0], timeArray[0] + 10, facecolor='0.5', alpha=0.5)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.dataAxes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        #self.logger.debug('Set limits: %f, %f', left, right)
        self.dataAxes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.dataAxes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.dataAxes.get_window_extent().width
        return  width / float(timeRange)






class Zoom(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'zoom',
                                   category = 'view',
                                   tags = None
                                  )
        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.zoom_icon_16

        self.beginLine = {}
        self.endLine = {}
        self.bg = {}
        self.motionNotifyCid = []
        self.startTime = None
        self.endTime = None

        # Add the plugin preferences.
        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio', 
                                                       value = 20,
                                                       limit = (1, 99)
                                                      )
        self.pref_manager.add_item(item = item)


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.onButtonPress
        hooks['button_release_event'] = self.onButtonRelease

        return hooks



    def onButtonPress(self, event, dataManager=None, displayManager=None):
        self.logger.debug('onButtonPress - button: %s', str(event.button))
        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            # Use the right mouse button to zoom out.
            self.startTime = event.xdata
            ratio = self.pref_manager.get_value('zoom ratio')
            duration = displayManager.endTime - displayManager.startTime
            shrinkAmount = duration * ratio/100.0
            tmp = self.startTime
            self.startTime = tmp - shrinkAmount*2.0
            self.endTime = tmp + shrinkAmount*2.0
            displayManager.setTimeLimits(UTCDateTime(self.startTime),
                                         UTCDateTime(self.endTime))

            displayManager.parent.updateDisplay()
            return

        #self.logger.debug('dataManager: %s\ndisplayManager: %s', dataManager, displayManager)

        #print 'Clicked mouse:\nxdata=%f, ydata=%f' % (event.xdata, event.ydata)
        #print 'x=%f, y=%f' % (event.x, event.y)

        self.startTime = event.xdata
        self.endTime = event.xdata

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    #bg = curView.plotCanvas.canvas.copy_from_bbox(curView.dataAxes.bbox)
                    #curView.plotCanvas.canvas.restore_region(bg)

                    if curView in self.endLine.keys():
                        self.endLine[curView].set_visible(False)
                        curView.dataAxes.draw_artist(self.endLine[curView])


                    if curView in self.beginLine.keys():
                        self.beginLine[curView].set_xdata(event.xdata)
                    else:
                        self.beginLine[curView] = curView.dataAxes.axvline(x=event.xdata)

                    curView.plotCanvas.canvas.draw()

                    cid = curView.plotCanvas.canvas.mpl_connect('motion_notify_event', lambda evt, dataManager=dataManager, displayManager=displayManager, callback=self.onMouseMotion : callback(evt, dataManager, displayManager))
                    self.motionNotifyCid.append((curView.plotCanvas.canvas, cid))


    def onMouseMotion(self, event, dataManger=None, displayManager=None):
        self.logger.debug('mouse motion')
        self.logger.debug('x: %f', event.x)
        if event.inaxes is not None:
            self.logger.debug('xData: %f', event.xdata)
            self.endTime = event.xdata

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    if event.inaxes is None:
                        inv = curView.dataAxes.transData.inverted()
                        tmp = inv.transform((event.x, event.y))
                        self.logger.debug('xTrans: %f', tmp[0])
                        event.xdata = tmp[0]
                    canvas = curView.plotCanvas.canvas
                    if curView not in self.bg.keys():
                        self.bg[curView] = canvas.copy_from_bbox(curView.dataAxes.bbox)
                    canvas.restore_region(self.bg[curView])

                    if curView not in self.endLine.keys():
                        self.endLine[curView] = curView.dataAxes.axvline(x=event.xdata, animated=True)
                    else:
                        self.endLine[curView].set_xdata(event.xdata)
                        self.endLine[curView].set_visible(True)

                    curView.dataAxes.draw_artist(self.endLine[curView])
                    canvas.blit()



    def onButtonRelease(self, event, dataManager=None, displayManager=None):
        self.logger.debug('onButtonRelease')
        for canvas, cid in self.motionNotifyCid:
            canvas.mpl_disconnect(cid)

        self.motionNotifyCid = []
        self.bg = {}


        # Delete all begin- and end lines from the axes.
        for curView in self.beginLine.keys():
            if curView in self.beginLine.keys():
                curView.dataAxes.lines.remove(self.beginLine[curView])
            if curView in self.endLine.keys():
                curView.dataAxes.lines.remove(self.endLine[curView])

        self.beginLine = {}
        self.endLine = {}



        # Call the setTimeLimits of the displayManager.
        # The timebase of the plots is unixseconds.
        if self.startTime == self.endTime:
            # This was a single click with no drag.
            ratio = self.pref_manager.get_value('zoom ratio')
            duration = displayManager.endTime - displayManager.startTime
            shrinkAmount = duration * ratio/100.0
            tmp = self.startTime
            self.startTime = tmp - shrinkAmount/2.0
            self.endTime = tmp + shrinkAmount/2.0
        elif self.endTime < self.startTime:
            tmp = self.startTime
            self.startTime = self.endTime
            self.endTime = tmp

        displayManager.setTimeLimits(UTCDateTime(self.startTime),
                                     UTCDateTime(self.endTime))

        displayManager.parent.updateDisplay()





############## DEMO PLUGIN FOR VIEWS ##########################################

class DemoPlotter(AddonPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        AddonPlugin.__init__(self,
                             name = 'demo plotter',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.attention_icon_16


    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            curView = displayManager.getViewContainer(curChannel.getSCNL(), self.name)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

            if curStream:
                #lineColor = [x/255.0 for x in curChannel.container.color]
                curView.plot(curStream, [0.3, 0, 0])

            curView.setXLimits(left = displayManager.startTime.timestamp,
                               right = displayManager.endTime.timestamp)
            curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return DemoView



class DemoView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.t0 = None
	self.lineColor = [x/255.0 for x in lineColor]

        self.scaleBar = None

        self.line = None



    def plot(self, stream, color):


        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray * 1/trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                timeArray = np.ma.array(timeArray[:-1], mask=trace.data.mask)


            if not self.line:
                self.line, = self.dataAxes.plot(timeArray, trace.data * -1, color = color)
            else:
                self.line.set_xdata(timeArray)
                #self.line.set_ydata(trace.data * -1)
                self.line.set_ydata(trace.data / np.log10(np.abs(trace.data)))

            self.dataAxes.set_frame_on(False)
            self.dataAxes.get_xaxis().set_visible(False)
            self.dataAxes.get_yaxis().set_visible(False)
            yLim = np.max(np.abs(trace.data))
            self.dataAxes.set_ylim(bottom = -yLim, top = yLim)


        # Add the scale bar.
        scaleLength = 10
        unitsPerPixel = (2*yLim) / self.dataAxes.get_window_extent().height
        scaleHeight = 3 * unitsPerPixel
        if self.scaleBar:
            self.scaleBar.remove()
        self.scaleBar = Rectangle((timeArray[-1] - scaleLength,
                                  -yLim+scaleHeight/2.0),
                                  width=scaleLength,
                                  height=scaleHeight,
                                  edgecolor = 'none',
                                  facecolor = '0.75')
        self.dataAxes.add_patch(self.scaleBar)
        #self.dataAxes.axvspan(timeArray[0], timeArray[0] + 10, facecolor='0.5', alpha=0.5)


    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.dataAxes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.dataAxes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    def getScalePixels(self):
        yLim = self.dataAxes.get_xlim()
        timeRange = yLim[1] - yLim[0]
        width = self.dataAxes.get_window_extent().width
        return  width / float(timeRange)



class SpectrogramPlotter(AddonPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        AddonPlugin.__init__(self,
                             name = 'spectrogram plotter',
                             category = 'visualize',
                             tags = None
                            )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.twitter_icon_16


    def plot(self, displayManager, dataManager):
        ''' Plot all available stations.

        '''
        self.plotStation(displayManager, dataManager, displayManager.showStations)


    def plotStation(self, displayManager, dataManager, station):
        ''' Plot one or more stations.

        '''
        for curStation in station:
            self.plotChannel(displayManager, dataManager, curStation.channels)



    def plotChannel(self, displayManager, dataManager, channels):
        ''' Plot one or more channels.

        '''
        stream = dataManager.procStream

        for curChannel in channels:
            curView = displayManager.getViewContainer(curChannel.getSCNL(), self.name)
            curStream = stream.select(station = curChannel.parent.name,
                                     channel = curChannel.name,
                                     network = curChannel.parent.network,
                                     location = curChannel.parent.obspy_location)

            if curStream:
                #lineColor = [x/255.0 for x in curChannel.container.color]
                curView.plot(curStream, [0.3, 0, 0])

            curView.setXLimits(left = displayManager.startTime.timestamp,
                               right = displayManager.endTime.timestamp)
            curView.draw()




    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return SpectrogramView



class SpectrogramView(View):
    '''
    A standard seismogram view.

    Display the data as a timeseries.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None, lineColor=(1,0,0)):
        View.__init__(self, parent=parent, id=id, parentViewport=parentViewport, name=name)

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.t0 = None


    def plot(self, stream, color):


        for trace in stream:
            timeArray = np.arange(0, trace.stats.npts)
            timeArray = timeArray * 1/trace.stats.sampling_rate
            timeArray = timeArray + trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(trace.data):
                timeArray = np.ma.array(timeArray[:-1], mask=trace.data.mask)

            if self.dataAxes.images:
                self.dataAxes.images.pop()


            spectrogram(trace.data, 
                        samp_rate = trace.stats.sampling_rate,
                        axes = self.dataAxes)


            extent = self.dataAxes.images[0].get_extent()
            newExtent = (extent[0] + trace.stats.starttime.timestamp,
                         extent[1] + trace.stats.starttime.timestamp,
                         extent[2],
                         extent[3])
            self.dataAxes.images[0].set_extent(newExtent)
            self.dataAxes.set_frame_on(False)



    def setYLimits(self, bottom, top):
        ''' Set the limits of the y-axes.
        '''
        self.dataAxes.set_ylim(bottom = bottom, top = top)


    def setXLimits(self, left, right):
        ''' Set the limits of the x-axes.
        '''
        self.logger.debug('Set limits: %f, %f', left, right)
        self.dataAxes.set_xlim(left = left, right = right)

        # Adjust the scale bar.



    #def getScalePixels(self):
    #    yLim = self.dataAxes.get_xlim()
    #    timeRange = yLim[1] - yLim[0]
    #    width = self.dataAxes.get_window_extent().width
    #    return  width / float(timeRange)



class PStackAddNodeDialog(wx.Dialog):
    ''' Dialog to add a processing node to the stack.

    '''
    def __init__(self, parent=None, availableNodes = None, size = (200,400)):
        ''' The constructor.
        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Add a processing node", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=size)
        
        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Sizer to layout the gui elements.
        sizer = wx.GridBagSizer(5,5)
        btnSizer = wx.StdDialogButtonSizer()

        self.nodeInventoryPanel = PStackNodeInventoryPanel(parent = self, availableNodes = availableNodes)

        # Add the buttons to the button sizer. 
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        
        # Add the elements to the base sizer.        
        sizer.Add(self.nodeInventoryPanel, pos=(0,0), flag = wx.EXPAND|wx.ALL, border= 2)
        sizer.Add(btnSizer, pos=(1,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)


       
    def getSelection(self):
        return self.nodeInventoryPanel.selectedNode 




class PStackNodeInventoryPanel(wx.Panel, listmix.ColumnSorterMixin):

    def __init__(self, parent, availableNodes, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent = parent, id = id)

        self.availableNodes = availableNodes

        self.selectedNode = None
        
        self.itemDataMap = {}
    
        # Create the icons for column sorting.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        # The sizer used for the panel layout.
        sizer = wx.GridBagSizer(5, 5)
        
        # The search field to do search while typing.
        self.searchButton = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        self.searchButton.SetDescriptiveText('Search processing nodes')
        self.searchButton.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancelSearch, self.searchButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onDoSearch, self.searchButton)
        
        sizer.Add(self.searchButton, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)
        
        # The processing node listbox.
        self.nodeListCtrl = NodeListCtrl(self, id=wx.ID_ANY,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_SINGLE_SEL
                                 | wx.LC_SORT_ASCENDING
                                 )

        self.nodeListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


        columns = {1: 'name', 2: 'mode', 3: 'category', 4: 'tags'}

        for colNum, name in columns.iteritems():
            self.nodeListCtrl.InsertColumn(colNum, name)

        self.fillNodeList(self.availableNodes)

        sizer.Add(self.nodeListCtrl, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=0)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(1)

        self.SetSizerAndFit(sizer)
        
        # Bind the select item event to track the selected processing
        # node.
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onNodeItemSelected, self.nodeListCtrl)
   

    
    def onDoSearch(self, evt):
        foundNodes = self.searchNodes(self.searchButton.GetValue())
        self.updateNodeInvenotryList(foundNodes)
    
    
    def onCancelSearch(self, evt):
        self.fillNodeList(self.availableNodes)
        self.searchButton.SetValue(self.searchButton.GetDescriptiveText())
    
    
    def onNodeItemSelected(self, evt):
        nodeName = evt.GetItem().GetText()
        for curNode in self.availableNodes:
            if nodeName == curNode.name:
                self.selectedNode = curNode


    def searchNodes(self, searchString):
        ''' Find the processing nodes containing the *searchString* in their 
        name or their tags.

        
        Parameters
        ----------
        searchString : String
            The string to search for.


        Returns
        -------
        nodesFound : List of :class:`~psysmon.core.packageNodes.CollectionNode` instances.
            The nodes found matching the *searchString*.
        '''
        nodesFound = {}
        for curNode in self.availableNodes:
            if searchString in ','.join([curNode.name]+curNode.tags):
                nodesFound[curNode.name] = curNode

        return nodesFound



    def fillNodeList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates:
            self.nodeListCtrl.InsertStringItem(index, curNode.name)
            self.nodeListCtrl.SetStringItem(index, 1, curNode.mode)
            self.nodeListCtrl.SetStringItem(index, 2, curNode.category)
            self.nodeListCtrl.SetStringItem(index, 3, ', '.join(curNode.tags))
            self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
            self.nodeListCtrl.SetItemData(index, index)
            index += 1
    
    
    def updateNodeInvenotryList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates.itervalues():
            self.nodeListCtrl.InsertStringItem(index, curNode.name)
            self.nodeListCtrl.SetStringItem(index, 1, curNode.mode)
            self.nodeListCtrl.SetStringItem(index, 2, curNode.category)
            self.nodeListCtrl.SetStringItem(index, 3, ', '.join(curNode.tags))
            self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
            self.nodeListCtrl.SetItemData(index, index)
            index += 1
         


    def onCollectionNodeHelp(self, event):
        pass



class NodeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        cmData = (("help", parent.onCollectionNodeHelp),)

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)
