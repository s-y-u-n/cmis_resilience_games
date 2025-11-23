from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReinforcementModel:
    """ノード補強モデル。

    alpha_factor: median capacity の倍率 c_α (> 1 を想定)。
    beta_factor: log 標準偏差の倍率 c_β (0 < c_β <= 1 を想定)。
    """

    alpha_factor: float = 1.0
    beta_factor: float = 1.0

