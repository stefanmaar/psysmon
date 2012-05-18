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
The pSysmon base module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the basic modules needed to run the pSysmon program.
'''

import os
import logging
import threading
import shelve
from datetime import datetime
from psysmon import __version__ as version
import psysmon.core.packageSystem
import psysmon.core.project
from psysmon.core.util import PsysmonError


class Base:
    '''The pSysmon Base class.

    The Base class is the lowest level class of the pSysmon model. It handles 
    the initialization of the pSysmon packages and stores the package objects.


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

        # The psysmon base directory.
        self.packageDirectory = os.path.join(self.baseDirectory, "packages")

        # The currently loaded pSysmon project.
        self.project = ""

        # The pSysmon version.
        self.version = version

        # The package manager handling the dynamically loaded packages.
        self.packageMgr = psysmon.core.packageSystem.PackageManager(self, [self.packageDirectory])



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
        '''
        try:
            dbConn = mysql.connect(dbHost, rootUser, rootPwd)
            cur = dbConn.cursor();
        except mysql.Error:
            raise

        try:
            # Create the pSysmon database for the user.
            userDb = "psysmon_" + user
            query = "CREATE DATABASE IF NOT EXISTS %s" % userDb
            cur.execute(query)

            # Create the user.
            query = "CREATE USER %s@'%s' IDENTIFIED BY '%s'" % (user, dbHost, userPwd)
            cur.execute(query)

            # Grant the privileges.
            query = "GRANT ALL ON %s.* TO '%s'@'%%'" % (userDb, user)
            cur.execute(query)
        except mysql.Error:
            raise
        finally:
            dbConn.close()


    def createPsysmonProject(self, name, baseDir, dbHost, user, userPwd):
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

        # Create the working psysmon project.
        self.project = psysmon.core.project.Project(psyBase = self,
                                                    name = name,
                                                    baseDir = baseDir,
                                                    user = psysmon.core.project.User(user, 'admin'),
                                                    dbHost = dbHost)

        # When creating a project, set the active user to the user creating 
        # the project (which is the *admin* user).
        self.project.activeUser = self.project.user[0]
        try:
            self.project.connect2Db(userPwd)    # Connect to the database.
        except Exception as e:
            msg = "Can't connect to the database.\n The database returned the following message:\n%s" % e
            raise PsysmonError(msg)     # If the connection fails, don't go on with the project creation.

        self.project.createDirectoryStructure()
        self.project.createDatabaseStructure(self.packageMgr.packages)
        self.project.setActiveUser(user, userPwd)               # Set the active user again to run all remaining project initialization methods.
        self.project.save()

        return True


    def loadPsysmonProject(self, filename):
        '''
        Load a psysmon project.

        Load pSysmon project settings saved in a python shelve file and create
        a psysmon project using the saved settings.

        Parameters
        ----------
        filename : String
            The filename of the project file.
        '''
        db = shelve.open(filename)
        projectDir = os.path.dirname(filename)
        self.project = psysmon.core.project.Project(psyBase = self,
                                                    name = db['name'],
                                                    baseDir=os.path.dirname(projectDir),
                                                    user=db['user'],
                                                    dbHost = db['dbHost'],
                                                    dbName = db['dbName'],
                                                    dbVersion = db['dbVersion'],
                                                    dbDriver = db['dbDriver'],
                                                    dbDialect = db['dbDialect']
                                                    )
        self.project.updateDirectoryStructure()
        self.project.setCollectionNodeProject()
        db.close()



    def closePsysmonProject(self):
        '''
        Close a pSysmon project.

        This sets the project attribute to None.
        '''
        self.project = None






## The Collection class.
#
# A collection holds the associated CollectionNode in a list.
# The collection controls the adding, removing, editing and execution of the 
# CollectionNodes.
class Collection:
    '''
    The Collection class.

    A collection holds the associated collection nodes in a list.
    The collection controls the adding, removing, editing and execution of the 
    collection nodes.

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
        '''
        The constructor.

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
        '''
        Get a node at a given position in the collection.

        Parameters
        ----------
        index : Integer
            The index of the collection node to get from the list.
        '''

        return self.nodes[index]


    def addNode(self, node, position=-1):
        '''
        Add a node to the collection.

        Insert a node before a specified position in the collection . If the 
        position is set to -1, the node is appended at the end of the collection.

        Parameters
        ----------
        node : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node to be added to the collection.
        position : Integer
            The position in the collection before which the node should be inserted.
        '''

        node.parentCollection = self
        if position==-1:
            self.nodes.append(node)
        else:
            self.nodes.insert(position, node)


    def popNode(self, position):
        '''
        Remove a node from the collection.

        Parameters
        ----------
        position : Integer
            The position of the node which should be removed.
        '''
        if len(self.nodes) > 0:
            return self.nodes.pop(position)


    def editNode(self, position):
        '''
        Edit a node.

        Edit the node at a given position in the collection. This is done by 
        calling the :meth:`~psysmon.core.packageNodes.CollectionNode.edit()` 
        method of the according :class:`~psysmon.core.packageNodes.CollectionNode` instance.

        Parameters
        ----------
        position : Integer
            The position in the collection of the node to edit.
        '''
        self.nodes[position].edit()


    def executeNode(self, position):
        '''
        Execute a node at a given position.

        Execute a node at *position*. This method is used to 
        execute standalone collection nodes.

        Parameters
        ----------
        position : Integer
            The position in the collection of the node to execute.
        '''
        self.nodes[position].execute()



    def execute(self, client=None):
        '''
        Executing the collection.

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
        #content = {}
        #db = shelve.open(self.dataShelf)
        #db['content'] = content
        #db.close()

        # Execute each node in the collection.
        for (ind, curNode) in enumerate(self.nodes):
            #pipe.send({'state': 'running', 'msg': 'Executing node %d' % ind, 'procId': self.procId})
            if ind == 0:
                curNode.run(procName=self.procName)
            else:
                #curNode.run(threadId=self.threadId)
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
        '''
        Set the the project attribute of all nodes in the collection.

        Parameters
        ----------
        project : :class:`~psysmon.core.project.Project`
            The working psysmon project.
        '''
        for curNode in self.nodes:
            curNode.project = project


    def createNodeLoggers(self):
        '''
        Create a logging.logger instance for each node in the collection.
        '''
        for curNode in self.nodes:
            # Create the logger instance.
            loggerName = __name__ + "." + curNode.__class__.__name__
            curNode.logger = logging.getLogger(loggerName)



    def log(self, nodeName, mode, msg):
        '''
        Log messages to the collection's log file.

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

        Parameters
        ----------
        data : Object
            The data to be saved in the collection's data shelf.

        description : String
            A short description of the data.

        name : String
            The name of the variable to fetch from the collection's data shelf.

        origin : String
            The name of the collection node pickling the data.
        '''
        db = shelve.open(self.dataShelf)
        content = db['content']
        content[name] = (origin, description)

        db[name] = data
        db['content'] = content
        db.close()


    def unpickleData(self, name):
        ''' Load the variable named *name* from the collection's data shelf.

        Parameters
        ----------
        name : String
            The name of the variable to fetch from the collection's data shelf.
        '''
        db = shelve.open(self.dataShelf)

        if name not in db.keys():
            return None
        else:
            return db[name]



    def hasDataOnShelf(self, name):
        ''' Check if the variable named *name* is available in the collection's 
        data shelf.

        Parameters
        ----------
        name : String
            The name of the variable to fetch from the collection's data shelf.
        '''
        db = shelve.open(self.dataShelf)
        if name in db.keys():
            retVal = True
        else:
            retVal = False
        db.close()

        return retVal


    def getShelfContent(self):
        ''' Get the content of the collections data shelf.

        '''
        db = shelve.open(self.dataShelf)
        if 'content' in db.keys():
            retVal = db['content']
        else:
            retVal = None
        db.close()

        return retVal


    def clearShelf(self):
        ''' Clear all the data stored in the collection's shelf.

        '''

        db = shelve.open(self.dataShelf)

        for curKey in db:
            del db[curKey]

        db['content'] = {}
        db.close()

