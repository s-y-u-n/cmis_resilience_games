from __future__ import annotations

import numpy as np
import pandas as pd


def estimate_pc_from_results(results_df: pd.DataFrame) -> float:
    """
    Estimate the critical value p_c from sweep results.

    A simple heuristic is used here: choose the p at which MCGC size
    drops below half of its maximum.
    """
    if "p" not in results_df.columns or "mcgc_size" not in results_df.columns:
        raise ValueError("results_df must contain 'p' and 'mcgc_size' columns.")

    df_sorted = results_df.sort_values("p")
    m = df_sorted["mcgc_size"].to_numpy()
    p_vals = df_sorted["p"].to_numpy()

    if m.size == 0:
        raise ValueError("results_df is empty.")

    threshold = 0.5 * np.max(m)
    idx = np.where(m <= threshold)[0]
    if idx.size == 0:
        return float(p_vals[-1])
    return float(p_vals[idx[0]])


def summarize_v_results(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize v(S) values per coalition / node.

    Expects at least columns:
      - 'coalition_id'
      - 'v_value'
    """
    if "coalition_id" not in results_df.columns or "v_value" not in results_df.columns:
        raise ValueError("results_df must contain 'coalition_id' and 'v_value' columns.")

    summary = (
        results_df.groupby("coalition_id", as_index=False)["v_value"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "v_mean", "std": "v_std", "count": "num_samples"})
    )
    return summary

