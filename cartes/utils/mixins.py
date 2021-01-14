from typing import Iterator, List, Tuple

import pandas as pd


class HTMLMixin:
    """Base class for HTML repr mixins.

    It may look vain, but it terminates the super()._repr_html_() cascade.
    """

    def _repr_html_(self) -> str:
        return ""


class HTMLTitleMixin(HTMLMixin):
    """A Mixin class to have the name of the class in the HTML repr."""

    def _repr_html_(self):
        return f"<h2>{type(self).__name__}</h2>" + super()._repr_html_()


class HTMLAttrMixin(HTMLMixin):
    """A Mixin class to build a table of attributes in the HTML repr.

    Classes using this Mixin should override the html_attr_list as an attribute
    or a property.
    """

    html_attr_list: List[str] = []

    def _expand_view(self) -> Iterator[Tuple[str, str]]:
        for key in self.html_attr_list:
            value = getattr(self, key, None)
            if value is None:
                continue
            if isinstance(value, list):
                for idx, v_ in enumerate(value):
                    yield key + f"_{idx}", v_
            elif isinstance(value, dict):
                yield from value.items()
            else:
                yield key, value

    def _attr_view(self) -> pd.DataFrame:
        return pd.DataFrame.from_records(  # one-trick poney
            [dict(elt for elt in self._expand_view())]
        ).T.rename(columns={0: ""})

    def _repr_html_(self):
        return (
            "<div style='float: left;'>"
            + self._attr_view()._repr_html_()
            + "</div>"
            + super()._repr_html_()
        )


class _HBox(object):
    def __init__(self, *args):
        self.elts = args

    def _repr_html_(self):
        return "".join(
            f"""
    <div style='
        margin: 1ex;
        min-width: 250px;
        max-width: 300px;
        display: inline-block;
        vertical-align: top;'>
        {elt._repr_html_()}
    </div>
    """
            for elt in self.elts
        )

    def __or__(self, other) -> "_HBox":
        if isinstance(other, _HBox):
            return _HBox(*self.elts, *other.elts)
        else:
            return _HBox(*self.elts, other)

    def __ror__(self, other) -> "_HBox":
        if isinstance(other, _HBox):
            return _HBox(*other.elts, *self.elts)
        else:
            return _HBox(other, *self.elts)


class HBoxMixin(object):
    """Enables a | operator for placing representations next to each other."""

    def __or__(self, other) -> _HBox:
        if isinstance(other, _HBox):
            return _HBox(self, *other.elts)
        else:
            return _HBox(self, other)
