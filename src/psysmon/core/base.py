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
from wx.lib.pubsub import Publisher as pub
import MySQLdb as mysql
from datetime import datetime
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

        Paramters
        ---------
        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base`
        :param baseDir: The pSysmon base directory. 
        :type baseDir: String

        '''

        # Check the baseDir parameter for errors.
        if not isinstance(baseDir, str):
            msg = "The baseDir should be a string."
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

        self.packages = {}
        ''' The loaded pSysmon packages.
        A dictionary of all pSysmon packages found in the packageDirectory.
        '''

        self.project = ""
        ''' The currently loaded pSysmon project.'''


    def scan4Package(self):
        '''
        Scan for available pSysmon packages.

        Scan the pSysmon package directory for packages.
        For each package directory found, the pkgInit function of the pkgInit module 
        is called. The packages created by the pkgInit function are added to 
        the packages attribute of the Base instance.
        '''
        packages2Register = [ name for name in os.listdir(self.packageDirectory) if os.path.isdir(os.path.join(self.packageDirectory, name)) and name[0]!='.']

        for curPkg in packages2Register:
            print "Registering package " + curPkg + "."
            pkgName = os.path.basename(curPkg)
            try:
                #pkgInit = __import__("psysmon.packages."+pkgName+".pkgInit", fromlist=['pkgInit'])
                #pkgInit = reload(pkgInit)
                #pkgObject = pkgInit.pkgInit();
                #pkgObject.setPyPackageName("psysmon.packages."+pkgName)
                #pkgObject.setBaseDir(os.path.join(self.packageDirectory, curPkg))
                #self.packages[pkgObject.name] = pkgObject
                pkgName = "psysmon.packages."+pkgName
                pkgModule = __import__(pkgName)
                pkgModule = sys.modules[pkgName]
                isOk = self.checkPackage(pkgModule)

                if isOk:
                    self.addPackage(pkgModule, pkgName, curPkg)

            except IndexError:
                print "No init file found."


    def checkPackage(self, pkg2Check):
        '''
        Check for valid package.

        Check if the package module contains the required attributes.
        '''
        requiredAttributes = ['name', 'version', 'author', 
                              'minPsysmonVersion', 'description', 'website']
        tmp = dir(pkg2Check)
        #if 'name' in tmp and 'version' in tmp and 'author' in tmp and 'minPsysmonVersion' and 'description' in tmp and 'website' in tmp:
        for curAttr in requiredAttributes:
            if curAttr not in tmp:
                return False

        return False


    def addPackage(self, pkgModule, pkgName, pkgBaseDir):
        '''
        Create and add a package.
        '''
        curPkg = Package(name=pkgModule.name,
                         version=pkgModule.version,
                         dependency=None)

        # Get the database queries.
        if 'databaseFactory' in dir(pkgModule):
            print "Getting the database queries."
            queries = pkgModule.databaseFactory()
            curPkg.addDbTableCreateQuery(queries)

        # Get the collection node templates.
        if 'nodeFactory' in dir(pkgModule):
            print "Getting the collection node templates."
            nodes = pkgModule.nodeFactory()
            curPkg.addCollectionNodeTemplate(nodes)

        # Set the collection node template runtime attributes.
        curPkg.setPyPackageName(pkgName)
        curPkg.setBaseDir(os.path.join(self.packageDirectory, pkgBaseDir))

        # Add the package to the packages list.
        self.packages[curPkg.name] = curPkg


    def getCollectionNodeTemplate(self, name):
        '''
        Get a collection node template.

        Search for the collection node template with the name *name* in the 
        packages and return it when found. If no template is found, return 
        *False*.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base` object.
        :param name: The name of the collection node template to get.
        :param self: String
        :rtype: :class:`~psysmon.core.base.CollectionNodeTemplate` or False
        '''
        for curPkg in self.packages.itervalues():
            tmp = curPkg.getCollectionNodeTemplate(name)
            if(tmp != False):
                return tmp

        return False



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
        self.project.createDatabaseStructure(self.packages)
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


    def searchCollectionNodeTemplates(self, searchString):
        '''
        Find collection node templates containing the searchString in their 
        name or their tags.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Base`
        :param searchString: The string to search for.
        :type searchString: String
        :rtype: A list of :class:`~psysmon.core.base.CollectionNodeTemplate` 
            instances.
        '''
        nodesFound = {}
        for curPkg in self.packages.itervalues():
            for curNode in curPkg.collectionNodeTemplates.itervalues():
                if searchString in ','.join([curNode.name]+curNode.tags):
                    nodesFound[curNode.name] = curNode

        return nodesFound


class Package:
    '''
    The pSysmon Package class.
    
    A pSysmon package provides the functionality to pSysmon. A package contains 
    a set of CollectionNodeTemplates which can be used by the pSysmon user to 
    create the collections. 

    Usage
    -----
    The packages are created in the pkgInit function of each pSysmon package.@n 
    Below follows an example of a package initialization::

        from psysmon.core.base import Package, CollectionNodeTemplate

        def pkgInit():
            # Create the pSysmon package.
            myPackage = Package(
                                name = 'geometry',
                                version = '0.1',
                                dependency = ''
                                )
            
            # The geom_recorder table.
            query = ("CREATE TABLE IF NOT EXISTS </PREFIX/>_geom_recorder "
                    "("
                    "id int(10) NOT NULL auto_increment,"
                    "serial varchar(45) NOT NULL default '',"
                    "type varchar(255) NOT NULL default '',"
                    "PRIMARY KEY  (id),"
                    "UNIQUE (serial, type)"
                    ") "
                    "ENGINE=MyISAM "
                    "DEFAULT CHARSET=latin1 "
                    "COLLATE latin1_general_cs")
            
            myPackage.addDbTableCreateQuery(query)

            # Create a pSysmon collection node template and add it to the package.
            property = {}
            property['inputFiles'] = []                     # The files to import.
            myNodeTemplate = CollectionNodeTemplate(
                                                    name = 'edit geometry',
                                                    type = 'standalone',
                                                    category = 'Geometry',
                                                    tags = ['stable'],
                                                    nodeClass = 'editGeometry',
                                                    property = property
                                                    )
            
            myPackage.addCollectionNodeTemplate(myNodeTemplate)
            
            return myPackage

    Package creation
    ----------------
    As you can see in the example code, first the Package is created using the 
    psysmon.core.base.Package constructor. The package name, version and dependency 
    are passed to the constructor.

    Database table creation
    -----------------------
    Each package can add database tables to the pSysmon database. These tables are 
    created for each project. To add a database table, place the mysql create 
    statement as shown in the example above into a python string. Add the table 
    create statement to the package by using the :meth:`~psysmon.core.base.Package.addDbTableCreateQuery` function.
    The *</PREFIX/>* tag in the mysql query will be replaced by pSysmon with the 
    current project name.

    Collection node template creation
    ---------------------------------
    Each package will provide one ore more collection nodes which can be used 
    by the user. To let pSysmon know what collection nodes each package provides 
    one has to create a CollectionNodeTemplate for each CollectionNode in the 
    pkgInit function. In the code example above, one CollectionNodeTemplate is 
    created by calling the CollectionNodeTemplate constructor and added to the 
    package *myPackage* by calling the :meth:`~psysmon.core.Base.Package.addCollectionNodeTemplate` function.
    To learn more about the parameters passet to the CollectionNodeTemplate, 
    especially the *property* parameter please see the CollectionNodeTemplate.
     
    .. seealso:: 
        class :class:`psysmon.core.base.CollectionNodeTemplate`
            The collection node template class.
                    
    '''

    ## The constructor
    #
    # Create a pSysmon package.@n
    # Use the addCollectionNodeTemplate and the addDbTableCreateQuery to fill 
    # the package content.@n
    # @note The only place where to use this constructor should be the pkgInit 
    # function of each pSysmon package.
    #
    # @param self The Object pointer.
    # @param name The name of the package.
    # @param version The version of the package. The package version is used to 
    # update the package database in case of a version change.
    # @param dependency A list of other packages needed to run this package.
    def __init__(self, name, version, dependency):   
        '''
        The constructor.

        Create a pSysmon package.
        After creating a package, the methods :meth:`~psysmon.core.base.Package.addCollectionNodeTemplate` 
        and :meth:`~psysmon.core.base.Package.addDbTableCreateQuery` to fill 
        the package with content.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.base.Package`
        :param name: The name of the package.
        :type name: String
        :param version: The version of the package.
        :type version: String
        :param dependency: [deprecated] A list of other packages needed to run this package.     
        :type dependency: String  
        '''

        self.pyPackage = ""
        '''
        The python package name of the package. 
            Type:
                String
        '''     

        self.name = name
        '''
        The package name. 
            Type:
                String
        '''

        self.version = version
        '''
        The package version. 
            Type:
                String
        '''

        self.dependency = dependency
        '''
        The package dependencies. 
            [deprecated]
        '''

        self.collectionNodeTemplates = {}
        '''
        The collection node templates of the package. 
            Type:
                Dictionary of :class:`~psysmon.core.base.CollectionNodeTemplate` instances.
                The key of the dictionary is the name of the collection node.
        '''

        self.dbTableCreateQueries = {}
        '''
        The package database table create queries.
            Each package can add its own database tables.
            Type:
                A dictionary of Strings. The key of the dictionary is the name of the 
                table.
        '''

        self.baseDir = ""
        '''
        The package directory.
            Type:
                String
        '''
        

        self.docDir = ""
        '''
        The package documentation directory.
            Type: String
        '''


    ## Set the python package name of the collectionNodeTemplates.
    # 
    # Each CollectionNodeTemplate holds the python package name (e.g. psysmon.packages.geometry) 
    # to which it belongs. This method sets the nodePkg property of each 
    # Collection node template.
    #
    # @see Base.scan4Package
    #
    # @param self The object pointer.
    # @param pyPackage The python package name.
    def setPyPackageName(self, pyPackage):
        for curNode in self.collectionNodeTemplates.itervalues():
            curNode.setNodePkg(pyPackage)


    ## Set the package base directory. 
    #
    # @param self The object pointer.
    # @param baseDir The full path to the package directory.
    def setBaseDir(self, baseDir):
        if os.path.isdir(baseDir):
            self.baseDir = baseDir 
            self.docDir = os.path.join(self.baseDir, "doc")


    ## Add a collection node template to the package.
    #
    # The @e curNode CollectionNodeTemplate will be added to the package dictionary 
    # @e collectionNodeTemplates. The key of the dictionary is the node's name.
    #
    # @param self The object pointer.
    # @param curNode The CollectionNodeTemplate to be added to the package.    
    def addCollectionNodeTemplate(self, nodes):
        if not nodes:
            return

        for curNode in nodes:
            curNode.parentPackage = self
            self.collectionNodeTemplates[curNode.name]= curNode


    ## Get a collection node template from the package.
    #
    # @param self The object pointer.
    # @param nodeName The name of the CollectionNodeTemplate to fetch.
    def getCollectionNodeTemplate(self, nodeName):
        if(self.collectionNodeTemplates.has_key(nodeName)):
            return self.collectionNodeTemplates[nodeName]
        else:
            return False


    ## Add a database table creation query to the package.
    #
    # If the package needs an own database table, the queries creating these 
    # tables can be added to the package using this function.@n
    # The queries are saved in a dictionary with the table name as the key.
    #
    # @param self The object pointer.
    # @param query The mysql query holding the table create statement.
    def addDbTableCreateQuery(self, queries):
        if not queries:
            return

        for curQuery in queries:
            ind = curQuery.find('</PREFIX/>')
            ind2 = curQuery.find(' ', ind)
            tableName = curQuery[ind+11:ind2]
            self.dbTableCreateQueries[tableName] = curQuery



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
    def log(self, nodeName, type, msg):
        curTime = datetime.now()
        timeStampString = datetime.strftime(curTime, '%Y-%m-%d %H:%M:%S')

        if type == 'error':
            modeString = '[ERR] '
        elif type == 'warning':
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





## The CollectionNode class.
# 
# All collection nodes provided by packages have to be subclasses of the 
# CollectionNode class. The abstract class requires the @e edit and the @e execute 
# function to be defined by the subclass.
#
# @subsection sub1 CollectionNodeTemplates and CollectionNodes
# When creating a pSysmon package in the pkgInit function one creates 
# CollectionNodeTemplates and adds them to the package. So how do CollectionNodeTemplates 
# and CollectionNodes work together?@n
# As the class name already suggests, the CollectionNodeTemplate is a template 
# which can be used to create instances of the CollectionNode which is provided 
# by the package. Each CollectionNodeTemplate has an attribute named @e nodeClass.
# This nodeClass has to be a class which is a subclass of the CollectionNode.@n
# 
# @subsection example An example
# Lets a look at the following CollectionNodeTemplate created in a pkgInit 
# function:
# 
# @code
#from psysmon.core.base import Package, CollectionNodeTemplate
#
#def pkgInit():
#    # Create the pSysmon package.
#    myPackage = Package(
#                        name = 'obspyImportWaveform',
#                        version = '0.1',
#                        dependency = ''
#                        )
#    
#    
#    # Create a pSysmon collection node template and add it to the package.
#    property = {}
#    property['inputFiles'] = []                     # The files to import.
#    property['lastDir'] = ""                        # The last used directory.
#    myNodeTemplate = CollectionNodeTemplate(
#                                            name = 'import waveform',
#                                            type = 'editable',
#                                            category = 'Data Import',
#                                            tags = ['stable'],
#                                            nodeClass = 'ImportWaveform',
#                                            property = property
#                                            )
#    
#    myPackage.addCollectionNodeTemplate(myNodeTemplate)
#    
#    return myPackage
# @endcode
#
# In this code example, a CollectionNodeTemplate named @e import @e waveform is 
# created which has the nodeClass @e ImportWaveform. As we already have learned, 
# the class @e ImportWaveform is the actual class providing the functionality and 
# it has to be a subclass of the CollectionNode class.@n
# 
# The basic skeleton of the ImportWaveform class should look like this:
# @code
#import psysmon.core.base
# 
#class ImportWaveform(psysmon.core.base.CollectionNode):
#    
#    def edit(self, psyProject):
#        print "Editing the node %s." % self.name
#        
#    def execute(self, psyProject, prevNodeOutput={}):
#        print "Executing the node %s." % self.name
#        
# @endcode
#
# The @e edit method is called when editing a collection node, the @e execute 
# method is called when executing the collection node. 
#
# @see base.CollectionNodeTemplate
# @see project.Project.addNode2Collection
class CollectionNode:

    ## The CollectionNode constructor.
    #
    # @param self The Object pointer.
    # @param name The name of the collection node.
    # @param type The type of the collection node.
    # Allowed values are:
    # - editable
    # - uneditable
    # - standalone
    # @param category The category to which the collection node is assigned to.
    # @param tags A list of strings containing the tags of the collection node. These values are 
    # not limited but they should contain one of the three development state tags:
    # - stable
    # - experimental
    # - damaged
    # @param property A dictionary containing the default properties of the 
    # collection node. This dictionary is used to initialize a new collection node 
    # and to save the user input for this collection node during the sessions.
    # @param parent The parent package of the collection node.
    def __init__(self, name, type, category, tags, property, parent, project):

        ## The name of the collection node.  
        self.name = name

        ## The type of the collection node.
        #
        # Each collection node can specify it's type. Currently there are three 
        # allowed values:
        # - editable The user can edit the node paramters.
        # - uneditable There are no node parameters to edit.
        # - standalone The node is not included in the collection execution. Each 
        # node can be executed individually using the collection listbox context menu.
        self.type = type

        ## The category of the collection node.
        self.category = category

        ## The tags assigned to the collection node.
        #
        # The tags attribute is a list of Strings.@n
        # Additionally to the category, one or more tags can be assigned to the 
        # collection node. These tags can be used when creating sub-selections of 
        # all available collection nodes.@n 
        # For example, a set of nodes has been created for the processing tasks 
        # at a certain institution or for a special project, one could tag these 
        # nodes with the institution name or the project name to make it easy for 
        # users to select these nodes or also to hide these nodes from their 
        # collection node inventory.@n
        # The tag values are not limited but they should contain one of the three 
        # development state tags:
        # - stable
        # - experimental
        # - damaged
        self.tags = tags

        ## The collection node properties.
        #
        # Each collection node can have a set of parameters which can be edited 
        # by the user and which are used when executing the collection node. 
        # These properties will also be saved with the collection node during 
        # the pSysmon sessions.@n
        # The @e property attribute is a dictionary with the property name as it's key.@n
        # @note Usually, the property values are defined in the pkgInit file.
        self.property = property

        ## The package which contains the collection node.
        self.parentPackage = parent

        ## The node's enabled state.
        # 
        # Mark the collection node as enabled or disabled.
        self.enabled = True

        ## The collection node's output.
        # 
        # The output dictionary can be used to pass parameters to the next
        # node in the collection. 
        self.output = {}

        ## The current pSysmon project.
        #
        self.project = project


        ## The parent collection holding the node instance.
        #
        self.parentCollection = None


        # If the node is executed in a collection thread a thread ID is
        # assigned.
        self.threadId = None


    ## The __getstate__ method.
    #
    # Remove the project instance before pickling the instance.
    def __getstate__(self):
        result = self.__dict__.copy()
        del result['project']
        return result

    ## The __setstate__ method.
    #
    # Fill the attributes after unpickling.
    def __setstate__(self, d):
        self.__dict__.update(d) # I *think* this is a safe way to do it
        self.project = None




    ## The collection node edit method.
    #
    # The CollecitonNode class requires from it's subclasses to define this method.@n 
    # The @e edit method is called to edit the collection node parameters. In 
    # the pSysmon GUI this is done using the collection listbox context menu.
    # Within the edit method it's up to the programmer of the collection node 
    # how to get the user input to change the collection node properties.
    #
    # @param self The object pointer.
    # @param project The current pSysmon project.
    def edit(self):
        assert False, 'edit must be defined'


    ## The collection node execute method.
    #
    # The CollecitonNode class requires from it's subclasses to define this method.@n 
    # The @e execute method is called to execute the collection node. In 
    # the pSysmon GUI this is done using the @e execute @e collection button.
    # Within the execute method it's up to the programmer of the collection node 
    # what algorithm actually is executed.
    #
    # @param self The object pointer.
    # @param project The current pSysmon project.
    # @param prevNodeOutput The output of the previous node in the collection
    def execute(self, prevNodeOutput={}):
        assert False, 'execute must be defined'   


    ## Run the collection node from within a thread.
    # 
    # A Collection object is designed to be executed as a thread. The Collection.execute() 
    # method calls the run method of each collection node. In the run method several 
    # thread dependent attributes can be set before executing the collection node.
    # Currently the threadId is saved as an attribute of the collection node 
    # so that the node knows to which thread it belongs to.
    def run(self, threadId, prevNodeOutput={}):
        self.threadId = threadId
        self.execute(prevNodeOutput)


    ## Log messages.
    #
    # The collection node is executed by a CollectionNode object. This object handles 
    # the logging of various messages (error, warning, status, ...) to a log file.
    # 
    # @see CollectionNode.log  
    def log(self, type, msg):

        # If the node is running in a thread, log to the collection (the
        # log file). 
        # If the thread is not running, log to the pSysmon log area.
        if self.threadId:
            self.parentCollection.log(self.name, type, msg)
        else:
            self.project.log(type, msg)



## The CollectionNodeTemplate class.
# 
# This class holds a template which is used to create collection nodes. The 
# CollectionNodeTemplate should be used only in the pkgInit functions to 
# register the pSysmon collection nodes within pSysmon.
#
# @subsection sub1 CollectionNodeTemplates and CollectionNodes
# When creating a pSysmon package in the pkgInit function one creates 
# CollectionNodeTemplates and adds them to the package. 
# As the class name already suggests, the CollectionNodeTemplate is a template 
# which can be used to create instances of the CollectionNode which is provided 
# by the package. 
# 
# @subsection example An example
# Lets take a look at the following CollectionNodeTemplate created in a pkgInit 
# function:
# 
# @code
#from psysmon.core.base import Package, CollectionNodeTemplate
#
#def pkgInit():
#    # Create the pSysmon package.
#    myPackage = Package(
#                        name = 'obspyImportWaveform',
#                        version = '0.1',
#                        dependency = ''
#                        )
#    
#    
#    # Create a pSysmon collection node template and add it to the package.
#    property = {}
#    property['inputFiles'] = []                     # The files to import.
#    property['lastDir'] = ""                        # The last used directory.
#    myNodeTemplate = CollectionNodeTemplate(
#                                            name = 'import waveform',
#                                            type = 'editable',
#                                            category = 'Data Import',
#                                            tags = ['stable'],
#                                            nodeClass = 'ImportWaveform',
#                                            property = property
#                                            )
#    
#    myPackage.addCollectionNodeTemplate(myNodeTemplate)
#    
#    return myPackage
# @endcode
#
# In this code example, a CollectionNodeTemplate named @e import @e waveform is 
# created. The CollectionNodeTemplate takes several parameters to specify the 
# collection node to be built using this template.
class CollectionNodeTemplate:

    ## The constructor.
    #
    # @param self The object pointer.
    # @param name The collection node name.
    # @param type The collection node type.
    # @param category The collection node category.
    # @param tags The collection node tags.
    # @param property A dictionary specifying the properties of the collection node. 
    # @param nodeClass The class to be used when creating the collection node from the template.
    def __init__(self, name, type, category, tags, nodeClass, property={}, docEntryPoint=None):
        ## The name of the collection node. 
        self.name = name

        ## The type of the collection node.
        #
        # Each collection node can specify it's type. Currently there are three 
        # allowed values:
        # - editable The user can edit the node paramters.
        # - uneditable There are no node parameters to edit.
        # - standalone The node is not included in the collection execution. Each 
        # node can be executed individually using the collection listbox context menu.
        self.type = type

        ## The category of the collection node.
        self.category = category

        ## The tags assigned to the collection node.
        #
        # The tags attribute is a list of Strings.@n
        # Additionally to the category, one or more tags can be assigned to the 
        # collection node. These tags can be used when creating sub-selections of 
        # all available collection nodes.@n 
        # For example, a set of nodes has been created for the processing tasks 
        # at a certain institution or for a special project, one could tag these 
        # nodes with the institution name or the project name to make it easy for 
        # users to select these nodes or also to hide these nodes from their 
        # collection node inventory.@n
        # The tag values are not limited but they should contain one of the three 
        # development state tags:
        # - stable
        # - experimental
        # - damaged
        self.tags = tags

        ## The collection node properties.
        #
        # Each collection node can have a set of parameters which can be edited 
        # by the user and which are used when executing the collection node. 
        # These properties will also be saved with the collection node during 
        # the pSysmon sessions.@n
        # The @e property attribute is a dictionary with the property name as it's key.@n
        # @note Usually, the property values are defined in the pkgInit file.
        self.property = property

        ## The package which contains the collection node.
        self.nodeClass = nodeClass

        ## The node documentation entry point.
        #
        # Each collection node should provide an online documentation in html
        # format. The entry point file can be given using this attribute.
        # the docEntryPoint file has to be saved in the package's doc folder.
        self.docEntryPoint = docEntryPoint 


        ## The package which contains the collection node.
        self.parentPackage = None


    ## Set the name of the collection node package.
    #
    #     
    def setNodePkg(self, nodePkg):
        ## The name of the python package containing the nodeClass.
        #
        # This attribute holds the name of the @b python package holding the 
        # nodeClass. This package is not to be mixed up with the pSysmon package.
        self.nodePkg = nodePkg



class inheritedBase(Base):
    '''
    This is a test class.
    '''        

    def __init(self):
        pass

