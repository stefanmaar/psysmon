# -*- coding: utf-8 -*-
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
The pSysmon base module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the basic classes needed to run the pSysmon program.
'''

import os
import json
import logging
import shelve
import threading
from datetime import datetime
from psysmon import __version__ as version
import psysmon.core.packageSystem
import psysmon.core.packageNodes
import psysmon.core.project
import psysmon.core.util
import psysmon.core.json_util
import psysmon.core.project_server
from psysmon.core.waveclient import PsysmonDbWaveClient, EarthwormWaveclient
from psysmon.core.error import PsysmonError
import psysmon.core.preferences_manager as pm
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import Pyro4 as pyro


class Base(object):
    '''Handle low level objects of psysmon.

    The Base class is the lowest level class of the pSysmon model. It handles 
    the initialization of the pSysmon packages and stores the package objects.

    Parameters
    ----------
    baseDir : String
        The pSysmon base directory. 


    Attributes
    ----------
    baseDirectory : String
        The pSysmon base directory.
        The base directory is the directory in which the pSysmon program is located.

    logger : :class:`logging`
        The system logger used for debugging and system wide error logging.

    packageDirectory : List of String
        The psysmon packages directories.

    packageMgr : :class:`~psysmon.core.packageSystem.PackageManager`
        The package manager handles the dynamically loaded packages.

    project : :class:`~psysmon.core.project.Project`
        The working pSysmon project.

    version : *String*
        The pSysmon version.


    '''

    def __init__(self, baseDir, package_directory = None, project_server = None, pref_manager = None):
        '''The constructor.

        Create an instance of the Base class.


        Parameters
        ----------
        baseDir : String
            The pSysmon base directory. 

        package_directory : List of String
            Directories outside the baseDir/packages directory which 
            contain pSysmon packages.
        '''

        # The system logger used for debugging and system wide error logging.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Check the baseDir parameter for errors.
        if not isinstance(baseDir, basestring):
            msg = "The baseDir %s should be a string." & baseDir
            raise IndexError(msg)

        if not os.path.isdir(baseDir):
            msg = "The specified directory " + baseDir + " doesn't seem to be a directory."
            raise IndexError(msg)

        # The psysmon base directory.
        self.baseDirectory = baseDir

        # The search path for psysmon packages.
        if package_directory is None:
            self.packageDirectory = [os.path.join(self.baseDirectory, "packages"), ]
        else:
            self.packageDirectory = package_directory

        # The currently loaded pSysmon project.
        self.project = ""

        # The pSysmon version.
        self.version = version

        # The psysmon preferences.
        self.pref_manager = pm.PreferencesManager()
        self.create_preferences()
        if pref_manager is not None:
            self.pref_manager.update(pref_manager)

        # The package manager handling the dynamically loaded packages.
        self.packageMgr = psysmon.core.packageSystem.PackageManager(parent = self,
                                                                    packageDirectories = self.packageDirectory)

        # Load the psysmon packages.
        self.packageMgr.scan4Package()

        # Metadata of the process in which the base instance is running. This
        # is used when creating new processes with cecSubprocess.
        self.process_meta = {}
        self.process_meta['name'] = 'main'
        self.process_meta['pid'] = None

        # The pyro project server lock.
        self.project_server_lock = threading.Lock()

        # The pyro project server state.
        self._project_server_starting = False
        self._project_server_started = False

        # The pyro nameserver name of the project server.
        self.pyro_project_server_name = 'psysmon.project_server'

        # The pyro daemon.
        self.pyro_daemon = None

        # The pyro nameserver.
        self.pyro_nameserver = None

        # The pyro project data server.
        if project_server is None:
            self.project_server = psysmon.core.project_server.ProjectServer()

            # Start the pyro project server.
            self.ps_thread = threading.Thread(target = self.start_project_server)
            self.ps_thread.start()
        else:
            self.project_server = project_server


    def __del__(self):
        '''
        '''
        self.logger.debug("__del__ method: cleaning instance")


    @property
    def project_server_started(self):
        '''
        '''
        self.project_server_lock.acquire()
        cur_state = self._project_server_started
        self.project_server_lock.release()
        return cur_state


    @property
    def project_server_starting(self):
        '''
        '''
        self.project_server_lock.acquire()
        cur_state = self._project_server_starting
        self.project_server_lock.release()
        return cur_state


    def create_preferences(self):
        ''' Create the psysmon preferences items.
        '''
        logging_page = self.pref_manager.add_page('logging')
        log_levels_group = logging_page.add_group('log levels')
        status_group = logging_page.add_group('status')


        # The log levels group items.
        pref_item = pm.SingleChoicePrefItem(name = 'main_loglevel',
                                            label = 'main log level',
                                            limit = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                                            value = 'INFO',
                                            tool_tip = 'The level of the main logger.')
        log_levels_group.add_item(item = pref_item)


        pref_item = pm.SingleChoicePrefItem(name = 'shell_loglevel',
                                            label = 'shell log level',
                                            limit = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                                            value = 'INFO',
                                            tool_tip = 'The level of the logger writing to the shell.')
        log_levels_group.add_item(item = pref_item)


        pref_item = pm.SingleChoicePrefItem(name = 'gui_status_loglevel',
                                            label = 'status log level',
                                            limit = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                                            value = 'INFO',
                                            tool_tip = 'The level of the logger writing to the psysmon status logging area.')
        log_levels_group.add_item(item = pref_item)


        pref_item = pm.SingleChoicePrefItem(name = 'collection_loglevel',
                                            label = 'collection log level',
                                            limit = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                                            value = 'INFO',
                                            tool_tip = 'The level of the logger writing to a log file when executing a collection.')
        log_levels_group.add_item(item = pref_item)



        # The status group items.
        pref_item = pm.IntegerSpinPrefItem(name = 'n_status_messages',
                                            label = '# status messages',
                                            limit = (10,1000),
                                            value = 100,
                                            tool_tip = 'The number of messages to show in the log area status.')
        status_group.add_item(item = pref_item)



    def start_project_server(self):
        ''' Start the pyro project server.
        '''
        self.project_server_lock.acquire()
        self._project_server_starting = True
        pyro.config.SERIALIZER = 'pickle'
        self.pyro_daemon = pyro.Daemon()
        self.pyro_project_server_uri = self.pyro_daemon.register(self.project_server)
        try:
            self.pyro_nameserver = pyro.locateNS()
            # Check if the name is available at the nameserver.
            ns_list = self.pyro_nameserver.list(prefix = 'psysmon.project_server')
            if len(ns_list) > 0:
                ps_id = sorted(ns_list.keys())[-1].split('_')[-1]
                if ps_id.isdigit() is False:
                    ps_id = 1
                else:
                    ps_id = int(ps_id) + 1
                self.pyro_project_server_name = self.pyro_project_server_name + '_' + str(ps_id)
            self.pyro_nameserver.register(self.pyro_project_server_name, self.pyro_project_server_uri)
            self.logger.info('Registered the project_server as %s with pyro uri: %s', 
                              self.pyro_project_server_name, 
                              self.pyro_project_server_uri)
        except:
            self.pyro_nameserver = None
            self.logger.warning('No pyro4 nameserver found.')
            self.logger.info('Registered the project server with pyro uri: %s.', self.pyro_project_server_uri)
        self._project_server_starting = False
        self._project_server_started = True
        self.project_server_lock.release()
        self.pyro_daemon.requestLoop()


    def stop_project_server(self):
        ''' Stop the pyro project server.
        '''
        if self.project_server_started:
            self.project_server_lock.acquire()
            try:
                if self.pyro_nameserver is not None:
                    self.pyro_nameserver.remove(self.pyro_project_server_name)
            finally:
                self.logger.debug('Shutting down the pyro_daemon.')
                self.pyro_daemon.shutdown()
                self._project_server_started = False
            self.project_server_lock.release()


    def createPsysmonDbUser(self, rootUser, rootPwd, dbHost, user, userPwd):
        '''Create a pSysmon database user.

        Create a nuew user in the mysql database. for each pSysmon user a 
        corresponding database name *psysmon_USERNAME* is created. In this 
        database, all project database tables will be created.


        Parameters
        ----------
        rootUser : String
            The username of the mysql root user or any other user 
            having root privileges.
        rootPwd : String
            The password for the rootUser.
        dbHost : String
            The host on which the mysql server is running.
        user : String
            The username of the user which should be created.
        userPwd : String
            The password of the user *username*.

        See Also
        --------
        psysmon.core.project.Project.createDatabaseStructure

        '''
        try:
            dbDialect = 'mysql'
            dbDriver = None
            if dbDriver:
                dialectString = dbDialect + "+" + dbDriver
            else:
                dialectString = dbDialect

            engineString = dialectString + "://" + rootUser + ":" + rootPwd + "@" + dbHost

            dbEngine = create_engine(engineString)
            conn = dbEngine.connect()
            conn.execute('commit')

        except SQLAlchemyError as e:
            self.logger.exception(e)
            raise
        except Exception as e:
            self.logger.exception(e)
            raise

        try:
            # Create the pSysmon database for the user.
            userDb = "psysmon_" + user
            query = "CREATE DATABASE IF NOT EXISTS %s" % userDb
            conn.execute(query)

            # Create the user.
            query = "CREATE USER %s@'%s' IDENTIFIED BY '%s'" % (user, dbHost, userPwd)
            conn.execute(query)

            # Grant the privileges.
            query = "GRANT ALL ON %s.* TO '%s'@'localhost'" % (userDb, user)
            conn.execute(query)

            conn.execute('commit')
        except SQLAlchemyError as e:
            print e
            raise
        finally:
            conn.close()


    def createPsysmonProject(self, name, base_dir, db_host, user_name, user_pwd,
                             author_name, author_uri, agency_name, agency_uri):
        '''Create a pSysmon project.

        The pSysmon project is the starting point when working with pSysmon.
        After creating an instance of the :class:`~psysmon.core.project.Project` 
        class, the project is initialized by the following steps:

        - Connect to the database. If this fails, a PsysmonError is raised.
        - Create the project directory structure in the project base directory.
        - Create the project database structure.
        - Initialize the project for the currently active user.
        - Save the project.

        Parameters
        ----------
        name : String
            The name of the project.
        baseDir : String
            The base directory of the pSysmon project. Inside the 
            base directory, the pSysmon project directory is created.
        dbHost : String
            The database host on which the mysql server for the 
            project is running.
        user : String
            The pSysmon user related to the project as the *admin*.
        userPwd : String
            The password of *user*.

        Returns
        -------
        projectCreated : Boolean
            Indicates if the project has been created succesfully.
            (True: project created; False: project not created)

        Raises
        ------
        PsysmonError : :class:`~psysmon.core.util.PsysmonError`
            Error while connecting to the database.
        '''

        # Create the admin user for the project.
        admin_user = psysmon.core.project.User(user_name = user_name, 
                                               user_mode = 'admin',
                                               user_pwd = user_pwd,
                                               author_name = author_name,
                                               author_uri = author_uri,
                                               agency_name = agency_name,
                                               agency_uri = agency_uri
                                              )

        # Create the project instance.
        self.project = psysmon.core.project.Project(psybase = self,
                                                    name = name,
                                                    user = admin_user,
                                                    base_dir = base_dir,
                                                    dbHost = db_host)

        # When creating a project, set the active user to the user creating 
        # the project (which is the *admin* user).
        self.project.activeUser = self.project.user[0]
        try:
            self.project.connect2Db() 
        except Exception as e:
            msg = "Can't connect to the database.\n The database returned the following message:\n%s" % e
            raise PsysmonError(msg)     # If the connection fails, don't go on with the project creation.

        self.project.createDirectoryStructure()
        self.project.createDatabaseStructure(self.packageMgr.packages)

        # By default add a psysmon Database waveclient with the name 'main
        # client'. Add the waveclient only, if the required packages are
        # present.
        required_packages = ['obspyImportWaveform', 'geometry']
        available_packages = [x for x in self.packageMgr.packages.keys() if x in required_packages]
        if required_packages == available_packages:
            waveclient = PsysmonDbWaveClient('db client', self.project)
            self.project.addWaveClient(waveclient)
            self.project.defaultWaveclient = 'db client'

        self.project.save_json()

        return True


    def load_json_project(self, filename, user_name, user_pwd, update_db = True):
        ''' Load a psysmon project from JSON formatted file.

        '''
        if not os.path.exists(filename):
            self.logger.error("The project file %s doesn't exist.", filename)
            self.project = None
            return False

        file_meta = psysmon.core.json_util.get_file_meta(filename)
        file_version = file_meta['file_version']
        json_decoder = psysmon.core.json_util.get_project_decoder(version = file_version)

        project_dir = os.path.dirname(filename)
        self.logger.info('Loading the project file %s (version %s) with decoder version %s.',
                         filename, file_version, json_decoder.version)

        try:
            with open(filename, 'r') as fid:
                file_data = json.load(fid, cls = json_decoder)
                # Old file versions didn't have the root dictionary of the file
                # container. 
                if file_version >= psysmon.core.util.Version('1.0.0'):
                    self.project = file_data['project']
                else:
                    self.project = file_data
        except:
            self.logger.exception("Error while decoding the project file.")
            self.project = None


        if not self.project:
            self.logger.error("Couldn't load the project file using the decoder.")
            return False

        # Set some runtime dependent variables.
        self.project.psybase = self
        self.project.base_dir = os.path.dirname(project_dir)
        self.project.updateDirectoryStructure()

        if file_version >= psysmon.core.util.Version('1.0.0'):
            # Load the collections of the users.
            # Since version 1.0.0 the collections have been seperated in a
            # dedicated directory.
            for cur_user in self.project.user:
                cur_user.load_collections(self.project.collectionDir)
                cur_user.setActiveCollection(cur_user.active_collection_name)
                del cur_user.__dict__['collection_names']
                del cur_user.__dict__['active_collection_name']

        self.project.setCollectionNodeProject()

        # Set the project of the db_waveclient (if available).
        for cur_waveclient in self.project.waveclient.itervalues():
            if cur_waveclient.mode == 'PsysmonDbWaveClient':
                cur_waveclient.project = self.project

        userSet = self.project.setActiveUser(user_name, user_pwd = user_pwd)
        if not userSet:
            self.project = None
            return False
        else:
            # Load the current database structure.
            self.project.loadDatabaseStructure(self.packageMgr.packages,
                                               update_db = update_db)

            # Load the geometry inventory.
            self.project.load_geometry_inventory()

            # Check if the default wave client exists.
            if self.project.defaultWaveclient not in self.project.waveclient.keys():
                self.project.defaultWaveclient = None

            # Set some variables depending on the database.
            for cur_waveclient in self.project.waveclient.itervalues():
                if cur_waveclient.mode == 'PsysmonDbWaveClient':
                    # Load the waveform directory list from database.
                    cur_waveclient.loadWaveformDirList()

            return True



    def loadPsysmonProject(self, filename, user_name, user_pwd):
        '''
        Load a psysmon project.

        Load pSysmon project settings saved in a python shelve file and create
        a psysmon project using the saved settings.

        Parameters
        ----------
        filename : String
            The filename of the project file.

        user_name : String
            The user name with which the project should be opened.

        user_pwd: String
            The password of the user.
        '''
        db = shelve.open(filename)
        projectDir = os.path.dirname(filename)
        self.project = psysmon.core.project.Project(psybase = self,
                                                    name = db['name'],
                                                    base_dir=os.path.dirname(projectDir),
                                                    user=db['user'],
                                                    dbHost = db['dbHost'],
                                                    dbName = db['dbName'],
                                                    pkg_version = db['pkg_version'],
                                                    db_version = db['db_version'],
                                                    dbDriver = db['dbDriver'],
                                                    dbDialect = db['dbDialect']
                                                    )
        self.project.defaultWaveclient = db['defaultWaveclient']
        self.project.scnlDataSources = db['scnlDataSources']
        self.project.updateDirectoryStructure()
        self.project.setCollectionNodeProject()
        waveclients2Add = db['waveclient']
        db.close()

        userSet = self.project.setActiveUser(user_name, user_pwd = user_pwd)
        if not userSet:
            self.project = None
            return False
        else:
            # Load the current database structure.
            self.project.loadDatabaseStructure(self.packageMgr.packages)

            for curName, curMode, curOptions in waveclients2Add:
                if curMode == 'psysmonDb':
                    waveclient = PsysmonDbWaveClient(curName, self.project)
                elif curMode == 'earthworm':
                    waveclient = EarthwormWaveclient(name=curName, **curOptions)
                else:
                    waveclient = None

                self.project.addWaveClient(waveclient)

            # Check if the database tables have to be updated.
            self.project.checkDbVersions(self.packageMgr.packages)

            # Check if the default wave client exists.
            if self.project.defaultWaveclient not in self.project.waveclient.keys():
                self.project.defaultWaveclient = 'main client'

            return True


    def closePsysmonProject(self):
        '''
        Close a pSysmon project.

        Close the currently active project by setting the project attribute to 
        None.
        '''
        del(self.project)
        self.project = None




class Collection(object):
    ''' Manage a list of collection nodes.

    A collection holds the associated collection nodes in a list.
    The collection controls the adding, removing, editing and execution of the 
    collection nodes.

    Parameters
    ----------
    name : String
        The name of the collection.

    tmpDir : String
        The project's temporary directory.

    Attributes
    ----------
    dataShelf : String
        The filename of the data file which is used to store values 
        passed from one collection node to another.

    name : String
        The name of the collection.

    nodes : list of :class:`~psysmon.core.packageNodes.CollectionNode`
        A list of collection node instances managed by the collection.

    tmpDir : String
        The project's temporary directory.
        Collection log files are saved there.
    '''

    def __init__(self, name, tmpDir = '.', nodes = None, project = None):
        ''' The constructor.

        Parameters
        ----------
        name : String
            The name of the collection.

        tmpDir : String
            The project's temporary directory.
        '''
        # The parent instance holding the collection.
        self.project = project

        ## The name of the collection.
        self.name = name

        ## A list CollectionNode objects contained in the collection.
        if nodes is None:
            nodes = []
        self.nodes = nodes

        for cur_node in self.nodes:
            cur_node.parentCollection = self

        ## The project's temporary directory.
        #
        # Collection log files go in there.
        self.tmpDir = tmpDir

        # The collection's data file.
        self.dataShelf = None


    def __getitem__(self, index):
        ''' Get a node at a given position in the collection.

        Parameters
        ----------
        index : Integer
            The index of the collection node to get from the list.

        Returns
        -------
        node : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node at position index.
        '''
        return self.nodes[index]

    def __len__(self):
        ''' The length of the collection.
        '''
        return len(self.nodes)


    @property
    def rid(self):
        ''' The resource ID of the collection node.
        '''
        if self.project is not None:
            rid = self.project.rid + '/' + self.p_name.replace(' ', '_')
        else:
            rid = self.name.replace(' ', '_')

        return rid


    @property
    def p_name(self):
        ''' The process name running the current collection node.
        '''
        if self.project is not None and self.project.psybase is not None:
            p_name = self.project.psybase.process_meta['name']
        else:
            p_name = ''

        return p_name


    def __getstate__(self):
        ''' Remove the project instance before pickling the instance.
        '''
        result = self.__dict__.copy()
        del result['project']
        return result


    def __setstate__(self, d):
        ''' Fill the attributes after unpickling.
        '''
        self.__dict__.update(d) # I *think* this is a safe way to do it
        self.project = None


    def save(self, path):
        ''' Save the collection to a json file.
        '''
        filename = os.path.join(path, self.name + '.json')
        file_content = {'collection': self}
        file_container = psysmon.core.json_util.FileContainer(file_content)
        with open(filename, mode = 'w') as fp:
            json.dump(file_container, fp = fp, cls = psysmon.core.json_util.CollectionFileEncoder)


    def setDataShelfFile(self, filename):
        ''' Set the dataShelf filename of the collection.

        Parameters
        ----------
        filename : String
            The full path to the dataShelf file.
        '''
        #TODO: Add some checks for valid file.
        self.dataShelf = filename


    def addNode(self, node, position=-1):
        ''' Add a node to the collection.

        Insert a node before a specified position in the collection . If the 
        position is set to -1, the node is appended at the end of the collection.

        Parameters
        ----------
        node : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node to be added to the collection.
        position : Integer, optional
            The position in the collection before which the node should be inserted (the default is -1).
        '''

        node.parentCollection = self
        if position==-1:
            self.nodes.append(node)
        else:
            self.nodes.insert(position, node)


    def addNode2Looper(self, node, position, looper_pos = 0):
        ''' Add a looper child node to a looper node.
        '''
        if not self.nodes:
            raise PsysmonError('No collection nodes available.')

        cur_node = self.nodes[position]
        if isinstance(cur_node, psysmon.core.packageNodes.LooperCollectionNode):
            # Add the node to the looper node.
            node.parentCollection = self
            cur_node.add_child(node, position = looper_pos)
        else:
            raise PsysmonError('The selected collection node is not a looper node.')

    def popNode(self, position):
        ''' Remove a node from the collection.

        Remove the node at position `position` from the collection.

        Parameters
        ----------
        position : Integer
            The position of the node which should be removed.

        Returns
        -------
        node : :class:`~psysmon.core.packageNodes.CollectionNode`
            The removed node.
        '''
        if len(self.nodes) > 0:
            return self.nodes.pop(position)


    def editNode(self, position):
        ''' Edit a node.

        Edit the node at a given position 'position' in the collection. This is done by 
        calling the :meth:`~psysmon.core.packageNodes.CollectionNode.edit()` 
        method of the according :class:`~psysmon.core.packageNodes.CollectionNode` instance.

        Parameters
        ----------
        position : Integer
            The position in the collection of the node to edit.
        '''
        self.nodes[position].edit()


    def executeNode(self, position):
        ''' Execute a node at a given position.

        Execute a node at position 'position'. This method is used to 
        execute standalone collection nodes.

        Parameters
        ----------
        position : Integer
            The position in the collection of the node to execute.
        '''
        self.nodes[position].execute()



    def execute(self, client=None):
        ''' Executing the collection.

        Sequentially execute the nodes in the collection. The collection is designed 
        to be executed as a new process. The process is started in the :meth:`~psysmon.core.project.Project.executeCollection()` method of the :class:`~psysmon.core.project.Project` class.

        The collection notifies the system by sending log messages of the type state.collection.execution.

        Parameters
        ----------
        pipe : :class:`~multiprocessing.Pipe`
            The multiprocessing pipe end.
        '''
        # TODO: Add a State of Health thread which sends heartbeats at
        # regular initervals.

        #pipe.send({'state': 'running', 'msg': 'Collection running', 'procId': self.procId})

        #e = threading.Event()
        #heartbeat = threading.Thread(name = 'heartbeat', 
        #                             target =self.heartBeat, 
        #                             args = (e,pipe))
        #heartbeat.start()

        # Create the collection's data file.
        #self.dataShelf = os.path.join(self.tmpDir, self.procName + ".scd")
        content = {}
        db = shelve.open(self.dataShelf.encode('utf8'))
        db['nodeDataContent'] = content
        db.close()

        # Execute each node in the collection.
        for (ind, curNode) in enumerate(self.nodes):
            #pipe.send({'state': 'running', 'msg': 'Executing node %d' % ind, 'procId': self.procId})
            if ind == 0:
                if curNode.mode != 'standalone' and curNode.enabled:
                    curNode.run(procName=self.procName)
            else:
                #curNode.run(threadId=self.threadId)
                if curNode.mode != 'standalone' and curNode.enabled:
                    curNode.run(procName=self.procName,
                                prevNodeOutput=self.nodes[ind-1].output)

        #e.set()
        #heartbeat.join()
        #pipe.send({'state': 'stopped', 'msg': 'Collection execution finished', 'procId': self.procId})


    def heartBeat(self, event, pipe):
        from time import sleep
        heartbeatInterval = 0.01

        timeout = 0;
        while timeout < 100:
            if event.isSet():
                pipe.send({'state': 'quiting', 'msg': 'Stopping heartbeat (%d)' % timeout, 'procId': self.procId})
                return
            pipe.send({'state': 'running', 'msg': 'I am alive (%d)' % timeout, 'procId': self.procId})
            timeout = timeout + 1
            sleep(heartbeatInterval)


    def set_project(self, project):
        ''' Set the project of the collection.

        Update the project of the collection nodes as well.

        Parameters
        ----------
        project : :class:`~psysmon.core.project.Project`
            The working psysmon project.
        '''
        self.project = project

        for curNode in self.nodes:
            curNode.project = self.project

            if isinstance(curNode, psysmon.core.packageNodes.LooperCollectionNode):
                for cur_child in curNode.children:
                    cur_child.project = self.project


    def createNodeLoggers(self):
        ''' Create a logger instance for each node in the collection.

        For each node in the collection create a :class:`logging.logger` instance.
        '''
        for curNode in self.nodes:
            # Create the logger instance.
            loggerName = __name__ + "." + curNode.__class__.__name__
            curNode.logger = logging.getLogger(loggerName)



    def log(self, nodeName, mode, msg):
        ''' Log messages to the collection's log file.

        The collection is executed as a process which has a unique id.
        For each process, a log file with the process ID as the filename is created 
        in the project's temporary directory. All messages created by the nodes in 
        the collection are written to this file.

        Parameters
        ----------
        nodeName : String
            The name of the node.
        mode : String
            The mode of the status message (error, warning, status).
        msg : String
            The status message to log.
        '''
        curTime = datetime.now()
        timeStampString = datetime.strftime(curTime, '%Y-%m-%d %H:%M:%S')

        if mode == 'error':
            modeString = '[ERR] '
        elif mode == 'warning':
            modeString = '[WRN] '
        else:
            modeString = ' '

        nodeName = "[%s]" % nodeName

        msgString = msg.rstrip()
        msgString = timeStampString + ">>" + nodeName + modeString + msgString + "\n"


        # If a thread is running, add the log message to the log file.
        if self.procId:
            logFile = open(os.path.join(self.tmpDir, self.procId + ".log"), 'a')
            logFile.write(msgString)
            logFile.close()


    def pickleData(self, name, data, description, origin):
        ''' Save the data in the collection's data shelf.

        The collection nodes of a collection can save data to the data shelf 
        of the collection node. This data can be used by following collection 
        nodes.

        Parameters
        ----------
        name : String
            The name of the variable to fetch from the collection's data shelf.

        data : Object
            The data to be saved in the collection's data shelf.

        description : String
            A short description of the data.

        origin : String
            The name of the collection node pickling the data.

        See Also
        --------
        psysmon.core.packageNodes.CollectionNode.provideData : Put data onto the data shelf of the collection.
        '''
        #nodeContent = namedtuple('nodeContent', 'name description origin')
        #nodeData = namedtuple('nodeData', 'name description origin data')

        db = shelve.open(self.dataShelf)
        content = db['nodeDataContent']
        content[(origin,name)] = (name, description, origin)
        db[origin + '.' + name] = (name, description, origin, data)

        db['nodeDataContent'] = content
        db.close()


    def unpickleData(self, name=None, origin=None):
        ''' Load data from the data shelf of the collection.


        Parameters
        ----------
        name : String, optional
            The name of the variable to fetch from the collection's data shelf.

        origin : String, optional
            The name of the collecionNode which created the nodeData.

        Returns
        -------
        data : list of objects
            The data loaded from the shelf. 

        See Also
        --------
        psysmon.core.packageNodes.CollectionNode.requireData : Require data from a collection by a collection node.
        '''

        db = shelve.open(self.dataShelf)
        if name is not None and origin is not None:
            if (origin+'.'+name) in db.keys():
                returnData = db[origin + '.' + name]
            else:
                returnData = None

        elif name is not None and origin is None:
            # Return all nodeData with the specified name.
            content = self.getShelfContent()
            returnData = []
            for curOrigin, curName in content.keys():
                if curName == name:
                    returnData.append(db[curOrigin + '.' + curName])

        elif name is None and origin is not None:
            # Return all nodeData with the specified origin.
            content = self.getShelfContent()
            returnData = []
            for curOrigin, curName in content.keys():
                if curOrigin == origin:
                    returnData.append(db[curOrigin + '.' + curName])
        else:
            # Return all available nodeData
            content = self.getShelfContent()
            returnData = []
            for curOrigin, curName in content.keys():
                returnData.append(db[curOrigin + '.' + curName])

        db.close()
        return returnData




    def hasDataOnShelf(self, name):
        ''' Check if a variable exists in the data shelf.

        Query the data shelf of the collection for the variable with name 'name'.

        Parameters
        ----------
        name : String
            The name of the variable to fetch from the collection's data shelf.

        Returns
        -------
        has_data : bool
            True if the variable 'name' is contained in the data shelf, False 
            otherwise.
        '''
        db = shelve.open(self.dataShelf)
        if name in db.keys():
            has_data = True
        else:
            has_data = False
        db.close()

        return has_data


    def getShelfContent(self):
        ''' Get the content of the collections data shelf.

        The content of the data shelf of a collection is saved in the 
        dictionary with the key 'nodeDataContent'. This variable is a dictionary 
        with the '(orgin, name)' as the key. It contains the name, description and 
        origin of the data in the shelf.

        Returns
        -------
        content : dictionary of tuples
            A dictionary holding the name, description and origin of the data content.
            The keys of the dictionary are tuples of (name, origin).

        See also
        --------
        pickleData : Save data in the data shelf of the collection.
        '''
        db = shelve.open(self.dataShelf)
        if 'nodeDataContent' in db.keys():
            content = db['nodeDataContent']
        else:
            content = None
        db.close()

        return content


    def clearShelf(self):
        ''' Clear all the data stored in the collection's shelf.

        Not yet implemented.
        '''
        pass
        #db = shelve.open(self.dataShelf)

        #for curKey in db:
        #    del db[curKey]

        #db['content'] = {}
        #db.close()

