# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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
'''

import logging
import os
import thread
import multiprocessing
import copy
from wx.lib.pubsub import Publisher as pub
from datetime import datetime
import psysmon.core.base
from psysmon.core.waveserver import WaveServer
from psysmon.core.util import PsysmonError
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Project:
    '''The pSysmon Project class.


    Attributes
    ----------
    activeUser : String
        The currently active user.

    baseDir : String
        The project's base directory. The *projectDir* resides in this directory.

    createTime : :class:`datetime.datetime`
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

    dbVersion : Dictionary of Strings
        A dictionary holding the versions of the individual package database 
        structures (key: package name).

    name : String
        The project name.

    projectDir : String
        The project directory.

    projectFile : String
        The project file holding all project settings.
        It is saved in the projectDir folder.

    saved : Boolean
        Is the project saved?

    user : List of Strings
        A list of users associated with the project.
        The user creating the project is always the admin user.

    waveformDirList : List of Strings
        A list of waveform directories associated with the project.
        Each entry in the list is a dictionary with the fields id, dir, dirAlias and description.

    '''

    def __init__(self, name, baseDir, user, dbDialect='mysql', dbDriver=None, dbHost='localhost', dbName="", dbVersion={}, createTime="", dbTables={}):
        '''The constructor.

        Create an instance of the Project class.

        Parameters
        ----------
        name : String
            The name of the project.
        baseDir : String
            The base directory of the project.
        user : String
            The admin user of the project.
        dbDialect : String
            The database dialect to be used by sqlalchemy.
        dbDriver : String
            The database driver to be used by sqlalchemy.
        dbHost : String
            The database host.
        dbName : String
            The name of the database associated with the project.
        dbVersion : Dictionary of Strings
            The database structure version used by the project. The name of 
            the package is the key of the dictionary.
        dbTableNames : Dictionary of Strings
            The database tablenames used by the project. The name of the table 
            (without prefix) is the key of the dictionary.
        '''

        # The project name.
        self.name = name

        # The time when the project has been created.
        if not createTime:
            self.createTime = datetime.utcnow()
        else:
            self.createTime = createTime

        # The project's base directory. 
        self.baseDir = baseDir

        # The project directory.
        self.projectDir = os.path.join(self.baseDir, self.name)

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

        # The sqlAlchemy database session.
        self.dbSessionClass = None

        # The project file.
        self.projectFile = self.name +".ppr"

        # The version dictionary of the package dtabase structures.
        self.dbVersion = dbVersion

        # A list of waveform directories associated with the project.
        self.waveformDirList = []

        # Is the project saved?
        self.saved = False

        # The thread lock object.
        self.threadMutex = None

        # A list of users associated with this project.
        self.user = []

        # The currently active user.
        self.activeUser = ""

        # Add the user(s) to the project user list.
        if isinstance(user, list):
            self.user.extend(user)
        else:
            self.user.append(user)


        # The logging configuration.
        self.logConfig = {}
        self.logConfig['level'] = 'DEBUG'





    def setCollectionNodeProject(self):
        '''Set the project attribute of each node in all collections of 
        the project.

        '''
        for curUser in self.user:
            for curCollection in curUser.collection.itervalues():
                curCollection.setNodeProject(self)



    def connect2Db(self, passwd):
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

        if passwd:
            engineString = dialectString + "://" + self.activeUser.name + ":" + passwd + "@" + self.dbHost + "/" + self.dbName
        else:
            engineString = dialectString + "://" + self.activeUser.name + "@" + self.dbHost + "/" + self.dbName

        self.dbEngine = create_engine(engineString)
        #self.dbEngine.echo = True
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


    def setActiveUser(self, userName, pwd):
        '''Set the active user of the project.

        Parameters
        ----------
        userName : String
        The name of the user to activate.
        pwd : String
            The user's password.

        Returns
        -------
        userCreated : Boolean
            Has the user been created successfully?
        '''
        for curUser in self.user:
            if curUser.name == userName:
                self.activeUser = curUser
                self.connect2Db(pwd)
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

        else:
            msg = "Cannot create the directory structure."
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
                msg = "The project data directory %s doesn't exist." % self.dataDir
                raise Exception(msg)

            ## The project's temporary directory.
            self.tmpDir = os.path.join(self.projectDir, "tmp")

            if not os.path.exists(self.tmpDir):
                msg = "The project temporary directory %s doesn't exist." % self.tmpDir
                raise Exception(msg)

        else:
            msg = "Cannot create the directory structure."
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


    def loadDatabaseStructure(self, packages):
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
        '''

        for _, curPkg in packages.iteritems():
            if not curPkg.databaseFactory:
                print "No databaseFactory method found."
                continue
            else:
                print "Creating the tables for package " + curPkg.name
                self.dbVersion[curPkg.name] = curPkg.version
                tables = curPkg.databaseFactory(self.dbBase)
                for curTable in tables:
                    # Add the table prefix.
                    curName = curTable.__table__.name
                    curTable.__table__.name = self.name + "_" + curTable.__table__.name
                    self.dbTables[curName] = curTable


    def checkDbVersions(self, packages):
        '''Check if the database has to be updated.

        packages : Dictionary of :class:`~psysmon.core.packageSystem.Package` instances.
            The packages to be checked for the database table to be updated.
        '''
        for curPkgKey, curPkg in packages.iteritems():
            if not curPkg.dbTableCreateQueries:
                continue
            else:
                if curPkg.name in self.dbVersion:
                    if(curPkg.version > self.dbVersion[curPkg.name]):
                        print "An update of the package database is needed."
                else:
                    # The package database tables have not yet been created. Create it now.
                    print "Creating the database tables of package %s" % curPkg.name
                    self.createDatabaseStructure({curPkgKey: curPkg})


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
        db['dbVersion'] = self.dbVersion
        db['user'] = self.user
        db['createTime'] = self.createTime
        db.close()
        self.saved = True 


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
        node = copy.deepcopy(nodeTemplate)
        node.project = self
        self.activeUser.addNode2Collection(node, position)



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


    def loadWaveformDirList(self):
        '''Load the waveform directories from the database table.

        '''
        # Clear the list to start from beginning.
        self.waveformDirList = []

        wfDir = self.dbTables['waveform_dir']
        wfDirAlias = self.dbTables['waveform_dir_alias']

        dbSession = self.getDbSession()
        for row in dbSession.query(wfDir.id, 
                                   wfDir.directory, 
                                   wfDirAlias.alias, 
                                   wfDir.description
                                  ).join(wfDirAlias, 
                                          wfDir.id==wfDirAlias.wf_id
                                        ).filter(wfDirAlias.user==self.activeUser.name):
            print row
            print row.keys()
            self.waveformDirList.append(dict(zip(['id', 'dir', 'dirAlias', 'description'], row)))

        print self.waveformDirList


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
        pub.sendMessage(msgTopic, msg)


    def getLogger(self, name):
        ''' Create a logging logger instance.

        Parameters
        ----------
        name : String
            The name of the logger. This should be the module name 
            using the logger.
        '''
        logger = logging.getLogger(name)
        logger.setLevel(self.logConfig['level'])
        ch = logging.StreamHandler()
        ch.setLevel(self.logConfig['level'])
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch) 
        return logger




