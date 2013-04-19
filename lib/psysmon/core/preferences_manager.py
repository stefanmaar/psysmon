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
from psysmon.core.guiBricks import SingleChoiceField
from psysmon.core.guiBricks import TextEditField
from psysmon.core.guiBricks import IntegerCtrlField
from psysmon.core.guiBricks import IntegerRangeField
from psysmon.core.guiBricks import FloatSpinField
from psysmon.core.guiBricks import MultiChoiceField
from psysmon.core.guiBricks import FileBrowseField
from psysmon.core.guiBricks import DirBrowseField


class PreferencesManager:
    ''' The preferences of the project.

    The PreferencesManager holds and organizes all project preferences.
    The preference items can be added to groups of the preferences manager.

    '''

    def __init__(self):
        ''' The constructor.

        '''
        # The pages (categories) of the project preferences.
        self.pages = {}
        self.pages['preferences'] = []

        # A dictionary with the GUI element field classes.
        self.gui_elements = {}
        self.gui_elements['single_choice'] = SingleChoiceField
        self.gui_elements['multi_choice'] = MultiChoiceField
        self.gui_elements['textedit'] = TextEditField
        self.gui_elements['integer_control'] = IntegerCtrlField
        self.gui_elements['integer_spin'] = IntegerRangeField
        self.gui_elements['float_spin'] = FloatSpinField
        self.gui_elements['filebrowse'] = FileBrowseField
        self.gui_elements['dirbrowse'] = DirBrowseField


    def __str__(self):
        ''' The string representation of the instance.

        '''
        out = ''
        for cur_name, cur_page in self.pages.items():
            for cur_item in cur_page:
                out += str(cur_item)

        return out


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

            if item.mode in self.gui_elements.keys():
                item.guiclass = self.gui_elements[item.mode]

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

        return found_items


class PreferenceItem:
    ''' A project preferences item.

    '''

    def __init__(self, name, value, mode, group = None, limit = None, parent_page = None, default = None, guiclass = None):
        ''' The constructor.

        '''
        # The name of the item.
        self.name = name

        # The value of the item.
        self.value = value

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

        # The GUI element which will be used to represent this field in
        # dialogs, panels, .... . When using a 'custom' mode, this value should
        # be set. For standard field modes, the gui_element will be set by the
        # preferences manager.
        self.guiclass = guiclass


    def __str__(self):
        ''' The string representation of the instance.

        '''
        return 'PREF:\t%s, %s, %s, %s' % (self.name, self.value, self.mode, self.parent_page)



    def set_value(self, value):
        ''' Set the value of the preference item.

        Parameters
        ----------
        value : depends on item mode
            The value of the preference item.
        '''
        print "preference_item - set_value\n"
        self.value = value



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

    def __init__(self, name, value, increment = 0.1, digits = 3, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'float_spin', **kwargs)

        self.increment = increment

        self.digits = digits


class IntegerControlPrefItem(PreferenceItem):
    '''
    '''

    def __init__(self, name, value, **kwargs):

        PreferenceItem.__init__(self, name = name, value = value, 
                mode = 'integer_control', **kwargs)


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


class CustomPrefItem(PreferenceItem):
    '''
    '''
    def __init__(self, name, value, **kwargs):
        PreferenceItem.__init__(self, name = name, value = value,
                                mode = 'custom', **kwargs)
