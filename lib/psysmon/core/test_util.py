from __future__ import division
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

from past.utils import old_div
import logging
import tempfile
import os
import os.path
import glob
import shutil
import copy

import scipy
import scipy.signal
import numpy as np

import psysmon
import psysmon.core.base
from psysmon.core.project import User
from psysmon.packages.geometry.inventory_parser import InventoryXmlParser
from psysmon.packages.geometry.db_inventory import DbInventory
from obspy.core.utcdatetime import UTCDateTime


def create_psybase(package_directory = None):
    ''' Create the psysmon base instance.

    '''
    # Get the pSysmon base directory.
    psyBaseDir = os.path.abspath(psysmon.__file__)
    psyBaseDir = os.path.dirname(psyBaseDir)

    # Initialize the pSysmon base object.
    psyBase = psysmon.core.base.Base(psyBaseDir, package_directory = package_directory)

    return psyBase



def create_dbtest_project(psybase):
    ''' Create a new project with parameters set to access the unit_test test 
    database.
    '''

    name = 'Unit Test'
    base_dir = tempfile.mkdtemp()
    user = User(user_name = 'unit_test',
                user_pwd = 'test',
                user_mode = 'admin',
                author_name = 'Stefan Test',
                author_uri = 'stest',
                agency_name = 'University of Test',
                agency_uri = 'at.uot'
               )
    db_host = 'localhost'
    project = psysmon.core.project.Project(psybase = psybase,
                                           name = name,
                                           base_dir = base_dir,
                                           user = user,
                                           dbHost = db_host,
                                           db_version = {}
                                          )

    return project


def create_empty_project(psybase):
    ''' Create a complete project including database.
    '''
    name = 'Unit Test'
    project_dir = tempfile.mkdtemp()
    user_name = 'unit_test'
    user_pwd = 'test'
    author_name = 'Stefan Test'
    author_uri = 'stest'
    agency_name = 'University of Test'
    agency_uri = 'at.uot'
    db_host = 'localhost'

    psybase.createPsysmonProject(name, project_dir, db_host, user_name,
                user_pwd, author_name, author_uri, agency_name, agency_uri)

    project = psybase.project

    return project



def create_full_project(psybase):
    ''' Create a complete project including database containing geometry and data.
    '''
    name = 'Unit Test'
    project_dir = tempfile.mkdtemp()
    user_name = 'unit_test'
    user_pwd = 'test'
    author_name = 'Stefan Test'
    author_uri = 'stest'
    agency_name = 'University of Test'
    agency_uri = 'at.uot'
    db_host = 'localhost'

    psybase.createPsysmonProject(name, project_dir, db_host, user_name,
                user_pwd, author_name, author_uri, agency_name, agency_uri)

    project = psybase.project

    data_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(data_path, 'tests', 'data')

    # Write the geometry from XML to Database.
    inventory_file = os.path.join(data_path, 'test_inventory_01.xml')
    xmlparser = InventoryXmlParser()
    inventory = xmlparser.parse(inventory_file)
    db_inventory = DbInventory.from_inventory_instance(name = 'test', project = project, inventory = inventory)
    try:
        db_inventory.commit()
    finally:
        db_inventory.close()

    # Load the geometry inventory from the database.
    project.load_geometry_inventory()

    # Add the waveform directory to the project.
    wf_dir = project.dbTables['waveform_dir']
    wf_diralias = project.dbTables['waveform_dir_alias']
    db_session = project.getDbSession()
    try:
        new_wfdir = wf_dir(data_path, '')
        new_alias = wf_diralias(project.activeUser.name,
                                data_path)
        new_wfdir.aliases.append(new_alias)
        db_session.add(new_wfdir)
        db_session.commit()
    finally:
        db_session.close()

    project.waveclient['db client'].loadWaveformDirList()

    # Import the data files.
    node_template = psybase.packageMgr.getCollectionNodeTemplate('import waveform')
    node = node_template()
    # Create a logger for the node.
    loggerName = __name__+ "." + node.__class__.__name__
    node.logger = logging.getLogger(loggerName)
    node.project = project
    # Set the node preferences and execute it.
    filenames = glob.glob(os.path.join(data_path, 'ZAMG-seis_event00017*.msd'))
    filelist = []
    for cur_file in filenames:
        fsize = os.path.getsize(cur_file);
        fsize = old_div(fsize,(1024.0*1024.0))           # Convert to MB
        filelist.append(('mseed', cur_file, '%.2f' % fsize))
    node.pref_manager.set_value('input_files', filelist)
    node.execute()

    # Import the earthquake bulletin to fill the events database.
    bulletin_file = os.path.join(data_path, 'test_earthquake_bulletin.txt')
    node_template = psybase.packageMgr.getCollectionNodeTemplate('import earthquake bulletin')
    node = node_template()
    # Create a logger for the node.
    loggerName = __name__+ "." + node.__class__.__name__
    node.logger = logging.getLogger(loggerName)
    node.project = project
    # Set the node preferences and execute it.
    input_files = [('IMS1.0', bulletin_file, 1),]
    node.pref_manager.set_value('input_files', input_files)
    node.execute()


    # Add some events to the database.
    db_session = project.getDbSession()
    try:
        cat_table = project.dbTables['event_catalog'];
        cat_orm = cat_table(name = 'test',
                            description = 'A test catalog.',
                            agency_uri = project.activeUser.agency_uri,
                            author_uri = project.activeUser.author_uri,
                            creation_time = UTCDateTime().isoformat())

        event_table = project.dbTables['event']
        # The first event is an earthquake.
        event_orm = event_table(ev_catalog_id = None,
                                start_time = UTCDateTime('2010-08-31T08:00:01').timestamp,
                                end_time = UTCDateTime('2010-08-31T08:00:16').timestamp,
                                description = 'A test event.',
                                agency_uri = project.activeUser.agency_uri,
                                author_uri = project.activeUser.author_uri,
                                creation_time = UTCDateTime().isoformat())
        cat_orm.events.append(event_orm)

        # The second event is just a dummy with some spikes on G_NAWA:HHZ.
        event_orm = event_table(ev_catalog_id = None,
                                start_time = UTCDateTime('2010-08-31T08:02:11').timestamp,
                                end_time = UTCDateTime('2010-08-31T08:02:17').timestamp,
                                description = 'Some spikes.',
                                agency_uri = project.activeUser.agency_uri,
                                author_uri = project.activeUser.author_uri,
                                creation_time = UTCDateTime().isoformat())
        cat_orm.events.append(event_orm)
        db_session.add(cat_orm)
        db_session.commit()
    finally:
        db_session.close()

    return project



def clear_project_database_tables(project):
    project.connect2Db()
    project.dbMetaData.reflect(project.dbEngine)
    tables_to_clear = [table for table in reversed(project.dbMetaData.sorted_tables) if table.key.startswith(project.slug)]
    for cur_table in tables_to_clear:
        project.dbEngine.execute(cur_table.delete())


def clear_database_tables(db_dialect, db_driver, db_user, db_pwd, db_host, db_name, project_name):
    from sqlalchemy import create_engine, MetaData

    project_slug = project_name.lower().replace(' ', '_')

    if db_driver is not None:
        dialect_string = db_dialect + "+" + db_driver
    else:
        dialect_string = db_dialect

    if db_pwd is not None:
        engine_string = dialect_string + "://" + db_user + ":" + db_pwd + "@" + db_host + "/" + db_name
    else:
        engine_string = dialect_string + "://" + db_user + "@" + db_host + "/" + db_name

    db_engine = create_engine(engine_string)
    db_engine.echo = True
    db_metadata = MetaData(db_engine)

    db_metadata.reflect(db_engine)
    tables_to_clear = [table for table in reversed(db_metadata.sorted_tables) if table.key.startswith(project_slug)]
    for cur_table in tables_to_clear:
        db_engine.execute(cur_table.delete())


def drop_database_tables(db_dialect, db_driver, db_user, db_pwd, db_host, db_name, project_name):
    from sqlalchemy import create_engine, MetaData

    project_slug = project_name.lower().replace(' ', '_')

    if db_driver is not None:
        dialect_string = db_dialect + "+" + db_driver
    else:
        dialect_string = db_dialect

    if db_pwd is not None:
        engine_string = dialect_string + "://" + db_user + ":" + db_pwd + "@" + db_host + "/" + db_name
    else:
        engine_string = dialect_string + "://" + db_user + "@" + db_host + "/" + db_name

    db_engine = create_engine(engine_string)
    db_engine.echo = True
    db_metadata = MetaData(db_engine)

    db_metadata.reflect(db_engine)
    tables_to_drop = [table for table in reversed(db_metadata.sorted_tables) if table.key.startswith(project_slug)]
    db_metadata.drop_all(tables = tables_to_drop)


def drop_project_database_tables(project):
    project.connect2Db()
    project.dbMetaData.reflect(project.dbEngine)
    tables_to_remove = [table for key, table in list(project.dbMetaData.tables.items()) if key.startswith(project.slug)]
    project.dbMetaData.drop_all(tables = tables_to_remove)


def remove_project_filestructure(project):
    shutil.rmtree(project.projectDir)


def remove_project(project_file, user_name, user_pwd):
    psybase = create_psybase()
    userdata = {}
    userdata['user'] = user_name
    userdata['pwd'] = user_pwd
    try:
        load_success = psybase.load_json_project(project_file, user_name, user_pwd, update_db = False)
        if load_success:
            drop_project_database_tables(psybase.project)
            remove_project_filestructure(psybase.project)
    finally:
        psybase.stop_project_server()


def clean_unittest_database():
    db_dialect = 'mysql'
    db_user = 'unit_test'
    db_host = 'localhost'
    db_name = 'psysmon_unit_test'
    project_name = 'Unit Test'
    db_pwd = 'test'
    db_driver = None

    drop_database_tables(db_dialect, db_driver, db_user, db_pwd, db_host, db_name, project_name)


def compute_synthetic_seismogram(length, sps, wavelet_offset, amp = 1., snr = None):
    ''' Compute a synthetic seismogram.
    '''
    wavelet = compute_wavelet(amp = 1., sps = sps)
    seismo = np.zeros(length * sps)
    offset_smp = int(wavelet_offset * sps)
    seismo[offset_smp] = 1.
    seismo = scipy.convolve(seismo, wavelet, 'full')
    seismo = seismo[:length * sps]

    if snr is not None and snr > 0:
        noise = np.random.normal(size = len(seismo)) / float(snr)
        seismo = seismo + noise

    seismo = seismo * amp

    return seismo


def compute_wavelet(amp, sps):
    ''' Compute a minimum phase wavelet.
    '''
    # Create a test wavelet.
    fc = 10.
    fn = old_div(fc, (old_div(sps,2)))

    # Create a butterworth filter. The butterworth wavelet is minimum-phase.
    b,a = scipy.signal.butter(4, fn)
    # Create an impulse signal.
    impulse = np.zeros(1000)
    impulse[0] = 1
    # Compute the impulse response of the filter.
    data = scipy.signal.lfilter(b, a, impulse)
    data = old_div(data, np.max(np.abs(data)))
    data = data * amp

    return data
