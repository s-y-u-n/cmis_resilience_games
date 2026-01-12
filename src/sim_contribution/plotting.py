from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_totals_and_regret(results: dict[str, pd.DataFrame], out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for algo, df in results.items():
        axes[0].plot(df["t"], df["total"], label=algo)
        axes[1].plot(df["t"], df["regret"], label=algo)

    axes[0].set_title("Total (true mu)")
    axes[0].set_ylabel("Total")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].set_title("Oracle regret (OracleValue - Total)")
    axes[1].set_xlabel("t")
    axes[1].set_ylabel("Regret")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_team_mu_hist(samples: dict[str, pd.DataFrame], out_path: Path, bins: int = 30) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for algo, df in samples.items():
        ax.hist(df["team_mu"].to_numpy(dtype=float), bins=bins, alpha=0.4, density=True, label=algo)
    ax.set_title("Team mu distribution (all periods)")
    ax.set_xlabel("mu(S)")
    ax.set_ylabel("density")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_team_mu_time_stats(results: dict[str, pd.DataFrame], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for algo, df in results.items():
        ax.plot(df["t"], df["team_mu_min"], label=f"{algo}: min", alpha=0.8)
        ax.plot(df["t"], df["team_mu_median"], label=f"{algo}: median", alpha=0.8)
        ax.plot(df["t"], df["team_mu_max"], label=f"{algo}: max", alpha=0.8)
    ax.set_title("Team mu min/median/max by period")
    ax.set_xlabel("t")
    ax.set_ylabel("mu(S)")
    ax.grid(True, alpha=0.3)
    ax.legend(ncols=2, fontsize=9)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_team_mu_quantiles(results: dict[str, pd.DataFrame], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for algo, df in results.items():
        ax.plot(df["t"], df["team_mu_q10"], label=f"{algo}: q10", alpha=0.9)
        ax.plot(df["t"], df["team_mu_q25"], label=f"{algo}: q25", alpha=0.9)
    ax.set_title("Team mu lower quantiles by period")
    ax.set_xlabel("t")
    ax.set_ylabel("mu(S)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
