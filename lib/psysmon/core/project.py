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

import os
import thread
import copy
from wx.lib.pubsub import Publisher as pub
import MySQLdb as mysql
from datetime import datetime
import psysmon.core.base
from psysmon.core.util import PsysmonError

## The pSysmon project.
#
#
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

    dbConn :
        The mySQL database connection.

    dbHost : String
        The host URL on which the mySQL database server is running.

    dbName : String
        The mySQL database name.
        The database of the project is named according tto the admin unser 
        using *psysmon_* as a prefix (e.g.: psysmon_ADMINUSERNAME).

    dbTableNames : Dictionary of Strings
        A dictionary of the project database table names.

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

    def __init__(self, name, baseDir, user, dbHost='localhost', dbName="", dbVersion={}, createTime="", dbTableNames={}):
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

        # The host on which the mySQL database server is running.
        self.dbHost = dbHost

        # The mySQL database name.
        if not dbName:
            self.dbName = "psysmon_" + user.name
        else:
            self.dbName = dbName

        # A dictionary of the project databaser table names.
        self.dbTableNames = dbTableNames

        # The project file.
        self.projectFile = self.name +".ppr"

        # The version dictionary of the package dtabase structures.
        self.dbVersion = dbVersion

        # A list of waveform directories associated with the project.
        self.waveformDirList = ()

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
        self.dbConn = mysql.connect(self.dbHost, self.activeUser.name, passwd, self.dbName)
        self.cur = self.dbConn.cursor(mysql.cursors.DictCursor)     # Fetch rows as dictionaries.


    ## Execute a database query.
    #
    # @param self The Object pointer.
    # @param query The mySQL query string. 
    # @param type The type of the query (select, insert, update, alter)    
    def executeQuery(self, query, mode='select'):
        '''Execute a database query.

        Parameters
        ----------
        query : String
            The mySQL query string.
        type : String
            The type of the query (select, insert, update, alter)

        Returns
        -------
        result : Dictionary
            A dictionary containing the query result. The dictionary has the 
            following keys:

            isError
                Did the query raise an error? (Boolean)

            msg
                The error message returned by the mySQL server. (String)

            data
                The data returned by the mySQL server. In case of *select* queries, 
                each queried column creates a key in the dictionary. (dictionary)

        Examples
        --------
        Select the data from the pSysmon geom_stations table. For this example 
        it is assumed, that *project* is a :class:`Project` instance and 
        the connection to the database has already been established:
        ::
            tableName = project.dbTableNames['geom_station']
            query =  ("SELECT"
                  "id, net_name, name, location, X, Y, Z, coord_system, description "
                  "FROM %s") % tableName 
            res = project.executeQuery(query)

            if not res['isError']:
                for curData in res['data']:
                    print "Station name %s" % curData['name']
            else:
                print res['msg']

        '''
        try:
            self.cur.execute(query)

            if mode == 'select':
                data = self.cur.fetchall()       # Return the selected data.
            elif mode == 'insert':
                data = int(self.cur.rowcount)    # Return the affected rows.
            elif mode == 'update':
                data = int(self.cur.rowcount)    # Return the affected rows.
            elif mode == 'alter':
                data = int(self.cur.rowcount)    # Return the affected rows.


            return {'isError': False,
                    'msg': '',
                    'data': data}

        except (mysql.DataError, mysql.IntegrityError, mysql.ProgrammingError), e:
            msg = ("The query that you have have passed is not valid. "
                   "Please check the query before trying to execute it again.\n"
                   "Your query (mode = %s):\n"
                   "%s\n" 
                   "The exact error information reads as follows:\n%s") % (mode, query, e)
            return {'isError': True,
                    'msg': msg,
                    'result': ''}
        except (mysql.OperationalError, mysql.InternalError, mysql.NotSupportedError), e:
            msg = ("An irrecoverable error has occured in the way your data was "
                   "processed. Please report this error to the pSysmon development team.\n"
                   "Your query (mode = %s):\n"
                   "%s\n" 
                   "The exact error information reads as follows:\n%s") % (mode, query, e)
            return {'isError': True,
                    'msg': msg,
                    'result': ''}
        except mysql.Warning:
            pass


    def executeManyQuery(self, query, data, mode='select'):
        '''Execute a database query having multiple values to insert, update or select.

        Parameters
        ----------
        data : Dictionary
            The data to be inserted or updated. The keys of the dictionary 
            represent the data column names.
        query : String
            The mySQL query string.
        type : String
            The type of the query (select, insert, update)

        Returns
        -------
        res : Dictionary
            A dictionary containing the query result. The dictionary has the 
            following keys:

            isError 
                Did the query raise an error? (Boolean)

            msg 
                The error message returned by the mySQL server. (String)

            data
                The data returned by the mySQL server. In case of *select* queries, 
                each queried column creates a key in the dictionary. (Dictionary)

        Examples
        --------
        This example is taken from :meth:'~psysmon.packages.geometry.Inventory.writeRecorders2Db`.
        First, the list *dbRecorderData* is filled with the data to be inserted 
        into the database table. Next the query statement is created and the 
        executeManyQuery is used to insert the *dbRecorderData* list.
        ::
            def writeRecorders2Db(self, project):
                # Create the data lists to be inserted into the db.
                dbRecorderData = []         # The recorder data.
                for curRecorder in self.recorders:
                    dbRecorderData.append((curRecorder.serial, curRecorder.type))


                # Write the recorder data to the geom_recorder table.
                tableName = project.dbTableNames['geom_recorder']
                query =  ("INSERT IGNORE INTO %s "
                          "(serial, type) "
                          "VALUES (%%s, %%s)") % tableName  
                res = project.executeManyQuery(query, dbRecorderData)

                if not res['isError']:
                    print("Successfully wrote the recorders to the database.")
                else:
                    print res['msg']   
        '''
        try:
            self.cur.executemany(query, data)

            if mode == 'select':
                data = self.cur.fetchall()       # Return the selected data.
            elif mode == 'insert':
                data = int(self.cur.rowcount)    # Return the affected rows.
            elif mode == 'update':
                data = int(self.cur.rowcount)    # Return the affected rows.

            return {'isError': False,
                    'msg': '',
                    'data': data}

        except (mysql.DataError, mysql.IntegrityError, mysql.ProgrammingError), e:
            msg = ("The query that you have have passed is not valid. "
                   "Please check the query before trying to execute it again.\n"
                   "Your query (mode = %s):\n"
                   "%s\n" 
                   "The exact error information reads as follows:\n%s") % (mode, query, e)
            return {'isError': True,
                    'msg': msg,
                    'result': ''}
        except (mysql.OperationalError, mysql.InternalError, mysql.NotSupportedError), e:
            msg = ("An irrecoverable error has occured in the way your data was "
                   "processed. Please report this error to the pSysmon development team.\n"
                   "Your query (mode = %s):\n"
                   "%s\n" 
                   "The exact error information reads as follows:\n%s") % (mode, query, e)
            return {'isError': True,
                    'msg': msg,
                    'result': ''}
        except mysql.Warning:
            pass


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
                self.loadWaveformDirList()
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

        In pSysmon, each package can create its own database tables. The table create queries 
        can be listed in the package's databaseFactory function which is located in 
        the package's __init__.py module.

        During pSysmon startup from each package, the database table create queries 
        are requested and saved in the dbTableCreateQueries attribute of the 
        :class:`~psysmon.core.packageSystem.Package` instance. 

        When creating a new project, the database tables are created using this method. 
        The method iterates over all packages passed to the method, checks for available 
        table creation queries and if any present, executes them.

        Parameters
        ----------
        packages : Dictionary of :class:`~psysmon.core.packageSystem.Package` instances.
            The packages to be used for the database structure creation.
            The key of the dictionary is the package name.
        '''

        for _, curPkg in packages.iteritems():
            if not curPkg.dbTableCreateQueries:
                print "No database table queries found."
                continue
            else:
                print "Creating the tables for package " + curPkg.name
                self.dbVersion[curPkg.name] = curPkg.version
                for curName, curQuery in curPkg.dbTableCreateQueries.iteritems():
                    # Replace the table prefix keyword with the project name.
                    curQuery = curQuery.replace("</PREFIX/>", self.name)
                    print "Executing query: " + curQuery
                    res = self.executeQuery(curQuery)

                    if res['isError']:
                        print res['msg']
                    else:
                        print "Success"

                    self.dbTableNames[curName] = self.name + '_' + curName


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
        db['dbHost'] = self.dbHost
        db['dbName'] = self.dbName
        db['dbVersion'] = self.dbVersion
        db['user'] = self.user
        db['createTime'] = self.createTime
        db['dbTableNames'] = self.dbTableNames
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
        wfDirTable = self.dbTableNames['waveformDir']
        wfDirAliasTable = self.dbTableNames['waveformDirAlias']

        query = ("SELECT wfDir.id, wfDir.directory as dir, wfDirAlias.alias as dirAlias, wfDir.description " 
                 "FROM %s as wfDir " 
                 "LEFT JOIN (select * from %s where user like '%s') as wfDirAlias on (wfDir.id = wfDirAlias.wf_id) "  
                 "order by wfDir.id") % (wfDirTable, wfDirAliasTable, self.activeUser.name)

        res = self.executeQuery(query)
        if not res['isError']:
            self.waveformDirList = res['data']
            print self.waveformDirList
        else:
            print res['msg']


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

        if self.activeCollection:
            if not project.threadMutex:
                project.threadMutex = thread.allocate_lock()

            col2Thread = copy.deepcopy(self.activeCollection)
            col2Thread.setNodeProject(project)     # Reset the project of the nodes. This has been cleard by the setstate method.
            curTime = datetime.now()
            timeStampString = datetime.strftime(curTime, '%Y%m%d%H%M%S%f')
            col2Thread.threadId = col2Thread.name + "_" + timeStampString

            msg = "Executing collection " + col2Thread.name + "with thread ID: " + col2Thread.threadId + "."
            project.log("status", msg)

            msgTopic = "state.collection.execution"
            msg = {}
            msg['state'] = 'starting'
            msg['startTime'] = curTime
            msg['isError'] = False
            msg['threadId'] = col2Thread.threadId
            pub.sendMessage(msgTopic, msg)

            thread.start_new_thread(col2Thread.execute, ())
        else:
            raise PsysmonError('No active collection found!') 




