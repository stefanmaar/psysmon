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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The importWaveform module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
import os

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog

import obspy.core

class ComputePpsdNode(psysmon.core.packageNodes.LooperCollectionChildNode):
    '''
    '''
    name = 'compute PPSD'
    mode = 'looper child'
    category = 'Frequency analysis'
    tags = ['stable', 'probability power spectral density']

    def __init__(self, **args):
        psysmon.core.packageNodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_parameters_prefs()
        self.create_output_prefs()


    def create_parameters_prefs(self):
        ''' Create the preference items of the parameters section.
        '''
        par_page = self.pref_manager.add_page('parameters')
        ppsd_group = par_page.add_group('ppsd')

        pref_item = psy_pm.FloatSpinPrefItem(name = 'ppsd_length',
                                             label = 'ppsd length [s]',
                                             value = 3600,
                                             limit = [0, 1e10],
                                             increment = 1,
                                             digits = 3,
                                             tool_tip = 'Length of data segments passed to psd [s].')
        ppsd_group.add_item(pref_item)


        pref_item = psy_pm.IntegerSpinPrefItem(name = 'ppsd_overlap',
                                             label = 'ppsd overlap [%]',
                                             value = 50,
                                             limit = [0, 99],
                                             tool_tip = 'Overlap of segments passed to psd [%].')
        ppsd_group.add_item(pref_item)


    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        out_page = self.pref_manager.add_page('output')
        out_group = out_page.add_group('output')

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the PPSD files.'
                                       )
        out_group.add_item(item)



    def edit(self):
        ''' Show the node edit dialog.
        '''
        dlg = ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None):
        '''
        '''
        ppsd_length = self.pref_manager.get_value('ppsd_length')
        ppsd_overlap = self.pref_manager.get_value('ppsd_overlap')

        start_time = process_limits[0]
        end_time = process_limits[1]


        self.logger.info('Processing time interval: %s to %s.', start_time.isoformat(),
                                                                end_time.isoformat())

        for cur_trace in stream:
            self.logger.info('Processing trace with id %s.', cur_trace.id)

            # Get the channel instance from the inventory.
            cur_channel = self.project.geometry_inventory.get_channel(station = cur_trace.stats.station,
                                                                      name = cur_trace.stats.channel,
                                                                      network = cur_trace.stats.network,
                                                                      location = cur_trace.stats.location)

            if len(cur_channel) == 0:
                self.logger.error("No channel found for trace %s", cur_trace.id)
                continue
            elif len(cur_channel) > 1:
                self.logger.error("Multiple channels found for trace %s; channels: %s", cur_trace.id, cur_channel)
            else:
                cur_channel = cur_channel[0]

            # Get the recorder and sensor parameters.
            rec_stream_tb = cur_channel.get_stream(start_time = start_time,
                                                   end_time = end_time)

            rec_stream_param = []
            comp_param = []
            for cur_rec_stream_tb in rec_stream_tb:
                cur_rec_stream = cur_rec_stream_tb.item
                cur_rec_stream_param = cur_rec_stream.get_parameter(start_time = start_time,
                                                                    end_time = end_time)
                rec_stream_param.extend(cur_rec_stream_param)

                comp_tb = cur_rec_stream.get_component(start_time = start_time,
                                                       end_time = end_time)
                for cur_comp_tb in comp_tb:
                    cur_comp = cur_comp_tb.item
                    cur_comp_param = cur_comp.get_parameter(start_time = start_time,
                                                            end_time = end_time)
                    comp_param.extend(cur_comp_param)

            if len(rec_stream_param) > 1 or len(comp_param) > 1:
                raise ValueError('There are more than one parameters for this component. This is not yet supported.')
            else:
                rec_stream_param = rec_stream_param[0]
                comp_param = comp_param[0]

            # Create the obspy PAZ dictionary.
            paz = {}
            paz['gain'] = 1
            paz['sensitivity'] = (rec_stream_param.gain * comp_param.sensitivity) / rec_stream_param.bitweight
            paz['poles'] = comp_param.tf_poles
            paz['zeros'] = comp_param.tf_zeros

            # Create the ppsd instance and add the stream.
            stats = cur_trace.stats
            ppsd = obspy.signal.PPSD(stats, paz = paz, ppsd_length = ppsd_length);

            self.logger.info("Adding the trace to the ppsd.")
            ppsd.add(cur_trace)

            ppsd_id = ppsd.id.replace('.','_')
            output_dir = self.pref_manager.get_value('output_dir')
            image_filename = os.path.join(output_dir, 'images', 'ppsd_%s_%s_%s.png' % (ppsd_id, start_time.isoformat().replace(':',''), end_time.isoformat().replace(':','')))
            pkl_filename = os.path.join(output_dir, 'ppsd_objects', 'ppsd_%s_%s_%s.pkl.bz2' % (ppsd_id, start_time.isoformat().replace(':',''), end_time.isoformat().replace(':','')))

            self.logger.info("Saving image to file %s.", image_filename)
            if not os.path.exists(os.path.dirname(image_filename)):
                os.makedirs(os.path.dirname(image_filename))
            ppsd.plot(filename = image_filename, period_lim = (1/250., 20))

            self.logger.info("Saving ppsd object to %s.", pkl_filename)
            if not os.path.exists(os.path.dirname(pkl_filename)):
                os.makedirs(os.path.dirname(pkl_filename))
            ppsd.save(pkl_filename, compress = True)
