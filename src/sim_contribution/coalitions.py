from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from sim_contribution.bitmask import iter_bits, popcount
from sim_contribution.model import PlayerParams


@dataclass(frozen=True)
class Coalitions:
    masks: np.ndarray  # (m,) int64
    sizes: np.ndarray  # (m,) int8
    members: list[list[int]]  # len m
    mu: np.ndarray  # (m,) float
    comp: np.ndarray  # (m,) float
    cost: np.ndarray  # (m,) float
    mask_to_index: dict[int, int]


def enumerate_masks(n: int, max_size: int = 3) -> np.ndarray:
    masks: list[int] = []
    for i in range(n):
        masks.append(1 << i)
    if max_size >= 2:
        for i in range(n):
            for j in range(i + 1, n):
                masks.append((1 << i) | (1 << j))
    if max_size >= 3:
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    masks.append((1 << i) | (1 << j) | (1 << k))
    return np.array(masks, dtype=np.int64)


def precompute_coalitions(players: PlayerParams) -> Coalitions:
    n = int(players.a.shape[0])
    masks = enumerate_masks(n, max_size=3)
    sizes = np.array([popcount(int(m)) for m in masks], dtype=np.int8)
    members = [list(iter_bits(int(m))) for m in masks]

    cos = (players.skills @ players.skills.T).astype(float)
    comp_pair = 1.0 - cos
    cost_pair = np.maximum(0.0, 1.0 - (players.c[:, None] + players.c[None, :]) / 2.0)

    mu = np.zeros((len(masks),), dtype=float)
    comp = np.zeros((len(masks),), dtype=float)
    cost = np.zeros((len(masks),), dtype=float)

    for idx, mem in enumerate(members):
        k = len(mem)
        if k == 1:
            i = mem[0]
            mu[idx] = float(players.a[i])
            continue

        pairs = list(combinations(mem, 2))
        pair_count = len(pairs)
        sum_a = float(players.a[mem].sum())
        sum_b = float(sum(players.b[i, j] for i, j in pairs))
        sum_comp = float(sum(comp_pair[i, j] for i, j in pairs))
        sum_cost = float(sum(cost_pair[i, j] for i, j in pairs))

        comp[idx] = sum_comp / pair_count
        cost[idx] = sum_cost
        mu[idx] = sum_a + sum_b + comp[idx] - cost[idx]

    mask_to_index = {int(m): int(i) for i, m in enumerate(masks)}
    return Coalitions(
        masks=masks,
        sizes=sizes,
        members=members,
        mu=mu,
        comp=comp,
        cost=cost,
        mask_to_index=mask_to_index,
    )

