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

import csv
import ftplib
import json
import os
import tempfile

import matplotlib.pyplot as plt
import mpl_toolkits.basemap as basemap
import numpy as np

import quarry_blast_validation
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm


class MssPublishBlastReport(package_nodes.CollectionNode):
    ''' Publish the blast report on the FTP server.

    '''
    name = 'mss publish report'
    mode = 'editable'
    category = 'mss'
    tags = ['macroseismic', 'mss', 'quarry', 'blast', 'report', 'publish', 'ftp']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.CollectionNode.__init__(self, **args)

        self.create_ftp_prefs()
        self.create_input_preferences()


    def create_ftp_prefs(self):
        ''' Create the general preference items.

        '''
        general_page = self.pref_manager.add_page('Ftp')
        server_group = general_page.add_group('server')

        # The Ftp Server IP.
        item = psy_pm.TextEditPrefItem(name = 'host',
                                       label = 'host',
                                       value = '',
                                       tool_tip = 'The IP address of the Ftp server.')
        server_group.add_item(item)

        # The Ftp Server username.
        item = psy_pm.TextEditPrefItem(name = 'username',
                                       label = 'username',
                                       value = '',
                                       tool_tip = 'The username of the Ftp server.')
        server_group.add_item(item)

        # The Ftp Server username.
        item = psy_pm.TextEditPrefItem(name = 'password',
                                       label = 'password',
                                       value = '',
                                       tool_tip = 'The password of the Ftp user.')
        server_group.add_item(item)

        # The name of the file with the blast details.
        item = psy_pm.TextEditPrefItem(name = 'filename',
                                       label = 'filename',
                                       value = '',
                                       tool_tip = 'The name of the file holding the blast details.')
        server_group.add_item(item)


    def create_input_preferences(self):
        ''' Create the input preferences.
        '''
        input_page = self.pref_manager.add_page('Input')
        bi_group = input_page.add_group('blast information')

        # The quarry blast information file.
        item = psy_pm.FileBrowsePrefItem(name = 'blast_file',
                                         label = 'blast file',
                                         value = '',
                                         filemask = 'json (*.json)|*.json',
                                         tool_tip = 'The quarry blast information file created with the quarry blast validation collection node.')
        bi_group.add_item(item)


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
        # Download the quarry information file.
        src_filename = self.pref_manager.get_value('filename')
        tmp_fid, tmp_filename = tempfile.mkstemp(prefix = 'quarry_validation',
                                        dir = self.project.tmpDir)
        ftp = ftplib.FTP(host = self.pref_manager.get_value('host'),
                         user = self.pref_manager.get_value('username'),
                         passwd = self.pref_manager.get_value('password'))
        try:
            with open(tmp_filename, 'wb') as fp:
                ftp.retrbinary('RETR ' + src_filename, fp.write)
        finally:
            ftp.quit()
            os.close(tmp_fid)


        # Load the quarry_blast information.
        blast_filename = self.pref_manager.get_value('blast_file')
        if os.path.exists(blast_filename):
            with open(blast_filename, 'r') as fp:
                quarry_blast = json.load(fp = fp,
                                         cls = quarry_blast_validation.QuarryFileDecoder)
        else:
            raise RuntimeError("Couldn't open the blast file %s.", blast_filename)


        # Parse the quarry information file.
        export_rows = []
        with open(tmp_filename, 'r') as fp:
            reader = csv.DictReader(fp, delimiter = ';')
            for cur_row in reader:
                if cur_row['Sprengnummer'] in quarry_blast.keys():
                    cur_blast = quarry_blast[cur_row['Sprengnummer']]
                    if 'psysmon_event_id' in cur_blast.keys():
                        cur_export_row = {}
                        cur_export_row['Sprengnummer'] = cur_row['Sprengnummer']
                        cur_export_row['ID'] = cur_blast['id']
                        cur_export_row['time [UTC]'] = cur_blast['event_time'].isoformat()
                        cur_export_row['network_mag'] = round(cur_blast['magnitude']['network_mag'], 2)
                        cur_export_row['network_mag_std'] = round(cur_blast['magnitude']['network_mag_std'], 2)
                        max_pgv = max(cur_blast['max_pgv']['data'].values())
                        max_pgv_ind = cur_blast['max_pgv']['data'].values().index(max_pgv)
                        cur_export_row['max_pgv [mm/s]'] = round(max_pgv * 1000, 3)
                        cur_export_row['max_pgv_station'] = cur_blast['max_pgv']['data'].keys()[max_pgv_ind]
                        export_rows.append(cur_export_row)
                    else:
                        self.logger.info("No related result found for blast %s.", cur_row['Sprengnummer'])



        if export_rows:
            export_filepath = os.path.join(self.project.tmpDir, 'sprengungen_auswertung.csv')
            with open(export_filepath, 'w') as fp:
                fieldnames = ['ID', 'Sprengnummer', 'time [UTC]', 'network_mag',
                              'network_mag_std', 'max_pgv [mm/s]', 'max_pgv_station']
                writer = csv.DictWriter(fp, fieldnames = fieldnames)
                writer.writeheader()
                writer.writerows(export_rows)



        # Plot the PGV vs. station.
        if export_rows:
            # Prepare the overal statistics.
            pgv_data = {}
            stations = []
            for cur_key, cur_blast in quarry_blast.iteritems():
                if 'psysmon_event_id' not in cur_blast.keys():
                    continue
                cur_data = cur_blast['max_pgv']['data']
                for cur_snl, cur_pgv in cur_data.iteritems():
                    if cur_snl not in pgv_data:
                        pgv_data[cur_snl] = [cur_pgv,]
                    else:
                        pgv_data[cur_snl].append(cur_pgv)


            proj = basemap.pyproj.Proj(init = 'epsg:' + cur_blast['epsg'])
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

            bp_data = [np.array(pgv_data[x.snl_string]) * 1000 for x in stations]

            for cur_key, cur_blast in quarry_blast.iteritems():
                self.logger.info("Plotting blast %s.", cur_key);
                blast_pgv = []
                if 'psysmon_event_id' not in cur_blast.keys():
                    continue
                cur_data = cur_blast['max_pgv']['data']
                for cur_station in stations:
                    if cur_station.snl_string in cur_data.keys():
                        blast_pgv.append(cur_data[cur_station.snl_string])
                    else:
                        blast_pgv.append(np.nan)

                blast_pgv = np.array(blast_pgv)
                blast_pgv = blast_pgv * 1000


                fig_height = 10
                fig_width = 16 / 2.54
                fig_dpi = 300
                fig = plt.figure(figsize = (fig_width, fig_height), dpi = fig_dpi)
                ax = fig.add_subplot(111)
                ax.boxplot(bp_data, zorder = 1, flierprops = {'marker': 'o', 'markerfacecolor': 'lightgray', 'markeredgecolor': 'lightgray', 'markersize': 4})
                ax.plot(np.arange(blast_pgv.size) + 1, blast_pgv, 'o', zorder = 3)
                ax.axhline(0.1, linewidth = 1, linestyle = '--', color = 'gray', zorder = 0);
                ax.set_xticklabels([str(x.name) for x in stations], rotation = 'vertical')
                ax.set_ylabel('PGV [mm/s]')
                ax.set_yscale('log')
                title_string = 'Sprengung %s, %s' % (cur_key, cur_blast['event_time'].isoformat())
                ax.set_title(title_string)
                fig.tight_layout()
                filepath = os.path.join(self.project.tmpDir, 'pgv_' + str(cur_blast['id']) + '.png')
                fig.savefig(filepath, dpi = 300, bbox_inches = 'tight')

                fig.clear()
                del fig





