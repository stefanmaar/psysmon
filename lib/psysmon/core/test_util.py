import logging
import tempfile
import os
import os.path
import glob
import shutil
import copy
import psysmon
from psysmon.core.base import Base
import psysmon.core.gui as psygui
from psysmon.core.project import User
from psysmon.packages.geometry.inventory import InventoryXmlParser
from psysmon.packages.geometry.db_inventory import DbInventory


def create_psybase():
    ''' Create the psysmon base instance.

    '''
    # Get the pSysmon base directory.
    psyBaseDir = os.path.abspath(psysmon.__file__)
    psyBaseDir = os.path.dirname(psyBaseDir)

    # Initialize the pSysmon base object.
    psyBase = Base(psyBaseDir)

    return psyBase



def create_dbtest_project(psybase):
    ''' Create a new project with parameters set to access the unit_test test 
    database.
    '''

    name = 'unit_test'
    project_dir = tempfile.mkdtemp()
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
                                           base_dir = project_dir,
                                           user = user,
                                           dbHost = db_host
                                          )

    return project

def create_empty_project(psybase):
    ''' Create a complete project including database.
    '''
    name = 'unit_test'
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
    name = 'unit_test'
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
    db_inventory = DbInventory.from_inventory(name = 'test', project = project, inventory = inventory)
    db_inventory.commit()
    db_inventory.close()

    # Add the waveform directory to the project.
    wf_dir = project.dbTables['waveform_dir']
    wf_diralias = project.dbTables['waveform_dir_alias']
    db_session = project.getDbSession()
    new_wfdir = wf_dir(data_path, '')
    new_alias = wf_diralias(project.activeUser.name,
                            data_path)
    new_wfdir.aliases.append(new_alias)
    db_session.add(new_wfdir)
    db_session.commit()
    db_session.close()
    project.waveclient['main client'].loadWaveformDirList()

    # Import the data files.
    node_template = psybase.packageMgr.getCollectionNodeTemplate('import waveform')
    node = node_template()
    # Create a logger for the node.
    loggerName = __name__+ "." + node.__class__.__name__
    node.logger = logging.getLogger(loggerName)
    node.project = project

    filenames = glob.glob(os.path.join(data_path, 'ZAMG-seis_event00017*.msd'))
    filelist = []
    for cur_file in filenames:
        filelist.append({'format': 'mseed', 'filename': cur_file})
    node.options['inputFiles'] = filelist
    node.execute()


    # Apply the geometry.
    node_template = psybase.packageMgr.getCollectionNodeTemplate('apply geometry')
    node = node_template()
    # Create a logger for the node.
    loggerName = __name__+ "." + node.__class__.__name__
    node.logger = logging.getLogger(loggerName)
    node.project = project
    node.execute()

    return project



def clear_project_database_tables(project):
    project.connect2Db()
    project.dbMetaData.reflect(project.dbEngine)
    tables_to_clear = [table for table in reversed(project.dbMetaData.sorted_tables) if table.key.startswith(project.name)]
    for cur_table in tables_to_clear:
        project.dbEngine.execute(cur_table.delete())


def clear_database_tables(db_dialect, db_driver, db_user, db_pwd, db_host, db_name, project_name):
    from sqlalchemy import create_engine, MetaData

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
    tables_to_clear = [table for table in reversed(db_metadata.sorted_tables) if table.key.startswith(project_name)]
    for cur_table in tables_to_clear:
        db_engine.execute(cur_table.delete())


def drop_database_tables(db_dialect, db_driver, db_user, db_pwd, db_host, db_name, project_name):
    from sqlalchemy import create_engine, MetaData

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
    tables_to_drop = [table for table in reversed(db_metadata.sorted_tables) if table.key.startswith(project_name)]
    db_metadata.drop_all(tables = tables_to_drop)


def drop_project_database_tables(project):
    project.connect2Db()
    project.dbMetaData.reflect(project.dbEngine)
    tables_to_remove = [table for key, table in project.dbMetaData.tables.items() if key.startswith(project.name)]
    project.dbMetaData.drop_all(tables = tables_to_remove)


def remove_project_filestructure(project):
    print "Removing project folder %s.\n" % project.projectDir
    shutil.rmtree(project.projectDir)


def remove_project(project_file, user_name, user_pwd):
    psybase = create_psybase()
    userdata = {}
    userdata['user'] = user_name
    userdata['pwd'] = user_pwd
    psybase.loadPsysmonProject(project_file, user_name, user_pwd)

    drop_project_database_tables(psybase.project)
    remove_project_filestructure(psybase.project)





def prepare_project(test_case):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel(psysmon.logConfig['level'])
        logger.addHandler(psysmon.getLoggerHandler())

        # Get the pSysmon base directory.
        psyBaseDir = '/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/01_src/psysmon/lib/psysmon/'
        psyBaseDir = os.path.dirname(psyBaseDir)

        # Initialize the pSysmon base object.
        psyBase = Base(psyBaseDir)
        #psyBase.scan4Package()

        # Load the pSysmon test project.
        path = "/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/03_pSysmonProjects/test/test.ppr"
        psyBase.loadPsysmonProject(path)

        # Quest for the user and the database password.
        psyBase.project.setActiveUser('stefan','')

        # Load the database structure of the project packages.
        psyBase.project.loadDatabaseStructure(psyBase.packageMgr.packages)

        # Create the project waveclient.
        waveclient = PsysmonDbWaveClient('main client', psyBase.project)
        psyBase.project.addWaveClient(waveclient)
        waveclient = EarthwormWaveClient('earthworm localhost')
        psyBase.project.addWaveClient(waveclient)
        test_case.app =psygui.PSysmonApp()

        nodeTemplate = psyBase.packageMgr.getCollectionNodeTemplate('tracedisplay')
        test_case.node = copy.deepcopy(nodeTemplate)
        test_case.node.project = psyBase.project

        # Create the node logger. This is usually done in the collection.
        loggerName = __name__ + "." + test_case.node.__class__.__name__
        test_case.node.logger = logging.getLogger(loggerName)
