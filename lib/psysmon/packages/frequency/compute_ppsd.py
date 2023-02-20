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
import copy
import os
import warnings

import psysmon
import psysmon.core.packageNodes
import psysmon.core.preferences_manager as psy_pm

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.gui.dialog.pref_listbook as psy_lb

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import obspy.core

plt.style.use(psysmon.plot_style)


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

        # The PPSD object.
        self.ppsd = None

        # The start and end times of the overall timespan used for the chunk
        # execution.
        self.overall_start_time = None
        self.overall_end_time = None


    @property
    def post_stream_length(self):
        ''' The time-span needed for correct processing prior to the start time
        of the stream passed to the execute method [s].
        '''
        ppsd_length = self.pref_manager.get_value('ppsd_length')
        overlap = self.pref_manager.get_value('ppsd_overlap')
        return ppsd_length * (overlap / 100.)


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
        img_group = out_page.add_group('image')

        item = psy_pm.FloatSpinPrefItem(name = 'img_width',
                                        label = 'width [cm]',
                                        value = 16.,
                                        increment = 1,
                                        digits = 1,
                                        limit = [1, 1000],
                                        tool_tip = 'The width of the PPSD image in cm.')
        img_group.add_item(item)

        item = psy_pm.FloatSpinPrefItem(name = 'img_height',
                                        label = 'height [cm]',
                                        value = 12.,
                                        increment = 1,
                                        digits = 1,
                                        limit = [1, 1000],
                                        tool_tip = 'The height of the PPSD image in cm.')
        img_group.add_item(item)

        item = psy_pm.IntegerSpinPrefItem(name = 'img_resolution',
                                          label = 'resolution [dpi]',
                                          value = 300.,
                                          limit = [1, 10000],
                                          tool_tip = 'The resolution of the PPSD image in dpi.')
        img_group.add_item(item)

    def edit(self):
        ''' Show the node edit dialog.
        '''
        dlg = psy_lb. ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()
        

    def make_output_dir(self, base_dir):
        ''' Build the output directory.
        '''
        output_dir = os.path.join(base_dir, 'ppsd')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        return output_dir


    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        '''
        '''
        start_time = process_limits[0]
        end_time = process_limits[1]
        output_dir = self.make_output_dir(base_dir = kwargs['output_dir'])

        self.logger.info('Processing time interval: %s to %s.', start_time.isoformat(),
                                                                end_time.isoformat())

        for cur_trace in stream:
            self.logger.info('Processing trace with id %s.', cur_trace.id)

            self.overall_start_time = start_time
            self.overall_end_time = end_time

            self.initialize_ppsd(cur_trace, start_time, end_time)

            self.logger.info("Adding the trace to the ppsd.")
            try:
                self.ppsd.add(cur_trace)
            except Exception:
                self.logger.exception("Error when adding the trace %s.", cur_trace)
            self.logger.info("Time limits of PPSD used times: %s to %s.", self.ppsd.current_times_used[0].isoformat(),
                                                                          self.ppsd.current_times_used[-1].isoformat())

            self.save_ppsd(output_dir = output_dir)


    def execute_chunked(self, chunk_count, total_chunks, stream,
                        process_limits = None, origin_resource = None, **kwargs):
        '''
        '''
        start_time = process_limits[0]
        end_time = process_limits[1]
        output_dir = self.make_output_dir(base_dir = kwargs['output_dir'])

        self.logger.info('Processing chunk %d/%d with time interval: %s to %s.', chunk_count, total_chunks,
                         start_time.isoformat(),
                         end_time.isoformat())
        for cur_trace in stream:
            self.logger.info('Processing trace with id %s.', cur_trace.id)

            if self.ppsd is None:
                # Initialize the PPSD.
                self.initialize_ppsd(cur_trace, start_time, end_time)
                self.overall_start_time = start_time
            if chunk_count == total_chunks:
                # Don't use the data past the intended end time.
                cur_trace = cur_trace.trim(starttime = start_time,
                                           endtime = end_time)
                self.overall_end_time = end_time

            self.logger.info("Adding the trace to the ppsd.")
            try:
                self.ppsd.add(cur_trace)
                self.logger.info("Time limits of PPSD used times: %s to %s.", self.ppsd.current_times_used[0].isoformat(),
                                 self.ppsd.current_times_used[-1].isoformat())
            except Exception:
                self.logger.warning("No PPSD data accumulated.")

        if chunk_count == total_chunks:
            self.overall_end_time = end_time
            self.save_ppsd(output_dir = output_dir)



    def initialize_ppsd(self, trace, start_time, end_time):
        ''' Initialize the PPSD.
        '''
        super(ComputePpsdNode, self).initialize()

        ppsd_length = self.pref_manager.get_value('ppsd_length')
        ppsd_overlap = self.pref_manager.get_value('ppsd_overlap') / 100.

        # Get the channel instance from the inventory.
        cur_channel = self.project.geometry_inventory.get_channel(station = trace.stats.station,
                                                                  name = trace.stats.channel,
                                                                  network = trace.stats.network,
                                                                  location = trace.stats.location)

        if len(cur_channel) == 0:
            self.logger.error("No channel found for trace %s. Can't initialize the PPSD object.", trace.id)
            raise RuntimeError("No channel found for trace %s. Can't initialize the PPSD object." % trace.id)
        elif len(cur_channel) > 1:
            self.logger.error("Multiple channels found for trace %s; channels: %s", trace.id, cur_channel)
            raise RuntimeError("Multiple channels found for trace %s; channels: %s. Can't initialize the PPSD object." % (trace.id, cur_channel))
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
        paz['gain'] = comp_param.tf_normalization_factor
        #paz['sensitivity'] = old_div((rec_stream_param.gain * comp_param.sensitivity), rec_stream_param.bitweight)
        paz['sensitivity'] = 1
        paz['poles'] = comp_param.tf_poles
        paz['zeros'] = comp_param.tf_zeros

        # Create the ppsd instance and add the stream.
        stats = trace.stats

        # Monkey patch the PPSD plot method.
        obspy.signal.PPSD.plot = ppsd_plot

        # TODO: Make the db_bins argument user-selectable. 
        # db_bins = (-200, -20, 1.)
        self.ppsd = obspy.signal.PPSD(stats,
                                      metadata = paz,
                                      ppsd_length = ppsd_length,
                                      overlap = ppsd_overlap)


    def save_ppsd(self, output_dir):
        '''
        '''
        ppsd_id = self.ppsd.id.replace('.', '_')
        start_string = self.overall_start_time.isoformat().replace(':', '')
        end_string = self.overall_end_time.isoformat().replace(':', '')

        # Add the station name and channel to the output directory.
        img_output_dir = os.path.join(output_dir,
                                      'images',
                                      self.ppsd.station,
                                      self.ppsd.channel)
        if not os.path.exists(img_output_dir):
            os.makedirs(img_output_dir)

        data_output_dir = os.path.join(output_dir,
                                       'ppsd_objects',
                                       self.ppsd.station,
                                       self.ppsd.channel)
        if not os.path.exists(data_output_dir):
            os.makedirs(data_output_dir)

        # Create the output filenames.
        filename = 'ppsd_%s_%s_%s.png' % (ppsd_id,
                                          start_string,
                                          end_string)
        image_filename = os.path.join(img_output_dir,
                                      filename)
        filename = 'ppsd_%s_%s_%s.pkl.npz' % (ppsd_id,
                                              end_string,
                                              end_string)
        npz_filename = os.path.join(data_output_dir,
                                    filename)

        # Set the viridis colomap 0 value to fully transparent white.
        cmap = plt.get_cmap('viridis')
        cmap = copy.copy(cmap)
        cmap.colors = np.array(cmap.colors)
        cmap.colors = np.hstack([cmap.colors, np.ones(cmap.N)[:, np.newaxis]])
        cmap.colors[0] = np.array([1, 1, 1, 0])
        cmap.colors = list(cmap.colors)

        # TODO: make the period limit user selectable
        width = self.pref_manager.get_value('img_width') / 2.54
        height = self.pref_manager.get_value('img_height') / 2.54
        dpi = self.pref_manager.get_value('img_resolution')
        fig = plt.figure(figsize = (width, height), dpi = dpi)
        try:
            fig = self.ppsd.plot(period_lim = (1/1000., 10),
                                 xaxis_frequency = True,
                                 cmap = cmap,
                                 show = False,
                                 show_coverage = True,
                                 fig = fig)
        except Exception:
            self.logger.error("Couldn't create the PPSD figure. Maybe there was no data accumulated.")

        try:
            self.logger.info("Saving image to file %s.", image_filename)
            if not os.path.exists(os.path.dirname(image_filename)):
                os.makedirs(os.path.dirname(image_filename))
            fig.savefig(image_filename, dpi = dpi)
        except Exception:
            self.logger.error("Couldn't save the PPSD.")

        try:
            self.logger.info("Saving ppsd object to %s.", npz_filename)
            if not os.path.exists(os.path.dirname(npz_filename)):
                os.makedirs(os.path.dirname(npz_filename))
            self.ppsd.save_npz(npz_filename)
        except Exception:
            self.logger.error("Couldn't save the PPSD data file.")

        # Delete the figure.
        fig.clear()
        plt.close(fig)
        del fig

        # Clear the ppsd object.
        self.ppsd = None

        # Reset the chunked window limits.
        self.overall_start_time = None
        self.overall_end_time = None



