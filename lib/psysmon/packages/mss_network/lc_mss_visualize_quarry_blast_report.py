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

import matplotlib.pyplot as plt
import mpl_toolkits.basemap as basemap
import numpy as np
import obspy.core
import obspy.core.utcdatetime as utcdatetime
import scipy

import quarry_blast_validation
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm


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
        filename = 'blast_report_pgv_boxplot_data.pkl'
        if os.path.exists(os.path.join(data_dir, filename)):
            with open(os.path.join(data_dir, filename), 'r') as fp:
                pgv_boxplot_data = pickle.load(fp)
        else:
            pgv_boxplot_data = {}

        # Load the pgv-distance data.
        filename = 'blast_report_pgv_distance_data.pkl'
        if os.path.exists(os.path.join(data_dir, filename)):
            with open(os.path.join(data_dir, filename), 'r') as fp:
                pgv_distance_data = pickle.load(fp)
        else:
            pgv_distance_data = {}

        baumit_id_slug = report_data['baumit_id'].replace('/', '-')
        output_dir = os.path.join(self.pref_manager.get_value('report_results_dir'), 'sprengung_%s' % baumit_id_slug)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        # Plot the PSD data.
        self.export_psd_data(report_data['psd_data'], output_dir, baumit_id_slug)

        # Plot the PGV boxplot.
        pgv_boxplot_data = self.export_pgv_boxplot(report_data['blast_data']['max_pgv']['data'], pgv_boxplot_data,
                                                   output_dir, baumit_id_slug, report_data['blast_data']['epsg'])

        # Plot the PGV-distance.
        pgv_distance_data = self.export_pgv_distance_plot(report_data['blast_data']['max_pgv']['data'],
                                                          pgv_distance_data,
                                                          output_dir,
                                                          baumit_id_slug,
                                                          report_data['blast_data']['epsg'],
                                                          (report_data['blast_data']['x'], report_data['blast_data']['y']),
                                                          report_data['blast_data']['magnitude']['network_mag'])


        # Save the PGV boxplot data.
        filename = 'blast_report_pgv_boxplot_data.pkl'
        with open(os.path.join(data_dir, filename), 'w') as fp:
            pickle.dump(pgv_boxplot_data, fp)

        # Save the PGV-distance data.
        filename = 'blast_report_pgv_distance_data.pkl'
        with open(os.path.join(data_dir, filename), 'w') as fp:
            pickle.dump(pgv_distance_data, fp)


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
            del fig


    def plot_psd_data(self, psd_data, title):
        ''' Create the PSD images.
        '''
        fig = plt.figure(figsize = (6.4, 8.8))
        ax = fig.add_subplot(1, 1, 1)

        for cur_key, cur_data in psd_data.items():
            cur_frequ = cur_data['frequ']
            cur_psd = cur_data['psd']
            cur_nfft = cur_data['n_fft']
            left_fft = int(np.ceil(cur_nfft / 2.))
            ax.plot(cur_frequ[1:left_fft], cur_psd[1:left_fft], label = cur_key)

        ax.set_xlabel('Frequenz [Hz]')
        ax.set_ylabel('PSD [(m/s)^2/HZ in dB rel. to 1 m/s]')
        ax.set_xscale('log')
        ax.legend()
        ax.set_title(title)
        fig.subplots_adjust(hspace=0)
        fig.tight_layout()
        return fig


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

        fig_height = 10
        fig_width = 16 / 2.54
        fig_dpi = 300
        fig = plt.figure(figsize = (fig_width, fig_height), dpi = fig_dpi)
        ax = fig.add_subplot(111)
        ax.boxplot(bp_data, zorder = 1, flierprops = {'marker': 'o', 'markerfacecolor': 'lightgray', 'markeredgecolor': 'lightgray', 'markersize': 4})
        ax.plot(np.arange(blast_pgv.size) + 1, blast_pgv, 'o', zorder = 3)
        ax.axhline(0.1, linewidth = 1, linestyle = '--', color = 'gray', zorder = 0);
        ax.set_ylabel('PGV [mm/s]')
        ax.set_yscale('log')
        ax.set_title(title)
        fig.tight_layout()
        filepath = os.path.join(output_dir, title + '.png')
        fig.savefig(filepath, dpi = 300, bbox_inches = 'tight')

        fig.clear()
        del fig


        # Update the PGV boxplot data.
        for k, cur_station in enumerate(stations):
            if cur_station.snl_string not in pgv_boxplot_data.keys():
                pgv_boxplot_data[cur_station.snl_string] = []
            pgv_boxplot_data[cur_station.snl_string].append(blast_pgv[k] / 1000)

        return pgv_boxplot_data



    def export_pgv_distance_plot(self, pgv_data, pgv_distance_data, output_dir, baumit_id_slug, epsg, epi, mag):
        ''' Create the PGV-distance plots.
        '''
        output_dir = os.path.join(output_dir, 'pgv_distance')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)


        # Prepare the past pgv-distance data.
        past_pgv_dist = []
        past_pgv_dist.append([])
        past_pgv_dist.append([])
        for cur_value in pgv_distance_data.values():
            past_pgv_dist[0].extend(cur_value[0])
            past_pgv_dist[1].extend(cur_value[1])
        past_pgv_dist[1] = np.array(past_pgv_dist[1]) * 1000


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
        m_ref = 2.2
        m_fac = 10**(mag - m_ref)
        blast_pgv = blast_pgv / m_fac


        # Plot the data.
        title = 'sprengung_%s_pgv-distance' % baumit_id_slug

        fig_height = 10
        fig_width = 16 / 2.54
        fig_dpi = 300
        fig = plt.figure(figsize = (fig_width, fig_height), dpi = fig_dpi)
        ax = fig.add_subplot(111)
        ax.plot(past_pgv_dist[0], past_pgv_dist[1], 'x',
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
        del fig


        # Update the PGV-distance data.
        pgv_distance_data[baumit_id_slug] = []
        pgv_distance_data[baumit_id_slug].append([x.epidist for x in stations])
        pgv_distance_data[baumit_id_slug].append(list(blast_pgv / 1000))

        return pgv_distance_data
