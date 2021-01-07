from pathlib import Path

from shapely.geometry import MultiPolygon, Polygon, base, polygon


class Descriptor:
    def __set_name__(self, obj, name):
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, path):
        setattr(obj, self.private_name, path)


class DirectoryCreateIfNotExists(Descriptor):
    def __set__(self, obj, path):
        if isinstance(path, str):
            path = Path(path)
        if path.exists() and not path.is_dir():
            raise RuntimeError(f"{path} exists and is not a directory")
        if not path.exists():
            path.mkdir(parents=True)
        setattr(obj, self.private_name, path)


def reorient(shape: base.BaseGeometry, orientation=-1) -> base.BaseGeometry:
    if isinstance(shape, Polygon):
        return polygon.orient(shape, orientation)
    if isinstance(shape, MultiPolygon):
        return MultiPolygon(reorient(p) for p in shape)
    return shape


class OrientedShape(Descriptor):
    def __set__(self, obj, shape):
        setattr(obj, self.private_name, reorient(shape, orientation=-1))
