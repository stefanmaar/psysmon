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
import logging
from sqlalchemy import MetaData


def scan_module_for_plugins(package_name, plugin_modules):
    ''' Scan a module file for classes inherited from a plugin node class.

    This function checks the base classes of all classes contained in the 
    specified list of module files. If one of the classes inherits from 
    one of the following classes, it is added to the returned list of 
    plugin templates.

    The plugin classes which are searched for are:

        - :class:`psysmon.core.plugins.ViewPlugin`
        - :class:`psysmon.core.plugins.OptionPlugin`
        - :class:`psysmon.core.plugins.InteractivePlugin`
        - :class:`psysmon.core.plugins.CommandPlugin`

    Parameters
    ----------
    package_name : String
        The name of the package containing the modules (e.g. psysmon.packages.tracedisplay).

    plugin_modules : List of Strings
        A list of strings containing the names of the module files.

    Returns
    -------
    plugin_templates : List of class objects
        A list of class objects which inherit from the PluginNode class.
    '''
    import inspect
    import importlib
    import psysmon.core.plugins

    plugin_classes = (psysmon.core.plugins.ViewPlugin,
                      psysmon.core.plugins.OptionPlugin,
                      psysmon.core.plugins.InteractivePlugin,
                      psysmon.core.plugins.CommandPlugin)

    plugin_templates = []
    for cur_plugin_module in plugin_modules:
        try:
            mod = importlib.import_module(package_name + '.' + cur_plugin_module)
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj):
                    for cur_base in obj.__bases__:
                        if cur_base in plugin_classes:
                            plugin_templates.append(obj)
                            break
        except Exception, e:
            print e
    return plugin_templates


def scan_module_for_collection_nodes(package_name, node_modules):
    ''' Scan a module file for classes inherited from the :class:`~psysmon.core.packageNodes.CollectionNode` class.

    Parameters
    ----------
    package_name : String
        The name of the package containing the modules (e.g. psysmon.packages.tracedisplay).

    plugin_modules : List of Strings
        A list of strings containing the names of the module files.

    Returns
    -------
    plugin_templates : List of class objects
        A list of class objects which inherit from the CollectionNode class.
    '''
    import inspect
    import importlib
    import psysmon.core.packageNodes

    node_templates = []
    for cur_node_module in node_modules:
        try:
            mod = importlib.import_module(package_name + '.' + cur_node_module)
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj) and psysmon.core.packageNodes.CollectionNode in obj.__bases__:
                    node_templates.append(obj)
        except Exception, e:
            print e
    return node_templates


def scan_module_for_processing_nodes(package_name, node_modules):
    ''' Scan a module file for classes inherited from the :class:`~psysmon.core.processingStack.ProcessingNode` class.

    Parameters
    ----------
    package_name : String
        The name of the package containing the modules (e.g. psysmon.packages.tracedisplay).

    plugin_modules : List of Strings
        A list of strings containing the names of the module files.

    Returns
    -------
    plugin_templates : List of class objects
        A list of class objects which inherit from the ProcessingNode class.
    '''
    import inspect
    import importlib
    import psysmon.core.processingStack

    node_templates = []
    for cur_node_module in node_modules:
        try:
            mod = importlib.import_module(package_name + '.' + cur_node_module)
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj) and psysmon.core.processingStack.ProcessingNode in obj.__bases__:
                    node_templates.append(obj)
        except Exception, e:
            print e
    return node_templates


