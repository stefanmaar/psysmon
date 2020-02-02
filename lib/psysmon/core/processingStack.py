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
The pSysmon processingStack module.

:copyright:
    Mertl Research GmbH

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the pSysmon processingStack system.
'''

from builtins import object
import copy
import itertools
import weakref
import logging

import psysmon
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.guiBricks import PrefEditPanel


class ProcessingStack(object):
    ''' The ProcessingStack class.

    The processing stack handles the editing and execution of the processing nodes.
    Processing nodes can be added to the stack. The position in the stack can be 
    changed. 
    When executing the processing stack, each processing node contained in the stack 
    is executed from top to bottom. 
    The processing stack takes care about passing the correct data to the processingNode
    and to pass the processed data to the next processing node.
    '''
    def __init__(self, name, project, nodes = None, parent = None):
        ''' The constructor

        '''
        # The name of the processing stack.
        self.name = name

        # The list of the processing nodes contained in the processing
        # stack.
        if nodes is None:
            self.nodes = []
        else:
            self.nodes = nodes
            for cur_node in self.nodes:
                cur_node.parentStack = self

        # The current project.
        self.project = project

        # The object holding the processing stack.
        if parent is not None:
            self._parent = weakref.ref(parent)
        else:
            self._parent = None


    @property
    def geometry_inventory(self):
        ''' The geometry inventory of the parent project.
        '''
        return self.project.geometry_inventory

    @property
    def parent(self):
        '''
        '''
        if self._parent is None:
            return self._parent
        else:
            return self._parent()


    def __getitem__(self, index):
        ''' Get a node at a given position of the processing stack.

        Parameters
        ----------
        index : Integer
            The index of the collection node to get from the nodes list.
        '''
        return self.nodes[index]


    def get_settings(self, upper_node_limit = None):
        ''' Get the settings of the nodes in the processing stack.

        The upper limit can be set by the upper_node_limit attribute.
        '''
        settings = {}
        for pos, cur_node in enumerate(self.nodes):
            settings[pos+1] = cur_node.settings

            if cur_node == upper_node_limit:
                break

        return settings


    def addNode(self, nodeTemplate, position = -1):
        ''' Add a node to the processing stack.

        Insert a node before a specified position in the processing stack.
        If the position is set to -1, the node is appended at the end of the stack.

        Parameters
        ----------
        node : :class:`~psysmon.core.processingStack.ProcessingNode`
            The node to be added to the collection.
        position : Integer
            The position in the stack before which the node should be inserted.
        '''
        node = copy.deepcopy(nodeTemplate)
        node.parentStack = self
        if position==-1:
            self.nodes.append(node)
        else:
            self.nodes.insert(position, node)


    def popNode(self, position):
        ''' Remove a node from the stack.

        Parameters
        ----------
        position : Integer
            The position of the node which should be removed.
        '''
        if len(self.nodes) > 0:
            return self.nodes.pop(position)


    def editNode(self, position):
        ''' Edit a node.

        Edit the node at a given position in the stack. This is done by 
        calling the :meth:`~psysmon.core.processingStack.ProcessingNode.edit()` 
        method of the according instance.

        Parameters
        ----------
        position : Integer
            The position in the stack of the node to edit.
        '''
        self.nodes[position].edit()



    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack.

        Parameters
        ----------

        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for curNode in self.nodes:
            curNode.clear_results()
            if curNode.isEnabled():
                curNode.execute(stream, process_limits, origin_resource)


    def clear_results(self):
        ''' Clear the results of all processing nodes.
        '''
        for cur_node in self.nodes:
            cur_node.clear_results()


    def get_results(self):
        ''' Get all results of the processing nodes.
        '''
        return list(itertools.chain.from_iterable([list(x.results.values()) for x in self.nodes]))






class ProcessingNode(object):
    ''' The ProcessingNode class.

    The processing node gets data from the processing stack, does some computation with 
    this data and returns the processed data to the processing stack.
    The type of data needed has to be defined by the ProcessingNode. Currently the processing 
    of obspy Stream objects is supported.
    The return value has to be of the same type as the data passed to the processing node.
    '''
    # The class to which the processing node is assigned to.
    # User *common* for nodes which can be used by every class.
    # Nodes with a specified nodeClass usually depend on some special 
    # variables which have to be passed to them using the variable kwargs 
    # argument.
    nodeClass = 'common'

    def __init__(self, name, mode, category, tags, enabled = True, docEntryPoint=None, parentStack=None):
        ''' The constructor

        '''
        # The name of the stack node.
        self.name = name

        # The mode of the stack node (editable, uneditable).
        self.mode = mode

        # The category of the stack node.
        self.category = category

        # The tags assigned to the stack node.
        self.tags = tags

        # The result of the processing node.
        self.results = {}

        # The preferences of the stack node.
        self.pref_manager = PreferencesManager()

        # The entry point of the documentation of the node.
        self.docEntryPoint = docEntryPoint

        # The parent stack holding the stack node.
        self.parentStack = parentStack

        # The enabled state of the node.
        self.enabled = enabled

    @property
    def settings(self):
        ''' The configuration settings of the node.
        '''
        settings = {}
        settings[self.name] = self.pref_manager.settings
        settings[self.name]['enabled'] = self.enabled
        return settings


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



    def isEnabled(self):
        ''' Check the enabled state of the node.

        '''
        return self.enabled



    def toggleEnabled(self):
        ''' Toggle the enabled state of the node.

        '''
        self.enabled = not self.enabled




    def getEditPanel(self, parent):
        ''' The method to build and return the edit panel for the processing 
        stack GUI.

        '''
        return PrefEditPanel(pref = self.pref_manager,
                             parent = parent)



    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        assert False, 'execute must be defined'


    def update_pref_manager(self, pref_manager):
        ''' Update the existing preferences manager with the one passed as an argument.

        This is used when loading a psysmon project. The preference items are created
        during the instance initialization of the processing nodes.
        The values saved in the project file are not updated. The update is done
        using this method.
        '''
        self.pref_manager.update(pref_manager)



    def add_result(self, name, res_type = 'value', metadata = None,
                   origin_resource = None, custom_class = None, **kwargs):
        ''' Add a result.

        Parameters
        ----------
        result : object
            The result to add to the processing node results.

        res_type : String
            The type of the result to add. ('value', 'custom')

        custom_class : class inhereted from :class:`ProcessingResult`
            The custom class of a result of kind 'custom'.
        '''
        if name not in iter(self.results.keys()):
            if res_type == 'value':
                self.results[name] = ValueResult(name = name,
                                                 origin_name = self.name,
                                                 origin_pos = self.parentStack.nodes.index(self),
                                                 res_type = res_type,
                                                 metadata = metadata,
                                                 origin_resource = origin_resource)
            elif res_type == 'grid_2d':
                self.results[name] = Grid2dResult(name = name,
                                                  origin_name = self.name,
                                                  origin_pos = self.parentStack.nodes.index(self),
                                                  metadata = metadata,
                                                  origin_resource = origin_resource)
            else:
                raise ValueError('The result of type %s is not supported.' % res_type)

        if self.results[name].type != res_type:
            raise ValueError("The type %s of the existing results doesn't match the type %s of the result to add." % (self.results[name].type, res_type))


        if res_type == 'value':
            self.results[name].add_value(**kwargs)
        elif res_type == 'grid_2d':
            self.results[name].add_grid(**kwargs)



    def clear_results(self):
        ''' Remove the results.
        '''
        self.results = {}


    def get_result_names(self):
        ''' Get the available result names.

        '''
        return list(set([x.name for x in self.results]))




