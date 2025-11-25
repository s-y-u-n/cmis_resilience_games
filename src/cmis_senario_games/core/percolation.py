from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .interdependency import InterdependentSystem


@dataclass
class PercolationParams:
    """
    Parameters for simple site percolation on the node set.
    """

    survival_prob: float
    random_seed: Optional[int] = None


def sample_initial_failure(system: InterdependentSystem, params: PercolationParams) -> np.ndarray:
    """
    Sample an initial alive/dead mask for nodes based on survival probability.

    Returns
    -------
    alive_mask : np.ndarray of shape (N,), bool
        True if the node survives the initial random failure.
    """
    num_nodes = system.network.num_nodes
    rng = np.random.default_rng(params.random_seed)
    return rng.random(num_nodes) < params.survival_prob

