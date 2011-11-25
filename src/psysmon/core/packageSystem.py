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
The pSysmon plugin system module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 (http://www.gnu.org/copyleft/gpl.html)

This module contains the classes needed to run the pSysmon plugin system.
'''

import os
import sys
from psysmon.core.packageNodes import CollectionNodeTemplate, CollectionNode

class PackageManager:
    '''
    The Package Manager keeps track of the pSysmon packages and 
    manages them.
    '''

    def __init__(self, parent, packageDirectories):
        '''
        The constructor.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.pluginSystem.PackageManager`
        :param packageDir: A list of directories holding the packages.
        :type self: A list of Strings.
        '''

        self.parent = parent
        # The parent object holding the package manager.

        self.packageDirectories = packageDirectories
        # A list of directories holding the packages.

        self.packages = {}
        # The packages managed by the PackageManager.

        # Search for available packages.
        self.scan4Package()



    def scan4Package(self):
        '''
        Scan for available pSysmon packages.

        Scan the package directories for packages.
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
        '''
        Check for valid package.

        Check if the package module contains the required attributes.
        '''

        requiredAttributes = ['name', 'version', 'author', 
                              'minPsysmonVersion', 'description', 'website']
        tmp = dir(pkg2Check)
        for curAttr in requiredAttributes:
            if curAttr not in tmp:
                self.parent.logger.debug("Attribute %s is missing!" % curAttr)
                return False

        return True



    def addPackage(self, pkgModule, pkgName, pkgBaseDir, packageDir):
        '''
        Create and add a package.
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
            curPkg.addCollectionNodeTemplate(nodes)

        # Set the collection node template runtime attributes.
        curPkg.setPyPackageName(pkgName)
        curPkg.setBaseDir(os.path.join(packageDir, pkgBaseDir))

        # Add the package to the packages list.
        self.packages[curPkg.name] = curPkg


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



class Package:
    '''
    The pSysmon Package class.

    A pSysmon package provides the functionality to pSysmon. A package contains 
    a set of CollectionNodeTemplates which can be used by the pSysmon user to 
    create the collections. 

    .. rubric:: Usage
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

    .. rubric:: Package creation

    As you can see in the example code, first the Package is created using the 
    psysmon.core.base.Package constructor. The package name, version and dependency 
    are passed to the constructor.

    .. rubric:: Database table creation

    Each package can add database tables to the pSysmon database. These tables are 
    created for each project. To add a database table, place the mysql create 
    statement as shown in the example above into a python string. Add the table 
    create statement to the package by using the :meth:`~psysmon.core.base.Package.addDbTableCreateQuery` function.
    The *</PREFIX/>* tag in the mysql query will be replaced by pSysmon with the 
    current project name.

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
