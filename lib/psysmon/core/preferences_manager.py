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
Module for handling object preferences.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

from builtins import str
from builtins import object


class PreferencesManager(object):
    ''' The preferences of the project.

    The PreferencesManager holds and organizes all project preferences.
    '''

    def __init__(self, pages = None):
        ''' The constructor.

        '''
        # The pages (categories) of the project preferences.
        if pages is None:
            self.pages = []
        else:
            self.pages = pages


    @property
    def settings(self):
        ''' The configuration settings of the preference items.
        '''
        settings = {}
        for cur_page in self.pages:
            settings[cur_page.name] = {}
            for cur_group in cur_page.groups:
                settings[cur_page.name][cur_group.name] = {}
                for cur_item in cur_group.items:
                    if not isinstance(cur_item, ActionItem):
                        settings[cur_page.name][cur_group.name][cur_item.name] = cur_item.settings

        return settings



    def __str__(self):
        ''' The string representation of the instance.

        '''
        out = ''
        for cur_page in self.pages:
            out += str(cur_page) + '\n'

        return out

    def __len__(self):
        ''' The number of preference groups.
        '''
        n_items = 0
        for cur_page in self.pages:
            n_items += len(cur_page)
        return n_items


    def get_page(self, name):
        ''' Get a page.
        '''
        cur_page = [x for x in self.pages if x.name == name]
        if len(cur_page) > 1:
            raise RuntimeError("More than one page with name %s found. This shouldn't happen.", name)
        elif len(cur_page) == 1:
            cur_page = cur_page[0]

        return cur_page


    def add_page(self, name):
        ''' Add a new page to the manager.

        Parameters
        ----------
        name : String
            The name of the new page.

        Returns
        -------
        page : Page
            The created page or if the page already exists the existing page.
        '''
        cur_page = self.get_page(name = name)
        if len(cur_page) == 0:
            cur_page = Page(name)
            self.pages.append(cur_page)

        return cur_page



    def get_item(self, name, pagename = None):
        ''' Get items with specified name [and pagename] from the preferences.

        name : String
            The name of the preferences item to find.

        pagename : String
            The name of the page to which the search should be limited.

        '''
        found_items = []
        if pagename is not None:
            cur_page = self.get_page(name = pagename)
            if cur_page:
                search_pages = [cur_page, ]
        else:
            search_pages = self.pages

        for cur_page in search_pages:
            tmp = cur_page.get_item(name = name)
            found_items.extend(tmp)

        return found_items


    def get_value(self, name, pagename = None):
        ''' Get items with specified name [and pagename] from the preferences.

        name : String
            The name of the preferences item to find.

        pagename : String
            The name of the page to which the search should be limited.

        '''
        found_items = self.get_item(name = name, pagename = pagename)
        values = [x.value for x in found_items]
        if len(values) == 1:
            values = values[0]

        #print("pref name: {}; value: {}".format(name, values))

        return values


    def get_limit(self, name, pagename = None):
        ''' Get item limits with specified name [and pagename] from the preferences.

        name : String
            The name of the preferences item to find.

        pagename : String
            The name of the page to which the search should be limited.

        '''
        found_items = self.get_item(name = name, pagename = pagename)
        limits = [x.limit for x in found_items]
        if len(limits) == 1:
            limits = limits[0]

        return limits


    def set_limit(self, name, limit, pagename = None):
        ''' Set the value of the specified item.

        name : String
            The name of the preferences item to set.

        value : String
            The new value of the preferences item.

        pagename : String
            The name of the page to which the search should be limited.
        '''
        found_items = self.get_item(name = name, pagename = pagename)
        for cur_item in found_items:
            cur_item.limit = limit
            if len(cur_item.gui_element) > 0:
                cur_item.update_limit()

        return found_items


    def set_value(self, name, value, pagename = None):
        ''' Set the value of the specified item.

        name : String
            The name of the preferences item to set.

        value : String
            The new value of the preferences item.

        pagename : String
            The name of the page to which the search should be limited.
        '''
        found_items = self.get_item(name = name, pagename = pagename)
        for cur_item in found_items:
            cur_item.value = value
            if len(cur_item.gui_element) > 0:
                cur_item.update_gui_element()

        return found_items


    def get_name(self, pagename = None):
        ''' Get all available preference names.

        Parameters
        ----------
        pagename : String
            The name of the page to which the search should be limited.

        Returns
        -------
        found_items : List of String
            The found preference names as a list.
        '''
        found_items = []
        if pagename is not None:
            cur_page = self.get_page(name = pagename)
            if cur_page:
                search_pages = [cur_page, ]
        else:
            search_pages = self.pages

        for cur_page in search_pages:
            for cur_group in cur_page.groups:
                found_items.extend([x.name for x in cur_group.items])

        return found_items


    def update(self, pref_manager):
        ''' Update the values of the preferences manager.
        '''
        #attr_to_update = ['value', 'limit']
        attr_to_update = ['value',]

        # 2016-12-15: Handle the change of the prefence_manager classes.
        if isinstance(pref_manager.pages, dict):
            # The preferences manager was saved using an old class.
            for cur_key in pref_manager.pages.keys():
                page_names = [x.name.lower() for x in self.pages]
                ext_pagename = cur_key.lower()
                if ext_pagename in page_names:
                    for cur_item in pref_manager.pages[cur_key]:
                        update_item = self.get_item(cur_item.name)
                        for cur_update_item in update_item:
                            for cur_attr in attr_to_update:
                                if cur_attr in list(cur_update_item.__dict__.keys()):
                                    setattr(cur_update_item, cur_attr, getattr(cur_item, cur_attr))
        else:
            # Use the uptodate version of the preference manager.
            for cur_ext_page in pref_manager.pages:
                page_names = [x.name for x in self.pages]
                if cur_ext_page.name in page_names:
                    for cur_ext_group in cur_ext_page.groups:
                        for cur_ext_item in cur_ext_group.items:
                            update_item = self.get_item(cur_ext_item.name, cur_ext_page.name)
                            for cur_update_item in update_item:
                                for cur_attr in attr_to_update:
                                    if cur_attr in list(cur_update_item.__dict__.keys()):
                                        setattr(cur_update_item, cur_attr, getattr(cur_ext_item, cur_attr))



