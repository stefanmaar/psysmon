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

import logging
import warnings

import psysmon


class ShortcutManager(object):

    def __init__(self):
        ''' The constructor

        '''
        # The logging logger instance.class ShortcutManager(object):


    def __init__(self):
        ''' The constructor

        '''
        # The logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.shortcuts = []

        # A dictionary holding the actions bound to a certain key combination.
        # The key of the dictionary is a tuple of none or more modifiers keys 
        # and the pressed key.
        self.actions = {}

        self.kwargs = {}


    def add_shortcut(self, origin_rid, key_combination, action, kind = 'down', action_kwargs = None):
        ''' Add an action to the shortcut options.

        Parameters
        ----------
        origin_rid : String
            The RID of the instance adding the shortcut.

        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        action : Method
            The method which should be executed when the key is pressed.

        kind : String
            The kind of mouse event (up, down).

        action_kwargs : Dictionary
            A dictionary holding the keyword arguments passed to the action.

        '''
        shortcut = Shortcut(origin_rid = origin_rid,
                            key_combination = key_combination,
                            action = action,
                            kind = kind,
                            action_kwargs = action_kwargs)
        self.shortcuts.append(shortcut)


    def get_shortcut(self, **kwargs):
        ''' Get the action bound to the keyCombination.

        Paramters
        ---------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        kind : String
            The kind of mouse event (up, down).

        Returns
        -------
        action : Method
            The method which should be executed when the key is pressed.
            None if no action is found.
        '''
        ret_val = self.shortcuts

        valid_keys = ['key_combination', 'origin_rid', 'kind']
        for cur_key, cur_value in kwargs.items():
            if cur_key in valid_keys:
                ret_val = [x for x in ret_val if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_val


    def remove_shortcut(self, **kwargs):
        ''' Remove action(s) from the manager.
        '''
        shortcuts_to_remove = self.get_shortcut(**kwargs)

        for cur_shortcut in shortcuts_to_remove:
            self.shortcuts.remove(cur_shortcut)

        return shortcuts_to_remove




class Shortcut(object):
    ''' A Shortcut action.
    '''

    def __init__(self, origin_rid, key_combination, action, kind = 'down', action_kwargs = None):
        ''' Initialize the instance.
        '''
        # The RID of the instance owning the shortcut.
        self.origin_rid = origin_rid

        self.key_combination = key_combination

        self.action = action

        self.kind = kind

        self.action_kwargs = action_kwargs

        self.logger = psysmon.get_logger(self)

        self.shortcuts = []

        # A dictionary holding the actions bound to a certain key combination.
        # The key of the dictionary is a tuple of none or more modifiers keys 
        # and the pressed key.
        self.actions = {}

        self.kwargs = {}


    def add_shortcut(self, origin_rid, key_combination, action,
                     kind = 'down', action_kwargs = None):
        ''' Add an action to the shortcut options.

        Parameters
        ----------
        origin_rid : String
            The RID of the instance adding the shortcut.

        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        action : Method
            The method which should be executed when the key is pressed.

        kind : String
            The kind of mouse event (up, down).

        action_kwargs : Dictionary
            A dictionary holding the keyword arguments passed to the action.

        '''
        shortcut = Shortcut(origin_rid = origin_rid,
                            key_combination = key_combination,
                            action = action,
                            kind = kind,
                            action_kwargs = action_kwargs)
        self.shortcuts.append(shortcut)


    def get_shortcut(self, **kwargs):
        ''' Get the action bound to the keyCombination.

        Paramters
        ---------
        keyCombination : tuple of Strings
            The key combination to which the action is bound to.
            E.g.: ('WXK_LEFT'), ('CTRL', 'P'), ('CTRL', 'ALT', 'P')

        kind : String
            The kind of mouse event (up, down).

        Returns
        -------
        action : Method
            The method which should be executed when the key is pressed.
            None if no action is found.
        '''
        ret_val = self.shortcuts

        valid_keys = ['key_combination', 'origin_rid', 'kind']
        for cur_key, cur_value in kwargs.items():
            if cur_key in valid_keys:
                ret_val = [x for x in ret_val if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_val


    def remove_shortcut(self, **kwargs):
        ''' Remove action(s) from the manager.
        '''
        shortcuts_to_remove = self.get_shortcut(**kwargs)

        for cur_shortcut in shortcuts_to_remove:
            self.shortcuts.remove(cur_shortcut)

        return shortcuts_to_remove




class Shortcut(object):
    ''' A Shortcut action.
    '''

    def __init__(self, origin_rid, key_combination, action,
                 kind = 'down', action_kwargs = None):
        ''' Initialize the instance.
        '''
        # The RID of the instance owning the shortcut.
        self.origin_rid = origin_rid

        self.key_combination = key_combination

        self.action = action

        self.kind = kind

        self.action_kwargs = action_kwargs
