from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
import pandas as pd

from ...core.cascade_engine import run_cascade
from ...core.interdependency import InterdependentSystem
from ...core.percolation import PercolationParams, sample_initial_failure


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


def _build_bipartite_layout(system: InterdependentSystem) -> tuple[dict[str, tuple[float, float]], list[str], list[str], list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    """
    Construct a simple two-column layout for layers A and B, including dependency edges.

    Returns
    -------
    pos : dict
        Positions for all nodes keyed by their string IDs ("A_i", "B_j").
    nodes_A, nodes_B : list[str]
        Node IDs for layer A and B.
    edges_A, edges_B, edges_dep : list[tuple[str, str]]
        Edge lists for intra-layer edges on A/B and inter-layer dependency edges.
    """
    network = system.network
    dependency = system.dependency

    if "A" not in network.layers or "B" not in network.layers:
        raise ValueError("InterdependentSystem must have layers 'A' and 'B' to build bipartite layout.")

    layer_a = network.layers["A"]
    layer_b = network.layers["B"]

    num_nodes = layer_a.num_nodes
    if layer_b.num_nodes != num_nodes:
        raise ValueError("Layers 'A' and 'B' must have the same number of nodes.")

    dep_A_to_B = np.asarray(dependency.dep_A_to_B, dtype=int)
    if dep_A_to_B.shape[0] != num_nodes:
        raise ValueError("Dependency dep_A_to_B length must match number of nodes in layer 'A'.")

    # Align B-layer positions so that dependencies are (approximately) horizontal.
    order_b = np.empty(num_nodes, dtype=int)
    for i, j in enumerate(dep_A_to_B):
        order_b[int(j)] = i

    y_coords = np.linspace(0.0, 1.0, num_nodes) if num_nodes > 1 else np.array([0.5])

    nodes_A = [f"A_{i}" for i in range(num_nodes)]
    nodes_B = [f"B_{j}" for j in range(num_nodes)]

    pos: dict[str, tuple[float, float]] = {}
    for i, node_id in enumerate(nodes_A):
        pos[node_id] = (0.0, float(y_coords[i]))
    for j, node_id in enumerate(nodes_B):
        pos[node_id] = (1.0, float(y_coords[order_b[j]]))

    edges_A = [(f"A_{int(u)}", f"A_{int(v)}") for u, v in np.asarray(layer_a.edges, dtype=int)]
    edges_B = [(f"B_{int(u)}", f"B_{int(v)}") for u, v in np.asarray(layer_b.edges, dtype=int)]
    edges_dep = [(f"A_{i}", f"B_{int(j)}") for i, j in enumerate(dep_A_to_B)]

    return pos, nodes_A, nodes_B, edges_A, edges_B, edges_dep


def _draw_defense_network(
    system: InterdependentSystem,
    coalition_mask: np.ndarray,
    final_alive_mask: np.ndarray,
    output_path: str | Path,
) -> None:
    """
    Draw the two-layer network with node colors encoding protection/failure status.
    """
    num_nodes = system.network.num_nodes
    coalition_bool = np.asarray(coalition_mask, dtype=bool)
    if coalition_bool.shape[0] != num_nodes:
        raise ValueError("coalition_mask length must match number of nodes.")

    final_alive = np.asarray(final_alive_mask, dtype=bool)
    if final_alive.shape[0] != num_nodes:
        raise ValueError("final_alive_mask length must match number of nodes.")

    # Classify nodes into four categories.
    survived = final_alive
    failed = ~final_alive
    protected = coalition_bool
    unprotected = ~coalition_bool

    category = np.empty(num_nodes, dtype=int)
    # 0: protected & survived
    # 1: protected & failed
    # 2: unprotected & survived
    # 3: unprotected & failed
    for i in range(num_nodes):
        if protected[i] and survived[i]:
            category[i] = 0
        elif protected[i] and failed[i]:
            category[i] = 1
        elif unprotected[i] and survived[i]:
            category[i] = 2
        else:
            category[i] = 3

    color_map = {
        0: "#1b9e77",  # protected & survived
        1: "#d95f02",  # protected & failed
        2: "#7570b3",  # unprotected & survived
        3: "#e7298a",  # unprotected & failed
    }

    pos, nodes_A, nodes_B, edges_A, edges_B, edges_dep = _build_bipartite_layout(system)

    node_colors_A = [color_map[int(category[int(n.split("_")[1])])] for n in nodes_A]
    node_colors_B = [color_map[int(category[int(n.split("_")[1])])] for n in nodes_B]

    fig_height = max(4.0, 0.25 * num_nodes)
    fig, ax = plt.subplots(figsize=(8.0, fig_height))

    # Build a graph containing all nodes and edges for drawing.
    g = nx.Graph()
    g.add_nodes_from(nodes_A + nodes_B)
    g.add_edges_from(edges_A + edges_B + edges_dep)

    # Draw intra-layer edges
    nx.draw_networkx_edges(
        g,
        pos,
        ax=ax,
        edgelist=edges_A,
        edge_color="tab:gray",
        alpha=0.6,
        width=1.0,
    )
    nx.draw_networkx_edges(
        g,
        pos,
        ax=ax,
        edgelist=edges_B,
        edge_color="tab:gray",
        alpha=0.6,
        width=1.0,
        style="dashed",
    )

    # Draw dependency edges
    nx.draw_networkx_edges(
        g,
        pos,
        ax=ax,
        edgelist=edges_dep,
        edge_color="lightgray",
        alpha=0.5,
        width=0.8,
    )

    # Draw nodes for each layer
    nx.draw_networkx_nodes(
        g,
        pos,
        nodelist=nodes_A,
        node_color=node_colors_A,
        node_size=200,
        edgecolors="black",
        linewidths=0.5,
        ax=ax,
    )
    nx.draw_networkx_nodes(
        g,
        pos,
        nodelist=nodes_B,
        node_color=node_colors_B,
        node_size=200,
        edgecolors="black",
        linewidths=0.5,
        ax=ax,
    )

    # Optionally label nodes for small N
    if num_nodes <= 30:
        labels = {n: n for n in nodes_A + nodes_B}
        nx.draw_networkx_labels(g, pos, labels=labels, font_size=8, ax=ax)

    ax.set_axis_off()
    ax.set_title("Defense pattern vs. cascade outcome (A/B layers)")

    legend_handles = [
        mpatches.Patch(color=color_map[0], label="protected & survived"),
        mpatches.Patch(color=color_map[1], label="protected & failed"),
        mpatches.Patch(color=color_map[2], label="unprotected & survived"),
        mpatches.Patch(color=color_map[3], label="unprotected & failed"),
    ]
    ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=2)

    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def plot_defense_failure_example(
    system: InterdependentSystem,
    coalition_mask: np.ndarray,
    percolation: PercolationParams,
    output_path: str | Path,
) -> None:
    """
    Visualize the network structure and an example of which nodes fail
    under a given defense (protection) pattern.

    This function:
      - samples one initial failure pattern from percolation parameters,
      - applies protection according to coalition_mask,
      - runs a single Buldyrev-style cascade, and
      - draws a two-layer network (A/B) using _draw_defense_network.
    """
    num_nodes = system.network.num_nodes
    coalition_bool = np.asarray(coalition_mask, dtype=bool)
    if coalition_bool.shape[0] != num_nodes:
        raise ValueError("coalition_mask length must match number of nodes.")

    # One example cascade realization for this defense pattern.
    initial_alive = sample_initial_failure(system, percolation)
    initial_alive[coalition_bool] = True
    cascade_result = run_cascade(system, initial_alive)

    _draw_defense_network(
        system=system,
        coalition_mask=coalition_bool,
        final_alive_mask=cascade_result.final_alive_mask,
        output_path=output_path,
    )


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


