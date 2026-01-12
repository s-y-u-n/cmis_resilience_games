from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from sim_contribution.plotting import (
    plot_team_mu_hist,
    plot_team_mu_quantiles,
    plot_team_mu_time_stats,
    plot_totals_and_regret,
)
from sim_contribution.simulate import SimulationConfig, run_simulation, save_bundle


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sim-contribution")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run UD/DU/Random simulation and write outputs.")
    run.add_argument("--n", type=int, default=12)
    run.add_argument("--T", type=int, default=200)
    run.add_argument("--d", type=int, default=8)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--noise-sigma", type=float, default=1.0)
    run.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: outputs/run_<timestamp>).",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    if args.cmd == "run":
        out_dir: Path
        if args.out is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_dir = Path("outputs") / f"run_{ts}"
        else:
            out_dir = args.out

        config = SimulationConfig(
            n=int(args.n),
            T=int(args.T),
            d=int(args.d),
            seed=int(args.seed),
            noise_sigma=float(args.noise_sigma),
        )
        bundle = run_simulation(config)
        save_bundle(bundle, out_dir)

        timeseries: dict[str, pd.DataFrame] = {
            algo: res.summary for algo, res in bundle.results.items()
        }
        samples: dict[str, pd.DataFrame] = {
            algo: res.team_mu_samples for algo, res in bundle.results.items()
        }

        plot_totals_and_regret(timeseries, out_dir / "plots" / "totals_regret.png")
        plot_team_mu_hist(samples, out_dir / "plots" / "team_mu_hist.png")
        plot_team_mu_time_stats(timeseries, out_dir / "plots" / "team_mu_min_median_max.png")
        plot_team_mu_quantiles(timeseries, out_dir / "plots" / "team_mu_quantiles.png")

        print(f"Wrote outputs to: {out_dir}")
        return

    raise SystemExit(2)

