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
The pSysmon package system module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the classes needed to run the pSysmon package system.
'''

import os
import sys

class PackageManager:
    '''The Package Manager keeps track of the pSysmon packages and 
    manages them. 

    The packages of type :class:`Package` are loaded from the 
    packageDirectories. A package manager can handle multiple 
    package directories.

    Attributes
    ----------
    parent : Object
        The parent object holding the package manager.

    packageDirectories : List of Strings
        A list of directories holding the packages.

    packages : Dictionary of :class:`Package`
        A dictionary of packages managed by the PackageManager.
        Key: package name

    '''

    def __init__(self, parent, packageDirectories):
        '''The constructor.

        Parameters
        ----------
        packageDir : List of Strings
            The directories holding the pSysmon packages.
        '''

        # The parent object holding the package manager.
        self.parent = parent

        # A list of directories holding the packages.
        self.packageDirectories = packageDirectories

        # The packages managed by the PackageManager.
        self.packages = {}

        # Search for available packages.
        self.scan4Package()



    def scan4Package(self):
        '''Scan for available pSysmon packages.

        Scan the package directories for packages. Each package has to be 
        contained in a seperate folder. Each folder found in the 
        packageDirectories is processed and if a valid package is found, 
        it is registerd within the packageManager.

        Parameters
        ----------
        self : :class:`PackageManager`
            The object pointer.

        See Also
        --------
        :meth:`PackageManager.checkPackage` : Check for a valid package.
        :meth:`PackageManager.addPackage` : Add a package to the package manager.
        :class:`Package` : The pSysmon package class.
        '''

        for curDir in self.packageDirectories:
            self.parent.logger.debug("Scanning directory %s", curDir)
            packages2Register = [ name for name in os.listdir(curDir) 
                                  if os.path.isdir(os.path.join(curDir, name)) 
                                  and name[0]!='.']

            for curPkg in packages2Register:
                self.parent.logger.debug("Registering package " + curPkg + ".")
                pkgName = os.path.basename(curPkg)
                try:
                    # TODO: If multiple package directories are used,
                    # the following import will not work. Change it.
                    pkgName = "psysmon.packages."+pkgName
                    pkgModule = __import__(pkgName)
                    pkgModule = sys.modules[pkgName]
                    isOk = self.checkPackage(pkgModule)

                    if isOk:
                        self.addPackage(pkgModule, pkgName, curPkg, curDir)
                    else:
                        self.parent.logger.debug("Package check failed!")

                except IndexError:
                    self.parent.logger.debug("No init file found.")



    def checkPackage(self, pkg2Check):
        '''Check if the package is a valid pSysmon package.

        Check if the package module contains the required attributes. The attributes are:

        - name
        - version
        - author
        - minPsysmonVersion
        - description
        - website


        Parameters
        ----------
        pkg2Check : :class:`Package`
            The package to check for validity.


        Returns
        -------
        isValid: Boolean 
            True if package is valid, False otherwhise.


        See Also
        --------
        :class:`Package`
        :meth:`PackageManager.scan4Package`
        '''

        # The list of the required pSysmon package attributes.
        requiredAttributes = ['name', 'version', 'author', 
                              'minPsysmonVersion', 'description', 'website']
        tmp = dir(pkg2Check)
        for curAttr in requiredAttributes:
            if curAttr not in tmp:
                self.parent.logger.debug("Attribute %s is missing!" % curAttr)
                return False

        return True



    def addPackage(self, pkgModule, pkgName, pkgBaseDir, packageDir):
        '''Add a package to the packageManager.

        Create a :class:`Package` instance with the passed parameters. If the 
        databaseFactory or the nodeFactory functions exist, they are executed 
        and the databaseQueries and collectionNodes are added to the package.
        

        Parameters
        ----------
        pkgModule : Python module
            The pSysmon package module.
        pkgName : String
            The name of the package to be added.
        pkgBaseDir : String
            The package directory name.
        packageDir : String
            The directory containing the package directory.

        See Also
        --------
        :class:`Package`
        '''
        curPkg = Package(name=pkgModule.name,
                         version=pkgModule.version,
                         dependency=None)

        # Get the database queries.
        if 'databaseFactory' in dir(pkgModule):
            self.parent.logger.debug("Getting the database queries.")
            queries = pkgModule.databaseFactory()
            curPkg.addDbTableCreateQuery(queries)

        # Get the collection node templates.
        if 'nodeFactory' in dir(pkgModule):
            self.parent.logger.debug("Getting the collection node templates.")
            nodes = pkgModule.nodeFactory()
            for curNode in nodes:
                curNode.parent = pkgName

            curPkg.addCollectionNodeTemplate(nodes)

        # Set the collection node template runtime attributes.
        curPkg.setPyPackageName(pkgName)
        curPkg.setBaseDir(os.path.join(packageDir, pkgBaseDir))

        # Add the package to the packages list.
        self.packages[curPkg.name] = curPkg


    def searchCollectionNodeTemplates(self, searchString):
        '''Find collection node templates containing the *searchString* in their 
        name or their tags. 

        
        Parameters
        ----------
        searchString : String
            The string to search for.


        Returns
        -------
        nodesFound : List of :class:`~psysmon.core.packageNodes.CollectionNode` instances.
            The nodes found matching the *searchString*.
        '''
        nodesFound = {}
        for curPkg in self.packages.itervalues():
            for curNode in curPkg.collectionNodeTemplates.itervalues():
                if searchString in ','.join([curNode.name]+curNode.tags):
                    nodesFound[curNode.name] = curNode

        return nodesFound


    
    def getCollectionNodeTemplate(self, name):
        '''Get a collection node template.

        Search for the collection node with the name *name* in the 
        packages and return it when found. If no template is found, return 
        *False*.


        Parameters
        ----------
        name : String
            The name of the collection node template to get.
       
        
        Returns
        ------- 
        foundNode : :class:`~psysmon.core.packageNodes.CollectionNode` or False
            The node found ini the packages matching the name *name*. If no 
            collection node is found, False is returned.
        '''
        for curPkg in self.packages.itervalues():
            tmp = curPkg.getCollectionNodeTemplate(name)
            if(tmp != False):
                return tmp

        return False



class Package:
    '''The pSysmon Package class.

    A pSysmon package provides the functionality to pSysmon. A package contains 
    a set of :class:`psysmon.core.packageNodes.CollectionNode' templates which 
    can be added to a collection by the pSysmon user.

    pSysmon packages are realized as `Python packages <http://docs.python.org/tutorial/modules.html#packages>`_ 
    and the functionality is provided as `Python modules <http://docs.python.org/tutorial/modules.html#modules>`_  
    contained in the package.

    
    Attributes
    ----------
    baseDir : String
        The package directory.

    docDir : String
        The package documentation directory.

    dbTableCreateQueries : Dictionary of Strings
        The mySQL table create queries. The key of the dictionary is the name of the table.
    
    collectionNodeTemplates : Dicitonary of :class:`~psysmon.core.base.CollectionNode` instances.
        The collection nodes contained in the package. Key of the dictionary is the 
        collection node's name.

    name : String
        The package name.

    pyPackage : String
        The python package name of the package.
    
    version : String
        The package version.

    

    Notes
    -----
    Each pSysmon package has to be contained in a seperat folder (the package 
    folder). Inside the package folder, the __init__.py file has to be created 
    to mark the folder as a `python package <http://docs.python.org/tutorial/modules.html#packages>`_ which can be imported using the 
    *import* statement.

    In the __init__.py various variables have to be set to mark the package as 
    a pSysmon package:

        name (*String*)
            The name of the package.

        version (*String*)
            The version of the package. Try to use the version.major.minor format (e.g.: 0.1.1).

        author (*String*)
            The author of the package.

        minPsysmonVersion (*String*)
            The minimume pSysmon version required to run the package.

        description (*String*)
            A short description of the package.

        website (*String*)
            An URL to the website containing information about the package.


    Once the package is marked as a pSysmon package by setting the variables above, 
    you can add the functionality to the package. This can be done by creating the 
    *nodeFactory* function. The nodeFactory creates a list of nodes which are 
    contained in the package. Take a look at the example_ to see how to use the 
    nodeFactory.

    **Creating database tables**

    Each package can create it's own database tables. To do this, create the 
    databaseFactory function in the __init__.py file. See the example_ below on how 
    to create the databaseFactory function.

    Each package can add database tables to the pSysmon database. These tables are 
    created for each project. To add a database table, place the mysql create 
    statement as shown in the example above into a python string. Add the table 
    create statement to the package by using the :meth:`~psysmon.core.base.Package.addDbTableCreateQuery` function.
    The *</PREFIX/>* tag in the mysql query will be replaced by pSysmon with the 
    current project name.


    Examples
    --------
    The packages are created in the __init__.py function of each pSysmon package.
    Below follows an example of a package initialization taken from the geometry 
    package::

        name = "geometry"
        version = "0.1.1"
        author = "Stefan Mertl"
        minPsysmonVersion = "0.0.1"
        description = "The geometry package."
        website = "http://www.stefanmertl.com"


        def nodeFactory():
            from applyGeometry import ApplyGeometry
            from editGeometry import EditGeometry

            nodeTemplates = []

            # Create a pSysmon collection node template and add it to the package.
            options = {}
            myNodeTemplate = EditGeometry(name = 'edit geometry',
                                          mode = 'standalone',
                                          category = 'Geometry',
                                          tags = ['stable'],
                                          options = options
                                          )
            nodeTemplates.append(myNodeTemplate) 

            # Create a pSysmon collection node template and add it to the package.
            options = {}
            myNodeTemplate = ApplyGeometry(name = 'apply geometry',
                                           mode = 'uneditable',
                                           category = 'Geometry',
                                           tags = ['stable'],
                                           options = options
                                           )
            nodeTemplates.append(myNodeTemplate)

            return nodeTemplates



        def databaseFactory():
            queries=[]

            # The geom_recorder table.
            myQuery = ("CREATE TABLE IF NOT EXISTS </PREFIX/>_geom_recorder "
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
            queries.append(myQuery)

            return queries


    .. rubric:: Collection node template creation

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
