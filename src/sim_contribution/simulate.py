from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from sim_contribution.algorithms import greedy_partition_du, greedy_partition_random, greedy_partition_ud
from sim_contribution.bitmask import iter_bits
from sim_contribution.coalitions import Coalitions, precompute_coalitions
from sim_contribution.model import ModelConfig, PlayerParams, generate_players
from sim_contribution.oracle import compute_oracle_value


@dataclass(frozen=True)
class SimulationConfig:
    n: int
    T: int
    d: int
    seed: int
    noise_sigma: float = 1.0


@dataclass(frozen=True)
class AlgorithmResult:
    algorithm: str
    totals: np.ndarray  # (T,)
    regrets: np.ndarray  # (T,)
    team_mu_samples: pd.DataFrame
    summary: pd.DataFrame


def _precompute_eps(
    T: int,
    coalition_masks: np.ndarray,
    sigma: float,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    eps = rng.normal(loc=0.0, scale=sigma, size=(T, len(coalition_masks))).astype(float)
    return eps


def _run_one(
    *,
    algorithm: str,
    n: int,
    T: int,
    coalitions: Coalitions,
    eps: np.ndarray,
    rng: np.random.Generator,
    oracle_value: float,
) -> AlgorithmResult:
    up = np.zeros((1 << n,), dtype=np.int64)
    down = np.zeros((1 << n,), dtype=np.int64)

    totals = np.zeros((T,), dtype=float)
    regrets = np.zeros((T,), dtype=float)

    sample_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for t in range(T):
        if algorithm == "UD":
            partition = greedy_partition_ud(n, up, down, rng).partition
        elif algorithm == "DU":
            partition = greedy_partition_du(n, up, down, rng).partition
        elif algorithm == "Random":
            partition = greedy_partition_random(n, rng).partition
        else:
            raise ValueError(f"unknown algorithm: {algorithm}")

        y_individual = np.zeros((n,), dtype=float)
        for i in range(n):
            m = 1 << i
            idx = coalitions.mask_to_index[m]
            y_individual[i] = coalitions.mu[idx] + eps[t, idx]

        team_mus: list[float] = []

        for team_mask in partition:
            team_idx = coalitions.mask_to_index[int(team_mask)]
            y_team = float(coalitions.mu[team_idx] + eps[t, team_idx])
            team_mu = float(coalitions.mu[team_idx])
            team_mus.append(team_mu)

            members = list(iter_bits(int(team_mask)))
            if len(members) >= 2:
                for k in members:
                    if y_team > y_individual[k]:
                        up[int(team_mask)] += 1
                    elif y_individual[k] > y_team:
                        down[int(team_mask)] += 1

            sample_rows.append(
                {
                    "t": t + 1,
                    "algorithm": algorithm,
                    "team_mask": int(team_mask),
                    "team_size": len(members),
                    "team_mu": team_mu,
                }
            )

        total_t = float(sum(team_mus))
        totals[t] = total_t
        regrets[t] = float(oracle_value - total_t)

        team_mus_arr = np.array(team_mus, dtype=float)
        summary_rows.append(
            {
                "t": t + 1,
                "algorithm": algorithm,
                "total": total_t,
                "regret": regrets[t],
                "team_mu_min": float(np.min(team_mus_arr)),
                "team_mu_median": float(np.median(team_mus_arr)),
                "team_mu_max": float(np.max(team_mus_arr)),
                "team_mu_q10": float(np.quantile(team_mus_arr, 0.10)),
                "team_mu_q25": float(np.quantile(team_mus_arr, 0.25)),
            }
        )

    return AlgorithmResult(
        algorithm=algorithm,
        totals=totals,
        regrets=regrets,
        team_mu_samples=pd.DataFrame(sample_rows),
        summary=pd.DataFrame(summary_rows),
    )


@dataclass(frozen=True)
class SimulationBundle:
    config: SimulationConfig
    players: PlayerParams
    coalitions: Coalitions
    oracle_value: float
    eps: np.ndarray
    results: dict[str, AlgorithmResult]


def run_simulation(config: SimulationConfig) -> SimulationBundle:
    if config.n <= 0:
        raise ValueError("n must be positive")
    if config.T <= 0:
        raise ValueError("T must be positive")
    if config.d <= 0:
        raise ValueError("d must be positive")
    if config.n > 24:
        raise ValueError("n is too large for the oracle DP and up/down arrays; choose n<=24")

    model_cfg = ModelConfig(n=config.n, d=config.d, seed=config.seed, noise_sigma=config.noise_sigma)
    players = generate_players(model_cfg)
    coalitions = precompute_coalitions(players)

    oracle_value = compute_oracle_value(config.n, coalitions, reconstruct=False).value

    eps_seed = config.seed + 10_000_019
    eps = _precompute_eps(config.T, coalitions.masks, config.noise_sigma, eps_seed)

    algos = ["UD", "DU", "Random"]
    results: dict[str, AlgorithmResult] = {}
    for algo in algos:
        algo_seed = config.seed + {"UD": 101, "DU": 202, "Random": 303}[algo]
        rng = np.random.default_rng(algo_seed)
        results[algo] = _run_one(
            algorithm=algo,
            n=config.n,
            T=config.T,
            coalitions=coalitions,
            eps=eps,
            rng=rng,
            oracle_value=oracle_value,
        )

    return SimulationBundle(
        config=config,
        players=players,
        coalitions=coalitions,
        oracle_value=float(oracle_value),
        eps=eps,
        results=results,
    )


def save_bundle(bundle: SimulationBundle, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "data").mkdir(parents=True, exist_ok=True)
    (out_dir / "plots").mkdir(parents=True, exist_ok=True)

    cfg = bundle.config
    (out_dir / "config.json").write_text(
        (
            "{\n"
            f'  "n": {cfg.n},\n'
            f'  "T": {cfg.T},\n'
            f'  "d": {cfg.d},\n'
            f'  "seed": {cfg.seed},\n'
            f'  "noise_sigma": {cfg.noise_sigma}\n'
            "}\n"
        ),
        encoding="utf-8",
    )

    (out_dir / "oracle_value.txt").write_text(f"{bundle.oracle_value}\n", encoding="utf-8")

    players = bundle.players
    np.savez_compressed(
        out_dir / "data" / "players.npz",
        a=players.a,
        c=players.c,
        skills=players.skills,
        b=players.b,
    )
    np.savez_compressed(out_dir / "data" / "eps.npz", eps=bundle.eps)

    coal_rows: list[dict[str, object]] = []
    for mask, size, mem, mu, comp, cost in zip(
        bundle.coalitions.masks,
        bundle.coalitions.sizes,
        bundle.coalitions.members,
        bundle.coalitions.mu,
        bundle.coalitions.comp,
        bundle.coalitions.cost,
    ):
        coal_rows.append(
            {
                "mask": int(mask),
                "size": int(size),
                "members": ",".join(map(str, mem)),
                "mu": float(mu),
                "comp": float(comp),
                "cost": float(cost),
            }
        )
    pd.DataFrame(coal_rows).to_csv(out_dir / "data" / "coalitions.csv", index=False)

    for algo, res in bundle.results.items():
        res.summary.to_csv(out_dir / "data" / f"timeseries_{algo}.csv", index=False)
        res.team_mu_samples.to_csv(out_dir / "data" / f"team_mu_samples_{algo}.csv", index=False)
