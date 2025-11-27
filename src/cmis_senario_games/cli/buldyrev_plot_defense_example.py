from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.cascade_engine import run_cascade
from ..core.experiment_runner import run_experiment
from ..core.io_config import load_yaml
from ..core.percolation import sample_initial_failure
from ..scenarios.buldyrev2010.config_schema import (
    BuldyrevExperimentConfig,
    BuldyrevNetworkConfig,
    load_buldyrev_experiment_config,
)
from ..scenarios.buldyrev2010.network_definition import (
    build_er_system,
    build_real_italy_system,
    build_sf_system,
)
from ..scenarios.buldyrev2010.visualization import (
    _draw_defense_network,
    plot_defense_failure_timeline,
)


def _build_system_from_network_config(net_cfg: BuldyrevNetworkConfig):
    """
    Construct an InterdependentSystem from a Buldyrev network configuration.
    """
    net_type = net_cfg.type

    if net_type == "er":
        if net_cfg.num_nodes is None or net_cfg.avg_degree is None or net_cfg.seed is None:
            raise ValueError("ER network requires num_nodes, avg_degree, and seed.")
        return build_er_system(net_cfg.num_nodes, net_cfg.avg_degree, net_cfg.seed)

    if net_type == "sf":
        if (
            net_cfg.num_nodes is None
            or net_cfg.k_min is None
            or net_cfg.seed is None
            or net_cfg.lambda_ is None
        ):
            raise ValueError("SF network requires num_nodes, lambda_, k_min, and seed.")
        return build_sf_system(net_cfg.num_nodes, net_cfg.lambda_, net_cfg.k_min, net_cfg.seed)

    if net_type == "real_italy":
        if not all(
            [
                net_cfg.power_nodes_path,
                net_cfg.power_edges_path,
                net_cfg.comm_nodes_path,
                net_cfg.comm_edges_path,
                net_cfg.dep_mapping_path,
            ]
        ):
            raise ValueError(
                "real_italy network requires power_nodes_path, power_edges_path, "
                "comm_nodes_path, comm_edges_path, and dep_mapping_path."
            )
        return build_real_italy_system(
            net_cfg.power_nodes_path,
            net_cfg.power_edges_path,
            net_cfg.comm_nodes_path,
            net_cfg.comm_edges_path,
            net_cfg.dep_mapping_path,
        )

    raise ValueError(f"Unsupported network type: {net_type}")


def _select_coalition_id(
    value_df: pd.DataFrame,
    exp_cfg_dict: dict,
    cli_coalition_id: str | None,
) -> str:
    """
    Decide which coalition_id to visualize.

    Priority:
      1. CLI --coalition-id
      2. experiment YAML: visualization.coalition_id
      3. random choice from value_df["coalition_id"]
    """
    if "coalition_id" not in value_df.columns:
        raise ValueError("value.csv must contain a 'coalition_id' column.")

    # 1) CLI argument has highest priority.
    if cli_coalition_id is not None:
        if cli_coalition_id not in value_df["coalition_id"].values:
            raise ValueError(f"coalition_id '{cli_coalition_id}' not found in value.csv.")
        return cli_coalition_id

    # 2) visualization.coalition_id in experiment YAML.
    vis_cfg = exp_cfg_dict.get("visualization", {}) or {}
    cfg_coalition_id = vis_cfg.get("coalition_id")
    if cfg_coalition_id is not None:
        if cfg_coalition_id not in value_df["coalition_id"].values:
            raise ValueError(f"coalition_id '{cfg_coalition_id}' from config not found in value.csv.")
        return cfg_coalition_id

    # 3) Fallback: random choice.
    coalition_ids = value_df["coalition_id"].unique()
    if coalition_ids.size == 0:
        raise ValueError("value.csv has no coalition_id rows.")
    rng = np.random.default_rng()
    idx = rng.integers(0, coalition_ids.size)
    chosen = str(coalition_ids[idx])
    print(f"[buldyrev-visualize-defense] No coalition specified; randomly selected {chosen}.")
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize a Buldyrev2010 defense pattern: "
            "network structure + example of which nodes fail."
        )
    )
    parser.add_argument(
        "--experiment",
        required=True,
        help="Path to an experiment YAML (e.g., experiments/buldyrev2010/italy_case_basic_run.yaml).",
    )
    parser.add_argument(
        "--coalition-id",
        help="Coalition ID to visualize (e.g., 'coalition_5'). If omitted, use config or random.",
    )

    args = parser.parse_args()

    exp_cfg_path = Path(args.experiment)
    exp_cfg_dict = load_yaml(exp_cfg_path)

    # Load scenario (Buldyrev) configuration.
    scenario_cfg_path = Path(exp_cfg_dict["scenario_config"])
    scenario_cfg: BuldyrevExperimentConfig = load_buldyrev_experiment_config(scenario_cfg_path)

    # Build interdependent system from network config.
    system = _build_system_from_network_config(scenario_cfg.network)

    # Ensure value.csv exists; if not, run the experiment once.
    output_dir = Path(exp_cfg_dict["output_dir"])
    figure_dir = Path(exp_cfg_dict["figure_dir"])
    value_path = output_dir / "value.csv"

    if not value_path.exists():
        print(
            "[buldyrev-visualize-defense] value.csv not found; "
            "running the experiment first to generate it."
        )
        run_experiment(str(exp_cfg_path))

    if not value_path.exists():
        raise FileNotFoundError(f"value.csv not found at {value_path}")

    value_df = pd.read_csv(value_path)

    coalition_id = _select_coalition_id(value_df, exp_cfg_dict, args.coalition_id)

    # Extract coalition mask for the chosen coalition_id.
    row = value_df[value_df["coalition_id"] == coalition_id]
    if row.empty:
        raise ValueError(f"coalition_id '{coalition_id}' not found in value.csv.")
    row = row.iloc[0]

    node_cols = [c for c in value_df.columns if c.startswith("node_")]
    if not node_cols:
        raise ValueError("value.csv must contain node_* columns to reconstruct coalitions.")

    coalition_mask = row[node_cols].to_numpy(dtype=bool)

    # Use percolation parameters from the scenario configuration.
    percolation = scenario_cfg.percolation

    # Run one cascade realization for this defense pattern, recording node history.
    num_nodes = system.network.num_nodes
    coalition_bool = np.asarray(coalition_mask, dtype=bool)
    if coalition_bool.shape[0] != num_nodes:
        raise ValueError("coalition_mask length must match number of nodes.")

    initial_alive = sample_initial_failure(system, percolation)
    initial_alive[coalition_bool] = True
    cascade_result = run_cascade(system, initial_alive, record_node_history=True)

    figure_dir.mkdir(parents=True, exist_ok=True)

    # 1) Network structure + final failure pattern
    network_path = figure_dir / f"defense_example_{coalition_id}.png"
    print(
        f"[buldyrev-visualize-defense] Drawing defense example for coalition_id={coalition_id} "
        f"-> {network_path}"
    )
    _draw_defense_network(
        system=system,
        coalition_mask=coalition_bool,
        final_alive_mask=cascade_result.final_alive_mask,
        output_path=network_path,
    )

    # 2) Node-by-step timeline of MCGC membership
    timeline_path = figure_dir / f"defense_timeline_{coalition_id}.png"
    print(
        f"[buldyrev-visualize-defense] Drawing failure timeline for coalition_id={coalition_id} "
        f"-> {timeline_path}"
    )
    plot_defense_failure_timeline(
        history=cascade_result.history,
        output_path=timeline_path,
    )


if __name__ == "__main__":
    main()
