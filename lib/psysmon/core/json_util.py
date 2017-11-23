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

''' JSON decoder and encoder.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import json
import logging

from obspy.core import UTCDateTime
import psysmon.core.util as util


# TODO: Add a File container holding the content of a json file. Use the file
# container to dump the file meta data using the Encoder.

class FileContainer(object):

    def __init__(self, data = {}):
        self.data = data


class ProjectFileEncoder(json.JSONEncoder):
    ''' A JSON encoder for the pSysmon project file.
    '''
    version = util.Version('1.0.0')

    def __init__(self, **kwarg):
        json.JSONEncoder.__init__(self, **kwarg)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # File format settings.
        self.indent = 4
        self.sort_keys = True


    def default(self, obj):
        ''' Convert pSysmon project objects to a dictionary.
        '''
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]
        #print 'Converting %s' % obj_class

        if obj_class == 'FileContainer':
            d = self.convert_filecontainer(obj)
        elif obj_class == 'Project':
            d = self.convert_project(obj)
        elif obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        elif obj_class == 'Version':
            d = self.convert_version(obj)
        elif obj_class == 'User':
            d = self.convert_user(obj)
        elif obj_class == 'Collection':
            d = self.convert_collection(obj)
        elif obj_class == 'PreferencesManager':
            d = self.convert_preferencesmanager(obj)
        elif obj_class == 'Page':
            d = self.convert_page(obj)
        elif obj_class == 'Group':
            d = self.convert_group(obj)
        elif obj_class == 'CustomPrefItem':
            d = self.convert_custom_preferenceitem(obj)
        elif obj_class == 'type':
            d = {}
        elif 'PreferenceItem' in base_class:
            d = self.convert_preferenceitem(obj)
        elif 'WaveClient' in base_class:
            d = self.convert_waveclient(obj)
        else:
            d = {'ERROR': 'MISSING CONVERTER for obj_class %s with base_class %s' % (str(obj_class), str(base_class))}

        # Add the class and module information to the dictionary.
        if obj_class != 'FileContainer':
            tmp = {'__baseclass__': base_class,
                   '__class__': obj.__class__.__name__,
                   '__module__': obj.__module__}
            d.update(tmp)

        return d


    def convert_filecontainer(self, obj):
        d = obj.data
        file_meta = {'file_version': self.version,
                     'save_date': UTCDateTime()}
        d['file_meta'] = file_meta
        return d


    def convert_project(self, obj):
        attr = ['name', 'dbDriver', 'dbDialect', 'dbHost',
                'dbName', 'pkg_version', 'db_version', 'createTime',
                'defaultWaveclient', 'scnlDataSources', 'user', 'waveclient',
                'db_table_version']
        d =  self.object_to_dict(obj, attr)
        return d


    def convert_utcdatetime(self, obj):
        return {'utcdatetime': obj.isoformat()}


    def convert_version(self, obj):
        return {'version': str(obj)}


    def convert_user(self, obj):
        attr = ['name', 'mode', 'author_name', 'author_uri',
                'agency_name', 'agency_uri']
        d = self.object_to_dict(obj, attr)
        if obj.activeCollection is None:
            d['activeCollection'] = None
        else:
            d['activeCollection'] = obj.activeCollection.name

        # Only the collection names are saved. The collection itself is written
        # to a separate json file.
        d['collection_names'] = sorted(obj.collection.keys())

        return d


    def convert_preferencesmanager(self, obj):
        attr = ['pages', ]
        d = self.object_to_dict(obj, attr)
        return d


    def convert_page(self, obj):
        attr = ['name', 'groups']
        d =self.object_to_dict(obj, attr)
        return d


    def convert_group(self, obj):
        attr = ['name', 'items']
        d =self.object_to_dict(obj, attr)
        return d


    def convert_custom_preferenceitem(self, obj):
        import inspect

        attr = ['name', 'value', 'label', 'default',
                'limit']
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
                'limit']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        arg = inspect.getargspec(obj.__init__)

        for cur_arg in arg.args:
            if cur_arg not in base_arg.args:
                d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_waveclient(self, obj):
        ignore_attr = ['project', 'logger', 'stock', 'stock_lock', 'stock_data_gaps', 'preload_threads', 'waveformDirList', 'client']
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


class ProjectFileDecoder_0_0_0(json.JSONDecoder):

    version = util.Version('0.0.0')

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
            elif class_name == 'Page':
                inst = self.convert_page(d)
            elif class_name == 'Group':
                inst = self.convert_group(d)
            elif class_name == 'CustomPrefItem':
                inst = self.convert_custom_preferenceitem(d, class_name, module_name)
            elif class_name == 'type':
                inst = self.convert_class_object(d, class_name, module_name)
            elif 'CollectionNode' in base_class:
                inst = self.convert_collectionnode(d, class_name, module_name)
            elif 'LooperCollectionNode' in base_class:
                inst = self.convert_looper_collection_node(d, class_name, module_name)
            elif 'LooperCollectionChildNode' in base_class:
                inst = self.convert_looper_collection_child_node(d, class_name, module_name)
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
        import psysmon.core.project
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
        import psysmon.core.project
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
        import psysmon.core.preferences_manager

        inst = psysmon.core.preferences_manager.PreferencesManager(pages = d['pages'])
        return inst


    def convert_page(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Page(name = d['name'], groups = d['groups'])
        return inst


    def convert_group(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Group(name = d['name'], items = d['items'])
        return inst


    def convert_collection(self, d):
        import psysmon.core.preferences_manager
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


    def convert_looper_collection_node(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_looper_collection_child_node(self, d, class_name, module_name):
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

        # 2016-12-15: Handle the change of the preference_manager classes.
        if 'group' in args.keys():
            del args['group']

        inst = class_(**args)
        return inst


    def convert_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())

        # 2016-12-15: Handle the change of the preference_manager classes.
        if 'group' in args.keys():
            del args['group']

        inst = class_(**args)
        return inst


    def convert_waveclient(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst




class ProjectFileDecoder_1_0_0(json.JSONDecoder):
    version = util.Version('1.0.0')

    def __init__(self, **kwarg):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)


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
            elif class_name == 'Page':
                inst = self.convert_page(d)
            elif class_name == 'Group':
                inst = self.convert_group(d)
            elif class_name == 'CustomPrefItem':
                inst = self.convert_custom_preferenceitem(d, class_name, module_name)
            elif class_name == 'Version':
                inst = self.convert_version(d)
            elif class_name == 'type':
                inst = self.convert_class_object(d, class_name, module_name)
            elif 'CollectionNode' in base_class:
                inst = self.convert_collectionnode(d, class_name, module_name)
            elif 'LooperCollectionNode' in base_class:
                inst = self.convert_looper_collection_node(d, class_name, module_name)
            elif 'LooperCollectionChildNode' in base_class:
                inst = self.convert_looper_collection_child_node(d, class_name, module_name)
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
        import psysmon.core.project
        inst = psysmon.core.project.Project(psybase = None,
                                            name = d['name'],
                                            user = d['user'],
                                            dbHost = d['dbHost'],
                                            dbName = d['dbName'],
                                            pkg_version = d['pkg_version'],
                                            db_table_version = d['db_table_version'],
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
        import psysmon.core.project
        inst = psysmon.core.project.User(user_name = d['name'],
                                         user_pwd = None,
                                         user_mode = d['mode'],
                                         author_name = d['author_name'],
                                         author_uri = d['author_uri'],
                                         agency_name = d['agency_name'],
                                         agency_uri = d['agency_uri']
                                         )
        # TODO: Load the collections from the collection files.
        #inst.collection = d['collection']
        inst.collection_names = d['collection_names']
        inst.active_collection_name = d['activeCollection']

        if d['activeCollection'] in inst.collection.keys():
            inst.activeCollection = inst.collection[d['activeCollection']]
        return inst


    def convert_utcdatetime(self, d):
        inst = UTCDateTime(d['utcdatetime'])
        return inst


    def convert_version(self, d):
        inst = util.Version(d['version'])
        return inst


    def convert_pref_manager(self, d):
        import psysmon.core.preferences_manager

        inst = psysmon.core.preferences_manager.PreferencesManager(pages = d['pages'])
        return inst


    def convert_page(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Page(name = d['name'], groups = d['groups'])
        return inst


    def convert_group(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Group(name = d['name'], items = d['items'])
        return inst


    def convert_collection(self, d):
        import psysmon.core.preferences_manager
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


    def convert_looper_collection_node(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_looper_collection_child_node(self, d, class_name, module_name):
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

        # 2016-12-15: Handle the change of the preference_manager classes.
        if 'group' in args.keys():
            del args['group']

        inst = class_(**args)
        return inst


    def convert_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())

        # 2016-12-15: Handle the change of the preference_manager classes.
        if 'group' in args.keys():
            del args['group']

        inst = class_(**args)
        return inst


    def convert_waveclient(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst





class ConfigFileEncoder(json.JSONEncoder):
    ''' A JSON encoder for the pSysmon project file.
    '''
    version = util.Version('1.0.0')

    def __init__(self, **kwarg):
        json.JSONEncoder.__init__(self, **kwarg)
        self.indent = 4
        self.sort_keys = True


    def default(self, obj):
        ''' Convert pSysmon project objects to a dictionary.
        '''
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]

        if obj_class == 'FileContainer':
            d = self.convert_filecontainer(obj)
        elif obj_class == 'Version':
            d = self.convert_version(obj)
        elif obj_class == 'PreferencesManager':
            d = self.convert_preferencesmanager(obj)
        elif obj_class == 'Page':
            d = self.convert_page(obj)
        elif obj_class == 'Group':
            d = self.convert_group(obj)
        elif obj_class == 'CustomPrefItem':
            d = self.convert_custom_preferenceitem(obj)
        elif obj_class == 'type':
            d = {}
        elif 'PreferenceItem' in base_class:
            d = self.convert_preferenceitem(obj)
        elif obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        else:
            d = {'ERROR': 'MISSING CONVERTER for obj_class %s with base_class %s' % (str(obj_class), str(base_class))}

        # Add the class and module information to the dictionary.
        if obj_class != 'FileContainer':
            tmp = {'__baseclass__': base_class,
                   '__class__': obj.__class__.__name__,
                   '__module__': obj.__module__}
            d.update(tmp)

        return d

    def convert_filecontainer(self, obj):
        d = obj.data
        file_meta = {'file_version': self.version,
                     'save_date': UTCDateTime()}
        d['file_meta'] = file_meta
        return d

    def convert_version(self, obj):
        return {'version': str(obj)}

    def convert_preferencesmanager(self, obj):
        attr = ['pages', ]
        d = self.object_to_dict(obj, attr)
        return d


    def convert_page(self, obj):
        attr = ['name', 'groups']
        d =self.object_to_dict(obj, attr)
        return d


    def convert_group(self, obj):
        attr = ['name', 'items']
        d =self.object_to_dict(obj, attr)
        return d


    def convert_custom_preferenceitem(self, obj):
        import inspect

        attr = ['name', 'value', 'label', 'default',
                'limit']
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
                'limit']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        arg = inspect.getargspec(obj.__init__)

        for cur_arg in arg.args:
            if cur_arg not in base_arg.args:
                d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_utcdatetime(self, obj):
        return {'utcdatetime': obj.isoformat()}


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


class ConfigFileDecoder_1_0_0(json.JSONDecoder):
    version = util.Version('1.0.0')

    def __init__(self, **kwarg):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)


    def convert_object(self, d):
        #print "Converting dict: %s." % str(d)

        if '__class__' in d:
            class_name = d.pop('__class__')
            module_name = d.pop('__module__')
            base_class = d.pop('__baseclass__')

            if class_name == 'PreferencesManager':
                inst = self.convert_pref_manager(d)
            elif class_name == 'Version':
                inst = self.convert_version(d)
            elif class_name == 'Page':
                inst = self.convert_page(d)
            elif class_name == 'Group':
                inst = self.convert_group(d)
            elif class_name == 'CustomPrefItem':
                inst = self.convert_custom_preferenceitem(d, class_name, module_name)
            elif class_name == 'type':
                inst = self.convert_class_object(d, class_name, module_name)
            elif 'PreferenceItem' in base_class:
                inst = self.convert_preferenceitem(d, class_name, module_name)
            elif class_name == 'UTCDateTime':
                inst = self.convert_utcdatetime(d)
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

    def convert_version(self, d):
        inst = util.Version(d['version'])
        return inst

    def convert_pref_manager(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.PreferencesManager(pages = d['pages'])
        return inst


    def convert_page(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Page(name = d['name'], groups = d['groups'])
        return inst


    def convert_group(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Group(name = d['name'], items = d['items'])
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


    def convert_utcdatetime(self, d):
        inst = UTCDateTime(d['utcdatetime'])
        return inst




class CollectionFileEncoder(json.JSONEncoder):
    ''' A JSON encoder for the pSysmon collection file.
    '''
    def __init__(self, **kwarg):
        json.JSONEncoder.__init__(self, **kwarg)
        self.indent = 4
        self.sort_keys = True

    def default(self, obj):
        ''' Convert pSysmon collection objects to a dictionary.
        '''
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]
        #print 'Converting %s' % obj_class

        if obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        elif obj_class == 'Collection':
            d = self.convert_collection(obj)
        elif 'CollectionNode' in base_class:
            d = self.convert_collection_node(obj)
        elif 'LooperCollectionNode' in base_class:
            d = self.convert_looper_collection_node(obj)
        elif 'LooperCollectionChildNode' in base_class:
            d = self.convert_looper_collection_child_node(obj)
        elif obj_class == 'PreferencesManager':
            d = self.convert_preferencesmanager(obj)
        elif obj_class == 'Page':
            d = self.convert_page(obj)
        elif obj_class == 'Group':
            d = self.convert_group(obj)
        elif obj_class == 'CustomPrefItem':
            d = self.convert_custom_preferenceitem(obj)
        elif obj_class == 'type':
            d = {}
        elif 'PreferenceItem' in base_class:
            d = self.convert_preferenceitem(obj)
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


    def convert_collection(self, obj):
        attr = ['name', 'nodes']
        return self.object_to_dict(obj, attr)


    def convert_collection_node(self, obj):
        attr = ['enabled', 'requires', 'provides', 'pref_manager']
        d = self.object_to_dict(obj, attr)
        return d


    def convert_looper_collection_node(self, obj):
        attr = ['enabled', 'requires', 'provides', 'pref_manager', 'children']
        d = self.object_to_dict(obj, attr)
        return d


    def convert_looper_collection_child_node(self, obj):
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


    def convert_page(self, obj):
        attr = ['name', 'groups']
        d =self.object_to_dict(obj, attr)
        return d


    def convert_group(self, obj):
        attr = ['name', 'items']
        d =self.object_to_dict(obj, attr)
        return d


    def convert_custom_preferenceitem(self, obj):
        #import inspect

        attr = ['name', 'value', 'label', 'default']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        #base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        #arg = inspect.getargspec(obj.__init__)

        #for cur_arg in arg.args:
        #    if cur_arg not in base_arg.args and cur_arg in attr:
        #        d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_preferenceitem(self, obj):
        #import inspect

        #attr = ['name', 'value', 'label', 'default',
        #        'limit']
        attr = ['name', 'value', 'tool_tip']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        #base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        #arg = inspect.getargspec(obj.__init__)

        #for cur_arg in arg.args:
        #    if cur_arg not in base_arg.args:
        #        d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_waveclient(self, obj):
        ignore_attr = ['project', 'logger', 'stock', 'stock_lock', 'stock_data_gaps', 'preload_threads', 'waveformDirList', 'client']
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


class CollectionFileDecoder(json.JSONDecoder):

    def __init__(self, **kwarg):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)

    def convert_object(self, d):
        #print "Converting dict: %s." % str(d)

        if '__class__' in d:
            class_name = d.pop('__class__')
            module_name = d.pop('__module__')
            base_class = d.pop('__baseclass__')

            if class_name == 'UTCDateTime':
                inst = self.convert_utcdatetime(d)
            elif class_name == 'Collection':
                inst = self.convert_collection(d)
            elif class_name == 'PreferencesManager':
                inst = self.convert_pref_manager(d)
            elif class_name == 'Page':
                inst = self.convert_page(d)
            elif class_name == 'Group':
                inst = self.convert_group(d)
            elif class_name == 'CustomPrefItem':
                inst = self.convert_custom_preferenceitem(d, class_name, module_name)
            elif class_name == 'type':
                inst = self.convert_class_object(d, class_name, module_name)
            elif 'CollectionNode' in base_class:
                inst = self.convert_collectionnode(d, class_name, module_name)
            elif 'LooperCollectionNode' in base_class:
                inst = self.convert_looper_collection_node(d, class_name, module_name)
            elif 'LooperCollectionChildNode' in base_class:
                inst = self.convert_looper_collection_child_node(d, class_name, module_name)
            elif 'PreferenceItem' in base_class:
                inst = self.convert_preferenceitem(d, class_name, module_name)
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


    def convert_utcdatetime(self, d):
        inst = UTCDateTime(d['utcdatetime'])
        return inst


    def convert_pref_manager(self, d):
        import psysmon.core.preferences_manager

        inst = psysmon.core.preferences_manager.PreferencesManager(pages = d['pages'])
        return inst


    def convert_page(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Page(name = d['name'], groups = d['groups'])
        return inst


    def convert_group(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.Group(name = d['name'], items = d['items'])
        return inst


    def convert_collection(self, d):
        import psysmon.core.preferences_manager
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


    def convert_looper_collection_node(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_looper_collection_child_node(self, d, class_name, module_name):
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

        # 2016-12-15: Handle the change of the preference_manager classes.
        if 'group' in args.keys():
            del args['group']

        inst = class_(**args)
        return inst


    def convert_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())

        # 2016-12-15: Handle the change of the preference_manager classes.
        if 'group' in args.keys():
            del args['group']

        inst = class_(**args)
        return inst


def get_project_decoder(version):
    ''' Get the correct json decoder based on the version.
    '''
    decoder = {}
    decoder['0.0.0'] = ProjectFileDecoder_0_0_0
    decoder['1.0.0'] = ProjectFileDecoder_1_0_0

    return decoder[str(version)]


def get_config_decoder(version):
    ''' Get the correct config file json decoder based on the version.
    '''
    decoder = {}
    decoder['0.0.0'] = ConfigFileDecoder_1_0_0
    decoder['1.0.0'] = ConfigFileDecoder_1_0_0

    return decoder[str(version)]


def get_file_meta(filename):
    ''' Extract the file metadata from a json file.
    '''
    with open(filename, 'r') as fid:
        container_data = json.load(fid)

    if container_data.has_key('file_meta'):
        # The project file has a meta data dictionary. Use it to select the
        # correct project file decoder.
        file_meta = container_data['file_meta']
        file_meta = {'file_version': util.Version(container_data['file_meta']['file_version']['version']),
                     'save_date': UTCDateTime(container_data['file_meta']['save_date']['utcdatetime'])}
    else:
        # This is an old project file version with no meta data dictionary.
        # Create a default meta data.
        file_meta = {'file_version': util.Version('0.0.0'),
                     'save_date': '1970-01-01T00:00:00'}

    return file_meta

