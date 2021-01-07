from typing import Iterator, List, Tuple

import pandas as pd


class HTMLMixin:
    def _repr_html_(self) -> str:
        return ""


class HTMLTitleMixin(HTMLMixin):
    def _repr_html_(self):
        return f"<h2>{type(self).__name__}</h2>" + super()._repr_html_()


class HTMLAttrMixin(HTMLMixin):
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
