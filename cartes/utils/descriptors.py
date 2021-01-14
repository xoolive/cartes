from pathlib import Path
from typing import Generic, TypeVar, Union

from shapely.geometry.base import BaseGeometry

from .geometry import reorient

T = TypeVar("T")


class Descriptor(Generic[T]):
    def __set_name__(self, obj, name: str) -> None:
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, obj, cls=None) -> T:
        return getattr(obj, self.private_name)

    def __set__(self, obj, value: T) -> None:
        setattr(obj, self.private_name, value)


class DirectoryCreateIfNotExists(Descriptor[Path]):
    def __set__(self, obj, path: Union[str, Path]) -> None:
        if isinstance(path, str):
            path = Path(path)
        if path.exists() and not path.is_dir():
            raise RuntimeError(f"{path} exists and is not a directory")
        if not path.exists():
            path.mkdir(parents=True)
        setattr(obj, self.private_name, path)


class OrientedShape(Descriptor[BaseGeometry]):
    """Ensures the given shape is properly oriented for Altair.

    Reference: https://altair-viz.github.io/user_guide/data.html?highlight=orient%20transform#winding-order
    """

    def __set__(self, obj, shape: BaseGeometry):
        setattr(obj, self.private_name, reorient(shape, orientation=-1))
