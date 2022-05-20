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
from builtins import object
import psysmon
from psysmon.core.preferences_manager import PreferencesManager

if psysmon.wx_available:
    import psysmon.gui.bricks


## The PluginNode class.
#
# Each collection node can load plugins which provide some functionality to
# the node. 
class PluginNode(object):
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

    def __init__(self, name, mode, category, tags, group = 'general',
                 icons = None, parent=None, docEntryPoint=None,
                 position_pref = 0, *kwargs):
        ''' The constructor.

        Create an instance of the PluginNode.

        Parameters
        ----------
        name : String
            The name of the plugin-node.
        mode : String
            The mode of the plugin-node (option, command, interactive, view).
        category : String
            The category of the plugin-node.
        tags : list of String
            A list of strings containing the tags of the collection node.
            These values are not limited but they should contain one of 
            the three development state tags:
             - stable
             - experimental
             - damaged
        group : String
            The group of the plugin-node. A group contains the categories (default = 'general').
        icons : List of Strings
            The icons used in the ribbonbar.
        nodeClass : String
            The name of the class for which the plugin-node has been written.
        parent : :class:`~psysmon.core.packageNodes.CollectionNode`
            The parent collectionNode which has loaded the plugin.
        docEntryPoint : String
            The path to where the documentation's index.html file can be found.
        position_pref : Integer
            The preferred position of the tool in the category section of the ribbon bar.
        '''
        # The name of the plugin.
        self.name = name

        # The mode of the plugin.
        self.mode = mode

        # The group of the plugin.
        self.group = group

        # The category of the plugin.
        self.category = category

        # The tags of the plugin.
        self.tags = tags

        # The parent collection node which contains the plugin.
        self.parent = parent

        # The preferences of the plugin.
        self.pref_manager = PreferencesManager()

        # The path to the html index file containing the documentation of the
        # plugin.
        self.docEntryPoint = docEntryPoint

        # The icons of the plugin.
        # The dictionary has to be filled in the constructor of the
        # plugin node. The icons icons['active'] and icons['inactive']
        # should be set.
        self.icons = {}

        # The accelerator string used for wxPython shortcuts.
        self.accelerator_string = None

        # The preferences dialog accelerator string used for wxPython
        # shortcuts.
        # This shortcut is used only, if the plugin has preferences in the
        # preferences manager.
        self.pref_accelerator_string = None

        self.menu_accelerator_string = None

        # Plugin shortcuts without a related menu item.
        self.shortcuts = {}

        # The activation state of the tool. This is used by view- and
        # interactive tools. For other tool modes, the active state is
        # always False.
        self.active = False

        # The preferred position within a category.
        self.position_pref = position_pref

    @property
    def rid(self):
        ''' The resource ID of the plugin.
        '''
        name_slug = self.name.replace(' ', '_')
        if self.parent:
            return self.parent.collection_node.rid + '/plugin/' + name_slug
        else:
            return '/plugin/' + name_slug


    def __getattr__(self, attrname):
        ''' Handle call of attributes which are derived from the parent recorder.
        '''
        if attrname in self.pref_manager.get_name():
            return self.pref_manager.get_value(attrname)
        else:
            raise AttributeError(attrname)


    def register(self, parent):
        ''' Register the plugin within a collection node.

        Parameters
        ----------
        parent : :class:`~psysmon.core.packageNodes.CollectionNode`

        '''
        self.parent = parent


    def register_keyboard_shortcuts(self):
        ''' Register the keyboard shortcuts.
        '''
        return None


    def activate(self):
        ''' Activate the plugin.
        '''
        self.active = True


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        self.active = False


    def buildMenu(self):
        ''' Build the menu which is added to the parent's menu bar.
        '''
        return None



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.

        '''
        return psysmon.gui.bricks.PrefEditPanel(pref = self.pref_manager,
                                                    parent = panelBar)


    def getHooks(self):
        ''' Register the callback methods for certain key events.

        The hooks are Matplotlib events (e.g. button_press_event, 
        button_release_event, motions_notify_event.
        Other types of hooks can be provided by the collection nodes.
        '''
        return None


    def initialize_preferences(self):
        ''' Initialize runtime dependent preference items.
        '''
        pass


    def get_virtual_stations(self):
        ''' Return the required virtual stations in a display group.

        Returns
        -------
        stations : list of strings
            The names of the required stations.
        '''
        return []




class OptionPlugin(PluginNode):
    ''' A plugin handling program options.

    An option plugin organizes one or more options.
    '''
    def __init__(self, name, category, tags, group = 'general', icons = None, parent = None, docEntryPoint = None, position_pref = 0):
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
                            group = group,
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint,
                            position_pref = position_pref)




class CommandPlugin(PluginNode):
    ''' A plugin executing a single command.

    A command plugin can be used to execute standalone programs which process the currently
    displayed data and maybe present the results in a new window (e.g. frequency spectrum, audification, ...).
    '''
    def __init__(self, name, category, tags, group = 'general', icons = None, parent = None, docEntryPoint = None, position_pref = 0):
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
                            group = group,
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint,
                            position_pref = position_pref)


    def run(self):
        ''' Run the command of the plugin.
        '''
        return None



class InteractivePlugin(PluginNode):
    ''' Interact with the user interface.

    The interactive plugin allows the user to interact with the parent window using 
    mouse clicks.
    '''
    def __init__(self, name, category, tags, group = 'general', icons = None, parent = None, docEntryPoint = None, position_pref = 0):
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
                            group = group,
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint,
                            position_pref = position_pref)

        self.cursor = None

        # The hotspot of the cursor image. It is measured relative to the
        # top-left corner of the image (0 - 1).
        self.cursor_hotspot = (0,0)





class ViewPlugin(PluginNode):
    ''' Add algorithms that are executed before displaying the data.

    This plugin is capable of creating individual views 
    which are used in the tracedisplay.
    '''

    def __init__(self, name, category, tags, group = 'general', icons = None, parent=None, docEntryPoint=None, position_pref = 0):
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
                            mode = 'view',
                            group = group,
                            category = category,
                            tags = tags,
                            icons = icons,
                            parent = parent,
                            docEntryPoint = docEntryPoint,
                            position_pref = position_pref)


        def getViewClass(self):
            ''' Get a class object of the view of the plugin.

            '''
            assert False, 'The getViewClass must be defined!'



class SharedInformationBag(object):
    ''' A container holding information shared between various plugins.

    The bag can be used by plugins to add and remove information that
    they like to share with other plugins.
    The bag can be placed in the instance holding the plugins (e.g.
    the tracedisplay instance).
    '''
    def __init__(self):
        ''' The initialization of the instance.
        '''
        self.shared_info = []


    def add_info(self, origin_rid, name, value):
        ''' Add an information to the bag.
        '''
        # Check if the value is a dictionary.
        if not isinstance(value, dict):
            raise ValueError('The value has to be a dictionary.')

        # Check if the info already exists in the bag.
        cur_info = self.get_info(origin_rid = origin_rid,
                                 name = name)
        if cur_info:
            if len(cur_info) > 1:
                raise RuntimeError("More than one info objects returned. This shouldn't happen.")
            else:
                cur_info = cur_info[0]
                cur_info.value = value
                cur_info.last_change_rid = origin_rid
        else:
            # If it doesn't exist, create a new one.
            cur_info = SharedInformation(origin_rid = origin_rid,
                                         name = name,
                                         value = value)
            self.shared_info.append(cur_info)


    def update_info(self, origin_rid, name, value, change_rid):
        ''' Update the value of an existing information.
        '''
        # Check if the value is a dictionary.
        if not isinstance(value, dict):
            raise ValueError('The value has to be a dictionary.')

        # Check if the info already exists in the bag.
        cur_info = self.get_info(origin_rid = origin_rid,
                                 name = name)
        if cur_info:
            if len(cur_info) > 1:
                raise RuntimeError("More than one info objects returned. This shouldn't happen.")
            else:
                cur_info = cur_info[0]
                cur_info.value = value
                cur_info.last_change_rid = change_rid
                return cur_info


    def remove_info(self, origin_rid, name = None):
        ''' Remove an information from the bag.
        '''
        # Check if the info exists in the bag.
        if name is None:
            info_list = self.get_info(origin_rid = origin_rid)
        else:
            info_list = [self.get_info(origin_rid = origin_rid,
                                     name = name),]
        removed_info = []

        for cur_info in info_list:
            self.shared_info.remove(cur_info)
            removed_info.append(cur_info)

        return removed_info



    def get_info(self, **kwargs):
        ''' Get an information from the bag.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information
        '''
        valid_keys = ['origin_rid', 'name']

        ret_val = self.shared_info

        for cur_key, cur_value in kwargs.items():
            if cur_key in valid_keys:
                ret_val = [x for x in ret_val if getattr(x, cur_key) == cur_value]
            else:
                raise RuntimeError('The search attribute %s is not allowed.' % cur_key)

        return ret_val



class SharedInformation(object):
    '''
    '''
    def __init__(self, origin_rid, name, value):
        ''' The initialization of the instance.
        '''
        # The resource id of the plugin that created the information.
        self.origin_rid = origin_rid

        # The name of the information.
        self.name = name

        # The value of the information.
        self.value = value

        # The rid of the instance which applied the last change.
        self.last_change_rid = origin_rid