## The pSysmon user.
# 
# The user class holds the details of the user and the userspecific project
# variables (e.g. collection, settings, ...).
class User:
    '''The pSysmon user class.

    A pSysmon project can be used by multiple users. For each user, an instance 
    of the :class:`User` class is created. The pSysmon users are managed within 
    the pSysmon :class:`Project`.

    Attributes
    ----------
    activeCollection (:class:`~psysmon.core.base.Collection)`
        The currently active collection of the user.

    collection (Dictionary of :class:`~psysmon.core.base.Collection` instances)
        The collections created by the user.

        The collections are stored in a dictionary with the collection name as 
        the key.

    mode : String
        The user mode (admin, editor).

    name : String
        The user name.
    '''

    def __init__(self, user, userMode):
        '''The constructor.

        Parameters
        ----------
        user : String
            The user name.

        userMode : String
            The user privileges. Currently allowed values are:

            - admin
            - editor
        '''

        ## The user name.
        self.name = user

        ## The user mode.
        #
        # The user privileges. 
        # Allowed values are: admin, editor.
        self.mode = userMode

        # The user collection.
        self.collection = {}

        # The currently active collection.
        self.activeCollection = None


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

        self.collection[name] = psysmon.core.base.Collection(name, tmpDir = project.tmpDir)
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
        if name in self.collection.keys():
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
        if self.activeCollection:
            self.activeCollection.addNode(node, position)
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
        if self.activeCollection:
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
        if self.activeCollection:
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
        if self.activeCollection:
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
        if self.activeCollection:
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

        def processChecker(process, parentEnd, mutex):
            from time import sleep

            # The time interval to check for process messages [s].
            checkInterval =0.5 

            # The timeout limit. After this timeout the process is 
            # marked as "not responding". The timeout interval should
            # be larger than the process's heartbeat interval. [s]
            timeout = 10

            procRunning = True
            isZombie = False
            print "Checking thread..."
            lastResponse = 0
            while procRunning:
                print "Waiting for message..."
                if parentEnd.poll(checkInterval):
                    msg = parentEnd.recv()
                    print msg
                    print "Received message: [%s]: %s" % (msg['state'], msg['msg'])

                    # Send the message to the system.
                    msgTopic = "state.collection.execution"
                    msg['isError'] = False
                    #pub.sendMessage(msgTopic, msg)

                    lastResponse = 0
                    if msg['state'] == 'stopped':
                        procRunning = False
                else:
                    lastResponse += checkInterval
                    print "No message received."

                if lastResponse > timeout:
                    procRunning = False
                    isZombie = True

            print "End checking thread..."

        if self.activeCollection:
            if not project.threadMutex:
                project.threadMutex = thread.allocate_lock()

            col2Proc = copy.deepcopy(self.activeCollection)
            col2Proc.setNodeProject(project)     # Reset the project of the nodes. This has been cleared by the setstate method.
            curTime = datetime.now()
            timeStampString = datetime.strftime(curTime, '%Y%m%d%H%M%S%f')
            col2Proc.procId = col2Proc.name + "_" + timeStampString

            msg = "Executing collection " + col2Proc.name + "with thread ID: " + col2Proc.procId + "."
            project.log("status", msg)

            msgTopic = "state.collection.execution"
            msg = {}
            msg['state'] = 'starting'
            msg['startTime'] = curTime
            msg['isError'] = False
            msg['procId'] = col2Proc.procId
            pub.sendMessage(msgTopic, msg)

            (parentEnd, childEnd) = multiprocessing.Pipe()
            print "proc Id: %s" % col2Proc.procId
            p = multiprocessing.Process(target=col2Proc.execute, args=(childEnd,))
            #p.daemon = True
            p.start()
            thread.start_new_thread(processChecker, (p, parentEnd, project.threadMutex))
        else:
            raise PsysmonError('No active collection found!') 




