from __future__ import annotations

from typing import Tuple

import networkx as nx
import numpy as np

from ...core.interdependency import DependencyMapping, InterdependentSystem
from ...core.network_model import MultiLayerNetwork, NetworkLayer


def _graph_to_layer(name: str, g: nx.Graph) -> NetworkLayer:
    nodes = list(g.nodes())
    num_nodes = len(nodes)
    # Ensure nodes are labeled 0..N-1
    if set(nodes) != set(range(num_nodes)):
        mapping = {old: new for new, old in enumerate(nodes)}
        g = nx.relabel_nodes(g, mapping, copy=True)
    edges = np.asarray(list(g.edges()), dtype=int)
    degrees = np.array([deg for _, deg in g.degree()], dtype=float)
    return NetworkLayer(name=name, num_nodes=num_nodes, edges=edges, degree_distribution=degrees)


def _build_identity_dependency(num_nodes: int) -> DependencyMapping:
    ids = np.arange(num_nodes, dtype=int)
    return DependencyMapping(dep_A_to_B=ids.copy(), dep_B_to_A=ids.copy())


def build_er_system(n: int, k_avg: float, seed: int) -> InterdependentSystem:
    """
    Build a 2-layer ER interdependent system with identity dependency mapping.
    """
    p = k_avg / max(1, n - 1)
    g_a = nx.erdos_renyi_graph(n, p, seed=seed)
    g_b = nx.erdos_renyi_graph(n, p, seed=seed + 1)

    layer_a = _graph_to_layer("A", g_a)
    layer_b = _graph_to_layer("B", g_b)

    network = MultiLayerNetwork(layers={"A": layer_a, "B": layer_b})
    dependency = _build_identity_dependency(n)
    return InterdependentSystem(network=network, dependency=dependency)


def build_sf_system(n: int, lambda_: float, k_min: int, seed: int) -> InterdependentSystem:
    """
    Build a 2-layer scale-free-like interdependent system.

    This uses a Barabási–Albert model as a simple approximation.
    The precise relationship between (lambda_, k_min) and the BA parameters
    is left for future refinement.
    """
    m = max(1, k_min)
    g_a = nx.barabasi_albert_graph(n, m, seed=seed)
    g_b = nx.barabasi_albert_graph(n, m, seed=seed + 1)

    layer_a = _graph_to_layer("A", g_a)
    layer_b = _graph_to_layer("B", g_b)

    network = MultiLayerNetwork(layers={"A": layer_a, "B": layer_b})
    dependency = _build_identity_dependency(n)
    return InterdependentSystem(network=network, dependency=dependency)


def build_real_italy_system(path_power: str, path_comm: str, path_dep: str) -> InterdependentSystem:
    """
    Placeholder for building an interdependent system from real Italian blackout data.

    Parameters are kept for future implementation; for now this raises NotImplementedError.
    """
    raise NotImplementedError(
        "Real-world Italy case-study network construction is not implemented yet. "
        "Expected inputs: power network, communication network, dependency links."
    )

