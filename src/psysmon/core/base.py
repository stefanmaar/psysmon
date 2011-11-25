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
    GNU General Public License, Version 3 (http://www.gnu.org/copyleft/gpl.html)

This module contains the basic modules needed to run the pSysmon program.
'''

import os
import sys
import logging
from wx.lib.pubsub import Publisher as pub
import MySQLdb as mysql
from datetime import datetime
from psysmon import version
import psysmon.core.packageSystem
import psysmon.core.project
from psysmon.core.util import PsysmonError


class Base:
    '''
    The pSysmon Base class.

    The Base class is the lowest level class of the pSysmon model. It handles 
    the initialization of the pSysmon packages and stores the package objects.


    '''

    def __init__(self, baseDir):
        '''
        The constructor.

        Create an instance of the Base class.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base`
        :param baseDir: The pSysmon base directory. 
        :type baseDir: String

        :ivar baseDirectory: The pSysmon base directory.
                            The base directory is the directory in which the pSysmon 
                            program is located. 
        :ivar packageDirectory: The psysmon packages directory.
        '''

        self.logger = logging.getLogger("base")
        ''' The system logger used for debugging and system wide error logging.'''

        # Configure the logger.
        self.configureLogger() 

        # Check the baseDir parameter for errors.
        if not isinstance(baseDir, basestring):
            msg = "The baseDir %s should be a string." & baseDir
            raise IndexError(msg)

        if not os.path.isdir(baseDir):
            msg = "The specified directory " + baseDir + " doesn't seem to be a directory."
            raise IndexError(msg)

        self.baseDirectory = baseDir
        ''' The pSysmon base directory.
        The base directory is the directory in which the pSysmon program is 
        located.
        '''

        self.packageDirectory = os.path.join(self.baseDirectory, "packages")
        ''' The pSysmon packages directory.
        The directory in which the pSysmon packages are located.
        '''

        self.project = ""
        ''' The currently loaded pSysmon project.'''


        self.version = version
        ''' The pSysmon version.'''

        self.packageMgr = psysmon.core.packageSystem.PackageManager(self, [self.packageDirectory])
        ''' The package manager handling the dynamically loaded packages. '''


    def configureLogger(self):
        '''
        Configure the pSysmon system logger.

        This can be used for system log messages (e.g. for debugging).
        '''
        print "Configuring logger."

        self.logger.setLevel(logging.DEBUG)

        # Create console handler and set level to debug.
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # Create a formatter.
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)



    def createPsysmonDbUser(self, rootUser, rootPwd, dbHost, user, userPwd):
        '''
        Create a pSysmon database user.

        Create a nuew user in the mysql database. for each pSysmon user a 
        corresponding database name \e psysmon_USERNAME is created. In this 
        database, all project database tables will be created.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base`
        :param rootUser: The username of the mysql root user or any other user 
            having root privileges.
        :type rootUser: String
        :param rootPwd: The password for the rootUser.
        :type rootPwd: String
        :param dbHost: The host on which the mysql server is running.
        :type dbHost: String
        :param user: The username of the user which should be created.
        :type user: String
        :param userPwd: The password of the user *username*.
        :type userPwd: String
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
        '''
        Create a pSysmon project.

        The pSysmon project is the starting point when working with pSysmon.
        After creating an instance of the :class:`~psysmon.core.project.Project` 
        class, the project is initialized by the following steps:
            - Connect to the database. If this fails, a PsysmonError is raised.
            - Create the project directory structure in the project base directory.
            - Create the project database structure.
            - Initialize the project for the currently active user.
            - Save the project.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base`
        :param name: The name of the project.
        :type name: String
        :param baseDir: The base directory of the pSysmon project. Inside the 
            base directory, the pSysmon project directory is created.
        :type baseDir: String
        :param dbHost: The database host on which the mysql server for the 
            project is running.
        :type dbHost: String
        :param user: The pSysmon user related to the project as the *admin*.
        :type user: String
        :param userPwd: The password of *user*.
        :type user: String
        :rtype: Boolean
        '''
        self.project = psysmon.core.project.Project(name=name,
                                                    baseDir=baseDir,
                                                    user=psysmon.core.project.User(user, 'admin'),
                                                    dbHost=dbHost)
        ''' The current pSysmon project. '''

        # When creating a project, set the active user to the user creating 
        # the project (which is the *admin* user).
        self.project.activeUser = self.project.user[0]
        try:
            self.project.connect2Db(userPwd)    # Connect to the database.
        except mysql.Error as e:
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

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base`
        :param filename: The filename of the project file.
        :type filename: String
        '''
        import shelve
        db = shelve.open(filename)
        projectDir = os.path.dirname(filename)
        self.project = psysmon.core.project.Project(name = db['name'],
                                                    baseDir=os.path.dirname(projectDir),
                                                    user=db['user'],
                                                    dbHost = db['dbHost'],
                                                    dbName = db['dbName'],
                                                    dbVersion = db['dbVersion'],
                                                    dbTableNames = db['dbTableNames']
                                                    )
        self.project.updateDirectoryStructure()
        self.project.setCollectionNodeProject()
        db.close()


    def closePsysmonProject(self):
        '''
        Close a pSysmon project.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base` instance
        '''
        self.project = None






## The Collection class.
#
# A collection holds the associated CollectionNode in a list.
# The collection controls the adding, removing, editing and execution of the 
# CollectionNodes.
class Collection:

    ## The constructor.
    # 
    # @param self The object pointer.
    # @param name The name of the collection.
    def __init__(self, name, tmpDir):

        ## The name of the collection.
        self.name = name

        ## A list CollectionNode objects contained in the collection.
        self.nodes = []

        ## The project's temporary directory.
        #
        # Collection log files go in there.
        self.tmpDir = tmpDir




    ## Get a node at a given position in the collection.
    #
    # @param self The object pointer.
    # @param index The index of the collection node to get from the list.
    def __getitem__(self, index):
        return self.nodes[index]

    ## Add a node to the collection.
    #
    # Insert a node before a specified position in the collection. If the 
    # position is set to -1, the node is appended at the end of the collection.
    #
    # @param self The Object pointer.
    # @param node The node to be added to the collection.
    # @param position The position in the collection before which the node should be inserted.    
    def addNode(self, node, position=-1):
        node.parentCollection = self
        if position==-1:
            self.nodes.append(node)
        else:
            self.nodes.insert(position, node)

    ## Remove a node from the collection.
    #
    # @param self The Object pointer.
    # @param position The position of the node which should be removed. 
    def popNode(self, position):
        if len(self.nodes) > 0:
            return self.nodes.pop(position)


    ## Edit a node.
    #
    # Edit the node at a given position in the collection. This is done by 
    # calling the CollectionNode.edit() method of the according CollectionNode object.
    #
    # @param self The Object pointer.
    # @param position The position in the collection of the node to edit.
    def editNode(self, position):
        self.nodes[position].edit()


    ## Execute a node at a given position.
    #
    # Execute a node at a given position. This is used to execute
    # standalone modules.
    #
    # @param self The object pointer.
    # @param position The position in the collection of the node to
    # edit.    
    def executeNode(self, position):
        self.nodes[position].execute()


    ## Execute a node.
    #
    # Execute the node at a given position in the collection.
    #
    # @param self The Object pointer.
    # @param position The position in the collection of the node to execute.
    #def executeNode(self, position):
    #    self.nodes[position].execute()


    ## Execute the collection.
    #
    # Sequentially execute the nodes in the collection. The collection is designed 
    # to be executed as a thread. The thread is started in the project.User.executeCollection() 
    # method.
    #
    # The collection notifies the system by sending log messages of the type state.collection.execution.
    #
    # @param self The Object pointer.
    def execute(self):
        msgTopic = "state.collection.execution"
        msg = {}
        msg['state'] = 'running'
        msg['isError'] = False
        msg['threadId'] = self.threadId
        pub.sendMessage(msgTopic, msg)

        for (ind, curNode) in enumerate(self.nodes):
            if ind == 0:
                curNode.run(threadId=self.threadId)
            else:
                #curNode.run(threadId=self.threadId)
                curNode.run(threadId=self.threadId,
                                prevNodeOutput=self.nodes[ind-1].output)

        msgTopic = "state.collection.execution"
        msg = {}
        msg['state'] = 'finished'
        msg['isError'] = False
        msg['threadId'] = self.threadId 
        pub.sendMessage(msgTopic, msg)


    ## Set the node's project attribute.
    #    
    def setNodeProject(self, project):
        for curNode in self.nodes:
            curNode.project = project


    ## Log messages to the collection's log file.
    # 
    # The collection is executed as a thread which has an unique id. 
    # For each thread, a log file with the thread ID as the filename is created 
    # in the project's temporary directory. All messages created by the nodes in 
    # the collection are written to this file.
    #        
    def log(self, nodeName, mode, msg):
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


        # If a threa is running, add the log message to the log file.
        if self.threadId:
            logFile = open(os.path.join(self.tmpDir, self.threadId + ".log"), 'a')
            logFile.write(msgString)
            logFile.close()







