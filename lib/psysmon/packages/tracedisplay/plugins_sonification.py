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
from psysmon.core.plugins import OptionPlugin, CommandPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.guiBricks as guiBricks
import psysmon.core.preferences_manager as preferences_manager
import threading
try:
    import pyo64 as pyo
except ImportError:
    import pyo

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
        self.pyo_server_started = False
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
        pref_item = preferences_manager.FloatSpinPrefItem(name = 'comp_mul', label = 'comp. makeup gain', value = 3, limit = [-100, 100])
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
                self.file_osc = pyo.Osc(self.file_table, freq = self.file_table.getRate())
                self.comp = pyo.Compress(self.file_osc, thresh = -30, ratio = 6, mul = 2, knee = 0.2, risetime = 0.1, falltime = 0.1)
                self.ind = 1
            else:
                self.file_table1 = pyo.SndTable(filename)
                self.file_osc1 = pyo.Osc(self.file_table1, freq = self.file_table1.getRate())
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

        self.is_running = False

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
        if self.is_running is False:
            self.init_display()
            print "##### after init_display"
            self.init_sound_table()
            print "##### after init_sound_table"
            self.play()
            print '---- end of run'
            self.is_running = True
        else:
            self.metro.stop()
            self.out.stop()
            self.is_running = False
            print '>>>> Set is_playing to FALSE'
            self.logger.debug('Stop playback. Set is_playing to FALSE.')

    def init_display(self):
        self.parent.setDuration(self.display_time)


    def init_sound_table(self):
        self.pos = 0
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
        #print stream.traces[0].data
        stream.traces[0].data = stream.traces[0].data / self.norm_factor
        #print stream.traces[0].data
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
        #print stream.traces[0].data
        data = stream.traces[0].data / self.norm_factor
        #print data
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