# A monkey patch of the obspy.signal.PPSD.plot method to deal with the problems
# of resizing the figure.
def ppsd_plot(self, fig = None, filename=None, show_coverage=True, show_histogram=True,
              show_percentiles=False, percentiles=[0, 25, 50, 75, 100],
              show_noise_models=True, grid=True, show=True,
              max_percentage=None, period_lim=(0.01, 179), show_mode=False,
              show_mean=False, cmap=obspy.imaging.cm.obspy_sequential, cumulative=False,
              cumulative_number_of_colors=20, xaxis_frequency=False):
    """
    Plot the 2D histogram of the current PPSD.
    If a filename is specified the plot is saved to this file, otherwise
    a plot window is shown.

    :type filename: str, optional
    :param filename: Name of output file
    :type show_coverage: bool, optional
    :param show_coverage: Enable/disable second axes with representation of
            data coverage time intervals.
    :type show_percentiles: bool, optional
    :param show_percentiles: Enable/disable plotting of approximated
            percentiles. These are calculated from the binned histogram and
            are not the exact percentiles.
    :type show_histogram: bool, optional
    :param show_histogram: Enable/disable plotting of histogram. This
            can be set ``False`` e.g. to make a plot with only percentiles
            plotted. Defaults to ``True``.
    :type percentiles: list of ints
    :param percentiles: percentiles to show if plotting of percentiles is
            selected.
    :type show_noise_models: bool, optional
    :param show_noise_models: Enable/disable plotting of noise models.
    :type grid: bool, optional
    :param grid: Enable/disable grid in histogram plot.
    :type show: bool, optional
    :param show: Enable/disable immediately showing the plot.
    :type max_percentage: float, optional
    :param max_percentage: Maximum percentage to adjust the colormap. The
        default is 30% unless ``cumulative=True``, in which case this value
        is ignored.
    :type period_lim: tuple of 2 floats, optional
    :param period_lim: Period limits to show in histogram. When setting
        ``xaxis_frequency=True``, this is expected to be frequency range in
        Hz.
    :type show_mode: bool, optional
    :param show_mode: Enable/disable plotting of mode psd values.
    :type show_mean: bool, optional
    :param show_mean: Enable/disable plotting of mean psd values.
    :type cmap: :class:`matplotlib.colors.Colormap`
    :param cmap: Colormap to use for the plot. To use the color map like in
        PQLX, [McNamara2004]_ use :const:`obspy.imaging.cm.pqlx`.
    :type cumulative: bool
    :param cumulative: Can be set to `True` to show a cumulative
        representation of the histogram, i.e. showing color coded for each
        frequency/amplitude bin at what percentage in time the value is
        not exceeded by the data (similar to the `percentile` option but
        continuously and color coded over the whole area). `max_percentage`
        is ignored when this option is specified.
    :type cumulative_number_of_colors: int
    :param cumulative_number_of_colors: Number of discrete color shades to
        use, `None` for a continuous colormap.
    :type xaxis_frequency: bool
    :param xaxis_frequency: If set to `True`, the x axis will be frequency
        in Hertz as opposed to the default of period in seconds.
    """
    self._PPSD__check_histogram()
    if fig is None:
        fig = plt.figure()
    fig.ppsd = obspy.core.util.AttribDict()

    if show_coverage:
        gs = matplotlib.gridspec.GridSpec(2, 1, height_ratios=[10, 1])
        ax = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        #ax = fig.add_axes([0.12, 0.3, 0.90, 0.6])
        #ax2 = fig.add_axes([0.15, 0.17, 0.7, 0.04])
    else:
        ax = fig.add_subplot(111)

    ax.set_axisbelow(True)

    if show_percentiles:
        # for every period look up the approximate place of the percentiles
        for percentile in percentiles:
            periods, percentile_values = \
                self.get_percentile(percentile=percentile)
            if xaxis_frequency:
                xdata = 1.0 / periods
            else:
                xdata = periods
            ax.plot(xdata, percentile_values, color="black", zorder=8)

    if show_mode:
        periods, mode_ = self.get_mode()
        if xaxis_frequency:
            xdata = 1.0 / periods
        else:
            xdata = periods
        if cmap.name == "viridis":
            color = "0.8"
        else:
            color = "black"
        ax.plot(xdata, mode_, color=color, zorder=9)

    if show_mean:
        periods, mean_ = self.get_mean()
        if xaxis_frequency:
            xdata = 1.0 / periods
        else:
            xdata = periods
        if cmap.name == "viridis":
            color = "0.8"
        else:
            color = "black"
        ax.plot(xdata, mean_, color=color, zorder=9)

    if show_noise_models:
        for periods, noise_model in (obspy.signal.spectral_estimation.get_nhnm(), obspy.signal.spectral_estimation.get_nlnm()):
            if xaxis_frequency:
                xdata = 1.0 / periods
            else:
                xdata = periods
            ax.plot(xdata, noise_model, '0.4', linewidth=2, zorder=10)

    if show_histogram:
        label = "[%]"
        if cumulative:
            label = "non-exceedance (cumulative) [%]"
            if max_percentage is not None:
                msg = ("Parameter 'max_percentage' is ignored when "
                       "'cumulative=True'.")
                warnings.warn(msg)
            max_percentage = 100
            if cumulative_number_of_colors is not None:
                cmap = matplotlib.colors.LinearSegmentedColormap(
                    name=cmap.name, segmentdata=cmap._segmentdata,
                    N=cumulative_number_of_colors)
        elif max_percentage is None:
            # Set default only if cumulative is not True.
            max_percentage = 30

        fig.ppsd.cumulative = cumulative
        fig.ppsd.cmap = cmap
        fig.ppsd.label = label
        fig.ppsd.max_percentage = max_percentage
        fig.ppsd.grid = grid
        fig.ppsd.xaxis_frequency = xaxis_frequency
        if max_percentage is not None:
            color_limits = (0, max_percentage)
            fig.ppsd.color_limits = color_limits

        self._plot_histogram(fig=fig)
        fig.ppsd.quadmesh.set_zorder(5)

    ax.semilogx()
    if xaxis_frequency:
        xlim = [1.0 / x for x in period_lim]
        ax.set_xlabel('Frequency [Hz]')
        ax.invert_xaxis()
    else:
        xlim = period_lim
        ax.set_xlabel('Period [s]')
    ax.set_xlim(sorted(xlim))
    ax.set_ylim(self.db_bin_edges[0], self.db_bin_edges[-1])
    if self.special_handling is None:
        ax.set_ylabel('Amplitude [$m^2/s^4/Hz$] [dB]', fontsize=8)
    else:
        ax.set_ylabel('Amplitude [dB]')
    ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
    ax.set_title(self._get_plot_title())

    if show_coverage:
        self._PPSD__plot_coverage(ax2)
        # emulating fig.autofmt_xdate():
        for label in ax2.get_xticklabels():
            label.set_ha("right")
            label.set_rotation(30)

    # Catch underflow warnings due to plotting on log-scale.
    _t = np.geterr()
    np.seterr(all="ignore")

    plt.tight_layout()
    try:
        if filename is not None:
            plt.savefig(filename)
            plt.close()
        elif show:
            plt.draw()
            plt.show()
        else:
            plt.draw()
            return fig
    finally:
        np.seterr(**_t)
