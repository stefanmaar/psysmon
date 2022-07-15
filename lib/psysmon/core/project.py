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
'''
Module for handling the pSysmon project and users.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the classes for the project and user management.
'''


#from future import standard_library
#standard_library.install_aliases()
from builtins import zip
from builtins import object
import glob
import json
import weakref
import logging
import os
import sys
import _thread
import subprocess
import copy
try:
    import wx
    from pubsub import pub
    from wx import CallAfter
    use_pub = True
except Exception:
    # psysmon has been installed in headless mode.
    use_pub = False
    pass
    
from datetime import datetime
import psysmon
import psysmon.core.base
from psysmon.core.error import PsysmonError
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import obspy.core
import obspy.core.utcdatetime as utcdatetime
import psysmon.cec
from psysmon.core.preferences_manager import PreferencesManager
import psysmon.core.util as psy_util
import psysmon.core.json_util
from psysmon.packages.geometry.db_inventory import DbInventory
import psysmon.core.database_util as db_util


class Project(object):
    ''' The psysmon project.

    The psysmon project handles low level communication with the database, 
    provides the waveclients, handles the collection nodes and collections, 
    manages the file structure and manages the users.

    Parameters
    ----------
    psybase : :class:`~psysmon.core.base.Base`
        The related pSysmon base instance.

    name : String
        The name of the project.

    base_dir : String
        The base directory of the project.

    user : List of :class:`~User` instance
        The users associated with the project.

    dbDialect : String, optional
        The database dialect to be used by sqlalchemy (default: mysql).

    dbDriver : String, optional
        The database driver to be used by sqlalchemy (default: None).

    dbHost : String, optional
        The database host (default: localhost).

    dbName : String, optional
        The name of the database associated with the project (default: "").

    pkg_version : Dictionary of Strings, optional
        The package versions used by the project. The name of 
        the package is the key of the dictionary (default: {}).

    createTime : :class:`~psysmon.core.UTCDateTime`, optional
        The time when the project has been created (default: UTCDateTime())

    dbTables : Dictionary of Strings, optional
        The database tablenames used by the project. The name of the table 
        (without prefix) is the key of the dictionary (default: {}).

    Attributes
    ----------
    activeUser : :class:`~User' instance
        The currently active user running the project.

    base_dir : String
        The project's base directory. The *projectDir* resides in this directory.

    createTime : :class:`obspy.core.UTCDateTime.UTCDateTime` instance
        The time when the project has been created.

    cur : 
        The mySQL database cursor.

    dbBase : 
        The sqlalchemy base class created by declarative_base().

    dbDialect : String
        The database engine to be used. See http://docs.sqlalchemy.org/en/latest/core/engines.html# 
        for the available database dialects.

    dbDriver : String
        The database driver to be used. Of course, the selected database API 
        has to be installed.

    dbEngine : :class:`~sqlalchemy.engine.base.Engine`
        The sqlalchemy database engine.

    dbHost : String
        The host URL on which the mySQL database server is running.

    dbMetaData : :class:`~sqlalchemy.schema.MetaData`
        The sqlalchemy metadata instance.

    dbName : String
        The mySQL database name.
        The database of the project is named according tto the admin unser 
        using *psysmon_* as a prefix (e.g.: psysmon_ADMINUSERNAME).

    dbSessionClass : :class:`~sqlalchemy.orm.session.Session`
        The sqlalchemy session class. This is used to create database sessions.
        Don't use this Attribute directly, call :meth:`getDbSession`.

    dbTables : Dictionary of sqlalchemy mapper classes.
        A dictionary of the project database table mapper classes.
        The name of the table is the key.

    pkg_version : Dictionary of Strings
        The package version strings of the packages which were present 
        when the project was created. The name of the package is the 
        key of the dictionary.

    db_version : Dictionary of Strings
        The package version strings of the packages for which a database 
        table was created. The name of the package is the key of the 
        dictionary.

    logger : :class:`logging.logger`
        The logger instance.

    name : String
        The project name.

    projectDir : String
        The project directory.

    projectFile : String
        The project file holding all project settings.
        It is saved in the projectDir folder.

    psybase : :class:`psysmon.core.base.Base`
        The related pSysmon base instance.

    rid : String
        The resource identifier of the current project-user:
        smi:AGENCY_URI.AUTHOR_URI/psysmon/PROJECT_NAME

        It is used for QuakeML compatible resource identification.

    saved : Boolean
        Is the project saved?

    slug : String
        A lowercase word with no blanks representing a compact 
        form of the project name. The slug is the lowercas version of the name 
        with all blanks replaced by underlines.

    user : List of :class:`User` instances
        A list of users associated with the project.
        The user creating the project is always the admin user.

    waveclient : Dictionary of :class:`psysmon.core.waveclient.WaveClient' instances
        The waveclients available for the project. The key of the dictionary 
        is the name of the waveclient.

    defaultWaveclient : String
        The name of the default waveclient. The default waveclient is used if 
        no individual assignement of a SCNL data stream to a data source is 
        available.
    '''


    def __init__(self, name, user,
                 psybase = None, base_dir = '',
                 dbDialect='mysql', dbDriver=None, dbHost='localhost', 
                 pkg_version = None, db_version = {}, dbName="",
                 db_table_version = None,
                 createTime=None, dbTables={}):
        '''The constructor.

        Create an instance of the Project class.

        Parameters
        ----------
        psybase : :class:`~psysmon.core.base.Base`
            The related pSysmon base instance.

        name : String
            The name of the project.

        base_dir : String
            The base directory of the project.

        user : :class:`~User` instance
            The admin user of the project.

        dbDialect : String, optional
            The database dialect to be used by sqlalchemy (default: mysql).

        dbDriver : String, optional
            The database driver to be used by sqlalchemy (default: None).

        dbHost : String, optional
            The database host (default: localhost).

        dbName : String, optional
            The name of the database associated with the project (default: "").

        createTime : :class:`~psysmon.core.UTCDateTime`, optional
            The time when the project has been created (default: UTCDateTime())

        dbTables : Dictionary of Strings, optional
            The database tablenames used by the project. The name of the table 
            (without prefix) is the key of the dictionary (default: {}).
    
        pkg_version : Dictionary of Strings
            The package version strings of the packages which were present 
            when the project was created. The name of the package is the 
            key of the dictionary.

        db_version : Dictionary of Strings
            The package version strings of the packages for which a database 
            table was created. The name of the package is the key of the 
            dictionary.
        '''

        # The logger.
        self.logger = psysmon.get_logger(self)

        # The parent psysmon base.
        if psybase is not None:
            self._psybase = weakref.ref(psybase)
        else:
            self._psybase = None

        # The project name.
        self.name = name

        # The slug of the project name.
        self.slug = self.name.lower().replace(' ', '_')

        # The time when the project has been created.
        if createTime is None:
            self.createTime = utcdatetime.UTCDateTime()
        else:
            self.createTime = createTime

        # The project's base directory. 
        self.base_dir = base_dir

        # The database engine to be used.
        self.dbDialect = dbDialect

        # The database driver to be used.
        self.dbDriver = dbDriver

        # The host on which the mySQL database server is running.
        self.dbHost = dbHost

        # The mySQL database name.
        if not dbName:
            self.dbName = "psysmon_" + user.name
        else:
            self.dbName = dbName

        # A dictionary of the project databaser table names.
        self.dbTables = dbTables

        # The sqlAlchemy database base instance.
        self.dbBase = None

        # The sqlAlchemy database session.
        self.dbSessionClass = None

        # The project file.
        self.projectFile = self.slug +".ppr"

        # The version dictionary of the package versions.
        self.pkg_version = {}
        if pkg_version is None:
            for cur_pkg in self.psybase.packageMgr.packages.values():
                self.pkg_version[cur_pkg.name] = cur_pkg.version
        else:
            self.pkg_version = pkg_version

        # The database table versions.
        self.db_table_version = {}
        if db_table_version is not None:
            self.db_table_version = db_table_version


        # The version dictionary of the packages which created at least 
        # one database table.
        self.db_version = db_version

        # Is the project saved?
        self.saved = False

        # The thread lock object.
        self.threadMutex = None

        # A list of users associated with this project.
        self.user = []

        # The currently active user.
        self.activeUser = None

        # Add the user(s) to the project user list.
        if isinstance(user, list):
            self.user.extend(user)
        else:
            self.user.append(user)

        self.setActiveUser(self.user[0].name)


        # The project's waveclients.
        self.waveclient = {}

        # The default waveclient.
        self.defaultWaveclient = None

        # The association of the SCNLs to the data sources (the waveclients).
        self.scnlDataSources = {}

        # The project preferences.
        self.pref_manager = PreferencesManager()

        # The geometry inventory.
        self.geometry_inventory = None


    @property
    def psybase(self):
        if self._psybase is not None:
            return self._psybase()
        else:
            return self._psybase

    @psybase.setter
    def psybase(self, value):
        if value is not None:
            self._psybase = weakref.ref(value)
        else:
            self._psybase = None


    @property
    def projectDir(self):
        return os.path.join(self.base_dir, self.slug)

    @property
    def rid(self):
        ''' The resource id of the current project-user.

        Returns
        -------
        rid : String
            The resource id of the current project user:
            smi:AGENCY_URI.AUTHOR_URI/psysmon/PROJECT_NAME
        '''
        project_uri = self.slug
        return 'smi:' + self.activeUser.get_rid() + '/psysmon/' + project_uri


    ## The __getstate__ method.
    #
    # Remove the project instance before pickling the instance.
    def __getstate__(self):
        result = self.__dict__.copy()

        # The following attributes can't be pickled and therefore have
        # to be removed.
        # These values have to be reset when loading the project.
        del result['logger']
        result['_psybase'] = None
        result['dbEngine'] = None
        result['dbSessionClass'] = None
        result['dbBase'] = None
        result['dbMetaData'] = None
        result['dbTables'] = {}
        result['waveclient'] = {}
        result['threadMutex'] = None
        result['geometry_inventory'] = None

        return result


    def __setstate__(self, d):
        ''' Fill missing attributes after unpickling.

        '''
        self.__dict__.update(d) # I *think* this is a safe way to do it

        # Track some instance attribute changes.
        if not "logger" in dir(self):
            self.logger = psysmon.get_logger(self)


    def export_data(self, uri, data):
        ''' Register data to be exported by the project server.
        '''
        self.psybase.project_server.register_data(uri, data)


    def load_geometry_inventory(self):
        ''' Load the geometry inventory from the database.

        The waveclient doesn't track changes of the geometry database
        after the inventory was loaded. If changes where made to the
        geometry database, the inventory of the waveclient has to be
        reloaded.
        '''
        self.geometry_inventory = DbInventory.load_inventory(self)



    def getPlugins(self, name):
        ''' Get the available plugins for a specified class name.

        Parameters
        ----------
        name : Tuple or list of String
            The name of the class for which the plugins should be returned.

        Returns
        -------
        plugins : List of plugin objects
            A list of plugin objects which are associated with the specified class name.

        See also
        --------
        psysmon.core.plugins
        psysmon.core.plugins.PluginNode
        psysmon.core.packageSystem.PackageManager
        '''
        plugins = []

        # Check for single string arguments.
        if isinstance(name, str):
            name = (name,)

        for curName in name:
            if curName in iter(self.psybase.packageMgr.plugins.keys()):
                plugins.extend([curPlugin() for curPlugin in self.psybase.packageMgr.plugins[curName]])
        return plugins



    def getProcessingNodes(self, selection = ('common',)):
        ''' Get all available processing Nodes.

        '''
        procNodes = []

        # Check for single string arguments.
        if isinstance(selection, str):
            selection = (selection, )

        for curKey in selection:
            if curKey in iter(self.psybase.packageMgr.processingNodes.keys()):
                procNodes.extend([curNode() for curNode  in self.psybase.packageMgr.processingNodes[curKey]])

        return procNodes



    def setCollectionNodeProject(self):
        '''Set the project attribute of each node in all collections of 
        the project.

        '''
        for curUser in self.user:
            for curCollection in curUser.collection.values():
                curCollection.set_project(self)


    def addWaveClient(self, waveclient):
        ''' Add a waveclient instance to the project.

        Parameters
        ----------
        waveclient : :class:`~psysmon.core.waveclient.PsysmonDbWaveClient`, :class:`~psysmon.core.waveclient.EarthwormWaveClient`, 
            The waveclient to be added to the project. Usually this 
            is an instance of a class derived from WaveClient.
        '''
        if waveclient.name in iter(self.waveclient.keys()):
            self.logger.error('The waveclient with name %s already exits.\nRemove it first to avoid troubles.', waveclient.name)
            return

        self.waveclient[waveclient.name] = waveclient


    def removeWaveClient(self, name):
        ''' Remove the waveclient with name 'name' from the project.
        The client with the name 'main client' can't be removed from 
        the project. The main client is the default psysmon database 
        client.

        Parameters
        ----------
        name : String
            The name of the waveclient to remove from the project.

        Returns
        -------
        waveclient : waveclient object
            The waveclient removed from the project.
        '''
        if name == 'main client':
            return None
        if name in iter(self.waveclient.keys()):
            return self.waveclient.pop(name)



    def handleWaveclientNameChange(self, oldName, client):
        ''' Make all changes needed if the name of a waveclient has been changed.

        '''
        # Change the key in the waveclient dictionary.
        self.removeWaveClient(oldName)
        self.addWaveClient(client)

        # Change the default waveclient if needed.
        if self.defaultWaveclient == oldName:
            self.defaultWaveclient = client.name


    def request_data_stream(self, start_time, end_time, scnl):
        ''' Get a data stream from the waveclient(s).

        Parameters
        ----------
        startTime : UTCDateTime
            The begin datetime of the data to fetch.

        endTime : UTCDateTime
            The end datetime of the data to fetch.

        scnl : List of Tuples (STATION, CHANNEL, NETWORK, LOCATION)
            The channels for which to get the waveform data.

        Returns
        -------
        stream : :class:`obspy.core.Stream`
            The requested waveform data. All traces are packed into one stream.

        '''
        collection = self.getActiveCollection()
        data_sources = collection.data_sources

        self.logger.debug('Requesting data for scnl: %s.', scnl)
        self.logger.debug('data_sources: %s.', data_sources)

        stream = obspy.core.Stream()

        waveclients = [data_sources[x] for x in scnl]
        unique_wc = list(set(waveclients))
        scnl_waveclients = {}
        for cur_wc in unique_wc:
            scnl_waveclients[cur_wc] = [x[0] for x in zip(scnl, waveclients) if x[1] == cur_wc]

        self.logger.debug("Using waveclients: %s.", scnl_waveclients)

        for cur_name in scnl_waveclients.keys():
            curWaveclient = self.waveclient[cur_name]
            curStream =  curWaveclient.getWaveform(startTime = start_time,
                                                   endTime = end_time,
                                                   scnl = scnl)
            if curStream:
                stream += curStream

        return stream




    def connect2Db(self):
        '''Connect to the mySQL database.

        This method creates the database connection and the database cursor 
        needed to execute queries. The active user is used to connect to the 
        database.

        Parameters
        ----------
        passwd : String
            The database password to be used.
        '''
        if self.dbDriver:
            dialectString = self.dbDialect + "+" + self.dbDriver
        else:
            dialectString = self.dbDialect

        if self.activeUser.pwd:
            engineString = dialectString + "://" + self.activeUser.name + ":" + self.activeUser.pwd + "@" + self.dbHost + "/" + self.dbName
        else:
            engineString = dialectString + "://" + self.activeUser.name + "@" + self.dbHost + "/" + self.dbName

        # Set the character encoding of the database queries.
        engineString = engineString + "?charset=utf8"

        self.dbEngine = create_engine(engineString)
        self.dbEngine.echo = False
        self.dbMetaData = MetaData(self.dbEngine)
        self.dbBase = declarative_base(metadata = self.dbMetaData)
        self.dbSessionClass = sessionmaker(bind=self.dbEngine)


    def getDbSession(self):
        ''' Create a sqlAlchemy database session.

        Returns
        -------
        session : :class:`orm.session.Session`
            A sqlAlchemy database session.
        '''
        return self.dbSessionClass()


    def setActiveUser(self, user_name, user_pwd = None):
        '''Set the active user of the project.

        Parameters
        ----------
        userName : String
            The name of the user to activate.

        Returns
        -------
        userCreated : Boolean
            Has the user been created successfully?
        '''
        for curUser in self.user:
            if curUser.name == user_name:
                if user_pwd is not None: 
                    curUser.pwd = user_pwd
                self.activeUser = curUser
                #self.connect2Db(pwd)
                return True

        return False


    def createDirectoryStructure(self):
        '''Create the project directory structure.

        Create all necessary folders in the projects projectDir.
        '''
        if not os.path.exists(self.projectDir):
            os.makedirs(self.projectDir)

            ## The project's data directory.
            self.dataDir = os.path.join(self.projectDir, "data")
            os.makedirs(self.dataDir)

            ## The project's temporary directory.
            self.tmpDir = os.path.join(self.projectDir, "tmp")
            os.makedirs(self.tmpDir)

            ## The project's collection directory.
            self.collectionDir = os.path.join(self.projectDir, "collection")
            os.makedirs(self.collectionDir)
            for cur_user in self.user:
                os.makedirs(os.path.join(self.collectionDir, cur_user.name))

        else:
            msg = "Cannot create the directory structure, the project directory {:s} doesn't exist.".format(self.projectDir)
            self.logger.error(msg)
            raise Exception(msg)


    def updateDirectoryStructure(self):
        '''Update the project directory structure.

        Check the completeness of the project directory and add 
        missing folders if necessary.
        '''
        if os.path.exists(self.projectDir):
            ## The project's data directory.
            self.dataDir = os.path.join(self.projectDir, "data")

            if not os.path.exists(self.dataDir):
                self.logger.warning("The project data directory %s doesn't exist. Creating it.",
                                     self.dataDir)
                os.makedirs(self.dataDir)

            ## The project's temporary directory.
            self.tmpDir = os.path.join(self.projectDir, "tmp")

            if not os.path.exists(self.tmpDir):
                self.logger.warning("The project temporary directory %s doesn't exist.",
                                    self.tmpDir)
                os.makedirs(self.tmpDir)

            ## The project's collection directory.
            self.collectionDir = os.path.join(self.projectDir, "collection")

            if not os.path.exists(self.collectionDir):
                self.logger.warning("The project collection directory %s doesn't exist. Creating it.",
                                    self.collectionDir)
                os.makedirs(self.collectionDir)

            for cur_user in self.user:
                user_dir = os.path.join(self.collectionDir, cur_user.name)
                if not os.path.exists(user_dir):
                    self.logger.warning("The user collection directory %s doesn't exist. Creating it." ,
                                        user_dir)
                    os.makedirs(user_dir)

        else:
            msg = "Cannot update the directory structure, the project directory {:s} doesn't exist.".format(self.projectDir)
            self.logger.error(msg)
            raise Exception(msg)


    def createDatabaseStructure(self, packages):
        '''Create the project's database structure.

        The createDatabaseStructure method is used to create the database 
        tables when a new project is created. First, the database structure is 
        loaded using the :meth:`loadDatabaseStructure`. Next, the sqlalchemy 
        MetaData instance is used to create the database tables.

        Parameters
        ----------
        packages : Dictionary of :class:`~psysmon.core.packageSystem.Package` instances.
            The packages to be used for the database structure creation.
            The key of the dictionary is the package name.
        '''
        self.loadDatabaseStructure(packages)

        self.dbMetaData.create_all()


    def loadDatabaseStructure(self, packages, update_db = True):
        '''Load the project's database structure.

        In pSysmon, each package can create its own database tables. 
        pSysmon uses the sqlalchemy database abstraction layer (DAL). The 
        database tables are created in the package's __init__.py file using 
        the sqlalchemy declarative mapping classes. These classes are defined 
        in the package's databaseFactory function.

        During pSysmon startup, from each package the databaseFactory method 
        is saved in the databaseFactory attribute of the 
        :class:`~psysmon.core.packageSystem.Package` instance. 

        The loadDatabaseStructure iterates over all packages and checks for 
        existing databaseFactory methods. If present, they are executed to 
        retrieve the mapping classes. These classes are saved in the dbTables 
        attribute and can be used by everyone to access the database tables.

        Parameters
        ----------
        packages : Dictionary of :class:`~psysmon.core.packageSystem.Package` instances.
            The packages to be used for the database structure creation.
            The key of the dictionary is the package name.

        update_db : Boolean
            True if the an update of the database tables should be done.
            False if no update should be done.
        '''

        if not self.dbBase:
            self.connect2Db()

        packages_with_dbf = [(key, pkg) for key, pkg in packages.items() if pkg.databaseFactory]
        packages_with_dbf = dict(packages_with_dbf)

        packages_wo_dep = [(key, pkg) for key, pkg in packages_with_dbf.items() if len(pkg.dependency) == 0]
        packages_wo_dep = dict(packages_wo_dep)
        packages_w_dep = [(key, pkg) for key, pkg in packages_with_dbf.items() if len(pkg.dependency) > 0]
        packages_w_dep = dict(packages_w_dep)
        
        sorted_keys = sorted(list(packages_wo_dep.keys()))
        sorted_packages = [packages_wo_dep[x] for x in sorted_keys]

        remaining_packages = packages_w_dep.copy()
        for k in range(len(packages_w_dep)):
            for key, pkg in remaining_packages.items():
                dependency = pkg.dependency
                dependency_ok = True
                for cur_depend in dependency:
                    if cur_depend not in sorted_keys:
                        dependency_ok = False
                        break
                    
                if dependency_ok:
                    sorted_keys.append(key)
                    sorted_packages.append(pkg)

            remaining_packages = [(key, pkg) for key, pkg in packages_w_dep.items() if key not in sorted_keys]
            remaining_packages = dict(remaining_packages)
            if len(remaining_packages) == 0:
                break

        if len(remaining_packages) > 0:
            self.logger.warning("There exist packages for which the dependencies are not fulfilled.")
            self.logger.warning("Packages with missing dependencies: %s.",
                                list(remaining_packages.keys()))
            
        save_needed = False
        for curPkg in sorted_packages:
            if not curPkg.databaseFactory:
                self.logger.warning("%s: No databaseFactory found. Package provides no database tables.", curPkg.name)
                continue
            else:
                self.logger.info("%s: databaseFactory found. Retrieving the table definitions.", curPkg.name)
                tables = curPkg.databaseFactory(self.dbBase)

                for curTable in tables:
                    # Add the table prefix.
                    curName = curTable.__table__.name
                    curTable.__table__.name = self.slug + "_" + curTable.__table__.name
                    table_version_changed = False
                    update_success = True

                    if update_db:
                        cur_version = psy_util.Version(curTable._version)

                        try:
                            # TODO: Create a database backup using mysqldump in
                            # case that a database migration is needed.

                            # Check for changes of the database table.
                            if curName not in iter(self.db_table_version.keys()):
                                self.logger.info("%s - No table version found in the project. This is a new table.",
                                                 curName)
                                update_success = db_util.db_table_migration(table = curTable,
                                                                            engine = self.dbEngine,
                                                                            prefix = self.slug + '_')
                                table_version_changed = True
                            elif cur_version > self.db_table_version[curName]:
                                self.logger.info("%s - The package table version %s is larger than the one currently used in the database (%s). An update is needed.",
                                                 curName, cur_version, self.db_table_version[curName])
                                update_success = db_util.db_table_migration(table = curTable,
                                                                            engine = self.dbEngine,
                                                                            prefix = self.slug + '_')
                                table_version_changed = True

                        except:
                            update_success = False
                            self.logger.exception("Couldn't migrate the table %s.", curName)

                    self.dbTables[curName] = curTable
                    if table_version_changed and update_success:
                        self.db_table_version[curName] = cur_version
                        save_needed = True

        if save_needed:
            # Save the project to update the package versions.
            self.logger.info("Saving the project file because of changes in the database table versions.")
            self.save_json()




    def save(self):
        '''Save the project to a file.

        Use the shelve module to save the project settings to a file.
        '''
        import shelve

        db = shelve.open(os.path.join(self.projectDir, self.projectFile))
        db['name'] = self.name
        db['dbDriver'] = self.dbDriver
        db['dbDialect'] = self.dbDialect
        db['dbHost'] = self.dbHost
        db['dbName'] = self.dbName
        db['pkg_version'] = self.pkg_version
        db['db_version'] = self.db_version
        db['user'] = self.user
        db['createTime'] = self.createTime
        db['waveclient'] = [(x.name, x.mode, x.options) for x in self.waveclient.values()]
        db['defaultWaveclient'] = self.defaultWaveclient
        db['scnlDataSources'] = self.scnlDataSources
        db.close()
        self.saved = True 


    def save_json(self):
        ''' Save the project to a JSON formatted file.

        '''
        # Save the project file.
        file_content = {'project': self}
        file_container = psysmon.core.json_util.FileContainer(file_content)
        with open(os.path.join(self.projectDir, self.projectFile), mode = 'w') as fid:
            json.dump(file_container, fp = fid, cls = psysmon.core.json_util.ProjectFileEncoder)

        # Save each collections of each user.
        for cur_user in self.user:
            cur_filepath = os.path.join(self.projectDir, self.collectionDir)
            cur_user.save_collections(cur_filepath)



    def addCollection(self, name):
        '''Add a collection to the project.

        The collection is added to the collection list of the active user.

        Parameters
        ----------
        name : String
            The name of the new collection.
        '''
        self.activeUser.addCollection(name, self)


    def getCollection(self):
        '''Get ALL collections of the currently active user.

        Returns
        -------
        collections : Dictionary of :class:`~psysmon.core.base.Collection` instances. 
            ALL collections of the currently active user.(key: collection name)
        '''
        return self.activeUser.collection


    def getActiveCollection(self):
        '''Get the ACTIVE collection of the active user.

        Returns
        -------
        collection : Dictionary of :class:`~psysmon.core.base.Collection` instances. 
            The ACTIVE collection of the currently active user.(key: collection name)
        '''
        return self.activeUser.activeCollection


    def setActiveCollection(self, name):
        '''Set the active collection of the active user.

        Parameters
        ----------
        name : String
            The name of the collection which should be activated.
        '''
        self.activeUser.setActiveCollection(name)


    def addNode2Collection(self, nodeTemplate, position=-1):
        '''Add a node to the active collection of the active user.

        Parameters
        ----------
        nodeTemplate : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node to be added to the collection.
        position : Integer
            The position before which to add the node to the 
            collection. -1 to add it at the end of the collection (default).
        '''
        #node = copy.deepcopy(nodeTemplate)
        node = nodeTemplate()
        node.project = self
        self.activeUser.addNode2Collection(node, position)


    def addNode2Looper(self, nodeTemplate, position, looper_pos = 0):
        ''' Add a looper child node to a looper node.
        '''
        node = nodeTemplate()
        node.project = self
        try:
            self.activeUser.addNode2Looper(node, position, looper_pos)
        except:
            self.logger.exception("Couldn't add the collection node to a looper node.")


    def removeNodeFromCollection(self, position):
        '''Remove a node from the active collection of the active user.

        Parameters
        ----------
        position : Integer
            The position of the node to remove.
        '''
        self.activeUser.removeNodeFromCollection(position)


    def getNodeFromCollection(self, position):
        '''Get a node from the active collection of the active user.

        Parameters
        ----------
        position : Integer 
            The position of the node to get.

        Returns
        -------
        collectionNode : :class:`~psysmon.core.packageNodes.CollectionNode` instance. 
            The requested collection node.
        '''
        return self.activeUser.getNodeFromCollection(position)


    def editNode(self, position):
        '''Edit a node of the active collection of the active user.

        Editing a node means calling the *edit()* method of the 
        :class:`~psysmon.core.packageNodes.CollectionNode` instance.

        Parameters
        ----------
        position : Integer
            The position of the node to edit.
        '''
        self.activeUser.editNode(position)


    def executeNode(self, position):
        '''Execute a node of the active collection of the active user.

        Executing a node means calling the *execute()* method of the 
        :class:`~psysmon.core.packageNodes.CollectionNode` instance.

        Parameters
        ----------
        position : Integer
            The position of the node to edit.
        '''
        self.activeUser.executeNode(position)


    def executeCollection(self):
        '''Execute the active collection of the active user.

        '''
        self.activeUser.executeCollection(self)



    def log(self, mode, msg):
        '''Send a general log message.

        Parameters
        ----------
        mode : String
            The mode of the log message.
        msg : String
            The log message to send.
        '''
        msgTopic = "log.general." + mode