class PackageManager:
    '''The Package Manager keeps track of the pSysmon packages and 
    manages them. 

    The packages of type :class:`Package` are loaded from the 
    packageDirectories. A package manager can handle multiple 
    package directories.


    Parameters
    ----------
    parent : obj
        The parent object holding the package manager.

    packageDir : List of Strings
        The directories holding the pSysmon packages.


    Attributes
    ----------
    parent : Object
        The parent object holding the package manager.

    packageDirectories : List of Strings
        A list of directories holding the packages.

    packages : Dictionary of :class:`Package`
        A dictionary of packages managed by the PackageManager.
        Key: package name

    plugins : Dictionary of :class:`~psysmon.core.plugins.PluginNode`
        A dictionary of plugins managed by the package manager. 
        Key: Name of the associated collection node.


    See Also
    --------
    :class:`Package` : The pSysmon package class.
    '''

    def __init__(self, parent=None, packageDirectories = []):
        '''The constructor.

        Parameters
        ----------
        parent : obj
            The parent object holding the package manager.

        packageDir : List of Strings
            The directories holding the pSysmon packages.

        '''

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The parent object holding the package manager.
        self.parent = parent

        # A list of directories holding the packages.
        self.packageDirectories = packageDirectories

        # The packages managed by the PackageManager.
        self.packages = {}

        # The plugins managed by the package manager.
        self.plugins = {}

        # The processing nodes managed by the package manager.
        self.processingNodes = {}


    def scan4Package(self):
        '''Scan for available pSysmon packages.

        Scan the package directories for packages. Each package has to be 
        contained in a seperate folder. Each folder found in the 
        packageDirectories is processed and if a valid package is found, 
        it is registerd within the packageManager.

        See Also
        --------
        :meth:`PackageManager.checkPackage` : Check for a valid package.
        :meth:`PackageManager.addPackage` : Add a package to the package manager.
        :class:`Package` : The pSysmon package class.
        '''

        for curDir in self.packageDirectories:
            #import psysmon.packages
            #pkg = psysmon.packages
            #prefix = pkg.__name__ + '.'
            #for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__, prefix):
            #    print "importer: %s; modname: %s; ispkg: %s\n" % (importer, modname, ispkg)

            self.logger.debug("Scanning directory %s", curDir)
            packages2Register = [ name for name in os.listdir(curDir) 
                                  if os.path.isdir(os.path.join(curDir, name)) 
                                  and name[0]!='.']

            for curPkg in packages2Register:
                self.logger.debug("Registering package " + curPkg + ".")
                pkgName = os.path.basename(curPkg)
                try:
                    sys.path.append(curDir)
                    pkgModule = __import__(pkgName)
                    pkgModule = sys.modules[pkgName]
                    isOk = self.checkPackage(pkgModule)

                    if isOk:
                        self.addPackage(pkgModule, pkgName, curPkg, curDir)
                    else:
                        self.logger.debug("Package check failed!")

                except IndexError:
                    self.logger.debug("No init file found.")




    def checkPackage(self, pkg2Check):
        '''Check if the package is a valid pSysmon package.

        Check if the package module contains the required attributes. 
        The required attributes are:

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
        isValid : Boolean 
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
                self.logger.debug("Attribute %s is missing!" % curAttr)
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

        self.dbMetadata = MetaData()

        # Get the database queries.
        if 'databaseFactory' in dir(pkgModule):
            self.logger.debug("Getting the database factory method.")
            curPkg.databaseFactory = pkgModule.databaseFactory

        # Get the collection node templates.
        if 'collection_node_modules' in dir(pkgModule):
            self.logger.debug('Getting the collection nodes.')
            node_templates = scan_module_for_collection_nodes(pkgModule.__name__, pkgModule.collection_node_modules)
            for cur_node in node_templates:
                cur_node.parent = pkgName
            curPkg.addCollectionNodeTemplate(node_templates)

        # Get the plugins provided by the package.
        if 'plugin_modules' in dir(pkgModule):
            self.logger.debug('Getting the plugins.')
            plugin_templates = scan_module_for_plugins(pkgModule.__name__, pkgModule.plugin_modules)
            self.addPlugins(plugin_templates)

        # Get the processing nodes provided by the package.
        if 'processing_node_modules' in dir(pkgModule):
            self.logger.debug('Getting the processing node templates')
            proc_nodes = scan_module_for_processing_nodes(pkgModule.__name__, pkgModule.processing_node_modules)
            self.addProcessingNodes(proc_nodes)

        # Add the package to the packages list.
        self.packages[curPkg.name] = curPkg


    def addPlugins(self, plugins):
        ''' Add the plugins to a map.

        Parameters
        ----------
        plugins : List of :class:`~psysmon.core.plugins.PluginNode`
            A list of plugins to be added to the package manager.
        '''
        for curPlugin in plugins:
            curKey = curPlugin.nodeClass
            if self.plugins.has_key(curKey):
                self.plugins[curKey].append(curPlugin)
            else:
                self.plugins[curKey] = [curPlugin, ]


    def addProcessingNodes(self, procNodes):
        ''' Add the processing nodes to the dictionary.

        Parameters
        ----------
        procNodes : List of :class:`~psysmon.core.processingStack.ProcessingNode`
            A list of processing nodes to be added to the package manager.
        '''
        for curNode in procNodes:
            curKey = curNode.nodeClass
            if curKey in self.processingNodes.keys():
                self.processingNodes[curKey].append(curNode)
            else:
                self.processingNodes[curKey] = [curNode, ]



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
    a set of :class:`~psysmon.core.packageNodes.CollectionNode`, 
    :mod:`~psysmon.core.plugins` and :class:`~psysmon.core.processingStack.ProcessingNode` templates which 
    can be added to a collection by the pSysmon user. Custom database tables can be defined as well.

    pSysmon packages are realized as `Python packages <http://docs.python.org/tutorial/modules.html#packages>`_ 
    and the functionality is provided as `Python modules <http://docs.python.org/tutorial/modules.html#modules>`_  
    contained in the package.

    Parameters
    ----------
    name : String
        The name of the package.
    version : String
        The version of the package.
    dependency : String [deprecated] 
        A list of other packages needed to run this package.

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

    The following variables are optional:

        collection_node_modules (*list of String*)
            The module files in which psysmon should search for collection nodes.

        plugin_modules (*list of String*)
            The module files in which psysmon should search for plugins.

        processing_node_modules (*list of String*)
            The module files in which psysmon should search for processing nodes.


    Once the package is marked as a pSysmon package by setting the variables above, 
    you can add the functionality to the package by defining collecition nodes,
    plugins and processing nodes. Moreover each package can add custom database 
    tables to the psysmon database.

    **Defining collection nodes**

    Collection nodes are defined as classes which inherit from the :class:`psysmon.core.packageNodes.CollectionNode` class.
    These classes can be defined in a module of your choice. To let psysmon know about 
    the collection node, the module file which contains the collection node class has 
    to be specified in the __init__.py file of the package. This is done by adding 
    the name of the module file to the *collection_node_modules* list. The name relative 
    to the psysmon package has to be given in the *collection_node_modules* list.
    The method :meth:`psysmon.core.packageSystem.scan_module_for_collection_nodes` is used 
    to search the module files for classes which inherit from the class :class:`psysmon.core.packageNodes.CollectionNode`.

    **Defining plugins**

    jj

    **Defining processing nodes**

    jj

    **Creating database tables**

    Each package can create it's own database tables. To do this, create the 
    *databaseFactory()* function in the __init__.py file. See the example_ below on how 
    to create the *databaseFactory()* function.

    Each package can add database tables to the pSysmon database. These tables are 
    created for each project. To add a database table, place the mysql create 
    statement as shown in the example above into a python string. Add the table 
    create statement to the package by using the :meth:`~psysmon.core.base.Package.addDbTableCreateQuery` function.
    The *</PREFIX/>* tag in the mysql query will be replaced by pSysmon with the 
    current project name.

    **Collection node template creation**

    Each package will provide one ore more collection nodes which can be used 
    by the user. To let pSysmon know what collection nodes each package provides 
    one has to create the *nodeFactory()* in the 
    __init__.py file (see the example below). The *nodeFactory()* creates the :class:`~psysmon.core.packageNodes.CollectionNode` 
    instances which will be used as the collection node templates by pSysmon. 

    In the code example below, two node templates (EditGeometry and ApplyGeometry) 
    are created in the *nodeFactory()*. The two classes are provided by the developer 
    creating the package and have to be located in the package directory. See 
    the documentation of :class:`~psysmon.core.packageNodes.CollectionNode` for 
    more details on how to write your own collection nodes.

    .. _example:

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

        # Specify the module(s) where to search for collection node classes.
        collection_node_modules = ['applyGeometry',
                                   'editGeometry']


        def databaseFactory(base):
            from sqlalchemy import Column, Integer, String, Float
            from sqlalchemy import ForeignKey, UniqueConstraint
            from sqlalchemy.orm import relationship

            tables = []


            # Create the geom_recorder table mapper class.
            class GeomRecorder(base):
                __tablename__ = 'geom_recorder'
                __table_args__ = (
                                  UniqueConstraint('serial', 'type'),
                                  {'mysql_engine': 'InnoDB'}
                                 )

                id = Column(Integer, primary_key=True, autoincrement=True)
                serial = Column(String(45), nullable=False)
                type = Column(String(255), nullable=False)
                description = Column(String(255), nullable=True)

                sensors = relationship('GeomSensor', 
                                       cascade = 'all',
                                       backref = 'parent')


                def __init__(self, serial, type):
                    self.serial = serial
                    self.type = type


                def __repr__(self):
                    return "Recorder\\nid: %d\\nserial: %s\\ntype: %s\\n" % (self.id, self.serial, self.type)

            tables.append(GeomRecorder)

            return tables




    See Also
    --------
    :class:`psysmon.core.packageNodes.CollectionNode`

    '''

    def __init__(self, name, version, dependency):   
        '''
        The constructor.

        Create a pSysmon package.
        After creating a package, the methods :meth:`~psysmon.core.base.Package.addCollectionNodeTemplate` 
        and :meth:`~psysmon.core.base.Package.addDbTableCreateQuery` to fill 
        the package with content.

        Parameters
        ----------
        name : String
            The name of the package.
        version : String
            The version of the package.
        dependency : String [deprecated] 
            A list of other packages needed to run this package.     
        '''

        # The python package name.
        self.pyPackage = ""

        # The pSysmon package name.
        self.name = name

        # The package version.
        self.version = version

        # The package dependencies.
        self.dependency = dependency

        #The collection node templates of the package.
        self.collectionNodeTemplates = {}

        # The package database factory method.
        self.databaseFactory = None

        # The package directory.
        self.baseDir = ""

        # The package documentation directory.
        self.docDir = ""    


    def setPyPackageName(self, pyPackage):
        ''' Set the python package name of the collectionNodeTemplates.

        Each CollectionNode holds the python package name (e.g.psysmon.packages.geometry) 
        to which it belongs. This method sets the nodePkg property of each 
        collection node.

        Parameters
        ----------
        pyPackage : String
            The python package name.

        See Also
        --------
        :class:`psysmon.base.Base.scan4Package`
        '''
        for curNode in self.collectionNodeTemplates.itervalues():
            curNode.setNodePkg(pyPackage)


    def setBaseDir(self, baseDir):
        ''' Set the package base directory.

        Parameters
        ----------
        baseDir : String
            The full path to the package directory.
        '''
        if os.path.isdir(baseDir):
            self.baseDir = baseDir 
            self.docDir = os.path.join(self.baseDir, "doc")


    def addCollectionNodeTemplate(self, nodes):
        ''' Add a collection node template to the package.

        The *nodes* collection nodes are added to the package dictionary 
        *collectionNodeTemplates*. The key of the dictionary is the node's name. 
        The nodes added will be the collection node templates used to create 
        new collection nodes to be added to a collection.

        Parameters
        ----------
        nodes : List of :class:`~psysmon.core.packageNodes.CollectionNode` instances.
            The collection nodes to be added to the package.
        '''
        if not nodes:
            return

        for curNode in nodes:
            curNode.parentPackage = self
            self.collectionNodeTemplates[curNode.name]= curNode


    def getCollectionNodeTemplate(self, nodeName):
        ''' Get a collection node template from the package.

        Parameters
        ----------
        nodeName : String
            The name of the collection node template to fetch.
        '''
        if(self.collectionNodeTemplates.has_key(nodeName)):
            return self.collectionNodeTemplates[nodeName]
        else:
            return False

