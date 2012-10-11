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
Module for handling object preferences.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''


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


    def add_item(self, pagename, item):
        ''' Add a preference item to a page of the manager.

        Parameters
        ----------
        pagename : String
            The name of the page to which the item should be added.

        item : :class:`~PreferenceItem`
            The item to be added to the page.
        '''
        if pagename in self.pages.keys():
            self.pages[pagename].append(item)



class PreferenceItem:
    ''' A project preferences item.

    '''

    def __init__(self, name, value, mode, group = None, limit = None, parent_page = None, default = None):
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


    def __str__(self):
        ''' The string representation of the instance.

        '''
        return 'PREF:\t%s, %s, %s' % (self.name, self.value, self.mode)



    def set_value(self, value):
        ''' Set the value of the preference item.

        Parameters
        ----------
        value : depends on item mode
            The value of the preference item.
        '''
        print "preference_item - set_value\n"
        self.value = value