## The pSysmon user.
# 
# The user class holds the details of the user and the userspecific project
# variables (e.g. collection, settings, ...).
class User(object):
    '''The pSysmon user class.

    A pSysmon project can be used by multiple users. For each user, an instance 
    of the :class:`User` class is created. The pSysmon users are managed within 
    the pSysmon :class:`Project`.

    Each user holds a set of uniform resource identifier attributes (agency_uri, 
    author_uri) which are used to build a resource identifier compatible to the 
    QuakeML definition. The psysmon resource identifier is built the following 
    way: smi:AGENCY_URI.AUTHOR_URI/psysmon/PROJECT_NAME

    Parameters
    ----------
    user_name : String
        The user name.

    user_pwd : String
        The database password of the user.

    user_mode : String
        The user privileges. Currently allowed values are:

        - admin
        - editor

    author_name : String
        The real name of the user.

    author_uri : String
        The uniform resource identifier of the author.

    agency_name : String
        The name of the agency to which the author is affiliated to.

    agency_uri : String
        The uniform resource identifier of the agency.

    Attributes
    ----------
    activeCollection : :class:`~psysmon.core.base.Collection`
        The currently active collection of the user.

    collection : Dictionary of :class:`~psysmon.core.base.Collection` instances
        The collections created by the user.

        The collections are stored in a dictionary with the collection name as 
        the key.

    mode : String
        The user mode (admin, editor).

    name : String
        The database user name.

    pwd : String
        The database password of the user.

    author_name : String
        The real name of the user.

    author_uri : String
        The uniform resource identifier of the author. 

    agency_name : String
        The name of the agency to which the user is affiliated to.

    agency_uri : String
        The uniform resource identifier of the author.

    '''

    def __init__(self, user_name, user_pwd, user_mode, author_name, author_uri,
                 agency_name, agency_uri):
        '''The constructor.

        Parameters
        ----------
        user_name : String
            The user name.

        user_pwd : String
            The database password of the user.

        user_mode : String
            The user privileges. Currently allowed values are:

            - admin
            - editor

        author_name : String
            The real name of the user.

        author_uri : String
            The uniform resource identifier of the author.

        agency_name : String
            The name of the agency to which the author is affiliated to.

        agency_uri : String
            The uniform resource identifier of the agency.
        '''

        # The logger.
        self.logger = psysmon.get_logger(self)

        ## The user name.
        self.name = user_name

        # The user's password.
        self.pwd = user_pwd

        ## The user mode.
        #
        # The user privileges. 
        # Allowed values are: admin, editor.
        self.mode = user_mode

        # The real name of the author.
        self.author_name = author_name

        # The URI of the author.
        self.author_uri = author_uri

        # The name of the agency of the author.
        self.agency_name = agency_name

        # The URI of the agency.
        self.agency_uri = agency_uri

        # The user collection.
        self.collection = {}

        # The currently active collection.
        self.activeCollection = None


    ## The __getstate__ method.
    #
    # Remove the project instance before pickling the instance.
    def __getstate__(self):
        result = self.__dict__.copy()

        # The logger can't be pickled. Remove it.
        del result['logger']
        return result


    ## The __setstate__ method.
    #
    # Fill the attributes after unpickling.
    def __setstate__(self, d):
        self.__dict__.update(d) # I *think* this is a safe way to do it
        self.project = None

        # Track some instance attribute changes.
        if not "logger" in dir(self):
            self.logger = psysmon.get_logger(self)

    # TODO: Change this method to a property.
    def get_rid(self):
        ''' Get the resource id of the user.

        Returns
        -------
        rid : String
            The resource id of the user (agency_uri.author_uri).
        '''
        return self.agency_uri.replace(' ', '_') + '.' + self.author_uri.replace(' ', '_')


    def save_collections(self, path):
        ''' Save the collections to json files.

        '''
        for cur_collection in self.collection.values():
            cur_collection.save(os.path.join(path, self.name))

    def load_collections(self, path):
        ''' Load the collections from json files.

        '''
        collection_files = glob.glob(os.path.join(path, self.name, '*.json'))
        for cur_filename in collection_files:
            self.logger.info('Loading collection file {:s}.'.format(cur_filename))
            #cur_filename = os.path.join(path, self.name, cur_name + '.json')
            file_meta = psysmon.core.json_util.get_file_meta(cur_filename)
            decoder = psysmon.core.json_util.get_collection_decoder(version = file_meta['file_version'])
            with open(cur_filename, mode = 'r') as fp:
                try:
                    file_data = json.load(fp, cls = decoder)
                    # Old file versions didn't have the root level dictionary of
                    # the file container.
                    if file_meta['file_version'] >= psysmon.core.util.Version('1.0.0'):
                        self.collection[file_data['collection'].name] = file_data['collection']
                    else:
                        self.collection[file_data.name] = file_data
                except Exception:
                    self.logger.exception("Failed loading the collection from file %s.",
                                          cur_filename)


    def addCollection(self, name, project):
        '''Add a collection to the collection dictionary. The collection 
        name is used as the dictionary key. 

        Parameters
        ----------
        name : String
            The name of the new collection.
        project : :class:`Project`
            The project holding the user.
        '''
        if not isinstance(self.collection, dict):
            self.collection = {}

        if name in iter(self.collection.keys()):
            self.logger.error("The collection already exists.")
            return

        self.collection[name] = psysmon.core.base.Collection(name, tmpDir = project.tmpDir, project = project)
        self.setActiveCollection(name)


    def setActiveCollection(self, name):
        '''Set the active collection.

        Get the collection with the key *name* from the collection 
        dictionary and assign it to the *activeCollection* attribute.

        Parameters
        ----------
        name : String
            The name of the collection which should be activated.
        '''
        if name in iter(self.collection.keys()):
            self.activeCollection = self.collection[name]


    def addNode2Collection(self, node, position):
        '''Add a collection node to the active collection.

        The *node* is added to the currently active collection at *position* 
        using the :meth:`~psysmon.core.base.Collection.addNode` method of the 
        :class:`~psysmon.core.base.Collection` class.

        Parameters
        ----------
        nodeTemplate : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node to be added to the collection.
        position : Integer
            The position before which to add the node to the 
            collection. -1 to add it at the end of the collection (default).

        Raises
        ------
        PsysmonError : :class:`~psysmon.core.util.PsysmonError` 
            Error raised when no active collection is present.
        '''
        if self.activeCollection is not None:
            self.activeCollection.addNode(node, position)
        else:
            raise PsysmonError('No active collection found!')


    def addNode2Looper(self, node, position, looper_pos = 0):
        ''' Add a looper child node to a looper node.
        '''
        if self.activeCollection is not None:
            self.activeCollection.addNode2Looper(node, position, looper_pos)
        else:
            raise PsysmonError('No active collection found!')


    def removeNodeFromCollection(self, position):
        '''Remove a node from the active collection.

        Parameters
        ----------
        position : Integer
            The position of the node to remove.

        Raises
        ------
        PsysmonError : :class:`PsysmonError` 
            Error raised when no active collection is present.
        '''
        if self.activeCollection is not None:
            self.activeCollection.popNode(position)
        else:
            raise PsysmonError('No active collection found!') 


    def getNodeFromCollection(self, position):
        '''Get the node at *position* from the active collection.

        Parameters
        ----------
        position : Integer
            The position of the node to get.

        Returns
        -------
        collectionNode : :class:`~psysmon.core.packageNodes.Collection` 
            The collection node at *position* in the active collection.

        Raises
        ------
        PsysmonError : :class:`PsysmonError` 
            Error raised when no active collection is present.
        '''
        if self.activeCollection is not None:
            return self.activeCollection[position]
        else:
            raise PsysmonError('No active collection found!') 




    def editNode(self, position):
        '''Edit the node at *position* of the active collection.

        Editing a node means calling the :meth:`~psysmon.core.packageNodes.CollectionNode.edit` method of the 
        :class:`~psysmon.core.packageNodes.CollectionNode` instance.

        Parameters
        ----------
        position : Integer
            The position of the node to edit.

        Raises
        ------
        PsysmonError : :class:`PsysmonError` 
            Error raised when no active collection is present.
        '''
        if self.activeCollection is not None:
            self.activeCollection.editNode(position)
        else:
            raise PsysmonError('No active collection found!') 


    def executeNode(self, position):
        '''Execute the node at *position* of the active collection.

        Executing a node means calling the :meth:`~psysmon.core.packageNodes.CollectionNode.execute` method of the 
        :class:`~psysmon.core.packageNodes.CollectionNode` instance.

        Parameters
        ----------
        position : Integer
            The position of the node to edit.

        Raises
        ------
        PsysmonError : :class:`PsysmonError` 
            Error raised when no active collection is present.
        '''
        if self.activeCollection is not None:
            self.activeCollection.executeNode(position)
        else:
            raise PsysmonError('No active collection found!') 


    def executeCollection(self, project):
        '''Execute the active collection.

        Start a new process to execute the currently active collection.
        A deep copy of the collection instance is create and this copy 
        is executed. This is done to prevent runtime interactions 
        when editing the collection node properties after a collection 
        has been executed.

        The start of the execution is logged and a state.collection.execution 
        message is sent to notify eventual listeners of the starting of 
        the execution.

        Parameters
        ----------
        project : :class:`Project`
            The pSysmon project.

        Raises
        ------
        PsysmonError : :class:`PsysmonError` 
            Error raised when no active collection is present.
        '''

        def processChecker(process, procName):
            from time import sleep

            # The time interval to check for process messages [s].
            checkInterval = 2

            # The timeout limit. After this timeout the process is 
            # marked as "not responding". The timeout interval should
            # be larger than the process's heartbeat interval. [s]
            timeout = 10

            procRunning = True
            isZombie = False
            self.logger.debug("Checking process...")
            lastResponse = 0
            while procRunning:
                #self.logger.debug("Waiting for message...")

                procStatus = process.poll()

                #self.logger.debug('procStatus: %s', procStatus)

                if procStatus != None:
                    procRunning = False
                    #self.logger.debug('Process %d has stopped with return code %s.', proc.pid, procStatus)
                    msgTopic = 'state.collection.execution'
                    msg['state'] = 'stopped'
                    msg['pid'] = process.pid
                    msg['returncode'] = process.returncode
                    msg['procName'] = procName
                    msg['curTime'] = datetime.now()
                    CallAfter(pub.sendMessage, msgTopic, msg = msg)

                else:
                    #self.logger.debug('Process %d is still running.', proc.pid)
                    msgTopic = 'state.collection.execution'
                    msg['state'] = 'running'
                    msg['pid'] = process.pid
                    msg['returncode'] = process.returncode
                    msg['procName'] = procName
                    msg['curTime'] = datetime.now()
                    CallAfter(pub.sendMessage, msgTopic, msg = msg)

                sleep(checkInterval)


                # Here is some code using the pipe and the heartbeat of the 
                # collection. I think this caused some unexpected crashes of 
                # the GUI. Might be some event loop race conditions.

                #if parentEnd.poll(checkInterval):
                    #msg = parentEnd.recv()
                    ##print msg
                    #self.logger.debug("Received message: [%s]: %s" % (msg['state'], msg['msg']))
