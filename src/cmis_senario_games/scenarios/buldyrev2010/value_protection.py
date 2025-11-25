from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...core.cascade_engine import run_cascade
from ...core.interdependency import InterdependentSystem
from ...core.percolation import PercolationParams, sample_initial_failure
from ...core.value_functions import GameType, ValueFunction


@dataclass
class BuldyrevProtectionConfig:
    """
    Configuration for Buldyrev-style protection games.
    """

    percolation: PercolationParams
    num_scenarios: int
    performance_metric: str = "mcgc_size"


class BuldyrevProtectionValue(ValueFunction):
    """
    Value function v(S) for Buldyrev2010 protection games.
    """

    game_type = GameType.PROTECTION

    def __init__(self, system: InterdependentSystem, config: BuldyrevProtectionConfig):
        self.system = system
        self.config = config

    def evaluate(self, coalition: np.ndarray) -> float:
        """
        Estimate v(S) = E[F_S(omega)] by Monte Carlo.

        coalition[i] = True means node i is protected and always survives
        the initial percolation step.
        """
        total = 0.0
        for _ in range(self.config.num_scenarios):
            alive0 = sample_initial_failure(self.system, self.config.percolation)
            alive0[coalition] = True  # protection
            result = run_cascade(self.system, alive0)
            total += result.m_infty
        return total / float(self.config.num_scenarios)

