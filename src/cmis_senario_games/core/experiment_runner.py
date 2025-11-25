from __future__ import annotations

from pathlib import Path

from .io_config import load_yaml


def run_experiment(experiment_config_path: str) -> None:
    """
    High-level experiment runner.

    Expected responsibilities (to be implemented):
      1. Load experiment YAML.
      2. Construct scenario-specific network and value function.
      3. Run v(S) evaluations, Shapley estimation, lex-cel ranking.
      4. Save results and figures under outputs/.
    """
    config_path = Path(experiment_config_path)
    config = load_yaml(config_path)
    # Placeholder: full experiment orchestration will be implemented later.
    raise NotImplementedError(
        f"Experiment runner is not implemented yet. Loaded config from {config_path}: {config}"
    )