#
                   # # Send the message to the system.
                    #msgTopic = "state.collection.execution"
                   # msg['isError'] = False
                    ##pub.sendMessage(msgTopic, msg)

                    #lastResponse = 0
                    #if msg['state'] == 'stopped':
                    #    procRunning = False
               # else:
                    #lastResponse += checkInterval
                   # self.logger.debug("No message received.")

                #if lastResponse > timeout:
                    #procRunning = False
                   # isZombie = True

            #self.logger.debug("End checking process %d.", proc.pid)


        if self.activeCollection is not None:
            if not project.threadMutex:
                project.threadMutex = _thread.allocate_lock()

            col2Proc = copy.deepcopy(self.activeCollection)
            curTime = datetime.now()
            timeStampString = datetime.strftime(curTime,'%Y%m%d_%H%M%S_%f')
            processName = col2Proc.name + "_" + timeStampString
            col2Proc.procName = col2Proc.name + "_" + timeStampString

            msg = "Executing collection " + col2Proc.name + "with process name: " + processName + "."
            self.logger.info(msg)

            if use_pub:
                msgTopic = "state.collection.execution"
                msg = {}
                msg['state'] = 'starting'
                msg['startTime'] = curTime
                msg['isError'] = False
                msg['pid'] = None
                msg['procName'] = col2Proc.procName
                pub.sendMessage(msgTopic, msg = msg)

            #(parentEnd, childEnd) = multiprocessing.Pipe()
            self.logger.debug("process name: %s" % col2Proc.procName)
            #thread.start_new_thread(processChecker, (p, parentEnd, project.threadMutex))

            # Store all the needed data in a temporary file.
            #import tempfile
            import shelve
            #tmpDir = tempfile.gettempdir()
            filename = os.path.join(project.tmpDir, col2Proc.procName + '.ced')  # ced for Collection Execution Data

            #db = shelve.open(filename.encode('utf-8'), flag='n')
            db = shelve.open(filename, flag='n')
            db['project'] = project
            db['collection'] = col2Proc
            db['package_directories'] = project.psybase.packageMgr.packageDirectories
            db['waveclient'] = [(x.name, x.mode, x.pickle_attributes) for x in project.waveclient.values()]
            db['project_server'] = project.psybase.project_server
            db['pref_manager'] = project.psybase.pref_manager
            db.close()


            # Start the collection using the cecClient as a subprocess.
            cecPath = os.path.dirname(os.path.abspath(psysmon.cec.__file__))
            #proc = subprocess.Popen([sys.executable, os.path.join(cecPath, 'cecSubProcess.py'), filename, col2Proc.procName], 
            #                        stdout=subprocess.PIPE)
            # TODO: Handle the matplotlib backend in the cecSubProcess whether
            # psysmon or psysmomat is used. The matplotlib backend is set in
            # the psysmon or psysmomat script. cecSubProcess is another process
            # and the matplotlib is set there.
            import matplotlib as mpl
            backend = mpl.rcParams['backend']
            proc = subprocess.Popen([sys.executable,
                                     os.path.join(cecPath, 'cecSubProcess.py'),
                                     filename,
                                     col2Proc.procName,
                                     backend])

            if use_pub:
                msgTopic = "state.collection.execution"
                msg = {}
                msg['state'] = 'started'
                msg['startTime'] = curTime
                msg['isError'] = False
                msg['pid'] = proc.pid
                msg['procName'] = col2Proc.procName
                pub.sendMessage(msgTopic, msg = msg)

            # Start the process checker only if the wx GUI is running.
            if psysmon.wx_available and wx.App.Get():
                _thread.start_new_thread(processChecker,
                                         (proc, col2Proc.procName))

        else:
            raise PsysmonError('No active collection found!')



