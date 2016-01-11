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

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from obspy.core.utcdatetime import UTCDateTime
import obspy.signal


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

        self.pref_manager.add_page(pagename)

        item = psy_pm.DirBrowsePrefItem(name = 'data_dir',
                                        label = 'psd data directory',
                                        group = 'parameters',
                                        value = '',
                                        tool_tip = 'Specify a directory where the PSD data files are located.'
                                       )
        self.pref_manager.add_item(pagename = pagename,
                                   item = item)


        pref_item = psy_pm.IntegerSpinPrefItem(name = 'plot_length',
                                             label = 'plot length [days]',
                                             group = 'parameters',
                                             value = 7,
                                             limit = [1, 365],
                                             tool_tip = 'The length of PSD plots [days].'
                                             )
        self.pref_manager.add_item(pagename = pagename,
                                   item = pref_item)



    def create_output_prefs(self):
        ''' Create the output preference items.
        '''
        pagename = '3 output'
        self.pref_manager.add_page(pagename)

        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        group = 'output',
                                        value = '',
                                        tool_tip = 'Specify a directory where to save the PSD images.'
                                       )
        self.pref_manager.add_item(pagename = pagename,
                                   item = item)

        item = psy_pm.CheckBoxPrefItem(name = 'with_average_plot',
                                       label = 'with average plot',
                                       group = 'output',
                                       value = False,
                                       tool_tip = 'Add the temporal average with noise models to the PSD plot.')
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
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        plot_length = self.pref_manager.get_value('plot_length')

        # Round the times to days.
        start_day = UTCDateTime(year = start_time.year,
                                month = start_time.month,
                                day = start_time.day)

        end_day = UTCDateTime(year = end_time.year,
                              month = end_time.month,
                              day = end_time.day)

        # If the start- and end day are equal, plot at least one day.
        if start_day == end_day:
            end_day = end_day + 86400

        # The length of the plot in seconds
        plot_length = plot_length * 86400
        plots_between = int((end_day - start_day) / plot_length)
        plot_list = [start_day + x * plot_length for x in range(plots_between+1)]

        if plot_list[-1] == end_day:
            plot_list = plot_list[:-1]

        if plot_list[-1] + plot_length < end_day:
            plot_list.append(plot_list[-1] + plot_length)

        for k, cur_start in enumerate(plot_list):
            cur_end = cur_start + plot_length

            for cur_scnl in self.pref_manager.get_value('scnl_list'):
                self.logger.info("Plotting PSD for %s from %s to %s.", ':'.join(cur_scnl), cur_start.isoformat(), cur_end.isoformat())
                psd_plotter = PSDPlotter(station = cur_scnl[0],
                                         channel = cur_scnl[1],
                                         network = cur_scnl[2],
                                         location = cur_scnl[3],
                                         starttime = cur_start,
                                         endtime = cur_end,
                                         data_dir = self.pref_manager.get_value('data_dir'),
                                         output_dir = self.pref_manager.get_value('output_dir'),
                                         with_average_plot = self.pref_manager.get_value('with_average_plot'))

                psd_plotter.plot()





