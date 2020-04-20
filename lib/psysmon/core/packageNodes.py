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
from __future__ import print_function

from builtins import object
import weakref
import logging

import psysmon
from psysmon.core.preferences_manager import PreferencesManager
import psysmon.core.result as core_result

class CollectionNode(object):
    ''' The base class of all psysmon collection nodes.

    All collection nodes contained in psysmon packages have to inherit from 
    the :class:`CollectionNode` class.

    Attributes
    ----------
    mode : Sting
        Specify the behavior in the collection. Allowed values are:

            - editable
                The user can edit the node parameters.
            - execute only
                There are no parameters to edit.
            - standalone
                The node is not included in the execution of the collection.
                Each node can be executed individually using the context 
                menu of the collection listbox.

    name : String
        The name of the collection node.


    '''

    ## The CollectionNode vnstructor.
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
    def name_slug(self):
        ''' A clean representation of the name.
        '''
        name_slug = self.name.replace(' ', '_').replace('/','_')
        name_slug = name_slug.lower()
        return name_slug

    @property
    def rid(self):
        ''' The resource ID of the collection node.
        '''
        name_slug = self.name.replace(' ', '_').replace('/','_')
        if self.parentCollection is not None:
            rid = self.parentCollection.rid + '/' + name_slug
        else:
            rid = name_slug

        return rid

    @property
    def settings(self):
        ''' The configuration settings of the node.
        '''
        settings = {}
        settings[self.name] = {}
        settings[self.name]['preferences'] = self.pref_manager.settings
        settings[self.name]['enabled'] = self.enabled
        return settings


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
        print("Requiring data with name: %s and origin: %s" % (name, origin))
        return self.parentCollection.unpickleData(name=name, origin=origin)


    def kwargs_exists(self, needed_keywords, **kwargs):
        ''' Check if the needed keywords exist in the passed kwargs dictionar.

        Paramters
        ---------
        needed_keywords : List of Strings
            The required keywords.
        '''
        for cur_kw in needed_keywords:
            if cur_kw not in iter(kwargs.keys()):
                return False

        return True





class LooperCollectionNode(CollectionNode):
    ''' A Collection node with a looping funcionality.

    The collection node can hold a list of child nodes which are executed in a loop.
    '''

    def __init__(self, children = None, **kwargs):
        ''' Initialize the instance.
        '''
        CollectionNode.__init__(self, **kwargs)

        self.children = []
        if children is not None:
            for cur_child in children:
                self.add_child(cur_child)

    @property
    def settings(self):
        ''' The configuration settings of the node.
        '''
        return self.get_settings()


    def add_child(self, child_node, position = None):
        ''' Add a child node to the looper.
        '''
        if position is not None:
            if position >= len(self.children):
                position = None
            elif position < 0:
                position = 0

        child_node.parent = self
        if position is None:
            self.children.append(child_node)
        else:
            self.children.insert(position, child_node)


    def remove_child(self, position):
        ''' Remove a child node from the looper.
        '''
        pass


    def move_node_up(self, node):
        ''' Move a node up in the looper collection.

        Paramters
        ---------
        node : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node to move.

        '''
        if node not in self.children:
            raise RuntimeError("The node is not part of the looper.")

        old_index = self.children.index(node)
        if old_index == 0:
            return
        self.children.remove(node)
        self.children.insert(old_index - 1, node)


    def move_node_down(self, node):
        ''' Move a node down in the looper collection.

        Paramters
        ---------
        node : :class:`~psysmon.core.packageNodes.CollectionNode`
            The node to move.

        '''
        if node not in self.children:
            raise RuntimeError("The node is not part of the looper.")

        old_index = self.children.index(node)
        if old_index == len(self.children) - 1:
            return
        self.children.remove(node)
        self.children.insert(old_index + 1, node)


    def get_settings(self, upper_node_limit = None):
        ''' Get the settings of the nodes in the processing stack.

        The upper limit can be set by the upper_node_limit attribute.
        '''
        settings = {}
        settings[self.name] = {}
        settings[self.name]['preferences'] = self.pref_manager.settings
        settings[self.name]['enabled'] = self.enabled
        settings[self.name]['looper_children'] = {}
        for pos, cur_node in enumerate(self.children):
            settings[self.name]['looper_children'][pos+1] = cur_node.settings

            if cur_node == upper_node_limit:
                break

        return settings


class LooperCollectionChildNode(CollectionNode):
    ''' A looper collection child node.

    '''

    def __init__(self, parent = None, **kwargs):
        ''' Initialize the instance.
        '''
        CollectionNode.__init__(self, **kwargs)

        self.result_bag = core_result.ResultBag()

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)


        # The parent object holding the package manager.
        if parent is not None:
            self._parent = weakref.ref(parent)
        else:
            self._parent = None


        # Indicate if waveform data is needed.
        self.need_waveform_data = True

        # Flag to indicate if the node has been initialized.
        self.initialized = False


    @property
    def pre_stream_length(self):
        ''' The time-span needed for correct processing prior to the start time
        of the stream passed to the execute method [s].
        '''
        return 0.


    @property
    def post_stream_length(self):
        ''' The time-span needed for correct processing after the end time
        of the stream passed to the execute method [s].
        '''
        return 0.


    @property
    def parent(self):
        '''
        '''
        if self._parent is None:
            return self._parent
        else:
            return self._parent()

    @parent.setter
    def parent(self, value):
        if value is not None:
            self._parent = weakref.ref(value)
        else:
            self._parent = None


    def __getstate__(self):
        ''' Remove instances that can't be pickled.
        '''
        result = self.__dict__.copy()

        # The following attributes can't be pickled and therefore have
        # to be removed.
        # These values have to be reset when loading the project.
        if 'logger' in iter(result.keys()):
            del result['logger']
        return result


    def __setstate__(self, d):
        ''' Fill missing attributes after unpickling.

        '''
        self.__dict__.update(d) # I *think* this is a safe way to do it
        #print dir(self)

        # Track some instance attribute changes.
        if not "logger" in dir(self):
            logger_prefix = psysmon.logConfig['package_prefix']
            loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
            self.logger = logging.getLogger(loggerName)

    def initialize(self, **kwargs):
        ''' Initialize the node.

        This method is called at the start of a loop. Use it to initialize
        or reset persistent values of the instance.
        '''
        self.initialized = True


    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the looper child.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.

        process_limits : List of UTCDateTime or None
            The time limits of the window to process.

        origin_resource : String
            The resource ID of the looper executing the node.

        channels : List of :class:`psysmon.packages.geometry.inventory.Channel`
            The channels which should be processed.
        '''
        assert False, 'execute must be defined'


    def cleanup(self, origin_resource = None):
        ''' Cleanup the node after the last cycle of the parent looper.

        origin_resource : String
            The resource ID of the looper executing the node.
        '''
        pass
