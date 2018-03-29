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
import datetime
import ftplib
import json
import os
import tempfile

import numpy as np
import obspy.core.utcdatetime as utcdatetime
import sqlalchemy.orm

import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.packages.event.core as event_core


class QuarryBlastValidation(package_nodes.CollectionNode):
    ''' Validation of quarry blast events using information 
    provided by the quarry operator.

    '''
    name = 'quarry blast validation'
    mode = 'looper child'
    category = 'classification'
    tags = ['mss', 'macroseismic', 'quarry', 'blast']


    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.CollectionNode.__init__(self, **args)

        self.create_ftp_prefs()
        self.create_output_prefs()
        #self.create_classification_prefs()



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


    def create_output_prefs(self):
        ''' Create the output preferences.
        '''
        output_page = self.pref_manager.add_page('output')
        files_group = output_page.add_group('files')

        # The output folder.
        item = psy_pm.DirBrowsePrefItem(name = 'output_dir',
                                        label = 'output directory',
                                        value = '',
                                        tool_tip = 'The directory where the resulting files are saved.')
        files_group.add_item(item = item)

        # The file prefix.
        item = psy_pm.TextEditPrefItem(name = 'prefix',
                                       label = 'prefix',
                                       value = '',
                                       tool_tip = 'The string prepended to the filename.')
        files_group.add_item(item = item)



    def create_classification_prefs(self):
        ''' Create the classification preference items.
        '''
        classify_page = self.pref_manager.add_page('classification')
        event_group = classify_page.add_group('event')

        # The type of the classified events.
        item = psy_pm.MultiChoicePrefItem(name = 'event_type',
                                          label = 'type',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The type of the classified events.')
        event_group.add_item(item)



    def edit(self):
        #event_types = self.load_event_types()
        #quarry_event = [x for x in event_types if x.name == 'quarry'][0]
        #self.pref_manager.set_limit('event_type', [x.name for x in quarry_event.children])

        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, prevNodeOutput = {}):
        ''' Execute the looper collection node.

        '''
        output_dir = self.pref_manager.get_value('output_dir')
        prefix = self.pref_manager.get_value('prefix')
        blast_filename = os.path.join(output_dir, prefix + 'quarry_blasts.json')


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

        if os.path.exists(blast_filename):
            with open(blast_filename, 'r') as fp:
                quarry_blast = json.load(fp = fp,
                                         cls = QuarryFileDecoder)
        else:
            quarry_blast = {}

        # Parse the quarry information file.
        with open(tmp_filename, 'r') as fp:
            reader = csv.DictReader(fp, delimiter = ';')
            for cur_row in reader:
                print cur_row
                if cur_row['Sprengnummer'] not in quarry_blast.keys():
                    tmp = {}
                    tmp['id'] = int(cur_row['ID'])

                    date = datetime.datetime.strptime(cur_row['Datum_Sprengung'], '%d.%m.%Y %H:%M:%S')
                    time = datetime.datetime.strptime(cur_row['Uhrzeit_Sprengung'], '%d.%m.%Y %H:%M:%S')
                    tmp['time'] = utcdatetime.UTCDateTime(year = date.year,
                                                          month = date.month,
                                                          day = date.day,
                                                          hour = time.hour,
                                                          minute = time.minute,
                                                          second = time.second)
                    x = []
                    try:
                        x.append(float(cur_row['Koord_x1'].replace(',', '.')))
                    except:
                        self.logger.warning("Koord_x1 couldn't be converted.")

                    try:
                        x.append(float(cur_row['Koord_x2'].replace(',', '.')))
                    except:
                        self.logger.warning("Koord_x2 couldn't be converted.")

                    y = []
                    try:
                        y.append(float(cur_row['Koord_y1'].replace(',', '.')))
                    except:
                        self.logger.warning("Koord_y1 couldn't be converted.")

                    try:
                        y.append(float(cur_row['Koord_y2'].replace(',', '.')))
                    except:
                        self.logger.warning("Koord_y2 couldn't be converted.")


                    z = []
                    try:
                        z.append(float(cur_row['Koord_z1'].replace(',', '.')))
                    except:
                        self.logger.warning("Koord_z1 couldn't be converted.")

                    try:
                        z.append(float(cur_row['Koord_z2'].replace(',', '.')))
                    except:
                        self.logger.warning("Koord_z2 couldn't be converted.")

                    if x:
                        tmp['x'] = np.mean(x)
                    else:
                        tmp['x'] = -9999

                    if y:
                        tmp['y'] = np.mean(y)
                    else:
                        tmp['y'] = -9999

                    if z:
                        tmp['z'] = np.mean(z)
                    else:
                        tmp['z'] = -9999

                    tmp['epsg'] = '31259'

                    quarry_blast[cur_row['Sprengnummer']] = tmp


        # Search for related events in the database.
        catalog_name = 'rt_binding'
        event_lib = event_core.Library('events')
        event_lib.load_catalog_from_db(self.project, name = catalog_name)
        catalog = event_lib.catalogs[catalog_name]

        for cur_key, cur_blast in quarry_blast.iteritems():
            catalog.clear_events()
            catalog.load_events(project = self.project,
                                start_time = cur_blast['time'] - 60,
                                end_time = cur_blast['time'] + 300)
            # Select by event type.
            quarry_events = [x for x in catalog.events if x.event_type and x.event_type.name == 'duernbach']
            if quarry_events:
                quarry_blast[cur_key]['psysmon_event_id'] = [x.db_id for x in quarry_events]
                for cur_event in quarry_events:
                    cur_event.tags = ['mss_result_needed', 'baumit_id:' + cur_key.replace(',', ';')]
                    cur_event.write_to_database(self.project)

        # Save the results.
        with open(blast_filename, 'w') as fp:
            json.dump(quarry_blast,
                      fp = fp,
                      cls = QuarryFileEncoder)




    def load_event_types(self):
        ''' Load the available event types from the database.
        '''
        db_session = self.project.getDbSession()
        event_types = []
        try:
            event_type_table = self.project.dbTables['event_type']
            query = db_session.query(event_type_table)
            query = query.options(sqlalchemy.orm.immediateload(event_type_table.children))
            query = query.options(sqlalchemy.orm.immediateload(event_type_table.parent))
            event_types = query.all()
        finally:
            db_session.close()

        return event_types



