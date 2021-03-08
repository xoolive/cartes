import json
from pathlib import Path
from typing import Any, Dict, Union

from . import markers

__all__ = ["matplotlib_style", "markers"]

matplotlib_style: Dict[str, Dict[str, Union[str, Any]]] = json.loads(
    (Path(__file__).parent / "matplotlib_style.json").read_text()
)

for _, value in matplotlib_style.items():
    if "marker" in value.keys():
        value["marker"] = getattr(markers, value["marker"])