class Page(object):
    ''' A page of the preference manager.
    '''

    def __init__(self, name, groups = None):
        ''' Initialize the instance.
        '''
        # The name of the page.
        self.name = name

        # The groups of the page.
        if groups is None:
            self.groups = []
        else:
            self.groups = groups


    def __len__(self):
        ''' The number of groups.
        '''
        return len(self.groups)


    def __str__(self):
        ''' The string representation of the page.
        '''
        out = ''
        for cur_group in self.groups:
            out += str(cur_group) + '\n'

        return out


    def get_group(self, name):
        ''' Get a group.
        '''
        cur_group = [x for x in self.groups if x.name == name]
        if len(cur_group) > 1:
            raise RuntimeError("More than one group with name %s found. This shouldn't happen.", name)
        elif len(cur_group) == 1:
            cur_group = cur_group[0]

        return cur_group


    def add_group(self, name):
        ''' Add a group to the page.
        '''
        cur_group = self.get_group(name = name)

        if len(cur_group) == 0:
            cur_group = Group(name = name)
            self.groups.append(cur_group)

        return cur_group


    def get_item(self, name):
        ''' Get items from the page.
        '''
        found_items = []
        for cur_group in self.groups:
            found_items.extend(cur_group.get_item(name = name))

        return found_items



class Group(object):
    ''' A group of a page in the preference manager.
    '''

    def __init__(self, name, items = None):
        ''' Initialize the instance.
        '''
        # The name of the group.
        self.name = name

        # The preference items of the group.
        if items is None:
            self.items = []
        else:
            self.items = items


    def __str__(self):
        ''' The string representation of the group.
        '''
        out = ''
        for cur_item in self.items:
            out += str(cur_item) + '\n'

        return out


    def add_item(self, item):
        ''' Add a preference item to the group.
        '''
        self.items.append(item)


    def get_item(self, name):
        ''' Get an item from the group.
        '''
        return [x for x in self.items if x.name == name]



class PreferenceItem(object):
    ''' A project preferences item.

    '''

    def __init__(self, name, value, mode, label = None,
                 limit = None, parent_page = None,
                 default = None, gui_element = None,
                 tool_tip = None, hooks = None, visible = True):
        ''' Initialization of the instance.

        '''
        # The name of the item.
        self.name = name

        # The value of the item.
        self.value = value

        # The label of the item.
        self.label = label
        if self.label is None:
            self.label = self.name

        # The tooltip string of the control element.
        self.tool_tip = tool_tip

        # The default value of this item.
        if default is None:
            default = value
        self.default = default

        # The mode of the item.
        self.mode = mode

        # The limits restricting the item value.
        self.limit = limit

        # The parent page of the PreferencesManager.
        self.parent_page = parent_page

        # The GUI element(s) linked to this preference item.
        if gui_element is None:
            gui_element = []
        self.gui_element = gui_element

        # Function hooks to be called in methods of the gui elements.
        if hooks is None:
            self.hooks = {}
        else:
            self.hooks = hooks

        # Flag to indicate if the prefrence item is visible in GUI.
        self.visible = visible


    @property
    def settings(self):
        return self.value

    #@property
    #def value(self):
    #    return self._value

    #@value.setter
    #def value(self, value):
    #    self._value = value




    def __str__(self):
        ''' The string representation of the instance.

        '''
        return 'PREF:\t%s, %s, %s, %s' % (self.name, self.value, self.mode, self.parent_page)


    def __getstate__(self):
        import types

        result = self.__dict__.copy()

        # The following attributes can't be pickled an therefore have to be
        # removed.
        # These values have to be reset when loading the project.
        hooks = {}
        for cur_key, cur_hook in self.hooks.items():
            if isinstance(cur_hook, types.MethodType):
                hooks[cur_key] = cur_hook.__name__
        result['hooks'] = hooks

        return result


    #TODO: Add a __setstate__ method which recreates the hooks callbacks.


    def set_gui_element(self, element):
        ''' Set the gui element displaying the preference item.

        '''
        if element not in self.gui_element:
            self.gui_element.append(element)

    def remove_gui_element(self, element):
        ''' Remove a gui element from the preference item.
        '''
        self.gui_element.remove(element)


    def update_gui_element(self):
        ''' Update the gui elements related to the item.

        '''
        for cur_element in self.gui_element:
            cur_element.setControlElementValue()


    def update_limit(self):
        ''' Update the limits of the gui elements.
        '''
        for cur_element in self.gui_element:
            cur_element.updateLimit()

    def enable_gui_element(self):
        ''' Enable the gui element to make it active for user interaction.
        '''
        for cur_element in self.gui_element:
            cur_element.labelElement.Enable()
            cur_element.controlElement.Enable()

    def disable_gui_element(self):
        ''' Disable the gui element to make it inactive for user interaction.
        '''
        for cur_element in self.gui_element:
            cur_element.labelElement.Disable()
            cur_element.controlElement.Disable()


class SingleChoicePrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'single_choice', **kwargs)



class MultiChoicePrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'multi_choice', **kwargs)



class FileBrowsePrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, filemask = '*.*', **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'filebrowse', **kwargs)

        self.filemask = filemask



class DirBrowsePrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, start_directory = '.', **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'dirbrowse', **kwargs)

        self.start_directory = start_directory


class FloatSpinPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, increment = 0.1, digits = 3, spin_format = '%f', **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'float_spin', **kwargs)

        self.increment = increment

        self.digits = digits

        self.spin_format = spin_format


class IntegerControlPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'integer_control', **kwargs)


class CheckBoxPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'checkbox', **kwargs)


class IntegerSpinPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'integer_spin', **kwargs)


class TextEditPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'textedit', **kwargs)


class DateTimeEditPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'datetime', **kwargs)


class ListCtrlEditPrefItem(PreferenceItem):
    '''
    '''
    def __init__(self, name, value, column_labels = None, **kwargs):
        ''' Initialize the instance.
        '''
        PreferenceItem.__init__(self, name = name, value = value,
                                mode = 'list_ctrl', **kwargs)

        self.column_labels = column_labels



class ListGridEditPrefItem(PreferenceItem):
    '''
    '''
    def __init__(self, name, value, column_labels = None, **kwargs):
        ''' Initialize the instance.
        '''
        PreferenceItem.__init__(self, name = name, value = value,
                                mode = 'list_grid', **kwargs)

        self.column_labels = column_labels


class ProcessingStackPrefItem(PreferenceItem):
    '''
    '''
    def __init__(self, name, value, **kwargs):
        PreferenceItem.__init__(self, name = name, value = value,
                                mode = 'processing_stack', **kwargs)


    @property
    def settings(self):
        '''
        '''
        settings = []
        if self.value:
            for cur_node in self.value:
                settings.append(cur_node.settings)

        return settings

    

class CustomPrefItem(PreferenceItem):
    '''
    '''
    def __init__(self, name, value, gui_class = None, **kwargs):
        PreferenceItem.__init__(self, name = name, value = value,
                                mode = 'custom', **kwargs)
        self.gui_class = gui_class



class ActionItem(object):
    '''
    '''
    def __init__(self, name, label, mode, action, tool_tip = None, visible = True):

        self.name = name

        self.label = label

        self.mode = mode

        self.action = action

        self.tool_tip = tool_tip

        self.gui_element = []

        # Flag to indicate if the prefrence item is visible in GUI.
        self.visible = visible


    def __getstate__(self):
        import types

        result = self.__dict__.copy()

        # The following attributes can't be pickled an therefore have to be
        # removed.
        # These values have to be reset when loading the project.
        if isinstance(self.action, types.MethodType):
            result['action'] = self.action.__name__
        result['gui_element'] = []

        return result


    #TODO: Add a __setstate__ method which recreates the action callback.



    def set_gui_element(self, element):
        ''' Set the gui element displaying the preference item.

        '''
        # Check for deleted elements.
        # TODO: Create GUI fields for the ActionItem similar to the PrefItems
        # to handle the removal of the gui_element when the GUI field is
        # deleted.

        # Remove the gui_elements for which the C++ part has been deleted.
        self.gui_element = [x for x in self.gui_element if x]

        if element not in self.gui_element:
            self.gui_element.append(element)


    def enable_gui_element(self):
        ''' Enable the gui element to make it active for user interaction.
        '''
        for cur_element in self.gui_element:
            cur_element.Enable()


    def disable_gui_element(self):
        ''' Disable the gui element to make it inactive for user interaction.
        '''
        for cur_element in self.gui_element:
            cur_element.Disable()