class QuarryFileEncoder(json.JSONEncoder):
    ''' A JSON encoder for the quarry blast file.
    '''

    def __init__(self, **kwargs):
        json.JSONEncoder.__init__(self, **kwargs)

        # File format settings.
        self.indent = 4
        self.sort_keys = True


    def default(self, obj):
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]

        if obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        else:
            d = {'ERROR': 'MISSING CONVERTER for obj_class %s with base_class %s' % (str(obj_class), str(base_class))}

        # Add the class and module information to the dictionary.
        if obj_class != 'FileContainer':
            tmp = {'__baseclass__': base_class,
                   '__class__': obj.__class__.__name__,
                   '__module__': obj.__module__}
            d.update(tmp)

        return d


    def convert_utcdatetime(self, obj):
        return {'utcdatetime': obj.isoformat()}



class QuarryFileDecoder(json.JSONDecoder):
    ''' A JSON decoder for the quarry blast file.
    '''

    def __init__(self, **kwarg):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)


    def convert_object(self, d):
        if '__class__' in d:
            class_name = d.pop('__class__')
            module_name = d.pop('__module__')
            base_class = d.pop('__baseclass__')

            if class_name == 'UTCDateTime':
                inst = self.convert_utcdatetime(d)
            else:
                inst = {'ERROR': 'MISSING CONVERTER'}
        else:
            inst = d

        return inst

    def convert_utcdatetime(self, d):
        inst = utcdatetime.UTCDateTime(d['utcdatetime'])
        return inst


