from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

from .fragility import FragilityParam
from .graph import Graph
from .hazard import GmpeParam, HazardScenario
from .reinforcement import ReinforcementModel
from .simulation import SimulationConfig, estimate_system_failure_probability


@dataclass
class ResilienceGame:
    """レジリエンス協力ゲーム。

    v(S) = P_sys(∅) - P_sys(S) を特性関数とする。
    """

    graph: Graph
    base_frag_params: Dict[int, FragilityParam]
    hazard: HazardScenario
    gmpe: GmpeParam
    reinforce: ReinforcementModel
    config: SimulationConfig

    def __post_init__(self) -> None:
        """ベースライン P_sys(∅) を事前計算する。"""
        self._P_sys_empty = estimate_system_failure_probability(
            coalition_S=set(),
            graph=self.graph,
            base_frag_params=self.base_frag_params,
            hazard=self.hazard,
            gmpe=self.gmpe,
            reinforce=ReinforcementModel(alpha_factor=1.0, beta_factor=1.0),
            config=self.config,
        )

    @property
    def baseline_failure_probability(self) -> float:
        """補強なし状態のシステム失敗確率 P_sys(∅)。"""
        return self._P_sys_empty

    def payoff(self, coalition_S: Set[int]) -> float:
        """特性関数 v(S) = P_sys(∅) - P_sys(S) を返す。"""
        p_sys_s = estimate_system_failure_probability(
            coalition_S=coalition_S,
            graph=self.graph,
            base_frag_params=self.base_frag_params,
            hazard=self.hazard,
            gmpe=self.gmpe,
            reinforce=self.reinforce,
            config=self.config,
        )
        return self._P_sys_empty - p_sys_s

