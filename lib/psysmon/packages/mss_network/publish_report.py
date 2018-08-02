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
import obspy.core.utcdatetime as utcdatetime

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
        self.create_output_preferences()


    def create_ftp_prefs(self):
        ''' Create the general preference items.

        '''
        general_page = self.pref_manager.add_page('Ftp')
        server_group = general_page.add_group('server')
        mss_group = general_page.add_group('mss server')

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


        # The MSS homepage server section.
        # The Ftp Server IP.
        item = psy_pm.TextEditPrefItem(name = 'mss_host',
                                       label = 'host',
                                       value = '',
                                       tool_tip = 'The IP address of the MSS homepage Ftp server.')
        mss_group.add_item(item)

        # The Ftp Server username.
        item = psy_pm.TextEditPrefItem(name = 'mss_username',
                                       label = 'username',
                                       value = '',
                                       tool_tip = 'The username of the MSS hompage Ftp server.')
        mss_group.add_item(item)

        # The Ftp Server username.
        item = psy_pm.TextEditPrefItem(name = 'mss_password',
                                       label = 'password',
                                       value = '',
                                       tool_tip = 'The password of the MSS homepage Ftp user.')
        mss_group.add_item(item)


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


    def create_output_preferences(self):
        ''' Create the output preferences.
        '''
        input_page = self.pref_manager.add_page('Output')
        res_group = input_page.add_group('result')

        # The quarry blast information file.
        item = psy_pm.DirBrowsePrefItem(name = 'result_dir',
                                         label = 'result directory',
                                         value = '',
                                         tool_tip = 'The directory where to store the result file.')
        res_group.add_item(item)


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
        result_dir = self.pref_manager.get_value('result_dir')

        # Load the quarry_blast information.
        blast_filename = self.pref_manager.get_value('blast_file')
        if os.path.exists(blast_filename):
            with open(blast_filename, 'r') as fp:
                quarry_blast = json.load(fp = fp,
                                         cls = quarry_blast_validation.QuarryFileDecoder)
        else:
            raise RuntimeError("Couldn't open the blast file %s.", blast_filename)


        export_rows = []


        # Parse the quarry information file.
        use_export_sprengung = False
        if use_export_sprengung:
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

            with open(tmp_filename, 'r') as fp:
                reader = csv.DictReader(fp, delimiter = ';')
                for cur_row in reader:
                    if cur_row['Sprengnummer'] in quarry_blast.keys():
                        cur_blast = quarry_blast[cur_row['Sprengnummer']]
                        if 'psysmon_event_id' in cur_blast.keys() and 'computed_on' in cur_blast.keys():
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
                            if 'DUBA:MSSNet:00' in cur_blast['dom_stat_frequ'].keys():
                                cur_export_row['dom_frequ_duba [Hz]'] = round(cur_blast['dom_stat_frequ']['DUBA:MSSNet:00'], 2)
                            else:
                                cur_export_row['dom_frequ_duba [Hz]'] = ''

                            if 'DUBAM:MSSNet:00' in cur_blast['dom_stat_frequ'].keys():
                                cur_export_row['dom_frequ_dubam [Hz]'] = round(cur_blast['dom_stat_frequ']['DUBAM:MSSNet:00'], 2)
                            else:
                                cur_export_row['dom_frequ_dubam [Hz]'] = ''

                            export_rows.append(cur_export_row)
                        else:
                            self.logger.info("No related result found for blast %s.", cur_row['Sprengnummer'])
        else:
            for cur_blast_key in sorted(quarry_blast.keys()):
                cur_blast = quarry_blast[cur_blast_key]
                if 'psysmon_event_id' in cur_blast.keys() and 'computed_on' in cur_blast.keys():
                    cur_export_row = {}
                    cur_export_row['Sprengnummer'] = cur_blast_key
                    cur_export_row['ID'] = cur_blast['id']
                    cur_export_row['time [UTC]'] = cur_blast['event_time'].isoformat()
                    cur_export_row['network_mag'] = round(cur_blast['magnitude']['network_mag'], 2)
                    cur_export_row['network_mag_std'] = round(cur_blast['magnitude']['network_mag_std'], 2)
                    max_pgv = max(cur_blast['max_pgv']['data'].values())
                    max_pgv_ind = cur_blast['max_pgv']['data'].values().index(max_pgv)
                    cur_export_row['max_pgv [mm/s]'] = round(max_pgv * 1000, 3)
                    cur_export_row['max_pgv_station'] = cur_blast['max_pgv']['data'].keys()[max_pgv_ind]

                    if 'max_pgv_3d' in cur_blast and 'DUBA:MSSNet:00' in cur_blast['max_pgv_3d']['data']:
                        cur_export_row['pgv_duba [mm/s]'] = round(cur_blast['max_pgv_3d']['data']['DUBA:MSSNet:00'] * 1000, 3)
                    elif 'max_pgv' in cur_blast and 'DUBA:MSSNet:00' in cur_blast['max_pgv']['data']:
                        cur_export_row['pgv_duba [mm/s]'] = round(cur_blast['max_pgv']['data']['DUBA:MSSNet:00'] * 1000, 3)
                    else:
                        cur_export_row['pgv_duba [mm/s]'] = ''

                    if 'DUBA:MSSNet:00' in cur_blast['dom_stat_frequ'].keys():
                        cur_export_row['dom_frequ_duba [Hz]'] = round(cur_blast['dom_stat_frequ']['DUBA:MSSNet:00'], 2)
                    else:
                        cur_export_row['dom_frequ_duba [Hz]'] = ''

                    if 'max_pgv_3d' in cur_blast and 'DUBAM:MSSNet:00' in cur_blast['max_pgv_3d']['data']:
                        cur_export_row['pgv_dubam [mm/s]'] = round(cur_blast['max_pgv_3d']['data']['DUBAM:MSSNet:00'] * 1000, 3)
                    elif 'max_pgv' in cur_blast and 'DUBAM:MSSNet:00' in cur_blast['max_pgv']['data']:
                        cur_export_row['pgv_dubam [mm/s]'] = round(cur_blast['max_pgv']['data']['DUBAM:MSSNet:00'] * 1000, 3)
                    else:
                        cur_export_row['pgv_dubam [mm/s]'] = ''

                    if 'DUBAM:MSSNet:00' in cur_blast['dom_stat_frequ'].keys():
                        cur_export_row['dom_frequ_dubam [Hz]'] = round(cur_blast['dom_stat_frequ']['DUBAM:MSSNet:00'], 2)
                    else:
                        cur_export_row['dom_frequ_dubam [Hz]'] = ''

                    export_rows.append(cur_export_row)
                else:
                    self.logger.info("No related result found for blast %s.", cur_blast_key)


        if export_rows:
            # Upload the overall result file.
            export_filepath = os.path.join(result_dir, 'sprengungen_auswertung.csv')
            with open(export_filepath, 'w') as fp:
                # The pgv_duba and pgv_dubam are based on the 3D-resultant. The
                # network max_pgv is based on the 2D-resultant used for the
                # magnitude computation.
                fieldnames = ['ID', 'Sprengnummer', 'time [UTC]', 'network_mag',
                              'network_mag_std', 'max_pgv [mm/s]', 'max_pgv_station',
                              'pgv_duba [mm/s]', 'dom_frequ_duba [Hz]',
                              'pgv_dubam [mm/s]', 'dom_frequ_dubam [Hz]']
                # Use a custom header.
                header = ['ID', 'Sprengnummer', 'time UTC', 'network_mag',
                          'network_mag_std', 'max_pgv mm/s', 'max_pgv_station',
                          'pgv_duba mm/s', 'dom_frequ_duba Hz',
                          'pgv_dubam mm/s', 'dom_frequ_dubam Hz']

                writer = csv.DictWriter(fp, fieldnames = fieldnames)
                #writer.writeheader()
                # Use the dictwriter underlying writer instance to write the
                # custom header.
                writer.writer.writerow(header)
                writer.writerows(export_rows)

            # Upload the result files.
            # TODO: Make this a user preference.
            upload = True
            if upload:
                ftp = ftplib.FTP(host = self.pref_manager.get_value('host'),
                                 user = self.pref_manager.get_value('username'),
                                 passwd = self.pref_manager.get_value('password'))
                try:
                    self.logger.info("Uploading the result file %s.", export_filepath)
                    with open(export_filepath, 'r') as fp:
                        ftp.storbinary('STOR ' + os.path.basename(export_filepath), fp)

                    # Check for needed upload of results.
                    save_blast_file = False
                    for cur_blast_key in sorted(quarry_blast.keys()):
                        cur_blast = quarry_blast[cur_blast_key]
                        if 'psysmon_event_id' in cur_blast.keys() and 'computed_on' in cur_blast.keys() and 'uploaded_on' not in cur_blast.keys():
                            # Upload the result images to the FTP Server.
                            self.logger.info('Uploading images of %s.', cur_blast_key)
                            cur_blast_dir = os.path.join(result_dir, 'sprengung_' + cur_blast_key)

                            # Upload the pgv file.
                            cur_file = os.path.join(cur_blast_dir, 'pgv', 'sprengung_' + cur_blast_key + '_pgv.png')
                            if os.path.exists(cur_file):
                                with open(cur_file) as fp:
                                    ftp.storbinary('STOR images/pgv/' + os.path.basename(cur_file), fp)
                            else:
                                self.logger.error('File %s does not exist.', cur_file)

                            # Upload the pgv_red file.
                            cur_file = os.path.join(cur_blast_dir, 'pgv_red', 'sprengung_' + cur_blast_key + '_pgv_red.png')
                            if os.path.exists(cur_file):
                                with open(cur_file) as fp:
                                    ftp.storbinary('STOR images/pgv_red/' + os.path.basename(cur_file), fp)
                            else:
                                self.logger.error('File %s does not exist.', cur_file)

                            # Upload the psd file of station DUBA.
                            cur_file = os.path.join(cur_blast_dir, 'psd', 'sprengung_' + cur_blast_key + '_psd_DUBA.png')
                            if os.path.exists(cur_file):
                                with open(cur_file) as fp:
                                    ftp.storbinary('STOR images/psd/' + os.path.basename(cur_file), fp)
                            else:
                                self.logger.error('File %s does not exist.', cur_file)

                            # Upload the psd file of station DUBAM.
                            cur_file = os.path.join(cur_blast_dir, 'psd', 'sprengung_' + cur_blast_key + '_psd_DUBAM.png')
                            if os.path.exists(cur_file):
                                with open(cur_file) as fp:
                                    ftp.storbinary('STOR images/psd/' + os.path.basename(cur_file), fp)
                            else:
                                self.logger.error('File %s does not exist.', cur_file)

                            # Add the uploaded_on flag.
                            quarry_blast[cur_blast_key]['uploaded_on'] = utcdatetime.UTCDateTime()
                            save_blast_file = True
                except:
                    self.logger.exception("Problems when uploading the result files.")
                finally:
                    ftp.quit()

                # Save the quarry blast information.
                if save_blast_file:
                    with open(blast_filename, 'w') as fp:
                        json.dump(quarry_blast,
                                  fp = fp,
                                  cls = quarry_blast_validation.QuarryFileEncoder)


            # Make this a user preference.
            upload_mss_homepage = True
            if upload_mss_homepage:
                ftp = ftplib.FTP(host = self.pref_manager.get_value('mss_host'),
                                 user = self.pref_manager.get_value('mss_username'),
                                 passwd = self.pref_manager.get_value('mss_password'))
                try:
                    self.logger.info("Uploading the json file %s.", blast_filename)
                    with open(blast_filename, 'r') as fp:
                        ftp.storbinary('STOR msn_ergebnisse/' + os.path.basename(blast_filename), fp)

                except:
                    self.logger.exception("Problems when uploading the json file to the MSS homepage.")
                finally:
                    ftp.quit()



