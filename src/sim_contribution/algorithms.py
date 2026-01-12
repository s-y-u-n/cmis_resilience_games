from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from sim_contribution.bitmask import iter_bits


@dataclass(frozen=True)
class GreedyResult:
    partition: list[int]


def _candidates_from_rmask(rmask: int) -> list[int]:
    members = list(iter_bits(rmask))
    cands: list[int] = []
    for i in members:
        cands.append(1 << i)
    for i, j in combinations(members, 2):
        cands.append((1 << i) | (1 << j))
    for i, j, k in combinations(members, 3):
        cands.append((1 << i) | (1 << j) | (1 << k))
    return cands


def greedy_partition_ud(n: int, up: np.ndarray, down: np.ndarray, rng: np.random.Generator) -> GreedyResult:
    rmask = (1 << n) - 1
    partition: list[int] = []
    while rmask:
        cands = _candidates_from_rmask(rmask)
        best_key: tuple[int, int] | None = None
        best: list[int] = []
        for s in cands:
            key = (int(up[s]), -int(down[s]))
            if best_key is None or key > best_key:
                best_key = key
                best = [s]
            elif key == best_key:
                best.append(s)
        chosen = int(rng.choice(best))
        partition.append(chosen)
        rmask ^= chosen
    return GreedyResult(partition=partition)


def greedy_partition_du(n: int, up: np.ndarray, down: np.ndarray, rng: np.random.Generator) -> GreedyResult:
    rmask = (1 << n) - 1
    partition: list[int] = []
    while rmask:
        cands = _candidates_from_rmask(rmask)
        best_key: tuple[int, int] | None = None
        best: list[int] = []
        for s in cands:
            key = (int(down[s]), -int(up[s]))
            if best_key is None or key < best_key:
                best_key = key
                best = [s]
            elif key == best_key:
                best.append(s)
        chosen = int(rng.choice(best))
        partition.append(chosen)
        rmask ^= chosen
    return GreedyResult(partition=partition)


def greedy_partition_random(n: int, rng: np.random.Generator) -> GreedyResult:
    rmask = (1 << n) - 1
    partition: list[int] = []
    while rmask:
        cands = _candidates_from_rmask(rmask)
        chosen = int(rng.choice(cands))
        partition.append(chosen)
        rmask ^= chosen
    return GreedyResult(partition=partition)

