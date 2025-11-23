from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FragilityParam:
    """ノードの fragility パラメータ。

    alpha: median capacity
    beta: log-standard deviation
    """

    node_id: int
    alpha: float
    beta: float

