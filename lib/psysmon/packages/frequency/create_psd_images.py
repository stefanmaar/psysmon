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
import shelve
import logging
import fnmatch
import re

import psysmon

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.gui.dialog.pref_listbook as psy_lb
    
from obspy.core.utcdatetime import UTCDateTime
import obspy.signal

# Set the matplotlib general settings.
#plt.style.use(['seaborn', 'seaborn-paper'])


class CreatePsdImagesNode(psysmon.core.packageNodes.CollectionNode):
    '''
    '''
    name = 'create PSD images'
    mode = 'editable'
    category = 'Frequency analysis'
    tags = ['development', 'power spectral density', 'image']

    def __init__(self, **args):
        psysmon.core.packageNodes.CollectionNode.__init__(self, **args)

        self.create_time_and_component_prefs()
        self.create_parameters_prefs()
        self.create_output_prefs()


    def create_time_and_component_prefs(self):
        ''' Create the preference items of the collection node.
        '''
        tc_page = self.pref_manager.add_page('select input')
        input_group = tc_page.add_group('input')
        tr_group = tc_page.add_group('time range')
        comp_group = tc_page.add_group('component selection')

        # The input data directory.
        pref_item = psy_pm.DirBrowsePrefItem(name = 'data_dir',
                                             label = 'psd data directory',
                                             value = '',
                                             tool_tip = 'Specify a directory where the PSD data files are located.')
        input_group.add_item(pref_item)

        # The start time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                                      label = 'start time',
                                                      value = UTCDateTime('2012-07-09T00:00:00'),
                                                      tool_tip = 'The start time of the interval to process.')
        tr_group.add_item(pref_item)

        # The end time
        pref_item = psy_pm.DateTimeEditPrefItem(name = 'end_time',
                                                      label = 'end time',
                                                      value = UTCDateTime('2012-07-09T00:00:00'),
                                                      tool_tip = 'The end time of the interval to process.')
        tr_group.add_item(pref_item)

        # The SCNL list
        pref_item = psy_pm.ListCtrlEditPrefItem(name = 'scnl_list',
                                           label = 'SCNL',
                                           value = [],
                                           column_labels = ['station', 'channel', 'network', 'location'],
                                           tool_tip = 'Select the components to process.'
                                          )
        comp_group.add_item(pref_item)


    def create_parameters_prefs(self):
        ''' Create the preference items of the parameters section.
        '''
        par_page = self.pref_manager.add_page('plot parameters')
        plot_group = par_page.add_group('plot')

        pref_item = psy_pm.SingleChoicePrefItem(name = 'plot_mode',
                                                label = 'plot mode',
                                                limit = ('free', 'daily', 'weekly', 'whole'),
                                                value = 'weekly',
                                                hooks = {'on_value_change': self.on_window_mode_selected},
                                                tool_tip = 'The mode of the plot window computation.')
        plot_group.add_item(pref_item)

        pref_item = psy_pm.IntegerSpinPrefItem(name = 'plot_length',
                                               label = 'plot length [seconds]',
                                               value = 86400,
                                               limit = [0, 1209600],
                                               tool_tip = 'The length of the plot in free mode in seconds.')
        plot_group.add_item(pref_item)

        pref_item = psy_pm.CheckBoxPrefItem(name = 'with_average_plot',
                                       label = 'with average plot',
                                       value = True,
                                       tool_tip = 'Add the temporal average with noise models to the PSD plot.')
        plot_group.add_item(pref_item)

        pref_item = psy_pm.FloatSpinPrefItem(name = 'lower_frequ',
                                               label = 'lower frequency [Hz]',
                                               value = 0.1,
                                               limit = [1e-6, 1e9],
                                               tool_tip = 'The lower frequency limit of the plot.')
        plot_group.add_item(pref_item)

        pref_item = psy_pm.CheckBoxPrefItem(name = 'use_upper_frequ',
                                            label = 'use upper frequency',
                                            value = False,
                                            tool_tip = 'Use the upper frequency value to set the upper frequency limit of the plot.',
                                            hooks = {'on_value_change': self.on_use_upper_frequ_changed})
        plot_group.add_item(pref_item)

        pref_item = psy_pm.FloatSpinPrefItem(name = 'upper_frequ',
                                               label = 'upper frequency [Hz]',
                                               value = 100,
                                               limit = [1e-6, 1e9],
                                               tool_tip = 'The upper frequency limit of the plot.')
        plot_group.add_item(pref_item)


    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        par_page = self.pref_manager.add_page('output')
        files_group = par_page.add_group('files')

        pref_item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                             label = 'output directory',
                                             value = '',
                                             tool_tip = 'Specify a directory where to save the PSD images.'
                                            )
        files_group.add_item(pref_item)

        
    def on_use_upper_frequ_changed(self):
        '''
        '''
        if self.pref_manager.get_value('use_upper_frequ'):
            item = self.pref_manager.get_item('upper_frequ')[0]
            item.enable_gui_element()
        else:
            item = self.pref_manager.get_item('upper_frequ')[0]
            item.disable_gui_element()

            
    def on_window_mode_selected(self):
        '''
        '''
        item = self.pref_manager.get_item('plot_length')[0]
        if self.pref_manager.get_value('plot_mode') == 'free':
            item.enable_gui_element()
        else:
            item.disable_gui_element()



    def edit(self):
        # Initialize the components
        if self.project.geometry_inventory:
            channels = sorted([x.scnl for x in self.project.geometry_inventory.get_channel()])
            self.pref_manager.set_limit('scnl_list', channels)
            
        dlg = psy_lb. ListbookPrefDialog(preferences = self.pref_manager)
        
        # Update the preference item gui elements based on the current
        # selections.
        self.on_window_mode_selected()
        self.on_use_upper_frequ_changed()
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        '''
        '''
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        plot_mode = self.pref_manager.get_value('plot_mode')
        lower_frequ = self.pref_manager.get_value('lower_frequ')
        use_upper_frequ = self.pref_manager.get_value('use_upper_frequ')
        if use_upper_frequ:
            upper_frequ = self.pref_manager.get_value('upper_frequ')
        else:
            upper_frequ = None

        if plot_mode == 'whole':
            plot_length = end_time - start_time
        elif plot_mode == 'free':
            plot_length = self.pref_manager.get_value('plot_length')
        elif plot_mode == 'daily':
            start_time = UTCDateTime(year = start_time.year,
                                     month = start_time.month,
                                     day = start_time.day)

            end_time = UTCDateTime(year = end_time.year,
                                   month = end_time.month,
                                   day = end_time.day)
            # If the start- and end day are equal, plot at least one day.
            if start_time == end_time:
                end_time = end_time + 86400
                
            plot_length = 86400
        elif plot_mode == 'weekly':
            start_time = UTCDateTime(start_time.year,
                                     start_time.month,
                                     start_time.day)
            start_time = start_time - start_time.weekday * 86400
            end_time = UTCDateTime(end_time.year,
                                   end_time.month,
                                   end_time.day)
            end_time = end_time + (7 - end_time.weekday) * 86400
            plot_length = 86400 * 7

        n_plots = int((end_time - start_time) / plot_length)
        if n_plots < 0:
            n_plots = 0
        plot_list = [start_time + x * plot_length for x in range(0, n_plots)]
        
        if plot_list[-1] == end_time:
            plot_list = plot_list[:-1]

        if plot_list[-1] + plot_length < end_time:
            plot_list.append(plot_list[-1] + plot_length)

        for k, cur_start in enumerate(plot_list):
            cur_end = cur_start + plot_length

            for cur_scnl in self.pref_manager.get_value('scnl_list'):
                self.logger.info("Plotting PSD for %s from %s to %s.", ':'.join(cur_scnl), cur_start.isoformat(), cur_end.isoformat())
                data_dir = self.pref_manager.get_value('data_dir')
                output_dir = self.pref_manager.get_value('output_dir')
                with_av_plot = self.pref_manager.get_value('with_average_plot')
                psd_plotter = PSDPlotter(station = cur_scnl[0],
                                         channel = cur_scnl[1],
                                         network = cur_scnl[2],
                                         location = cur_scnl[3],
                                         starttime = cur_start,
                                         endtime = cur_end,
                                         data_dir = data_dir,
                                         output_dir = output_dir,
                                         with_average_plot = with_av_plot,
                                         min_frequ = lower_frequ,
                                         max_frequ = upper_frequ,
                                         plot_mode = plot_mode)

                psd_plotter.plot()





