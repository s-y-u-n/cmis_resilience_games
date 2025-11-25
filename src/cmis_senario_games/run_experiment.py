from __future__ import annotations

import argparse

from .core.experiment_runner import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cmis_senario_games experiments.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to an experiment YAML configuration file.",
    )
    args = parser.parse_args()
    run_experiment(args.config)


if __name__ == "__main__":
    main()

