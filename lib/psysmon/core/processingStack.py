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

import copy
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.guiBricks import PrefEditPanel

class ProcessingStack:
    ''' The ProcessingStack class.

    The processing stack handles the editing and execution of the processing nodes.
    Processing nodes can be added to the stack. The position in the stack can be 
    changed. 
    When executing the processing stack, each processing node contained in the stack 
    is executed from top to bottom. 
    The processing stack takes care about passing the correct data to the processingNode
    and to pass the processed data to the next processing node.
    '''
    def __init__(self, name, project, inventory):
        ''' The constructor

        '''
        # The name of the processing stack.
        self.name = name

        # The list of the processing nodes contained in the processing
        # stack.
        self.nodes = []

        # The current project.
        self.project = project

        # The currently used inventory.
        self.inventory = inventory


    def __getitem__(self, index):
        ''' Get a node at a given position of the processing stack.

        Parameters
        ----------
        index : Integer
            The index of the collection node to get from the nodes list.
        '''
        return self.nodes[index]


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



    def execute(self, stream):
        ''' Execute the stack.

        Parameters
        ----------

        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for curNode in self.nodes:
            if curNode.isEnabled():
                curNode.execute(stream)





class ProcessingNode:
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

    def __init__(self, name, mode, category, tags, options = {}, docEntryPoint=None, parentStack=None, *kwargs):
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

        # The options of the stack node.
        self.options = options

        # The preferences of the stack node.
        self.pref_manager = PreferencesManager()

        # The entry point of the documentation of the node.
        self.docEnctryPoint = docEntryPoint

        # The parent stack holding the stack node.
        self.parentStack = parentStack

        # The enabled state of the node.
        self.enabled = True


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



    def execute(self, stream):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        assert False, 'execute must be defined'

