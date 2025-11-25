from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from ...core.interdependency import InterdependentSystem


def plot_pc_curve(results_df: pd.DataFrame, output_path: str | Path) -> None:
    """
    Plot p vs MCGC size / existence probability curve.

    Expects at least two columns in results_df:
      - "p": survival probability
      - "mcgc_size": relative size of the MCGC
    """
    if "p" not in results_df.columns or "mcgc_size" not in results_df.columns:
        raise ValueError("results_df must contain 'p' and 'mcgc_size' columns.")

    df_sorted = results_df.sort_values("p")

    fig, ax = plt.subplots()
    ax.plot(df_sorted["p"], df_sorted["mcgc_size"], marker="o")
    ax.set_xlabel("p (survival probability)")
    ax.set_ylabel("MCGC size")
    ax.grid(True)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def plot_node_importance_shapley(
    phi: np.ndarray,
    system: InterdependentSystem,
    output_path: str | Path,
) -> None:
    """
    Visualize node Shapley values on one of the network layers.

    Currently uses a spring layout on layer "A" (if present) or the first layer.
    """
    network = system.network
    if "A" in network.layers:
        layer = network.layers["A"]
    else:
        layer = next(iter(network.layers.values()))

    g = nx.Graph()
    g.add_nodes_from(range(layer.num_nodes))
    g.add_edges_from(map(tuple, np.asarray(layer.edges)))

    if phi.shape[0] != layer.num_nodes:
        raise ValueError("phi length must match number of nodes in the chosen layer.")

    pos = nx.spring_layout(g, seed=0)

    fig, ax = plt.subplots()
    nodes = nx.draw_networkx_nodes(
        g,
        pos,
        node_color=phi,
        cmap="viridis",
        ax=ax,
    )
    nx.draw_networkx_edges(g, pos, ax=ax, alpha=0.3, width=0.5)
    ax.set_axis_off()
    fig.colorbar(nodes, ax=ax, label="Shapley value")
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)

