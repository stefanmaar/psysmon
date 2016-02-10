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

## Documentation for class Base
# 
#
#    A class which behaves like a dictionary.
#
#    Basic Usage
#    -----------
#    You may use the following syntax to change or access data in this
#    class.
#
#    >>> stats = AttribDict()
#    >>> stats.network = 'OE'
#    >>> stats['station'] = 'CONA'
#    >>> stats.get('network')
#    'OE'
#    >>> stats['network']
#    'OE'
#    >>> stats.station
#    'CONA'
#    >>> x = stats.keys()
#    >>> x = sorted(x)
#    >>> x[0:3]
#    ['network', 'station']
#
#    Parameters
#    ----------
#    data : dict, optional
#        Dictionary with initial keywords.
#    
# The AttribDict class has been taken from the ObsPy package and modified.
#
# The ObsPy package is
# copyright:
#    The ObsPy Development Team (devs@obspy.org)
# license:
#    GNU Lesser General Public License, Version 3
#    (http://www.gnu.org/copyleft/lesser.html)
#


from obspy.core import UTCDateTime
from wx import DateTime, DateTimeFromDMY


def _wxdate2pydate(date):
     if date is None:
         return None

     assert isinstance(date, DateTime)
     if date.IsValid():
         ymd = map(int, date.FormatISODate().split('-'))
         return UTCDateTime(*ymd)
     else:
         return None 



def _pydate2wxdate(date):
     if date is None:
         return None

     assert isinstance(date, UTCDateTime)
     tt = date.timetuple()
     dmy = (tt[2], tt[1]-1, tt[0])
     return DateTimeFromDMY(*dmy)


def version_tuple(version_string):
    ''' Convert a version string (e.g. 0.1.2) into a compareable tuple.

    '''
    return tuple(map(int, version_string.split('.')))



def traceid_to_scnl(trace_id):
    ''' Convert a obspy trace id to a SCNL tuple.

    Parameters
    ----------
    trace_id : String
        A string representing the obspy trace ID
        (network.station.location.channel)
    '''
    network, station, location, channel = trace_id.split('.')
    return((station, channel, network, location))



class AttribDict(dict, object):

    readonly = []

    def __init__(self, data={}):
        dict.__init__(data)
        self.update(data)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, dict.__repr__(self))

    def __setitem__(self, key, value):
        super(AttribDict, self).__setattr__(key, value)
        super(AttribDict, self).__setitem__(key, value)

    def __getitem__(self, name):
        if name in self.readonly:
            return self.__dict__[name]
        return super(AttribDict, self).__getitem__(name)

    def __delitem__(self, name):
        super(AttribDict, self).__delattr__(name)
        return super(AttribDict, self).__delitem__(name)

    def pop(self, name, default={}):
        value = super(AttribDict, self).pop(name, default)
        del self.__dict__[name]
        return value

    def popitem(self):
        (name, value) = super(AttribDict, self).popitem()
        super(AttribDict, self).__delattr__(name)
        return (name, value)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, pickle_dict):
        self.update(pickle_dict)

    __getattr__ = __getitem__
    __setattr__ = __setitem__
    __delattr__ = __delitem__

    def copy(self):
        return self.__class__(self.__dict__.copy())

    def __deepcopy__(self, *args, **kwargs):
        st = self.__class__()
        st.update(self)
        return st

    def update(self, adict={}):
        for (key, value) in adict.iteritems():
            if key in self.readonly:
                continue
            self[key] = value




