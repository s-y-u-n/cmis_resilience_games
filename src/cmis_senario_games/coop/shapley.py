from __future__ import annotations

from typing import Dict, Iterable, List

from ..core.game import ResilienceGame


def shapley_values(
    game: ResilienceGame,
    *,
    num_samples: int = 10_000,
    random_seed: int = 0,
) -> Dict[int, float]:
    """ResilienceGame に対する Shapley 値をモンテカルロで近似計算する。

    現時点ではシンプルな順序サンプリングに基づく実装の骨組みのみを提供し、
    実際のアルゴリズムは後続の実装フェーズで詰める。
    """
    import numpy as np

    rng = np.random.default_rng(random_seed)
    players: List[int] = sorted(node.id for node in game.graph.nodes)
    n = len(players)
    phi = {i: 0.0 for i in players}

    # TODO: 効率的な Shapley 近似アルゴリズムの実装
    for _ in range(num_samples):
        perm = players.copy()
        rng.shuffle(perm)
        coalition: set[int] = set()
        prev_value = 0.0
        for i in perm:
            coalition.add(i)
            value = game.payoff(coalition)
            marginal = value - prev_value
            phi[i] += marginal
            prev_value = value

    for i in players:
        phi[i] /= float(num_samples)
    return phi

