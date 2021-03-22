import logging
import re
from abc import ABC, abstractmethod
from numbers import Real
from typing import Any, Dict, List, Mapping, Optional, Union

from .. import Nominatim

QueryType = Union[bool, int, str, List, Mapping[str, Any]]


class Generator(ABC):
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, obj, objtype=None) -> str:
        elt = getattr(obj, self.private_name, None)
        if elt is None:
            return ""
        return self.generate(elt, obj)

    def __set__(self, obj, value):
        if value is not None:
            value = self.transform(value)
            self.validate(value)
        setattr(obj, self.private_name, value)

    def transform(self, value) -> Any:
        return value

    @abstractmethod
    def validate(self, value):
        pass

    @abstractmethod
    def generate(self, elt, obj) -> str:
        pass


def expand(key: str, value: Union[bool, str, Dict[str, str]]):
    if not re.match(r"^[\w\d_]+$", key):
        key = f'"{key}"'
    if isinstance(value, bool):
        return f"[{key}]"
    if isinstance(value, Real):
        return f"[{key}={value}]"
    if isinstance(value, str):
        if not re.match(r"^[\w\d_]+$", value):
            value = f'"{value}"'
        return f"[{key}={value}]"
    if "regex" in value:
        value = value["regex"]
        return f'[{key}~"{value}"]'
    raise ValueError(f"Unknown elements in area dictionary {value}")


class Area(Generator):
    def transform(self, value):
        if isinstance(value, str):
            value = Nominatim.search(value)
        return value

    def validate(self, value):
        if isinstance(value, Nominatim):
            return
        if not (isinstance(value, dict)):
            msg = "The area parameter must be a dictionary or a Nominatim"
            raise TypeError(msg)
        for elt in value.values():
            if not any(isinstance(elt, t) for t in [Real, str, dict]):
                raise TypeError(
                    "All values in the area dictionary must be either "
                    "numeric, str or a dict[str, str]"
                )

    def generate(self, elt, obj) -> str:
        res = ";"
        if isinstance(elt, dict):
            if "as_" in elt:
                res = f"->.{elt['as_']};"
                del elt["as_"]
            return (
                "area"
                + "".join(expand(key, value) for key, value in elt.items())
                + res
            )
        elif isinstance(elt, Nominatim):
            type_ = elt.json["osm_type"]
            if type_ == "relation":
                type_ = "rel"
            return f"{type_}(id:{elt.json['osm_id']});map_to_area" + res
        msg = "The area parameter must be a dictionary or a Nominatim"
        raise TypeError(msg)


class Bounds(Generator):
    def transform(self, value):
        if hasattr(value, "shape"):
            value = value.shape.bounds
        return value

    def validate(self, value):
        try:
            west, south, east, north = value
            assert all(isinstance(x, Real) for x in value)
        except Exception as exc:
            logging.warning(exc)
            raise TypeError(
                "The bounds attribute must be a shape object or "
                "a tuple of four float (west, south, east, north)"
            )

    def generate(self, value, obj) -> str:
        west, south, east, north = value
        return f"[bbox:{south},{west},{north},{east}]"


class NodeWayRel(Generator):
    def transform(self, value):
        if isinstance(value, dict):
            if not any(x in value for x in ["node", "way", "rel", "nwr"]):
                value = dict(nwr=value)
            value = [value]
        return value

    def validate(self, value):
        pass

    def generate(self, value, obj) -> str:
        return "".join(self.generate_single(elt, obj) for elt in value)

    def generate_single(self, elt, obj) -> str:
        for res, elt in elt.items():
            break
        # Particular situation of pivot relations
        if list(elt.keys()) == ["area"]:
            if elt["area"] is True:
                res += "(pivot);out geom;"
            else:
                res += f"(pivot.{elt['area']});out geom;"
            return res
        if getattr(obj, "_area", None) is not None:
            area_name = elt.get("area", None)
            if area_name:
                del elt["area"]
                res += f"(area.{area_name})"
            else:
                res += "(area)"
        if "around" in elt:
            res += f"(around:{elt['around']})"
            del elt["around"]
        res += "".join(expand(key, value) for key, value in elt.items())
        res += ";out geom;"
        return res


def make_querytype(
    values: Optional[QueryType] = None, key="nwr"
) -> List[QueryType]:
    if values is None:
        return []
    if isinstance(values, list):
        return list(
            (
                {key: elt}
                if not any(
                    x in elt.keys() for x in ["node", "way", "rel", "nwr"]
                )
                else elt
            )
            for elt in values
        )
    else:
        return [{key: values}]


class Query:
    area = Area()
    bounds = Bounds()
    nwr = NodeWayRel()

    def __init__(
        self,
        *,
        out: str = "json",
        timeout: int = 180,
        **kwargs: QueryType,
    ) -> None:
        self.out = out
        self.timeout = timeout
        self.area = kwargs.get("area", None)
        self.bounds = kwargs.get("bounds", None)

        node = make_querytype(kwargs.get("node", None), "node")
        way = make_querytype(kwargs.get("way", None), "way")
        rel = make_querytype(kwargs.get("rel", None), "rel")
        nwr = make_querytype(kwargs.get("nwr", None), "nwr")

        kwargs = dict(
            (key, value)
            for key, value in kwargs.items()
            if key not in ["area", "bounds", "node", "way", "rel", "nwr"]
        )
        if len(kwargs):
            nwr.append(dict(nwr=kwargs))

        self.nwr = nwr + node + way + rel

    def generate(self) -> str:
        res = f"[out:{self.out}][timeout:{self.timeout}]{self.bounds};"
        res += f"{self.area}"
        res += f"{self.nwr}"
        return res
