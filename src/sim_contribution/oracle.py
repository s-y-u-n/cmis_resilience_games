from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from sim_contribution.bitmask import lowest_bit_index
from sim_contribution.coalitions import Coalitions


@dataclass(frozen=True)
class OracleResult:
    value: float
    partition: list[int] | None = None


def compute_oracle_value(n: int, coalitions: Coalitions, reconstruct: bool = False) -> OracleResult:
    if n <= 0:
        raise ValueError("n must be positive")
    if n > 24:
        raise ValueError("n is too large for 2^n DP; choose n<=24 or implement an approximation")

    full_mask = (1 << n) - 1
    dp = np.full((1 << n,), -np.inf, dtype=float)
    dp[0] = 0.0
    choice: np.ndarray | None = np.zeros((1 << n,), dtype=np.int64) if reconstruct else None

    mu_by_mask: dict[int, float] = {int(m): float(v) for m, v in zip(coalitions.masks, coalitions.mu)}

    for mask in range(1, full_mask + 1):
        i = lowest_bit_index(mask)
        best = -np.inf
        best_s = 0

        s1 = 1 << i
        best = mu_by_mask[s1] + dp[mask ^ s1]
        best_s = s1

        remaining_bits = [j for j in range(n) if (mask >> j) & 1 and j != i]

        for j in remaining_bits:
            s2 = s1 | (1 << j)
            val = mu_by_mask[s2] + dp[mask ^ s2]
            if val > best:
                best = val
                best_s = s2

        for j, k in combinations(remaining_bits, 2):
            s3 = s1 | (1 << j) | (1 << k)
            val = mu_by_mask[s3] + dp[mask ^ s3]
            if val > best:
                best = val
                best_s = s3

        dp[mask] = best
        if choice is not None:
            choice[mask] = best_s

    if not reconstruct:
        return OracleResult(value=float(dp[full_mask]), partition=None)

    partition: list[int] = []
    mask = full_mask
    assert choice is not None
    while mask:
        s = int(choice[mask])
        partition.append(s)
        mask ^= s
    return OracleResult(value=float(dp[full_mask]), partition=partition)

