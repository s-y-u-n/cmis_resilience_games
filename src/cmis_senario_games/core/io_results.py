from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from .value_functions import GameType


@dataclass
class ValueResult:
    """
    Single v(S) evaluation result.
    """

    game_type: GameType
    scenario_name: str
    coalition_id: str
    coalition_mask: np.ndarray
    v_value: float


def value_results_to_dataframe(results: Sequence[ValueResult]) -> pd.DataFrame:
    """
    Convert a sequence of ValueResult objects into a pandas DataFrame.
    """
    rows = []
    for r in results:
        row = asdict(r)
        # Store coalition_mask as a boolean array; the exact serialization
        # strategy (e.g. list vs. bitstring) can be revisited later.
        row["coalition_mask"] = r.coalition_mask.astype(bool)
        rows.append(row)
    return pd.DataFrame(rows)


def save_value_results_parquet(results: Sequence[ValueResult], path: str | Path) -> None:
    """
    Save value results to a Parquet file.
    """
    df = value_results_to_dataframe(results)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p)


def save_value_results_csv(results: Sequence[ValueResult], path: str | Path) -> None:
    """
    Save value results to a CSV file.
    """
    df = value_results_to_dataframe(results)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)

