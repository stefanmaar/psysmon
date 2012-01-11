


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


class PsysmonError(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    

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