class ActionHistory:
    ''' Keep track of actions in a GUI.

    This helper class provides the recording of actions executed by the user 
    which changed the attributes of a class or other variables.

    Each of the attributes can be mapped to a database field and the according 
    UPDATE query can be created if needed.

    Attributes
    ----------
    attrMap : Dictionary of Strings
        A Dictionary of Strings with the attribute name as the key and the 
        corresponding database table field as the value.

    actionTypes : Dictionary of Strings
        A dictionary of Strings with the action type as the key and a 
        description as the value. With this dictionary, the user can define 
        allowed actions to be recorded by the ActionHistory class.

    actions : A list of `~psysmon.core.util.Action` instances
        The actions recorded by the Action History class. Each action in the 
        list is a dictionary 
    '''

    def __init__(self, attrMap, actionTypes):
        ''' The constructor.

        '''

        # The mapping of the attributes to database table fields.
        self.attrMap = attrMap

        # The allowed types of actions.
        self.actionTypes = actionTypes

        # The recorded actions.
        self.actions = []


    def do(self, action):
        ''' Register an action in the history.

        '''
        print "Registering action: " + action.style
        self.actions.append(action)


    def undo(self):
        ''' Undo the last action in the history.

        '''
        print "undo action"
        if not self.hasActions:
           return

        action2Undo = self.pop()
        action2Undo.undo()


    def hasActions(self):
        ''' Check if actions have been registered.

        '''
        if self.actions:
            return True
        else:
            return False


    def pop(self, style=None):
        ''' Pop the last action in the stack.

        '''
        if not self.actions:
            return None

        if not style:
            if self.actions:
                return self.actions.pop()
        else:
            actions2Fetch = [curAction for curAction in self.actions if curAction.style == style]
            if actions2Fetch:
                for curAction in actions2Fetch:
                    self.actions.remove(curAction)
            return actions2Fetch


    def getUpdateString(self, actions):
        ''' Build the database UPDATE string.

        '''
        updateString = ''

        # Get all attributes names to process.
        attrNames = [curAction['attrName'] for curAction in actions]
        attrNames = list(set(attrNames))        # Remove duplicates.

        # Process the attribute names.
        for curAttr in attrNames:
            actions2Process = [curAction for curAction in actions if curAction['attrName'] == curAttr]
            firstAction = actions2Process[0]

            if(len(actions2Process) >= 2):
                lastAction = actions2Process[-1]
            else:
                lastAction = firstAction

            # If the attribute exists in the attribute map, create the update string.
            if curAttr in self.attrMap.keys():
                curStr = "%s = '%s'," %(self.attrMap[curAttr], str(lastAction['dataAfter']))
                updateString += curStr 


        # Remove the trailing comma from the string.            
        return updateString[:-1]




class Action:
    ''' The Action class used by `~psysmon.core.util.ActionHistory`.


    Attributes
    ----------
    style : String
        The style of the action. These styles are supported:

        - 'VALUE_CHANGE'
        - 'METHOD'


    '''


    def __init__(self, style, affectedObject, dataBefore, dataAfter, 
                 undoMethod=None, undoParameters=None):
        ''' The constructor.

        '''
        allowedStyles = ('VALUE_CHANGE', 'METHOD')
        if style not in allowedStyles:
            raise PsysmonError('style %s is not supported' % style)


        # The type of the action.
        self.style = style

        # The object which the action affects.
        self.affectedObject = affectedObject

        # The value of the attribute before the action has been done.
        self.dataBefore = dataBefore

        # The value of the attribute after the action has been done.
        self.dataAfter = dataAfter

        # The method or function to be called to undo the action.
        self.undoMethod = undoMethod

        # The parameters to be passed to the undoMethod.
        self.undoParameters = undoParameters


    def undo(self):
        ''' Undo the action.

        '''
        if self.style == 'METHOD':
            self.undoMethod(self.undoParameters)



class HookManager(object):
    ''' A class handling the callback hooks.
    '''
    def __init__(self, caller):
        ''' Initialize the instance.

        Parameters
        ----------
        caller : object
            The instance calling the hooks.
        '''
        # The object calling the hooks.
        self.caller = caller

        # The allowed hook names and a short description.
        self.hooks = {}

        # The keyword arguments of a hook.
        self.hook_kwargs = {}

        # The allowed matplotlib event hooks called from the views.
        self.view_hooks = {}


    def add_hook(self, name, description, passed_args = None):
        ''' Add a hook name to the allowed hooks.
        '''
        self.hooks[name] = description

        if passed_args is None:
            passed_args = {}

        if not isinstance(passed_args, dict):
            raise ValueError('The passed_args argument has to be a dictionary.')

        self.hook_kwargs[name] = passed_args


    def add_view_hook(self, name, description):
        ''' Add a hook name to the allowed hooks.
        '''
        self.view_hooks[name] = description


    def call_hook(self, receivers, hook_name, **kwargs):
        ''' Call the hook of the receivers.

        Parameters:
        -----------
        receivers : list of objects
            The objects for which the hooks are called.
        '''
        if hook_name not in self.hooks.keys():
            raise RuntimeError('The name %s is not available in the allowed hooks.' % hook_name)

        for cur_receiver in receivers:
            hooks = cur_receiver.getHooks()
            if hooks:
                if hook_name in hooks.keys():
                    kwargs = {x:kwargs[x] for x in kwargs if x in self.hook_kwargs[hook_name]}
                    hooks[hook_name](**kwargs)

