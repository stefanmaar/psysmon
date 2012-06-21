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
    Mertl Research GmbH

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the pSysmon plugin system.
'''

## The PluginNode class.
#
# Each collection node can load plugins which provide some functionality to
# the node. 
class PluginNode:
    ''' The PluginNode class.
    Each collection node can load plugins which provide some functionality to the node.
    '''

    def __init__(self, name, mode, category, tags, nodeClass, icons = None, parent=None, docEntryPoint=None):
        ''' The constructor.

        Create an instance of the PluginNode.

        Parameters
        ----------
        name : String
            The name of the plugin-node.
        mode : String
            The mode of the plugin-node (option, command, interactive, addon).
        category : String
            The category of the plugin-node.
        tags : list of String
            A list of strings containing the tags of the collection node.
            These values are not limited but they should contain one of 
            the three development state tags:
             - stable
             - experimental
             - damaged
        nodeClass : String
            The name of the class for which the plugin-node has been written.
        parent : :class:`~psysmon.core.packageNodes.CollectionNode`
            The parent collectionNode which has loaded the plugin.
        docEntryPoint : String
            The path to where the documentation's index.html file can be found.
        '''
        # The name of the plugin.
        self.name = name

        # The mode of the plugin.
        self.mode = mode

        # The category of the plugin.
        self.category = category

        # The tags of the plugin.
        self.tags = tags


        # The class to which the plugin belongs to.
        self.nodeClass = nodeClass

        # The parent collection node which contains the plugin.
        self.parent = parent

        # The path to the html index file containing the documentation of the
        # plugin.
        self.docEntryPoint = docEntryPoint

        # The icons of the plugin.
        # The dictionary has to be filled in the constructor of the
        # plugin node. The icons icons['active'] and icons['inactive']
        # should be set.
        self.icons = {}


    def register(self, parent):
        ''' Register the plugin within a collection node.

        Parameters
        ----------
        parent : :class:`~psysmon.core.packageNodes.CollectionNode`

        '''
        self.parent = parent



    def buildMenu(self):
        ''' Build the menu which is added to the parent's menu bar.
        '''
        pass



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.

        '''
        pass

    def getHooks(self):
        ''' Register the mouse event hooks for interactive plugins.

        '''
        pass


    def buildToolbarButton(self):
        pass



