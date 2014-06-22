"""
Extended data storage functionality for python.
"""

from functools import reduce
from types import FunctionType
from itertools import product

class array:
    """
    N dimensional array data structure. Includes options for building contents
    programatically.
    """
    
    def __init__(self, *shape, build=None,\
                 buildLinear=False, ignoreIterable=False):        
        self.degree = len(shape)
        self.shape = shape
        self.length = reduce(lambda a,b:a*b,shape)        
        self._populate(self.length, self.shape, build, buildLinear, ignoreIterable)

    def _populate(self, length, shape, build, buildLinear, ignoreIterable):
        # populate by function
        if isinstance(build, FunctionType):
            # gives function single indeces
            if buildLinear:
                self.data = [ build(i) for i in range(length) ]
            # gives function coordinates
            else:
                self.data = [ build(*reversed(point)) for point in\
                              product(*( range(n) for n in shape )) ]
        # populate by iterable
        elif hasattr(build, '__iter__') and not ignoreIterable:
            self.data = [ i for i in build ]
        # populate by build value
        else:
            self.data = [build]*length            

    def __len__(self):
        return self.length

    def __iter__(self):
        return iter(self.data)

    def itercoords(self):
        return iter(product(*( range(n) for n in self.shape )))

    def _findKey(self, key):
        # get by single linear index
        if isinstance(key, int):
            return index

        # get by a coordinate sequence
        elif hasattr(key,'__iter__') and hasattr(key,'__len__')\
             and len(key) == self.degree:
            size = self.length
            index = 0
            for d, n in reversed(tuple(zip(self.shape, key))):
                if n+1>d:
                    raise IndexError("Array index request {} out of range"\
                                     .format(n))
                size //= d
                index += size*n
            return index
        else:
            raise TypeError
        pass 

    def __getitem__(self, key):
        return self.data[self._findKey(key)]

    def __setitem__(self, key, value):
        self.data[self._findKey(key)] = value

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return str(self)
