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

import wx

class PreferencesManager:
    ''' The preferences of the project.

    The PreferencesManager holds and organizes all project preferences.
    The preference items can be added to groups of the preferences manager.

    '''

    def __init__(self, pages = None):
        ''' The constructor.

        '''
        # The pages (categories) of the project preferences.
        if pages is None:
            self.pages = {}
            self.pages['preferences'] = []
        else:
            self.pages = pages

        self.group_order = []


    @property
    def settings(self):
        ''' The configuration settings of the preference items.
        '''
        settings = {}
        for cur_name, cur_page in self.pages.items():
            settings[cur_name] = {}
            for cur_item in cur_page:
                settings[cur_name][cur_item.name] = cur_item.value

        return settings



    def __str__(self):
        ''' The string representation of the instance.

        '''
        out = ''
        for cur_name, cur_page in self.pages.items():
            for cur_item in cur_page:
                out += str(cur_item) + '\n'

        return out

    def __len__(self):
        ''' The number of preference items.
        '''
        n_items = 0
        for cur_page in self.pages.itervalues():
            n_items += len(cur_page)
        return n_items


    def add_page(self, name):
        ''' Add a new page to the manager.

        Parameters
        ----------
        name : String 
            The name of the new page.
        '''
        if name not in self.pages.keys():
            self.pages[name] = []


    def add_item(self, item, pagename = 'preferences'):
        ''' Add a preference item to a page of the manager.

        Parameters
        ----------
        pagename : String
            The name of the page to which the item should be added.

        item : :class:`~PreferenceItem`
            The item to be added to the page.
        '''
        if pagename in self.pages.keys():
            item.parent_page = pagename

            self.pages[pagename].append(item)


    def get_item(self, name, pagename = None):
        ''' Get items with specified name [and pagename] from the preferences.

        name : String
            The name of the preferences item to find.

        pagename : String
            The name of the page to which the search should be limited.

        '''
        found_items = []
        if pagename is not None:
            if pagename in self.pages.keys():
                found_items = [x for x in self.pages[pagename] if x.name == name]

        else:
            for cur_page in self.pages.values():
                tmp = [x for x in cur_page if x.name == name]
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
            if pagename in self.pages.keys():
                found_items = [x.name for x in self.pages[pagename]]

        else:
            for cur_page in self.pages.values():
                tmp = [x.name for x in cur_page]
                found_items.extend(tmp)

        return found_items


    def update(self, pref_manager):
        ''' Update the values of the preferences manager.
        '''
        attr_to_update = ['value', 'limit']
        for cur_key in pref_manager.pages.keys():
            if cur_key in self.pages.keys():
                for cur_item in pref_manager.pages[cur_key]:
                    update_item = self.get_item(cur_item.name, cur_key)
                    for cur_update_item in update_item:
                        for cur_attr in attr_to_update:
                            if cur_attr in cur_update_item.__dict__.keys():
                                setattr(cur_update_item, cur_attr, getattr(cur_item, cur_attr))



class PreferenceItem(object):
    ''' A project preferences item.

    '''

    def __init__(self, name, value, mode, label = None,
                 group = None, limit = None, parent_page = None,
                 default = None, gui_element = None,
                 tool_tip = None, position = None, hooks = None):
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

        # The group of the item.
        self.group = group

        # The limits restricting the item value.
        self.limit = limit

        # The parent page of the PreferencesManager.
        self.parent_page = parent_page

        # The GUI element(s) linked to this preference item.
        if gui_element is None:
            gui_element = []
        self.gui_element = gui_element

        # The position of the preference item within a group.
        self.position = position

        # Function hooks to be called in methods of the gui elements.
        if hooks is None:
            self.hooks = {}
        else:
            self.hooks = hooks


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
        for cur_key, cur_hook in self.hooks.iteritems():
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
            cur_element.controlElement.SetValue(self.value)


    def update_limit(self):
        ''' Update the limits of the gui elements.
        '''
        for cur_element in self.gui_element:
            cur_element.updateLimit();

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
    def __init__(self, name, label, group, mode, action, tool_tip = None):

        self.name = name

        self.label = label

        self.group = group

        self.mode = mode

        self.action = action

        self.tool_tip = tool_tip

        self.gui_element = []


    def __getstate__(self):
        import types

        result = self.__dict__.copy()

        # The following attributes can't be pickled an therefore have to be
        # removed.
        # These values have to be reset when loading the project.
        if isinstance(self.action, types.MethodType):
            result['action'] = self.action.__name__

        return result


    #TODO: Add a __setstate__ method which recreates the action callback.



    def set_gui_element(self, element):
        ''' Set the gui element displaying the preference item.

        '''
        # Check for deleted elements.
        # TODO: Create GUI fields for the ActionItem similar to the PrefItems
        # to handle the removal of the gui_element when the GUI field is
        # deleted.
        self.gui_element = [x for x in self.gui_element if not isinstance(x, wx._core._wxPyDeadObject)]
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

