from abc import ABCMeta, abstractproperty


class GeoObject(metaclass=ABCMeta):
    @abstractproperty
    def __geo_interface__(self):
        return 0

    @classmethod
    def __subclasshook__(cls, C):
        if cls is GeoObject:
            if any("__geo_interface__" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented
