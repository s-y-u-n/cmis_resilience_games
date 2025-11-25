from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class LexCelConfig:
    """
    Configuration for lexicographic + cell-based ranking.

    This is intentionally lightweight; more options can be added as needed.
    """

    primary_weight: float = 1.0


def rank_players_lexcel(
    contributions: np.ndarray,
    tie_break_metric: Optional[np.ndarray],
    config: LexCelConfig,
) -> np.ndarray:
    """
    Rank players given contribution scores and an optional tie-break metric.

    Parameters
    ----------
    contributions : np.ndarray
        Primary contribution scores (e.g., Shapley values).
    tie_break_metric : np.ndarray or None
        Optional secondary metric for tie-breaking.
    config : LexCelConfig
        Configuration (currently unused except for future extensions).

    Returns
    -------
    np.ndarray
        Ranking indices for each player (0 = highest rank).
    """
    contributions = np.asarray(contributions)

    if tie_break_metric is not None:
        tie_break_metric = np.asarray(tie_break_metric)
        if tie_break_metric.shape != contributions.shape:
            raise ValueError("tie_break_metric must have the same shape as contributions.")
        # Sort by (contributions desc, tie_break_metric desc)
        order = np.lexsort((-tie_break_metric, -contributions))
    else:
        # Sort by contributions in descending order
        order = np.argsort(-contributions)

    # ranking[player_id] = rank (0 = best)
    ranking = np.empty_like(order)
    ranking[order] = np.arange(order.size)
    return ranking

