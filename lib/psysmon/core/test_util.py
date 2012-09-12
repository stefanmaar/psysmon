import logging
import os
import copy
import psysmon
from psysmon.core.base import Base
import psysmon.core.gui as psygui
from psysmon.core.project import User


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
    base_dir = '/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/03_pSysmonProjects'
    user = User(user_name = 'unit_test',
                user_pwd = '',
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
                                           dbHost = db_host
                                          )

    return project


def clear_database(project):
        project.connect2Db()
        project.dbMetaData.reflect(project.dbEngine)
        project.dbMetaData.drop_all()
        project.dbMetaData.clear()



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
