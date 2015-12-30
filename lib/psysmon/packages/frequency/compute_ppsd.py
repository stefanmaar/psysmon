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
from obspy.core.utcdatetime import UTCDateTime


class ComputePpsdNode(psysmon.core.packageNodes.CollectionNode):
    '''
    '''
    name = 'compute PPSD'
    mode = 'editable'
    category = 'Frequency analysis'
    tags = ['development', 'probability power spectral density']

    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        self.create_time_and_component_prefs()
        self.create_parameters_prefs()
        self.create_output_prefs()


    def create_time_and_component_prefs(self):
        ''' Create the preference items of the collection node.
        '''
        pagename = '1 time and components'
        self.pref_manager.add_page(pagename)

        # The start time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                                      label = 'start time',
                                                      value = UTCDateTime('2012-07-09T00:00:00'),
                                                      group = 'time range',
                                                      tool_tip = 'The start time of the interval to process.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        # The end time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                                      label = 'end time',
                                                      value = UTCDateTime('2012-07-09T00:00:00'),
                                                      group = 'time range',
                                                      tool_tip = 'The end time of the interval to process.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)

        # The SCNL list
        pref_item = psy_pm.ListCtrlEditPrefItem(name = 'scnl_list',
                                           label = 'SCNL',
                                           value = [],
                                           column_labels = ['station', 'channel', 'network', 'location'],
                                           group = 'component selection',
                                           tool_tip = 'Select the components to process.'
                                          )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


    def create_parameters_prefs(self):
        ''' Create the preference items of the parameters section.
        '''
        pagename = '2 parameters'
        self.pref_manager.add_page(pagename)

        pref_item = psy_pm.FloatSpinPrefItem(name = 'ppsd_length',
                                             label = 'ppsd length [s]',
                                             group = 'PPSD',
                                             value = 3600,
                                             limit = [0, 1e10],
                                             increment = 1,
                                             digits = 3,
                                             tool_tip = 'Length of data segments passed to psd [s].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


        pref_item = psy_pm.IntegerSpinPrefItem(name = 'ppsd_overlap',
                                             label = 'ppsd overlap [%]',
                                             group = 'PPSD',
                                             value = 50,
                                             limit = [0, 99],
                                             tool_tip = 'Overlap of segments passed to psd [%].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


        pref_item = psy_pm.SingleChoicePrefItem(name = 'plot_interval',
                                                label = 'plot interval',
                                                group = 'PPSD',
                                                limit = ('day', 'week', 'complete'),
                                                value = 'week',
                                                tool_tip = 'The length of the PPSD plots.')
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)


    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        pagename = '4 output'
        self.pref_manager.add_page(pagename)

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        group = 'output',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the PPSD files.'
                                       )
        self.pref_manager.add_item(pagename = pagename,
                                   item = item)




    def edit(self):
        # Initialize the components
        if self.project.geometry_inventory:
            channels = sorted([x.scnl for x in self.project.geometry_inventory.get_channel()])
            self.pref_manager.set_limit('scnl_list', channels)

        dlg = ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        '''
        '''
        ppsd_length = self.pref_manager.get_value('ppsd_length')
        ppsd_overlap = self.pref_manager.get_value('ppsd_overlap')
        plot_interval = self.pref_manager.get_value('plot_interval')
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')

        # Round the times to days.
        start_day = UTCDateTime(year = start_time.year,
                                month = start_time.month,
                                day = start_time.day)

        end_day = UTCDateTime(year = end_time.year,
                              month = end_time.month,
                              day = end_time.day)

        # Adjust the start- and end-day for the weekly interval
        if plot_interval == 'week':
            weekday = self.starttime.weekday
            start_day = start_day - weekday * 86400
            weekday = self.endtime.weekday
            end_day = end_day + (6 - weekday) * 86400


        end_day = end_day + 86400

        if plot_interval == 'day':
            days_between = (end_day - start_day) / 86400.
            start_day_list = [start_day + x*86400 for x in range(0, int(days_between))]
            plot_window_length = 86400
        elif plot_interval == 'week':
            weeks_between = (end_day - start_day) / (86400. * 7.)
            start_day_list = [start_day + x*86400*7 for x in range(0, int(weeks_between))]
            plot_window_length = 86400 * 7
        if plot_interval == 'complete':
            start_day_list = [start_day, ]
            plot_window_length = end_day - start_day


        for cur_start_day in start_day_list:
            cur_start_time = cur_start_day
            cur_end_time = cur_start_day + plot_window_length
            self.logger.info('Processing time interval: %s to %s.', cur_start_time.isoformat(),
                                                                    cur_end_time.isoformat())

            for cur_scnl in self.pref_manager.get_value('scnl_list'):
                self.logger.info('Processing SCNL %s.', cur_scnl)

                # Get the channel instance from the inventory.
                cur_channel = self.project.geometry_inventory.get_channel(station = cur_scnl[0],
                                                                          network = cur_scnl[2],
                                                                          location = cur_scnl[3],
                                                                          name = cur_scnl[1])
                if len(cur_channel) == 0:
                    self.logger.error("No channel found for scnl: %s", cur_scnl)
                    continue
                elif len(cur_channel) > 1:
                    self.logger.error("Multiple channels found for scnl: %s; channels: %s", cur_scnl, cur_channel)
                else:
                    cur_channel = cur_channel[0]

                # Get the recorder and sensor parameters.
                rec_stream_tb = cur_channel.get_stream(start_time = cur_start_time,
                                                       end_time = cur_end_time)

                rec_stream_param = []
                comp_param = []
                for cur_rec_stream_tb in rec_stream_tb:
                    cur_rec_stream = cur_rec_stream_tb.item
                    cur_rec_stream_param = cur_rec_stream.get_parameter(start_time = cur_start_time,
                                                                        end_time = cur_end_time)
                    rec_stream_param.extend(cur_rec_stream_param)

                    comp_tb = cur_rec_stream.get_component(start_time = cur_start_time,
                                                           end_time = cur_end_time)
                    for cur_comp_tb in comp_tb:
                        cur_comp = cur_comp_tb.item
                        cur_comp_param = cur_comp.get_parameter(start_time = cur_start_time,
                                                                end_time = cur_end_time)
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

                # Get the waveform data. Split the request into days to avoid
                # memory overload.
                days_between = (cur_end_time - cur_start_time) / 86400.
                process_days = [cur_start_time + x * 86400 for x in range(0, int(days_between))]
                cur_stream = obspy.core.Stream()
                for cur_process_day in process_days:
                    cur_process_end = cur_process_day + 86400
                    self.logger.info('Load data stream for time interval: %s to %s.',
                                     cur_process_day.isoformat(),
                                     cur_process_end.isoformat())

                    st = self.project.request_data_stream(start_time = cur_process_day,
                                                          end_time = cur_process_end,
                                                          scnl = [cur_scnl,])
                    st = st.copy()
                    cur_stream += st


                if not cur_stream:
                    self.logger.info('No data found for the given timespan.')
                    continue

                # Create the ppsd instance and add the stream.
                stats = cur_stream.traces[0].stats
                ppsd = obspy.signal.PPSD(stats, paz = paz, ppsd_length = ppsd_length);

                self.logger.info("Adding the stream to the ppsd.")
                ppsd.add(cur_stream)

                ppsd_id = ppsd.id.replace('.','_')
                output_dir = self.pref_manager.get_value('output_dir')
                image_filename = os.path.join(output_dir, 'images', 'ppsd_%s_%s_%s.png' % (ppsd_id, cur_start_time.isoformat().replace(':',''), cur_end_time.isoformat().replace(':','')))
                pkl_filename = os.path.join(output_dir, 'ppsd_objects', 'ppsd_%s_%s_%s.pkl.bz2' % (ppsd_id, cur_start_time.isoformat().replace(':',''), cur_end_time.isoformat().replace(':','')))

                self.logger.info("Saving image to file %s.", image_filename)
                if not os.path.exists(os.path.dirname(image_filename)):
                    os.makedirs(os.path.dirname(image_filename))
                ppsd.plot(filename = image_filename, period_lim = (1/250., 20))

                self.logger.info("Saving ppsd object to %s.", pkl_filename)
                if not os.path.exists(os.path.dirname(pkl_filename)):
                    os.makedirs(os.path.dirname(pkl_filename))
                ppsd.save(pkl_filename, compress = True)
