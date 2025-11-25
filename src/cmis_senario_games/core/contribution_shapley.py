from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .value_functions import ValueFunction


@dataclass
class ShapleyConfig:
    """
    Configuration for Monte Carlo Shapley value estimation.
    """

    num_samples: int
    random_seed: Optional[int] = None


def estimate_shapley(value_fn: ValueFunction, num_players: int, config: ShapleyConfig) -> np.ndarray:
    """
    Estimate Shapley values by Monte Carlo permutation sampling.

    Parameters
    ----------
    value_fn : ValueFunction
        Cooperative-game characteristic function.
    num_players : int
        Number of players.
    config : ShapleyConfig
        Sampling configuration.

    Returns
    -------
    np.ndarray of shape (num_players,)
        Approximated Shapley value for each player.
    """
    rng = np.random.default_rng(config.random_seed)
    phi = np.zeros(num_players, dtype=float)

    for _ in range(config.num_samples):
        order = rng.permutation(num_players)
        coalition = np.zeros(num_players, dtype=bool)

        # Value for empty coalition
        v_prev = value_fn.evaluate(coalition)

        for i in order:
            coalition[i] = True
            v_new = value_fn.evaluate(coalition)
            phi[i] += v_new - v_prev
            v_prev = v_new

    return phi / float(config.num_samples)

