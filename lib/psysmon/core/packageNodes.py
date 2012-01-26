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
    def __init__(self, name, mode, category, tags, options, requires=None, provides=None, docEntryPoint=None, parent=None, project=None):

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
        self.mode = mode

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
        self.options = options

        self.docEntryPoint = docEntryPoint

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

        # The variables required by the node.
        self.requires = requires

        # The variables provided by the node.
        self.provides = provides

        ## The current pSysmon project.
        #
        self.project = project


        ## The parent collection holding the node instance.
        #
        self.parentCollection = None


        # If the node is executed in a collection thread a thread ID is
        # assigned.
        self.procId = None


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

        # Track some instance attribute changes.
        if not "mode" in dir(self):
            self.mode = self.type

        if not "options" in dir(self):
            self.options = self.property


    ## Set the name of the collection node package.
    #
    #
    def setNodePkg(self, nodePkg):
        ## The name of the python package containing the nodeClass.
        #
        # This attribute holds the name of the @b python package holding the
        # nodeClass. This package is not to be mixed up with the pSysmon package.
        self.nodePkg = nodePkg


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
    # Currently the procId is saved as an attribute of the collection node
    # so that the node knows to which thread it belongs to.
    def run(self, procId, prevNodeOutput={}):
        self.procId = procId
        self.execute(prevNodeOutput)


    ## Log messages.
    #
    # The collection node is executed by a CollectionNode object. This object handles
    # the logging of various messages (error, warning, status, ...) to a log file.
    #
    # @see CollectionNode.log
    def log(self, mode, msg):

        # If the node is running in a thread, log to the collection (the
        # log file).
        # If the thread is not running, log to the pSysmon log area.
        if self.procId:
            self.parentCollection.log(self.name, mode, msg)
        else:
            self.project.log(mode, msg)


    def provideData(self, name, data, description):
        ''' Provide the data to the other collection nodes.

        Parameters
        ----------
        name : String
            The name of the data provided.

        data : Object
            The data provided to the next collection nodes.

        description : String
            A short description of the data.
        '''
        self.parentCollection.pickleData(name = name,
                                         data = data,
                                         description = description,
                                         origin = self.name
                                         )

    def requireData(self, names):
        ''' Require data from the collection's shelf.

        Parameters
        ----------
        names : List of Strings
            The names of the variables to restore from the collection's 
            shelf.
        '''
        requiredData = {}
        for curName in names:
            print "Requiring data with name: %s" % curName
            requiredData[curName] = self.parentCollection.unpickleData(curName)

        return requiredData



