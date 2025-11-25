from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np


@dataclass
class NetworkLayer:
    """
    Single-layer network description.

    Nodes are assumed to be indexed 0..num_nodes-1.
    Edges are stored as an array of shape (m, 2) with integer node IDs.
    """

    name: str
    num_nodes: int
    edges: np.ndarray
    degree_distribution: Optional[np.ndarray] = None


@dataclass
class MultiLayerNetwork:
    """
    Multi-layer network where each layer shares the same node ID space.
    """

    layers: Dict[str, NetworkLayer]

    @property
    def num_nodes(self) -> int:
        if not self.layers:
            return 0
        # Assume all layers share the same number of nodes.
        first_layer = next(iter(self.layers.values()))
        return first_layer.num_nodes

