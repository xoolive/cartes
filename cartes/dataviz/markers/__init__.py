import json
from pathlib import Path

import numpy as np
from matplotlib import path

current_dir = Path(__file__).parent
__all__ = list(p.stem for p in current_dir.glob("*.json"))


def __getattr__(name: str) -> path.Path:
    file_path = current_dir / (name + ".json")
    if file_path.exists():
        data = json.loads(file_path.read_text())
        return path.Path(
            vertices=data["vertices"], codes=np.array(data["codes"], np.uint8)
        )

    raise AttributeError(
        f"No {name}.json file found in {current_dir.absolute()}."
    )