class PSDPlotter:

    def __init__(self, station, channel, network, location, data_dir, output_dir, starttime = None, endtime = None, with_average_plot = False):
        ''' The constructor.

        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.station = station

        self.channel = channel

        self.network = network

        self.location = location

        self.data_dir = data_dir

	self.output_dir = output_dir

        self.starttime = starttime

        self.endtime = endtime

        self.with_average_plot = with_average_plot


    def scan_for_files(self):
        ''' Scan for all files matching the unit, channel and stream in the data_dir.

        '''
	file_list = []
        for (path, dirs, files) in os.walk(self.data_dir):
            namefilter = '*%s_%s_%s_%s.psd' % (self.station, self.channel, self.network, self.location)
            files = fnmatch.filter(files, namefilter)
            files = sorted(files)
            for cur_file in files:
                parts = re.split('_|\.', cur_file)

                cur_year = int(parts[0][:4])
                cur_month = int(parts[0][4:6])
                cur_day = int(parts[0][6:8])
                cur_date = UTCDateTime(year = cur_year, month = cur_month, day = cur_day)
                cur_station = parts[1]
                cur_channel = parts[2]
                cur_location = parts[3]
                cur_location = parts[4]

                if (cur_station.upper() == self.station.upper() and
                    cur_location == self.location and
                    cur_channel == self.channel and
                    (cur_date >= self.starttime and cur_date < self.endtime)):
                    file_list.append(os.path.join(path, cur_file))

        return sorted(file_list)


    def plot(self):
        ''' Plot the psd data and save it to an file.
        '''
        # Get the files containing the PSD data.
        self.logger.info('Scanning for files.')
        file_list = self.scan_for_files()

        if len(file_list) == 0:
            self.logger.error('No files found.')
            return

        self.logger.debug('Preparing the PSD data.')
        psd_data = {}
        psd_nfft = None
        window_length = None
        window_overlap = None
        for cur_file in file_list:
            self.logger.info('Reading file %s.', cur_file)
            db = shelve.open(cur_file)
            cur_psd_data = db['psd_data']
            db.close()


            # Check the nfft value.
            nfft = list(set([x['psd_nfft'] for x in cur_psd_data.itervalues()]))
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
                self.logger.error('The nfft (%d) differs from the initial nfft (%d).', nfft, psd_nfft)


            # Check the window_length value.
            cur_window_length = list(set([x['window_length'] for x in cur_psd_data.itervalues()]))
            if len(cur_window_length) != 1:
                self.logger.error('The window_length of the PSDs are not equal: %s', cur_window_length)
                continue
            else:
                cur_window_length = cur_window_length[0]

            if window_length is None:
                window_length = cur_window_length
            elif cur_window_length != window_length:
                self.logger.error('The window_length (%d) differs from the initial window_length (%d).', cur_window_length, window_length)



            # Check the window_overlap.
            cur_window_overlap = list(set([x['window_overlap'] for x in cur_psd_data.itervalues()]))
            if len(cur_window_overlap) != 1:
                self.logger.error('The window_overlap of the PSDs are not equal: %s', cur_window_overlap)
                continue
            else:
                cur_window_overlap = cur_window_overlap[0]

            if window_overlap is None:
                window_overlap = cur_window_overlap
            elif cur_window_overlap != window_overlap:
                self.logger.error('The window_overlap (%d) differs from the initial window_overlap (%d).', cur_window_overlap, window_overlap)

            # All checks passed, update the dictionary.
            psd_data.update(cur_psd_data)


        unit = [x['unit'] for x in psd_data.itervalues() if x['P'] is not None]
        unit = list(set(unit))

        if len(unit) == 0:
            self.logger.error('No unit specifier was found: %s. I set the unit to undefined.', unit)
            unit = 'undefined'
        if len(unit) == 1:
            unit = unit[0]
        else:
            self.logger.error('More than one unit specifier were found: %s. I set the unit to undefined.', unit)
            unit = 'undefined'

        # Plot the psd data to file.
        self.logger.info("Creating the images.")
        min_frequ = 0.1



        psd_matrix = np.zeros((psd_nfft/2. + 1, len(psd_data)))
        frequ = None
        time_key = sorted([x for x in psd_data.keys()])
        for m, cur_psd in enumerate([psd_data[x] for x in time_key]):
            if cur_psd['frequ'] is not None:
                psd_matrix[:,m] = cur_psd['P']
                if frequ is None:
                    frequ = cur_psd['frequ']

            else:
                psd_matrix[:,m] = np.nan

        if frequ is None:
            # There was no valid data found at all. Don't create an image.
            self.logger.warning("No data found.")
            return

        psd_matrix = np.ma.masked_where(np.isnan(psd_matrix), psd_matrix)

        #psd_matrix = psd_matrix[frequ >= min_frequ, :]

        time = np.array([UTCDateTime(x) for x in time_key])
        time = time - self.starttime
        time = time / 3600.

        cur_scnl = (self.station, self.channel, self.network, self.location)
        dpi = 300.
        cm_to_inch = 2.54
        avg_width = 4 / cm_to_inch
        psd_min_width = 10 / cm_to_inch
        cb_width = 2 / cm_to_inch
        plot_length = self.endtime - self.starttime
        #width = (plot_length / (window_length * (1-window_overlap / 100))) * 3 / dpi
        psd_width = len(time) / dpi
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
        tick_label_size = 8
        title_size = 10

        fig = plt.figure(figsize=(width, height), dpi = dpi)
        if self.with_average_plot:
            #gs = gridspec.GridSpec(1, 2,
            #                       width_ratios = [1, 4])
            #ax_avg = fig.add_subplot(gs[0, 0])
            #ax_psd = fig.add_subplot(gs[0, 1])

            ax_avg = fig.add_axes([0, 0.15, avg_width/width, 0.75])
            ax_psd = fig.add_axes([avg_width/width, 0.15, psd_width/width, 0.75])
            pos = ax_psd.get_position()
            ax_cb = fig.add_axes([pos.x1, 0.15, cb_width/width, 0.75])
            ax_avg.set_yscale('log')
            ax_avg.set_ylim((min_frequ, np.max(frequ)))
        else:
            ax_psd = fig.add_subplot(111)


        ax_psd.set_yscale('log')
        ax_psd.set_ylim((min_frequ, np.max(frequ)))
        ax_psd.set_xlim((0, (self.endtime - self.starttime)/3600.))
        amp_resp = 10 * np.log10(np.abs(psd_matrix))
        if unit == 'm/s':
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp, vmin = -220, vmax = -80)
            unit_label = '(m/s)^2/Hz'
        elif unit == 'm/s^2':
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp, vmin = -220, vmax = -80)
            unit_label = '(m/s^2)^2/Hz'
        elif unit == 'counts':
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp)
            unit_label = 'counts^2/Hz'
        else:
            pcm = ax_psd.pcolormesh(time, frequ, amp_resp)
            unit_label = '???^2/Hz'

        if self.with_average_plot:
            avg_amp_resp = np.mean(amp_resp, 1)
            med_amp_resp = np.median(amp_resp, 1)
            p_nhnm, nhnm = obspy.signal.spectral_estimation.get_NHNM()
            p_nlnm, nlnm = obspy.signal.spectral_estimation.get_NLNM()

            # obspy returns the NLNM and NHNM values in acceleration.
            # Convert them to the current unit (see Bormann (1998)).
            if unit == 'm':
                nhnm = nhnm + 40 * np.log10(p_nhnm/ (2 * np.pi))
                nlnm = nlnm + 40 * np.log10(p_nlnm/ (2 * np.pi))
            elif unit == 'm/s':
                nhnm = nhnm + 20 * np.log10(p_nhnm/ (2 * np.pi))
                nlnm = nlnm + 20 * np.log10(p_nlnm/ (2 * np.pi))
            elif unit != 'm/s^2':
                nhnm = None
                nlnm = None
                self.logger.error('The NLNM and NHNM is not available for the unit: %s.', unit)

            if nlnm is not None:
                ax_avg.plot(nlnm, 1/p_nlnm, color = 'lightgray')

            if nhnm is not None:
                ax_avg.plot(nhnm, 1/p_nhnm, color = 'lightgray')

            ax_avg.plot(avg_amp_resp, frequ, color = 'saddlebrown')
            ax_avg.plot(med_amp_resp, frequ, color = 'darkviolet')

            ax_avg.set_xlim(pcm.get_clim())
            xlim = ax_avg.get_xlim()
            #xtick_labels = -np.arange(np.abs(xlim[1]), np.abs(xlim[0]), 50)
            xtick_labels = xlim
            ax_avg.set_xticks(xtick_labels)
            #ax_avg.set_xticks(xtick_labels.astype(np.int))
            #ax_avg.set_xticklabels(ax_avg.get_xticks(), rotation = 'vertical', va = 'top')
            ax_avg.set_xticklabels(ax_avg.get_xticks())
            ax_avg.invert_xaxis()

        cb = fig.colorbar(pcm, ax = ax_psd, cax = ax_cb)
        cb.set_label('PSD ' + unit_label + ' in dB', fontsize = axes_label_size)
        cb.ax.tick_params(axis = 'both', labelsize = tick_label_size)

        xlim = ax_psd.get_xlim()

        if plot_length <= 86400:
            tick_interval = 2
        elif plot_length <= 86400 * 7:
            tick_interval = 12
        else:
            tick_interval = 24
        xticks = np.arange(xlim[0],xlim[1], tick_interval)
        xticks = np.append(xticks, xlim[1])
        ax_psd.set_xticks(xticks)
        ax_psd.set_xlabel('Time since %s [h]' % self.starttime.isoformat(), fontsize = axes_label_size)

        if self.with_average_plot:
            ax_avg.set_ylabel('Frequency [Hz]', fontsize = axes_label_size)
            ax_avg.xaxis.tick_top()
            ax_avg.xaxis.set_ticks_position('both')
            ax_psd.yaxis.tick_right()
            ax_psd.yaxis.set_ticks_position('both')
        else:
            ax_psd.set_ylabel('Frequency [Hz]', fontsize = axes_label_size)

        ax_psd.set_title('PSD %s %s' % (self.starttime.isoformat(), ':'.join(cur_scnl)), fontsize = title_size)

        # Customize the label appearance.
        ax_psd.tick_params(axis = 'both', labelsize = tick_label_size)
        if self.with_average_plot:
            ax_avg.tick_params(axis = 'both', labelsize = tick_label_size)

        # Rearrange the axes to include all labels.
        if self.with_average_plot:
            # Fix the average axes.
            bbox = ax_avg.yaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.inverse_transformed(fig.transFigure)
            pos = ax_avg.get_position()
            pos.x0 = pos.x0 + np.abs(bbox_i.x0)
            ax_avg.set_position(pos)

            # Shift the colorbar to the right of the psd axis labels.
            bbox = ax_psd.yaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.inverse_transformed(fig.transFigure)
            pos = cb.ax.get_position()
            pos.x0 = bbox_i.x1 + 0.25/cm_to_inch/width
            pos.x1 = pos.x0 + 0.5/cm_to_inch/width
            cb.ax.set_position(pos)

            # Change the right border of the psd plot to make space for the
            # colorbar.
            bbox = ax_cb.yaxis.get_tightbbox(fig.canvas.get_renderer())
            bbox_i = bbox.inverse_transformed(fig.transFigure)
            pos = ax_psd.get_position()
            pos.x1 = pos.x1 - (bbox_i.x1 - 1)
            ax_psd.set_position(pos)
            pos = ax_cb.get_position()
            pos.x0 = pos.x0 - (bbox_i.x1 - 1)
            pos.x1 = pos.x1 - (bbox_i.x1 - 1)
            ax_cb.set_position(pos)

            # TODO: Adjust the height of the axes as well to make shure, that
            # the axis ticks and labels and the figure title are shown.


        filename = '%s_%s_%s_%s_%s_%s.png' % (self.starttime.strftime('%Y%m%d'),
                                              self.endtime.strftime('%Y%m%d'),
                                              self.station, self.channel,
                                              self.network, self.location)
        filename = filename.lower()
        output_dir = os.path.join(self.output_dir, self.station.lower())
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        filename = os.path.join(output_dir, filename)

        self.logger.info("Saving PSD image file ...")
        fig.savefig(filename, dpi=dpi)
        self.logger.info("Saved PSD image to file %s.", filename)
        fig.clear()
        plt.close(fig)
        del fig

