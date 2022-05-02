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
from __future__ import division
import pdb
from builtins import range
from builtins import object
from past.utils import old_div
import os
import shelve
import logging
import fnmatch
import re

import psysmon

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
plt.style.use(psysmon.plot_style)

import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.gui.dialog.pref_listbook as psy_lb
from obspy.core.utcdatetime import UTCDateTime
import obspy.signal

# Set the matplotlib general settings.
plt.style.use(['seaborn', 'seaborn-paper'])


class CreatePpsdImagesNode(psysmon.core.packageNodes.CollectionNode):
    '''
    '''
    name = 'create PPSD images'
    mode = 'editable'
    category = 'Frequency analysis'
    tags = ['development', 'probabilistic power spectral density', 'image']

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


        pref_item = psy_pm.IntegerSpinPrefItem(name = 'plot_length',
                                             label = 'plot length [days]',
                                             value = 7,
                                             limit = [1, 365],
                                             tool_tip = 'The length of PSD plots [days].'
                                             )
        plot_group.add_item(pref_item)

        pref_item = psy_pm.CheckBoxPrefItem(name = 'with_average_plot',
                                       label = 'with average plot',
                                       value = False,
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


    def edit(self):
        # Initialize the components
        if self.project.geometry_inventory:
            channels = sorted([x.scnl for x in self.project.geometry_inventory.get_channel()])
            self.pref_manager.set_limit('scnl_list', channels)

        dlg = psy_lb. ListbookPrefDialog(preferences = self.pref_manager)
        self.on_use_upper_frequ_changed()
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        '''
        '''
        start_time = self.pref_manager.get_value('start_time')
        end_time = self.pref_manager.get_value('end_time')
        plot_length = self.pref_manager.get_value('plot_length')
        lower_frequ = self.pref_manager.get_value('lower_frequ')
        use_upper_frequ = self.pref_manager.get_value('use_upper_frequ')
        if use_upper_frequ:
            upper_frequ = self.pref_manager.get_value('upper_frequ')
        else:
            upper_frequ = None

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
        plots_between = int(old_div((end_day - start_day), plot_length))
        plot_list = [start_day + x * plot_length for x in range(plots_between+1)]

        if plot_list[-1] == end_day:
            plot_list = plot_list[:-1]

        if plot_list[-1] + plot_length < end_day:
            plot_list.append(plot_list[-1] + plot_length)

        for k, cur_start in enumerate(plot_list):
            cur_end = cur_start + plot_length

            for cur_scnl in self.pref_manager.get_value('scnl_list'):
                self.logger.info("Plotting PPSD for %s from %s to %s.", ':'.join(cur_scnl), cur_start.isoformat(), cur_end.isoformat())
                ppsd_plotter = PPSDPlotter(station = cur_scnl[0],
                                           channel = cur_scnl[1],
                                           network = cur_scnl[2],
                                           location = cur_scnl[3],
                                           starttime = cur_start,
                                           endtime = cur_end,
                                           data_dir = self.pref_manager.get_value('data_dir'),
                                           output_dir = self.pref_manager.get_value('output_dir'))
                ppsd_plotter.plot()





class PPSDPlotter(object):

    def __init__(self, station, channel, network, location,
                 data_dir, output_dir, starttime = None, endtime = None):
        ''' Initialize the instance.

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

        self.psd_nfft = None
        self.psd_unit = None
        self.psd_window_length = None
        self.psd_window_overlap = None

        self.plot_min_frequ = None
        self.plot_max_frequ = None

        self.ppsd = None
        self.ppsd_f = None
        self.ppsd_p = None


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


    def compute_ppsd(self):
        ''' Compute the PPSD data from PSD.

        '''
        # Get the files containing the PSD data.
        self.logger.info('Scanning for files in %s.', self.data_dir)
        file_list = self.scan_for_files()

        if len(file_list) == 0:
            self.logger.error('No files found.')
            return

        ppsd = None
        f_edges = np.logspace(np.log10(1e-3),
                              np.log10(400),
                              500)
        sps = 400
        nfft = 8192
        df = sps / (nfft / 2)
        # Don't use the zero frequency. This causes problems when using the
        # logarithm.
        f_edges = np.arange(df, 400, df)
        f_centers = f_edges[:-1] + np.diff(f_edges) / 2
        p_edges = np.linspace(0, 100, 101)
        # Load the psd data from each file.
        for cur_file in file_list:
            cur_psd_dict = self.load_psd(cur_file)
            if cur_psd_dict is None:
                self.logger.error('Data check failed. Skipping file %s.', cur_file)
                continue
            self.logger.info('Data check passed. Adding the data.')
            self.logger.debug('Processing %d PSDs with timestamps:\n%s.',
                              len(cur_psd_dict),
                              sorted(list(cur_psd_dict.keys())))

            # Binning of the data to a 2D histogram.
            for cur_psd_data in cur_psd_dict.values():
                cur_frequ = cur_psd_data['frequ']
                cur_psd = 10 * np.log10(cur_psd_data['P'])
                # interpolate the frequency to the bin values.
                cur_bin_psd = np.interp(f_centers, cur_frequ, cur_psd)
                hist, xedges, yedges = np.histogram2d(f_centers,
                                                      cur_bin_psd,
                                                      bins = (f_edges, p_edges))
                #hist, xedges, yedges = np.histogram2d(cur_frequ,
                #                                      cur_psd,
                #                                      bins = (f_edges, p_edges))
                hist = hist.T

                if ppsd is None:
                    ppsd = hist
                else:
                    ppsd += hist

        self.ppsd = ppsd
        self.ppsd_f = f_edges
        self.ppsd_p = p_edges



    def load_psd(self, filepath):
        ''' Load the PSD data from a file.
        '''
        cur_psd_data = {}
        self.logger.info('Reading file %s.', filepath)
        db = shelve.open(filepath)
        cur_psd_data.update(db)
        db.close()

        if self.check_psd_data(cur_psd_data):
            return cur_psd_data
        else:
            return None


    def check_psd_data(self, psd_data):
        ''' Check the consistency of the PSD data.
        '''
        is_consistent = True

        unit = [x['unit'] for x in psd_data.values() if x['P'] is not None]
        unit = list(set(unit))

        # Check the units of the psd.
        if len(unit) == 0:
            self.logger.error('No unit specifier was found: %s. Setting the unit to undefined.', unit)
            unit = 'undefined'
        if len(unit) == 1:
            unit = unit[0]
        else:
            self.logger.error('More than one unit specifier were found: %s. Skipping this PSD file.', unit)
            unit = 'undefined'
            is_consistent = False

        if self.psd_unit is None:
            self.psd_unit = unit
        elif unit != self.psd_unit:
            self.logger.error("The unit (%s) differs from the initial value (%s). Skipping this PSD file.", unit, self.psd_unit)
            is_consistent = False


        # TODO: How to handle PSDs with different nfft and window length?

        # All checks passed.
        return is_consistent


    def plot(self):
        ''' Plot the psd data and save it to an file.
        '''
        # Compute the PPSD data.
        self.logger.info('Computing the PPSD data.')
        self.compute_ppsd()

        # Plot the psd data to file.
        self.logger.info("Creating the images.")


        # Set the frequency limits of the plot.
        if self.plot_min_frequ is None:
            min_frequ = np.min(self.ppsd_f)
        else:
            min_frequ = self.plot_min_frequ

        if self.plot_max_frequ is None:
            max_frequ = np.max(self.ppsd_f)
        else:
            max_frequ = self.plot_max_frequ


        cur_scnl = (self.station, self.channel, self.network, self.location)

        # Compute the figure dimension
        cm_to_inch = 2.54
        dpi = 300
        psd_width = 12
        psd_height = 8
        cb_width = 1

        psd_width /= cm_to_inch
        psd_height /= cm_to_inch
        cb_width /= cm_to_inch

        width = psd_width + cb_width
        height = psd_height

        # Create the figure.
        fig = plt.figure(figsize = (width, height), dpi = dpi)

        # Font sizes.
        axes_label_size = 8
        tick_label_size = 6
        title_size = 8

        fig = plt.figure(figsize=(width, height), dpi = dpi)
        ax_psd = fig.add_axes([0.1, 0.15, psd_width / width, 0.75])
        pos = ax_psd.get_position()
        ax_cb = fig.add_axes([pos.x1 + 0.01, 0.15, cb_width / width, 0.75])

        ax_psd.set_xscale('log')
        ax_psd.set_xlim((min_frequ, max_frequ))
        if self.psd_unit == 'm/s':
            #pcm = ax_psd.pcolormesh(time, frequ, amp_resp, vmin = -220, vmax = -80, cmap = 'viridis')
            unit_label = '(m/s)^2/Hz'
        elif self.psd_unit == 'm/s^2':
            #pcm = ax_psd.pcolormesh(time, frequ, amp_resp, vmin = -220, vmax = -80, cmap = 'viridis')
            unit_label = '(m/s^2)^2/Hz'
        elif self.psd_unit == 'counts':
            pcm = ax_psd.pcolormesh(self.ppsd_f, self.ppsd_p, self.ppsd, cmap = 'viridis')
            unit_label = 'counts^2/Hz'
        else:
            #pcm = ax_psd.pcolormesh(time, frequ, amp_resp, cmap = 'viridis')
            unit_label = '???^2/Hz'

        cb = fig.colorbar(pcm, ax = ax_psd, cax = ax_cb)
        cb.set_label('probability [%]', fontsize = axes_label_size)
        cb.ax.tick_params(axis = 'both', labelsize = tick_label_size)

        xlim = ax_psd.get_xlim()

        ax_psd.set_xlabel('Frequency [Hz]', fontsize = axes_label_size)

        # TODO: Add the units label.
        ax_psd.set_ylabel('Power Spectral Density', fontsize = axes_label_size)

        ax_psd.set_title('PPSD %s %s' % (self.starttime.isoformat(), ':'.join(cur_scnl)), fontsize = title_size)

        # Customize the label appearance.
        ax_psd.tick_params(axis = 'both', labelsize = tick_label_size)


        # Save the plot to a file.
        filename = '%s_%s_%s_%s_%s_%s.png' % (self.starttime.strftime('%Y%m%d'),
                                              self.endtime.strftime('%Y%m%d'),
                                              self.network, self.station,
                                              self.location, self.channel)
        filename = filename.lower()
        output_dir = os.path.join(self.output_dir, self.network.lower(), self.station.lower(), self.location.lower())
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = os.path.join(output_dir, filename)

        self.logger.info("Saving PSD image file ...")
        fig.savefig(filename, dpi=dpi)
        self.logger.info("Saved PSD image to file %s.", filename)
        fig.clear()
        plt.close(fig)
        del fig

