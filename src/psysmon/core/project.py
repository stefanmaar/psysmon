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
    GNU General Public License, Version 3 (http://www.gnu.org/copyleft/gpl.html)
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
    '''
    The pSysmon Project class.

    '''

    def __init__(self, name, baseDir, user, dbHost='localhost', dbName="", dbVersion={}, createTime="", dbTableNames={}):
        '''
        The constructor.

        Create an instance of the Project class.

        Parameters
        ----------
        :param self: The object pointer.
        :type self: :class:`~psysmon.core.project.Project`
        :param name: The name of the project.
        :type name: String
        :param baseDir: The base directory of the project.
        :type baseDir: String
        :param user: The admin user of the project.
        :type user: String
        :param dbHost: The database host.
        :type dbHost: String
        :param dbName: The name of the database associated with the project.
        :type dbName: String
        :param dbVersion: The database structure version used by the project.
        :type dbVersion: Dictionary of Strings with the name of the package as the key.
        :param createTime: DEPRECATED
        :param dbTableNames: The database tablenames used by the project.
        :type dbTableNames: Dictionary of Strings with the name of the table (without prefix) as the key.
        '''

        self.name = name
        ''' The project name.'''

        if not createTime:
            self.createTime = datetime.utcnow()
            ''' The time when the project has been created.'''
        else:
            self.createTime = createTime

        self.baseDir = baseDir
        ''' The project's base directory. '''

        self.projectDir = os.path.join(self.baseDir, self.name)
        ''' The project directory. '''

        self.dbHost = dbHost
        ''' The host on which the mySQL database server is running.'''

        if not dbName:
            self.dbName = "psysmon_" + user.name
        else:
            self.dbName = dbName
            ''' 
            The mySQL database name.
            The database of the project is named according to the admin 
            username using psysmon_ as a prefix (psysmon_ADMINUSERNAME).
            '''

        self.dbTableNames = dbTableNames
        '''
        A dictionary of the project databaser table names.
        '''

        self.projectFile = self.name +".ppr"
        '''
        The project file.
        The project file is saved in the project Dir.
        '''

        self.dbVersion = dbVersion
        '''
        The version dictionary of the package dtabase structures.
        key: package name
        '''

        self.waveformDirList = ()
        '''
        A list of waveform directories associated with the project.
        Each entry in the list is a dictionary with the fields id, dir, dirAlias and description.
        '''

        self.saved = False
        '''
        Is the project saved?
        '''

        self.threadMutex = None
        '''
        The thread lock object.
        '''

        self.user = []
        '''
        A list of users associated with this project.
        The user creating the project is always the admin user.
        '''

        self.activeUser = ""
        '''
        The currently active user.
        '''

        # Add the user(s) to the project user list.
        if isinstance(user, list):
            self.user.extend(user)
        else:
            self.user.append(user)



    def setCollectionNodeProject(self):
        for curUser in self.user:
            for curCollection in curUser.collection.itervalues():
                curCollection.setNodeProject(self)



    ## Connect to the mySQL database.
    #
    # This method creates the database connection and the cursor needed to 
    # execute the queries.
    #
    # @param self The Object pointer.
    # @param passwd The user's database password.     
    def connect2Db(self, passwd):    
        ## The mySQL database connection.
        self.dbConn = mysql.connect(self.dbHost, self.activeUser.name, passwd, self.dbName)
        self.cur = self.dbConn.cursor(mysql.cursors.DictCursor)     # Fetch rows as dictionaries.


    ## Execute a database query.
    #
    # @param self The Object pointer.
    # @param query The mySQL query string. 
    # @param type The type of the query (select, insert, update, alter)    
    def executeQuery(self, query, mode='select'):
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


    ## Execute a database query having multiple values to insert, update or select.
    #
    # @param self The Object pointer.
    # @param query The mySQL query string as required by the mysqldb.executemany method. 
    # @param data The data to be processed by the query.
    # @param type The type of the query (select, insert, update)       
    def executeManyQuery(self, query, data, mode='select'):
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
        for curUser in self.user:
            if curUser.name == userName:
                self.activeUser = curUser
                self.connect2Db(pwd)
                self.loadWaveformDirList()
                return True

        return False

    ## Create the project directory structure.
    #
    # @param self The Object pointer.        
    def createDirectoryStructure(self):
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


    ## Update the project directory structure.
    #
    # @param self The Object pointer.        
    def updateDirectoryStructure(self):
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


    ## Create the project's database structure.
    #
    # @param self The Object pointer.
    # @param packages The packages to be used for the database structure creation. 
    def createDatabaseStructure(self, packages):

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


    ## Check if the database has to be updated.
    #
    # @param self The object pointer.
    # @param packages The packages to be checked for a database to be updated.
    def checkDbVersions(self, packages):
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


    ## Save the project to a file.
    #
    # @param self. The object pointer.
    def save(self):
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


    ## Add a collection to the project.
    #
    # @param self The object pointer.
    # @param name The name of the new collection.
    def addCollection(self, name):
        self.activeUser.addCollection(name, self)


    ## Get all collections of the project.
    #
    # @param self The object pointer.
    def getCollection(self):
        return self.activeUser.collection


    ## Get the currently active collection.
    #
    # @param self The object pointer.
    def getActiveCollection(self):
        return self.activeUser.activeCollection


    def setActiveCollection(self, name):
        self.activeUser.setActiveCollection(name)


    def addNode2Collection(self, nodeTemplate, position=-1):
        try:
            # The collection node class module should begin with a lower case letter.
            nodeModuleName = nodeTemplate.nodeClass[0].lower() + nodeTemplate.nodeClass[1:]
            nodeModule = __import__(nodeTemplate.nodePkg+"." + nodeModuleName, fromlist=[nodeTemplate.nodeClass])
        except:
            # If this doesn't work, try the original class name.
            nodeModule = __import__(nodeTemplate.nodePkg+"." + nodeTemplate.nodeClass, fromlist=[nodeTemplate.nodeClass])

        nodeClass = getattr(nodeModule,nodeTemplate.nodeClass)
        node = nodeClass(name = nodeTemplate.name,
                         mode = nodeTemplate.mode,
                         category = nodeTemplate.category,
                         tags = nodeTemplate.tags,
                         parent = nodeTemplate.nodePkg,
                         options = nodeTemplate.options,
                         project = self
                         )
        self.activeUser.addNode2Collection(node, position)



    def removeNodeFromCollection(self, position):
        self.activeUser.removeNodeFromCollection(position)


    def getNodeFromCollection(self, position):
        return self.activeUser.getNodeFromCollection(position)


    def editNode(self, position):
        self.activeUser.editNode(position)


    def executeNode(self, position):
        self.activeUser.executeNode(position)


    def executeCollection(self):
        self.activeUser.executeCollection(self)


    def loadWaveformDirList(self):
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
        msgTopic = "log.general." + mode
        pub.sendMessage(msgTopic, msg)






## The pSysmon user.
# 
# The user class holds the details of the user and the userspecific project
# variables (e.g. collection, settings, ...).
class User:

    def __init__(self, user, userMode):
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
        if not isinstance(self.collection, dict):
            self.collection = {}

        self.collection[name] = psysmon.core.base.Collection(name, tmpDir = project.tmpDir)
        self.setActiveCollection(name)

    def setActiveCollection(self, name):
        if name in self.collection.keys():
            self.activeCollection = self.collection[name]


    def addNode2Collection(self, node, position):
        if self.activeCollection:
            self.activeCollection.addNode(node, position)
        else:
            raise PsysmonError('No active collection found!')


    def removeNodeFromCollection(self, position):
        if self.activeCollection:
            self.activeCollection.popNode(position)
        else:
            raise PsysmonError('No active collection found!') 


    def getNodeFromCollection(self, position):
        if self.activeCollection:
            return self.activeCollection[position]
        else:
            raise PsysmonError('No active collection found!') 


    def editNode(self, position):
        if self.activeCollection:
            self.activeCollection.editNode(position)
        else:
            raise PsysmonError('No active collection found!') 

    def executeNode(self, position):
        if self.activeCollection:
            self.activeCollection.executeNode(position)
        else:
            raise PsysmonError('No active collection found!') 

    ## Execute the active collection.
    #
    # Start a thread to execute the current collection. A deep copy of the 
    # collection object is created and this copy is executed. The deep copy is
    # used to prevent the changes of the node's input and output parameters 
    # during the execution of the thread.
    #
    # @param self. The Object pointer.    
    def executeCollection(self, project):
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




