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
The package node base classes.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the base classes of the nodes used in 
the :mod:`~psysmon.core.packageSystem`.
'''

from psysmon.core.preferences_manager import PreferencesManager

class CollectionNode:
    ''' The base class of all psysmon collection nodes.

    All collection nodes contained in psysmon packages have to inherit from 
    the :class:`CollectionNode` class.

    Attributes
    ----------
    mode : Sting
        Specify the behavior in the collection. Allowed values are:
        
            - editable
                The user can edit the node parameters.
            - uneditable
                There are no parameters to edit.
            - standalone
                The node is not included in the execution of the collection.
                Each node can be executed individually using the context 
                menu of the collection listbox.

    name : String
        The name of the collection node.


    '''

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

    name = None

    ## The type of the collection node.
    #
    # Each collection node can specify it's type. Currently there are three
    # allowed values:
    # - editable The user can edit the node paramters.
    # - uneditable There are no node parameters to edit.
    # - standalone The node is not included in the collection execution. Each
    # node can be executed individually using the collection listbox context menu.
    mode = None

    # The category of the collection node.
    category = None

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
    tags = []


    # The entry point of the documentation of the collection node.
    docEntryPoint = None

    def __init__(self, requires=None, provides=None, parent=None,
                 project=None, enabled = True, pref_manager = None):
        ## The package which contains the collection node.
        self.parentPackage = parent

        # The preferences manager of the node.
        if pref_manager is None:
            self.pref_manager = PreferencesManager()
        else:
            self.pref_manager = pref_manager

        ## The node's enabled state.
        #
        # Mark the collection node as enabled or disabled.
        self.enabled = enabled

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
        self.procName = None

    @property
    def rid(self):
        ''' The resource ID of the collection node.
        '''
        name_slug = self.name.replace(' ', '_')
        if self.parentCollection is not None:
            rid = self.parentCollection.rid + '/' + name_slug
        else:
            rid = name_slug

        return rid


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
        #if not "mode" in dir(self):
        #    self.mode = self.type

        #if not "options" in dir(self):
        #    self.options = self.property



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
    def run(self, procName, prevNodeOutput={}):
        self.procName = procName
        self.execute(prevNodeOutput)


    def update_pref_manager(self, pref_manager):
        ''' Update the existing preferences manager with the one passed as an argument.
        '''
        self.pref_manager.update(pref_manager)


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
        if self.procName:
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

    def requireData(self, name=None, origin=None):
        ''' Require data from the collection's shelf.

        Parameters
        ----------
        names : List of Strings
            The names of the variables to restore from the collection's 
            shelf.
        '''
        print "Requiring data with name: %s and origin: %s" % (name, origin)
        return self.parentCollection.unpickleData(name=name, origin=origin)




