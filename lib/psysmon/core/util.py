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


import json
from obspy.core import UTCDateTime
from wx import DateTime, DateTimeFromDMY
import psysmon.core.project


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




class ProjectFileEncoder(json.JSONEncoder):
    ''' A JSON encoder for the pSysmon project file.
    '''
    def __init__(self, **kwarg):
        json.JSONEncoder.__init__(self, **kwarg)
        self.indent = 4
        self.sort_keys = True

    def default(self, obj):
        ''' Convert pSysmon project objects to a dictionary.
        '''
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]
        #print 'Converting %s' % obj_class

        if obj_class == 'Project':
            d = self.convert_project(obj)
        elif obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        elif obj_class == 'User':
            d = self.convert_user(obj)
        elif obj_class == 'Collection':
            d = self.convert_collection(obj)
        elif 'CollectionNode' in base_class:
            d = self.convert_collection_node(obj)
        elif obj_class == 'PreferencesManager':
            d = self.convert_preferencesmanager(obj)
        elif obj_class == 'CustomPrefItem':
            d = self.convert_custom_preferenceitem(obj)
        elif obj_class == 'type':
            d = {}
        elif 'PreferenceItem' in base_class:
            d = self.convert_preferenceitem(obj)
        elif 'WaveClient' in base_class:
            d = self.convert_waveclient(obj)
        elif 'ProcessingNode' in base_class:
            d = self.convert_processing_node(obj)
        else:
            d = {'ERROR': 'MISSING CONVERTER for obj_class %s with base_class %s' % (str(obj_class), str(base_class))}

        # Add the class and module information to the dictionary.
        tmp = {'__baseclass__': base_class,
               '__class__': obj.__class__.__name__,
               '__module__': obj.__module__}
        d.update(tmp)

        return d


    def convert_project(self, obj):
        attr = ['name', 'dbDriver', 'dbDialect', 'dbHost',
                'dbName', 'pkg_version', 'db_version', 'createTime',
                'defaultWaveclient', 'scnlDataSources', 'user', 'waveclient']
        d =  self.object_to_dict(obj, attr)
        #d['waveclient'] = [(x.name, x.mode, x.options) for x in obj.waveclient.itervalues()]
        return d


    def convert_utcdatetime(self, obj):
        return {'utcdatetime': obj.isoformat()}


    def convert_user(self, obj):
        attr = ['name', 'mode', 'author_name', 'author_uri', 
                'agency_name', 'agency_uri', 'collection']
        d = self.object_to_dict(obj, attr)
        if obj.activeCollection is None:
            d['activeCollection'] = obj.activeCollection
        else:
            d['activeCollection'] = obj.activeCollection.name

        return d


    def convert_collection(self, obj):
        attr = ['name', 'nodes']
        return self.object_to_dict(obj, attr)


    def convert_collection_node(self, obj):
        attr = ['enabled', 'requires', 'provides', 'pref_manager']
        d = self.object_to_dict(obj, attr)
        return d


    def convert_processing_node(self, obj):
        attr = ['pref_manager', 'enabled']
        d = self.object_to_dict(obj, attr)
        return d


    def convert_preferencesmanager(self, obj):
        attr = ['pages', ]
        d = self.object_to_dict(obj, attr)
        return d


    def convert_custom_preferenceitem(self, obj):
        import inspect

        attr = ['name', 'value', 'label', 'default',
                'group', 'limit']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        arg = inspect.getargspec(obj.__init__)

        for cur_arg in arg.args:
            if cur_arg not in base_arg.args and cur_arg in attr:
                d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_preferenceitem(self, obj):
        import inspect

        #attr = ['name', 'value', 'label', 'default', 
        #        'group', 'limit', 'guiclass', 'gui_element']
        attr = ['name', 'value', 'label', 'default',
                'group', 'limit']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        arg = inspect.getargspec(obj.__init__)

        for cur_arg in arg.args:
            if cur_arg not in base_arg.args:
                d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_waveclient(self, obj):
        ignore_attr = ['project', 'logger', 'stock', 'stock_lock', 'preload_threads', 'waveformDirList', 'client']
        attr = [x for x in obj.__dict__.keys() if x not in ignore_attr]
        d = self.object_to_dict(obj, attr)
        return d


    def object_to_dict(self, obj, attr):
        ''' Copy selceted attributes of object to a dictionary.
        '''
        def hint_tuples(item):
            if isinstance(item, tuple):
                return {'__tuple__': True, 'items': item}
            if isinstance(item, list):
                return [hint_tuples(e) for e in item]
            else:
                return item

        d = {}
        for cur_attr in attr:
            d[cur_attr] = hint_tuples(getattr(obj, cur_attr))

        return d



