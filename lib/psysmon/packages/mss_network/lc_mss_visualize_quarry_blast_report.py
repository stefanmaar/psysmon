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

import json
import os
import pickle

import matplotlib
import matplotlib.pyplot as plt
import mpl_toolkits.basemap as basemap
import numpy as np
import obspy.core
import obspy.core.utcdatetime as utcdatetime
import seaborn as sns
import scipy


import quarry_blast_validation
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm

sns.set_style('whitegrid')
sns.set_style('ticks')
sns.set_context('paper')


class MssVisualizeQuarryBlastReport(package_nodes.LooperCollectionChildNode):
    ''' Create a report of a quarry blast recorded on the MSS network.

    '''
    name = 'mss visualize report data'
    mode = 'looper child'
    category = 'mss'
    tags = ['macroseismic', 'mss', 'quarry', 'blast', 'visualize']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        # No waveform data is needed.
        self.need_waveform_data = False

        self.create_input_preferences()


    def create_input_preferences(self):
        ''' Create the input preferences.
        '''
        input_page = self.pref_manager.add_page('Input/Output')
        rd_group = input_page.add_group('report data')
        rr_group = input_page.add_group('report results')

        # The report data directory.
        item = psy_pm.DirBrowsePrefItem(name = 'report_data_dir',
                                        label = 'report data directory',
                                        value = '',
                                        tool_tip = 'The directory holding the quarry blast report data.')
        rd_group.add_item(item)

        # The quarry blast information file.
        item = psy_pm.FileBrowsePrefItem(name = 'blast_file',
                                         label = 'blast file',
                                         value = '',
                                         filemask = 'json (*.json)|*.json',
                                         tool_tip = 'The quarry blast information file created with the quarry blast validation collection node.')
        rd_group.add_item(item)

        # The report results directory.
        item = psy_pm.DirBrowsePrefItem(name = 'report_results_dir',
                                        label = 'report results directory',
                                        value = '',
                                        tool_tip = 'The directory where to save the report result files.')
        rr_group.add_item(item)



    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Check for needed keyword arguments.
        if not self.kwargs_exists(['event'], **kwargs):
            raise RuntimeError("The needed event argument was not passed to the execute method.")

        event = kwargs['event']

        # Load the report data.
        data_dir = self.pref_manager.get_value('report_data_dir')
        filename = 'blast_report_data_event_%010d.pkl' % event.db_id
        with open(os.path.join(data_dir, filename), 'r') as fp:
            report_data = pickle.load(fp)


        # Load the pgv boxplot data.
        overall_data = self.load_overall_data()

        baumit_id_slug = report_data['baumit_id'].replace('/', '-')
        output_dir = os.path.join(self.pref_manager.get_value('report_results_dir'), 'sprengung_%s' % baumit_id_slug)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)


        plt.close('all')
        # Plot the PSD data.
        self.export_psd_data(report_data['psd_data'], output_dir, baumit_id_slug)

        # Plot the PGV boxplot.
        self.export_pgv_boxplot(report_data['blast_data']['max_pgv']['data'],
                                overall_data['pgv_boxplot'],
                                output_dir,
                                baumit_id_slug,
                                report_data['blast_data']['epsg'])

        # Plot the PGV-distance.
        self.export_pgv_red_plot(report_data['blast_data']['max_pgv']['data'],
                                 overall_data['pgv_dist'],
                                 output_dir,
                                 baumit_id_slug,
                                 report_data['blast_data']['epsg'],
                                 (report_data['blast_data']['x'], report_data['blast_data']['y']),
                                 report_data['blast_data']['magnitude']['network_mag'])



    def load_overall_data(self):
        ''' Load the already existing blast results and create the needed data for the plots.
        '''
        # Load the quarry_blast information.
        blast_filename = self.pref_manager.get_value('blast_file')
        if os.path.exists(blast_filename):
            with open(blast_filename, 'r') as fp:
                quarry_blast = json.load(fp = fp,
                                         cls = quarry_blast_validation.QuarryFileDecoder)
        else:
            raise RuntimeError("Couldn't open the blast file %s.", blast_filename)

        # Extract the data needed for the plots.
        pgv_boxplot_data = {}
        pgv_dist_data = []
        for cur_key in sorted(quarry_blast.keys()):
            cur_blast = quarry_blast[cur_key]

            # Use entries with computed results only.
            if 'computed_on' not in cur_blast.keys():
                continue

            # Get the pgv values for the boxplots. 
            for cur_snl_string, cur_pgv in cur_blast['max_pgv']['data'].items():
                if cur_snl_string not in pgv_boxplot_data:
                    pgv_boxplot_data[cur_snl_string] = []
                pgv_boxplot_data[cur_snl_string].append(cur_pgv)

            # Get the epidistance, pgv, magnitude pairs for the red_pgv plots.
            # Compute the epidistance and sort the stations according to it.
            stations = []
            proj = basemap.pyproj.Proj(init = 'epsg:' + cur_blast['epsg'])
            ref_x = cur_blast['x']
            ref_y = cur_blast['y']

            # Get the needed stations from the geometry inventory.
            station_names = [x.split(':')[0] for x in cur_blast['max_pgv']['data'].keys()]
            for cur_station_name in station_names:
                cur_station = self.project.geometry_inventory.get_station(name = cur_station_name)[0]
                stat_lonlat = cur_station.get_lon_lat()
                stat_x, stat_y = proj(stat_lonlat[0], stat_lonlat[1])
                cur_station.epidist = np.sqrt((stat_x - ref_x)**2 + (stat_y - ref_y)**2)
                stations.append(cur_station)
            stations = sorted(stations, key = lambda x: x.epidist)

            # Get the PGV data related to the sorted stations.
            sorted_pgv = []
            for cur_station in stations:
                if cur_station.snl_string in cur_blast['max_pgv']['data'].keys():
                    sorted_pgv.append(cur_blast['max_pgv']['data'][cur_station.snl_string])
                else:
                    sorted_pgv.append(np.nan)

            # Add the extracted data to the overall list. 
            pgv_dist_data.extend(zip([x.epidist for x in stations], sorted_pgv, [cur_blast['magnitude']['network_mag']] * len(sorted_pgv)))

        overall_data = {}
        overall_data['pgv_boxplot'] = pgv_boxplot_data
        overall_data['pgv_dist'] = np.array(pgv_dist_data)

        return overall_data




    def export_psd_data(self, psd_data, output_dir, baumit_id_slug):
        ''' Export the PSD to image files.
        '''
        output_dir = os.path.join(output_dir, 'psd')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        station_names = list(set([x.split('.')[1] for x in psd_data.keys()]))

        for cur_name in station_names:
            channel_keys = [x for x in psd_data.keys() if x.split('.')[1] == cur_name]
            channel_data = [psd_data[x] for x in channel_keys]
            cur_psd_data = dict(zip(channel_keys, channel_data))
            title = 'sprengung_%s_psd_%s' % (baumit_id_slug, cur_name)
            fig = self.plot_psd_data(cur_psd_data, title)
            filename = title + '.png'
            fig.savefig(os.path.join(output_dir, filename), dpi = 150)
            fig.clear()
            plt.close(fig)
            del fig


    def plot_psd_data(self, psd_data, title):
        ''' Create the PSD images.
        '''
        fig = plt.figure(figsize = (8.8, 6.4), dpi = 72)
        ax = fig.add_subplot(1, 1, 1)
        ax.minorticks_on()

        #self.plot_noise_model(ax)

        for cur_key, cur_data in psd_data.items():
            cur_nfft = cur_data['n_fft']
            left_fft = int(np.ceil(cur_nfft / 2.))
            cur_frequ = cur_data['frequ'][1:left_fft]
            cur_psd = cur_data['psd'][1:left_fft]

            # Smooth the psd.
            win_len = 21
            op = np.ones(win_len)
            op = op / np.sum(op)
            cur_psd_smooth = np.convolve(op, cur_psd, mode = 'same')
            cur_frequ_smooth = cur_frequ[int(np.ceil(win_len/2)):]
            cur_psd_smooth = cur_psd_smooth[int(np.ceil(win_len/2)):]

            ax.plot(cur_frequ, cur_psd, color = sns.xkcd_rgb['light grey'])
            ax.plot(cur_frequ_smooth[10:-10], cur_psd_smooth[10:-10], label = cur_key, zorder = 20)

        ax.set_xlabel('Frequenz [Hz]')
        ax.set_ylabel('PSD [(m/s)^2/HZ in dB rel. to 1 m/s]')
        ax.set_xscale('log')
        ax.grid(b = True, which = 'major')
        ax.grid(b = True, which = 'minor', linestyle = ':', axis = 'x')
        ax.legend()
        ax.set_title(title)
        fig.subplots_adjust(hspace=0)
        fig.tight_layout()
        return fig

    def plot_noise_model(self, ax):
        p_nhnm, nhnm = obspy.signal.spectral_estimation.get_nhnm()
        p_nlnm, nlnm = obspy.signal.spectral_estimation.get_nlnm()

        # obspy returns the NLNM and NHNM values in acceleration.
        # Convert them to the current unit (see Bormann (1998)).
        nhnm = nhnm + 20 * np.log10(p_nhnm/ (2 * np.pi))
        nlnm = nlnm + 20 * np.log10(p_nlnm/ (2 * np.pi))
        #ax.plot(1/p_nlnm, nlnm, color = self.line_colors['nlnm'])
        ax.plot(1/p_nhnm, nhnm, color = sns.xkcd_rgb['very light blue'], linestyle = '--')



    def export_pgv_boxplot(self, pgv_data, pgv_boxplot_data, output_dir, baumit_id_slug, epsg):
        ''' Export the PGV boxplot image.
        '''
        # Prepare the output directory.
        output_dir = os.path.join(output_dir, 'pgv')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # Sort the stations according to the reference location.
        stations = []
        proj = basemap.pyproj.Proj(init = 'epsg:' + epsg)
        ref_x = -21514.445
        ref_y = 301766.29

        station_names = [x.split(':')[0] for x in pgv_data.keys()]
        for cur_station_name in station_names:
            cur_station = self.project.geometry_inventory.get_station(name = cur_station_name)[0]
            stat_lonlat = cur_station.get_lon_lat()
            stat_x, stat_y = proj(stat_lonlat[0], stat_lonlat[1])
            cur_station.epidist = np.sqrt((stat_x - ref_x)**2 + (stat_y - ref_y)**2)
            stations.append(cur_station)
        stations = sorted(stations, key = lambda x: x.epidist)

        # Get the PGV boxplot data related to the sorted stations.
        bp_data = [np.array(pgv_boxplot_data[x.snl_string]) * 1000 if x.snl_string in pgv_boxplot_data.keys() else np.empty(0) for x in stations]

        # Get the PGV data related to the sorted stations.
        sorted_pgv = []
        for cur_station in stations:
            if cur_station.snl_string in pgv_data.keys():
                sorted_pgv.append(pgv_data[cur_station.snl_string])
            else:
                sorted_pgv.append(np.nan)

        blast_pgv = np.array(sorted_pgv)
        blast_pgv = blast_pgv * 1000

        # Plot the data.
        title = 'sprengung_%s_pgv' % baumit_id_slug

        fig_height = 10 / 2.54
        fig_width = 16 / 2.54
        fig_dpi = 300
        fig = plt.figure(figsize = (fig_width, fig_height), dpi = fig_dpi)
        ax = fig.add_subplot(111)
        ax.boxplot(bp_data, zorder = 1, flierprops = {'marker': 'o', 'markerfacecolor': 'lightgray', 'markeredgecolor': 'lightgray', 'markersize': 4})
        ax.plot(np.arange(blast_pgv.size) + 1, blast_pgv, 'o', zorder = 3)
        ax.axhline(0.1, linewidth = 1, linestyle = '--', color = 'gray', zorder = 0);
        ax.set_xticks(np.arange(blast_pgv.size) + 1)
        ax.set_xticklabels([str(x.name) for x in stations], rotation = 'vertical')
        ax.set_ylabel('PGV [mm/s]')
        ax.set_yscale('log')
        ax.set_title(title)
        fig.tight_layout()

        # Plot the PGV values.
        ylim = ax.get_ylim()
        for k, cur_pgv in enumerate(blast_pgv):
            bbox_props = dict(boxstyle = 'round,pad=0.3',
                              facecolor = 'white',
                              edgecolor = 'black',
                              linewidth = 1)
            cur_text = ax.text(k + 1, ylim[0], '%.3f' % cur_pgv,
                               ha = 'center',
                               va = 'bottom',
                               size = 6,
                               bbox = bbox_props)

        filepath = os.path.join(output_dir, title + '.png')
        fig.savefig(filepath, dpi = 300, bbox_inches = 'tight')

        fig.clear()
        plt.close(fig)
        del fig



    def export_pgv_red_plot(self, pgv_data, past_pgv_dist, output_dir, baumit_id_slug, epsg, epi, mag):
        ''' Create the PGV-distance plots.
        '''
        output_dir = os.path.join(output_dir, 'pgv_red')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # The reference magnitude.
        m_ref = 2.2

        # Convert the past pgv-distance data to mm/s.
        past_pgv_dist[:,1] = past_pgv_dist[:,1] * 1000
        past_pgv_dist[:,1] = past_pgv_dist[:,1] / (10**(past_pgv_dist[:,2] - m_ref))

        # Compute the epidistance and sort the stations according to it.
        stations = []
        proj = basemap.pyproj.Proj(init = 'epsg:' + epsg)
        ref_x = epi[0]
        ref_y = epi[1]

        station_names = [x.split(':')[0] for x in pgv_data.keys()]
        for cur_station_name in station_names:
            cur_station = self.project.geometry_inventory.get_station(name = cur_station_name)[0]
            stat_lonlat = cur_station.get_lon_lat()
            stat_x, stat_y = proj(stat_lonlat[0], stat_lonlat[1])
            cur_station.epidist = np.sqrt((stat_x - ref_x)**2 + (stat_y - ref_y)**2)
            stations.append(cur_station)
        stations = sorted(stations, key = lambda x: x.epidist)

        # Get the PGV data related to the sorted stations.
        sorted_pgv = []
        for cur_station in stations:
            if cur_station.snl_string in pgv_data.keys():
                sorted_pgv.append(pgv_data[cur_station.snl_string])
            else:
                sorted_pgv.append(np.nan)

        blast_pgv = np.array(sorted_pgv)
        blast_pgv = blast_pgv * 1000

        # Normalize the data to M_ref.
        m_fac = 10**(mag - m_ref)
        blast_pgv = blast_pgv / m_fac



        # Plot the data.
        title = 'sprengung_%s_pgv_red' % baumit_id_slug

        fig_width = 16 / 2.54
        fig_height = 10 / 2.54
        fig_dpi = 300
        fig = plt.figure(figsize = (fig_width, fig_height), dpi = fig_dpi)
        ax = fig.add_subplot(111)
        ax.plot(past_pgv_dist[:,0], past_pgv_dist[:,1], 'x',
                markeredgewidth = 0.5, zorder = 0, markersize = 3, color = 'gray')
        ax.plot([x.epidist for x in stations], blast_pgv, 'o', zorder = 3)
        #ax.axhline(0.1, linewidth = 1, linestyle = '--', color = 'gray', zorder = 0);
        ax.set_xticks(np.arange(blast_pgv.size) + 1)
        ax.set_xticklabels([str(x.name) for x in stations], rotation = 'vertical')
        ax.set_ylabel('PGV red. M_mss=2.2 [mm/s]')
        ax.set_xlabel('distance [m]')
        ax.set_yscale('log')
        ax.set_xscale('log')
        ax.set_xlim((100, 50000))
        ax.set_ylim((1e-3, 10))
        ax.set_title(title)
        fig.tight_layout()
        filepath = os.path.join(output_dir, title + '.png')
        fig.savefig(filepath, dpi = 300, bbox_inches = 'tight')

        fig.clear()
        plt.close(fig)
        del fig