def plot_defense_failure_timeline(
    history: dict,
    output_path: str | Path,
) -> None:
    """
    Plot a node-by-step timeline showing when each node in the MCGC fails.

    Expects that run_cascade was called with record_node_history=True so that
    history contains a key 'mcgc_mask' with a list of boolean arrays
    (one per cascade step) indicating which nodes are in the MCGC.
    """
    mcgc_masks = history.get("mcgc_mask")
    if mcgc_masks is None:
        raise ValueError("history must contain 'mcgc_mask'; run run_cascade with record_node_history=True.")
    if not mcgc_masks:
        raise ValueError("history['mcgc_mask'] is empty.")

    # Shape: (num_steps, num_nodes)
    mcgc_array = np.vstack([np.asarray(mask, dtype=bool) for mask in mcgc_masks])
    num_steps, num_nodes = mcgc_array.shape

    fig_height = max(4.0, 0.25 * num_nodes)
    fig, ax = plt.subplots(figsize=(8.0, fig_height))

    # Rows: node index, Columns: cascade step
    im = ax.imshow(
        mcgc_array.T,
        aspect="auto",
        interpolation="nearest",
        origin="lower",
        cmap="Greens",
    )

    ax.set_xlabel("cascade step")
    ax.set_ylabel("node index")

    # Keep tick labels manageable for large N / many steps.
    if num_steps > 20:
        ax.set_xticks([])
    if num_nodes > 40:
        ax.set_yticks([])

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("MCGC membership (1=alive, 0=failed)")

    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
