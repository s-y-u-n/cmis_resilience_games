from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .network_model import MultiLayerNetwork


@dataclass
class DependencyMapping:
    """
    Mapping of inter-layer dependencies.

    Buldyrev2010 assumes 1:1 bidirectional dependence between two layers A, B:
      dep_A_to_B[i] = j   (node i in layer A depends on node j in layer B)
      dep_B_to_A[j] = i
    """

    dep_A_to_B: np.ndarray
    dep_B_to_A: np.ndarray


@dataclass
class InterdependentSystem:
    """
    Interdependent multi-layer system: network + dependency mapping.
    """

    network: MultiLayerNetwork
    dependency: DependencyMapping

