from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GmpeParam:
    """GMPE パラメータ。

    a, b, c, d, h: 論文の式に対応する係数。
    sigma_inter: between-event 標準偏差 (η)。
    sigma_intra: within-event 標準偏差 (ε)。
    """

    a: float
    b: float
    c: float
    d: float
    h: float
    sigma_inter: float
    sigma_intra: float


@dataclass
class HazardScenario:
    """ハザードシナリオ（単一地震イベント）。"""

    magnitude: float
    epicenter_x: float
    epicenter_y: float
    annual_rate: float