class ProjectFileDecoder(json.JSONDecoder):

    def __init__(self, **kwarg):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)

    def convert_object(self, d):
        #print "Converting dict: %s." % str(d)

        if '__class__' in d:
            class_name = d.pop('__class__')
            module_name = d.pop('__module__')
            base_class = d.pop('__baseclass__')

            if class_name == 'Project':
                inst = self.convert_project(d)
            elif class_name == 'User':
                inst = self.convert_user(d)
            elif class_name == 'UTCDateTime':
                inst = self.convert_utcdatetime(d)
            elif class_name == 'Collection':
                inst = self.convert_collection(d)
            elif class_name == 'PreferencesManager':
                inst = self.convert_pref_manager(d)
            elif class_name == 'CustomPrefItem':
                inst = self.convert_custom_preferenceitem(d, class_name, module_name)
            elif class_name == 'type':
                inst = self.convert_class_object(d, class_name, module_name)
            elif 'CollectionNode' in base_class:
                inst = self.convert_collectionnode(d, class_name, module_name)
            elif 'PreferenceItem' in base_class:
                inst = self.convert_preferenceitem(d, class_name, module_name)
            elif 'WaveClient' in base_class:
                inst = self.convert_waveclient(d, class_name, module_name)
            elif 'ProcessingNode' in base_class:
                inst = self.convert_processing_node(d, class_name, module_name)
            else:
                inst = {'ERROR': 'MISSING CONVERTER'}

        else:
            inst = d

        return inst


    def decode_hinted_tuple(self, item):
        if isinstance(item, dict):
            if '__tuple__' in item:
                return tuple(item['items'])
        elif isinstance(item, list):
                return [self.decode_hinted_tuple(x) for x in item]
        else:
            return item


    def convert_project(self, d):
        inst = psysmon.core.project.Project(psybase = None,
                                            name = d['name'],
                                            user = d['user'],
                                            dbHost = d['dbHost'],
                                            dbName = d['dbName'],
                                            pkg_version = d['pkg_version'],
                                            db_version = d['db_version'],
                                            dbDriver = d['dbDriver'],
                                            dbDialect = d['dbDialect'],
                                            createTime = d['createTime']
                                            )

        inst.defaultWaveclient = d['defaultWaveclient']
        inst.scnlDataSources = d['scnlDataSources']
        inst.waveclient = d['waveclient']

        return inst


    def convert_user(self, d):
        inst = psysmon.core.project.User(user_name = d['name'],
                                         user_pwd = None,
                                         user_mode = d['mode'],
                                         author_name = d['author_name'],
                                         author_uri = d['author_uri'],
                                         agency_name = d['agency_name'],
                                         agency_uri = d['agency_uri']
                                         )
        inst.collection = d['collection']

        if d['activeCollection'] in inst.collection.keys():
            inst.activeCollection = inst.collection[d['activeCollection']]
        return inst


    def convert_utcdatetime(self, d):
        inst = UTCDateTime(d['utcdatetime'])
        return inst


    def convert_pref_manager(self, d):
        inst = psysmon.core.preferences_manager.PreferencesManager(pages = d['pages'])
        return inst

    def convert_collection(self, d):
        inst = psysmon.core.base.Collection(name = d['name'], nodes = d['nodes'])

        return inst


    def convert_class_object(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_


    def convert_collectionnode(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_processing_node(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_custom_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst


    def convert_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst


    def convert_waveclient(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst





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

