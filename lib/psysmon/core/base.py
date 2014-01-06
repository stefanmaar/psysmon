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
import logging
import shelve
from datetime import datetime
from psysmon import __version__ as version
import psysmon.core.packageSystem
import psysmon.core.project
from psysmon.core.waveclient import PsysmonDbWaveClient, EarthwormWaveclient
from psysmon.core.util import PsysmonError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


class Base:
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

    packageDirectory : String
        The psysmon packages directory.

    packageMgr : :class:`~psysmon.core.packageSystem.PackageManager`
        The package manager handles the dynamically loaded packages.

    project : :class:`~psysmon.core.project.Project`
        The working pSysmon project.

    version : *String*
        The pSysmon version.


    '''

    def __init__(self, baseDir):
        '''The constructor.

        Create an instance of the Base class.


        Parameters
        ----------
        baseDir : String
            The pSysmon base directory. 
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
        self.packageDirectory = os.path.join(self.baseDirectory, "packages")

        # The currently loaded pSysmon project.
        self.project = ""

        # The pSysmon version.
        self.version = version

        # The package manager handling the dynamically loaded packages.
        self.packageMgr = psysmon.core.packageSystem.PackageManager(self, [self.packageDirectory, ])

        # Load the psysmon packages.
        self.packageMgr.scan4Package()



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
            print e
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
        # client'.
        waveclient = PsysmonDbWaveClient('main client', self.project)
        self.project.addWaveClient(waveclient)
        self.project.defaultWaveclient = 'main client'

        self.project.save()

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




class Collection:
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

    def __init__(self, name, tmpDir):
        ''' The constructor.

        Parameters
        ----------
        name : String
            The name of the collection.

        tmpDir : String
            The project's temporary directory.
        '''

        ## The name of the collection.
        self.name = name

        ## A list CollectionNode objects contained in the collection.
        self.nodes = []

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
        db = shelve.open(self.dataShelf)
        db['nodeDataContent'] = content
        db.close()

        # Execute each node in the collection.
        for (ind, curNode) in enumerate(self.nodes):
            #pipe.send({'state': 'running', 'msg': 'Executing node %d' % ind, 'procId': self.procId})
            if ind == 0:
                if curNode.mode != 'standalone':
                    curNode.run(procName=self.procName)
            else:
                #curNode.run(threadId=self.threadId)
                if curNode.mode != 'standalone':
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


    def setNodeProject(self, project):
        ''' Set the the project attribute of all nodes in the collection.

        Parameters
        ----------
        project : :class:`~psysmon.core.project.Project`
            The working psysmon project.
        '''
        for curNode in self.nodes:
            curNode.project = project


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