class PSDPlotter(object):

    def __init__(self, station, channel, network, location,
                 data_dir, output_dir, starttime = None, endtime = None,
                 with_average_plot = False, min_frequ = 0.1, max_frequ = None,
                 plot_mode = None):
        ''' The constructor.

        '''
        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.station = station

        self.channel = channel

        self.network = network

        self.location = location

        self.data_dir = data_dir

        self.output_dir = output_dir

        self.starttime = starttime

        self.endtime = endtime

        self.with_average_plot = with_average_plot

        self.min_frequ = min_frequ

        self.max_frequ = max_frequ

        self.plot_mode = plot_mode


    def scan_for_files(self):
        ''' Scan for all files matching the unit, channel and stream in the data_dir.

        '''
        file_list = []
        for (path, dirs, files) in os.walk(self.data_dir):
            namefilter = 'psd_*%s_%s_%s_%s.db' % (self.station, self.channel, self.network, self.location)
            files = fnmatch.filter(files, namefilter)
            files = sorted(files)
            for cur_file in files:
                parts = re.split('_|\.', cur_file)

                cur_year = int(parts[1][:4])
                cur_month = int(parts[1][4:6])
                cur_day = int(parts[1][6:8])
                cur_date = UTCDateTime(year = cur_year, month = cur_month, day = cur_day)
                cur_station = parts[3]
                cur_channel = parts[4]
                cur_location = parts[5]
                cur_location = parts[6]

                if (cur_station.upper() == self.station.upper() and
                    cur_location == self.location and
                    cur_channel == self.channel and
                    (cur_date >= self.starttime and cur_date < self.endtime)):
                    file_list.append(os.path.join(path, cur_file))

        return sorted(file_list)


    def collect_psd_data(self, file_list):
        ''' Create the PSD data dictionary.
        '''
        psd_data = {}
        psd_data['meta'] = {}
        psd_data['data'] = {}
        psd_nfft = None
        psd_max_frequ = None
        window_length = None
        window_overlap = None
        for cur_file in file_list:
            cur_psd_data = {}
            self.logger.info('Reading file %s.', cur_file)
            db = shelve.open(cur_file)
            cur_psd_data.update(db)
            db.close()


            # Check the nfft value.
            nfft = list(set([x['psd_nfft'] for x in cur_psd_data.values()]))
            if len(nfft) != 1:
                self.logger.error('The nfft values of the PSDs are not equal: %s', nfft)
                continue
            else:
                nfft = nfft[0]

            if psd_nfft is None:
                # The first file determines the nfft value. All other files
                # must have the same nfft.
                psd_nfft = nfft
            elif nfft != psd_nfft:
                self.logger.error('The nfft (%d) differs from the initial nfft (%d). Skipping this PSD file.', nfft, psd_nfft)
                continue

            # Check the frequency array.
            max_frequ = list(set([x['frequ'][-1] for x in cur_psd_data.values()]))
            if len(max_frequ) != 1:
                self.logger.error("The maximum frequency value of the PSDs ar not equal: %s. Skipping this PSD file.", max_frequ)
                continue
            else:
                max_frequ = max_frequ[0]

            if psd_max_frequ is None:
                psd_max_frequ = max_frequ
            elif max_frequ != psd_max_frequ:
                self.logger.error("The maximum frequency value (%f) differs from the initial value (%f). Skipping this PSD file.", max_frequ, psd_max_frequ)
                continue


            # Check the window_length value.
            cur_window_length = list(set([x['window_length'] for x in cur_psd_data.values()]))
            if len(cur_window_length) != 1:
                self.logger.error('The window_length of the PSDs are not equal: %s. Skipping this PSD file.', cur_window_length)
                continue
            else:
                cur_window_length = cur_window_length[0]

            if window_length is None:
                window_length = cur_window_length
            elif cur_window_length != window_length:
                self.logger.error('The window_length (%d) differs from the initial window_length (%d). Skippin this PSD file.', cur_window_length, window_length)
                continue



            # Check the window_overlap.
            cur_window_overlap = list(set([x['window_overlap'] for x in cur_psd_data.values()]))
            if len(cur_window_overlap) != 1:
                self.logger.error('The window_overlap of the PSDs are not equal: %s. Skipping this PSD file.', cur_window_overlap)
                continue
            else:
                cur_window_overlap = cur_window_overlap[0]

            if window_overlap is None:
                window_overlap = cur_window_overlap
            elif cur_window_overlap != window_overlap:
                self.logger.error('The window_overlap (%d) differs from the initial window_overlap (%d). Skipping this PSD file.', cur_window_overlap, window_overlap)
                continue

            # All checks passed, update the dictionary.
            psd_data['data'].update(cur_psd_data)

        psd_data['meta']['overall_nfft'] = psd_nfft
        psd_data['meta']['overall_max_frequ'] = psd_max_frequ
        psd_data['meta']['overall_window_length'] = window_length
        psd_data['meta']['overall_window_overlap'] = window_overlap

        return psd_data

    def create_psd_array(self, psd_data):
        ''' Create a regular numpy array of the PSD data.
        '''
        window_length = psd_data['meta']['overall_window_length']
        psd_nfft = psd_data['meta']['overall_nfft']
        overlap = psd_data['meta']['overall_window_overlap'] / 100
        # The length of the gap between two successive data windows.
        win_limit = window_length * (1 - overlap)
        frequ = None
        time_key = sorted([x for x in psd_data['data'].keys()])

        if win_limit == 0:
            msg = "The overlap of the data window is 100%. " \
                  "Can't create the spectrogram plots with this data."
            self.logger.error(msg)
            raise RuntimeError(msg)

        # Find gaps in the data and add a time entry after each gap to create a
        # column in the PSD matrix that is filled with NaN values. This
        # prevents that the PSD column is extended to the next valid data
        # column.
        time = np.array([UTCDateTime(x) for x in time_key])
        dt = np.diff(time)
        gaps = dt > win_limit
        gap_times = time[:-1][gaps]
        n_gaps = dt[gaps] / win_limit
        gap_fill = [(x + win_limit * (y + 1)).isoformat() for (k, x) in enumerate(gap_times) for y in range(int(n_gaps[k]) - 1)]
        #time_key.extend([(x + window_length).isoformat() for x in gap_times])
        time_key.extend(gap_fill)
        time_key = sorted(time_key)

        # Create the PSD matrix used for plotting.
        psd_matrix = np.zeros((int(psd_nfft / 2 + 1), len(time_key)))
        psd_matrix[:] = np.nan

        for m, cur_psd in enumerate([psd_data['data'].get(x, None) for x in time_key]):
            if cur_psd is None:
                continue

            if cur_psd['frequ'] is not None:
                psd_matrix[:, m] = cur_psd['P']
                if frequ is None:
                    frequ = cur_psd['frequ']

        time = np.array([UTCDateTime(x) for x in time_key])
        time = time - self.starttime
        time = time.astype(float)

        return time, frequ, psd_matrix


    def plot(self):
        ''' Plot the psd data and save it to an file.
        '''
        # Get the files containing the PSD data.
        self.logger.info('Scanning for files in %s.', self.data_dir)
        file_list = self.scan_for_files()

        if len(file_list) == 0:
            self.logger.error('No files found.')
            return

        # Get the PSD data from the files.
        self.logger.debug('Preparing the PSD data.')
        psd_data = self.collect_psd_data(file_list = file_list)

        unit = [x['unit'] for x in psd_data['data'].values() if x['P'] is not None]
        unit = list(set(unit))

        if len(unit) == 0:
            self.logger.error('No unit specifier was found: %s. I set the unit to undefined.', unit)
            unit = 'undefined'
        if len(unit) == 1:
            unit = unit[0]
        else:
            self.logger.error('More than one unit specifier were found: %s. I set the unit to undefined.', unit)
            unit = 'undefined'

        # Create the regular PSD array.
        time, frequ, psd_matrix = self.create_psd_array(psd_data = psd_data)

        if frequ is None:
            # There was no valid data found at all. Don't create an image.
            self.logger.warning("No data found.")
            return

        # Plot the psd data to file.
        self.logger.info("Creating the images.")

        # Convert the time to hours.
        time = time / 3600.

        # Set the frequency limits of the plot.
        min_frequ = self.min_frequ
        if self.max_frequ is None:
            max_frequ = np.max(frequ)
        else:
            max_frequ = self.max_frequ

        psd_matrix = np.ma.masked_where(np.isnan(psd_matrix), psd_matrix)

        cur_scnl = (self.station, self.channel, self.network, self.location)
        dpi = 300.
        cm_to_inch = 2.54
        avg_width = 4 / cm_to_inch
        psd_min_width = 10 / cm_to_inch
        cb_width = 1 / cm_to_inch
        plot_length = self.endtime - self.starttime
        #width = (plot_length / (window_length * (1-window_overlap / 100))) * 3 / dpi
        #psd_width = old_div(len(time), dpi)
        psd_width = (plot_length / (np.median(np.diff(time)) * 3600)) / dpi
        if psd_width < psd_min_width:
            psd_width = psd_min_width

        height = 8 / cm_to_inch
        width = avg_width + psd_width + cb_width

        # TODO: Add the feature to specify the total width and height. This is
        # useful for preparing the plots for publication.
        #width = 16 / cm_to_inch
        #avg_width = 2 / cm_to_inch
        #cb_width = 1 / cm_to_inch

        # Font sizes.
        axes_label_size = 8
        tick_label_size = 6
        title_size = 8

        plt.style.use('classic')
        fig = plt.figure(figsize=(width, height), dpi = dpi)
        if self.with_average_plot:
            #gs = gridspec.GridSpec(1, 2,
            #                       width_ratios = [1, 4])
            #ax_avg = fig.add_subplot(gs[0, 0])
            #ax_psd = fig.add_subplot(gs[0, 1])

            ax_avg = fig.add_axes([0, 0.15, avg_width / width, 0.75])
            ax_psd = fig.add_axes([avg_width / width, 0.15, psd_width / width, 0.75])
            pos = ax_psd.get_position()
            ax_cb = fig.add_axes([pos.x1, 0.15, cb_width / width, 0.75])
            ax_avg.set_yscale('log')
            ax_avg.set_ylim((min_frequ, max_frequ))
        else:
            ax_psd = fig.add_axes([0.1, 0.15, psd_width / width, 0.75])
            pos = ax_psd.get_position()
            ax_cb = fig.add_axes([pos.x1 + 0.01, 0.15, cb_width / width, 0.75])


        ax_psd.set_yscale('log')
        ax_psd.set_ylim((min_frequ, max_frequ))
        ax_psd.set_xlim((0, (self.endtime - self.starttime) / 3600.))
        
        amp_resp = 10 * np.log10(np.abs(psd_matrix))
        if unit == 'm/s':
            self.logger.info("time: %s", time.dtype)
            self.logger.info("frequ: %s", frequ.dtype)
            self.logger.info("amp_resp: %s", amp_resp.dtype)
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp,
                                    vmin = -220,
                                    vmax = -80,
                                    cmap = 'viridis')
            unit_label = '(m/s)^2/Hz'
        elif unit == 'm/s^2':
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp,
                                    vmin = -220,
                                    vmax = -80,
                                    cmap = 'viridis')
            unit_label = '(m/s^2)^2/Hz'
        elif unit == 'counts':
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp,
                                    cmap = 'viridis')
            unit_label = 'counts^2/Hz'
        else:
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp,
                                    cmap = 'viridis')
            unit_label = '???^2/Hz'

        if self.with_average_plot:
            avg_amp_resp = np.mean(amp_resp, 1)
            med_amp_resp = np.median(amp_resp, 1)
            p_nhnm, nhnm = obspy.signal.spectral_estimation.get_nhnm()
            p_nlnm, nlnm = obspy.signal.spectral_estimation.get_nlnm()

            # obspy returns the NLNM and NHNM values in acceleration.
            # Convert them to the current unit (see Bormann (1998)).
            if unit == 'm':
                nhnm = nhnm + 40 * np.log10(p_nhnm / (2 * np.pi))
                nlnm = nlnm + 40 * np.log10(p_nlnm / (2 * np.pi))
            elif unit == 'm/s':
                nhnm = nhnm + 20 * np.log10(p_nhnm / (2 * np.pi))
                nlnm = nlnm + 20 * np.log10(p_nlnm / (2 * np.pi))
            elif unit != 'm/s^2':
                nhnm = None
                nlnm = None
                self.logger.error('The NLNM and NHNM is not available for the unit: %s.', unit)

            if nlnm is not None:
                ax_avg.plot(nlnm, 1 / p_nlnm,
                            color = 'lightgray')

            if nhnm is not None:
                ax_avg.plot(nhnm, 1 / p_nhnm,
                            color = 'lightgray')

            ax_avg.plot(avg_amp_resp, frequ,
                        color='saddlebrown',
                        label='avg')
            ax_avg.plot(med_amp_resp, frequ,
                        color='darkviolet',
                        label='med')

            ax_avg.set_xlim(pcm.get_clim())
            xlim = ax_avg.get_xlim()
            # xtick_labels = -np.arange(np.abs(xlim[1]), np.abs(xlim[0]), 50)
            xtick_labels = xlim
            ax_avg.set_xticks(xtick_labels)
            # ax_avg.set_xticks(xtick_labels.astype(np.int))
            # ax_avg.set_xticklabels(ax_avg.get_xticks(), rotation = 'vertical', va = 'top')
            ax_avg.set_xticklabels(ax_avg.get_xticks())
            ax_avg.invert_xaxis()
            ax_avg.set_xlabel('PSD [dB]', fontsize=axes_label_size)
            ax_avg.legend(loc='lower left', fontsize=tick_label_size)

        cb = fig.colorbar(pcm, cax = ax_cb)
        cb.set_label('PSD ' + unit_label + ' in dB',
                     fontsize = axes_label_size)
        cb.ax.tick_params(axis = 'both',
                          labelsize = tick_label_size)

        xlim = ax_psd.get_xlim()

        if plot_length <= 86400:
            tick_interval = 2
        elif plot_length <= 86400 * 7:
            tick_interval = 12
        else:
            tick_interval = 24
        xticks = np.arange(xlim[0], xlim[1], tick_interval)
        xticks = np.append(xticks, xlim[1])
        ax_psd.set_xticks(xticks)
        ax_psd.set_xlabel('Time since %s [h]' % self.starttime.isoformat(),
                          fontsize = axes_label_size)

        if self.with_average_plot:
            ax_avg.set_ylabel('Frequency [Hz]',
                              fontsize = axes_label_size)
            ax_avg.xaxis.tick_top()
            ax_avg.xaxis.set_ticks_position('both')
            ax_psd.yaxis.tick_right()
            ax_psd.yaxis.set_ticks_position('both')
        else:
            ax_psd.xaxis.set_ticks_position('both')
            ax_psd.yaxis.set_ticks_position('both')
            ax_psd.set_ylabel('Frequency [Hz]',
                              fontsize = axes_label_size)

        ax_psd.set_title('PSD %s %s' % (self.starttime.isoformat(), ':'.join(cur_scnl)), fontsize = title_size)

        # Customize the label appearance.
        ax_psd.tick_params(axis = 'both', labelsize = tick_label_size)
        if self.with_average_plot:
            ax_avg.tick_params(axis = 'both', labelsize = tick_label_size)

        # Rearrange the axes to include all labels.
        if self.with_average_plot:
            # Fix the average axes.
            bbox = ax_avg.yaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.transformed(fig.transFigure.inverted())
            pos = ax_avg.get_position()
            pos.x0 = pos.x0 + np.abs(bbox_i.x0)
            ax_avg.set_position(pos)

            # Reposition the avg x-axes label.
            bbox = ax_avg.xaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.transformed(ax_avg.transAxes.inverted())
            ax_avg.xaxis.set_label_coords(0.5, bbox_i.y1)


            # Shift the colorbar to the right of the psd axis labels.
            bbox = ax_psd.yaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.transformed(fig.transFigure.inverted())
            pos = cb.ax.get_position()
            pos.x0 = bbox_i.x1 + 0.25 / cm_to_inch / width
            pos.x1 = pos.x0 + 0.5 / cm_to_inch / width
            cb.ax.set_position(pos)

            # Change the right border of the psd plot to make space for the
            # colorbar.
            bbox = ax_cb.yaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.transformed(fig.transFigure.inverted())
            pos = ax_psd.get_position()
            pos.x1 = pos.x1 - (bbox_i.x1 - 1)
            ax_psd.set_position(pos)
            pos = ax_cb.get_position()
            pos.x0 = pos.x0 - (bbox_i.x1 - 1)
            pos.x1 = pos.x1 - (bbox_i.x1 - 1)
            ax_cb.set_position(pos)

            # TODO: Adjust the height of the axes as well to make shure, that
            # the axis ticks and labels and the figure title are shown.    

        plot_mode = self.plot_mode
        if not plot_mode:
            plot_mode = 'unknown'
        filename = '%s_%s_%s_%s_%s_%s_%s.png' % (plot_mode,
                                                 self.starttime.strftime('%Y%m%d'),
                                                 self.endtime.strftime('%Y%m%d'),
                                                 self.network, self.station,
                                                 self.location, self.channel)

        output_dir = os.path.join(self.output_dir,
                                  self.network,
                                  self.station,
                                  self.location)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = os.path.join(output_dir, filename)

        self.logger.info("Saving PSD image file ...")
        fig.savefig(filename, dpi=dpi)
        self.logger.info("Saved PSD image to file %s.", filename)
        fig.clear()
        plt.close(fig)
        del fig
