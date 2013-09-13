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
Extend psysmon with custom code.

:copyright:
    Mertl Research GmbH

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the pSysmon plugin system.
'''

from psysmon.core.preferences_manager import PreferencesManager

## The PluginNode class.
#
# Each collection node can load plugins which provide some functionality to
# the node. 
class PluginNode:
    ''' The base class of all plugin nodes.

    This class is the base class on which all plugins are built.

    Attributes
    ----------
    nodeClass : String
        The name of the class which can use the plugin. Use 'common' for 
        a plugin that can be used by every class. Default is 'common'.
    '''
    # The class to which the plugin is assigned to.
    # Use *common* for plugins which can be used by every class.
    # Nodes with a specified nodeClass usually depend on some special 
    # variables which have to be passed to them using the variable kwargs 
    # argument.
    nodeClass = 'common'

    def __init__(self, name, mode, category, tags, icons = None, parent=None, docEntryPoint=None, *kwargs):
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
        icons : List of Strings
            The icons used in the ribbonbar.
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

        # The parent collection node which contains the plugin.
        self.parent = parent

        # The preferences of the plugin.
        self.pref = PreferencesManager()

        # The path to the html index file containing the documentation of the
        # plugin.
        self.docEntryPoint = docEntryPoint

        # The icons of the plugin.
        # The dictionary has to be filled in the constructor of the
        # plugin node. The icons icons['active'] and icons['inactive']
        # should be set.
        self.icons = {}

        # The activation state of the tool. This is used by addon- and
        # interactive tools. For other tool modes, the active state is
        # always False.
        self.active = False


    def register(self, parent):
        ''' Register the plugin within a collection node.

        Parameters
        ----------
        parent : :class:`~psysmon.core.packageNodes.CollectionNode`

        '''
        self.parent = parent


    def setActive(self):
        ''' Set the active state of the plugin to True.
        '''
        self.active = True


    def setInactive(self):
        ''' Set the active state of the plugin to False.
        '''
        self.active = False


    def buildMenu(self):
        ''' Build the menu which is added to the parent's menu bar.
        '''
        return None



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.

        '''
        return None


    def editPreferences(self):
        ''' Create a dialog to edit the preferences.

        '''
        self.logger.debug('Editing the preferences of plugin: %s', self.name)





class OptionPlugin(PluginNode):
    ''' A plugin handling program options.

    An option plugin organizes one or more options.
    '''
    def __init__(self, name, category, tags, icons = None, parent = None, docEntryPoint = None):
        ''' The constructor.

        Create an instance of the PluginNode.

        Parameters
        ----------
        name : String
            The name of the plugin-node.
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
        PluginNode.__init__(self,
                            name = name,
                            mode = 'option',
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint)


class CommandPlugin(PluginNode):
    ''' A plugin executing a single command.

    A command plugin can be used to execute standalone programs which process the currently
    displayed data and maybe present the results in a new window (e.g. frequency spectrum, audification, ...).
    '''
    def __init__(self, name, category, tags, icons = None, parent = None, docEntryPoint = None):
        ''' The constructor.

        Create an instance of the PluginNode.

        Parameters
        ----------
        name : String
            The name of the plugin-node.
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
        PluginNode.__init__(self,
                            name = name,
                            mode = 'command',
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint)


    def run(self):
        ''' Run the command of the plugin.
        '''
        return None



class InteractivePlugin(PluginNode):
    ''' Interact with the user interface.

    The interactive plugin allows the user to interact with the parent window using 
    mouse clicks.
    '''
    def __init__(self, name, category, tags, icons = None, parent = None, docEntryPoint = None):
        ''' The constructor.

        Create an instance of the PluginNode.

        Parameters
        ----------
        name : String
            The name of the plugin-node.
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
        icons : Dictionary of python images
            The key of the dictionary is the state of the icon ('active', 'inactive', 'selected').
            The pSysmon icons in the :class:psysmon.artwork.icons module should be used.
        parent : :class:`~psysmon.core.packageNodes.CollectionNode`
            The parent collectionNode which has loaded the plugin.
        docEntryPoint : String
            The path to where the documentation's index.html file can be found.
        '''
        PluginNode.__init__(self,
                            name = name,
                            mode = 'interactive',
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint)


    def getHooks(self):
        ''' Register the mouse event hooks for interactive plugins.

        '''
        return None



class AddonPlugin(PluginNode):
    ''' Add algorithms that are executed before displaying the data.

    This is an addon plugin, that's capable of creating individual views 
    which are used in the tracedisplay.
    '''

    def __init__(self, name, category, tags, icons = None, parent=None, docEntryPoint=None):
        ''' The constructor.

        Create an instance of the PluginNode.

        Parameters
        ----------
        name : String
            The name of the plugin-node.
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
        PluginNode.__init__(self,
                            name = name,
                            mode = 'addon',
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint)


        def getViewClass(self):
            ''' Get a class object of the view of the plugin.

            '''
            assert False, 'The getViewClass must be defined!'
