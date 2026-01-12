from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PlayerParams:
    a: np.ndarray  # (n,)
    c: np.ndarray  # (n,)
    skills: np.ndarray  # (n, d) normalized
    b: np.ndarray  # (n, n) symmetric with zeros diag


@dataclass(frozen=True)
class ModelConfig:
    n: int
    d: int
    seed: int
    noise_sigma: float = 1.0


def _normalize_rows(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("skills contains a zero vector; normalization is undefined")
    return x / norms


def generate_players(config: ModelConfig) -> PlayerParams:
    rng = np.random.default_rng(config.seed)

    a = rng.normal(loc=0.0, scale=1.0, size=(config.n,)).astype(float)
    c = rng.uniform(low=0.0, high=1.0, size=(config.n,)).astype(float)
    skills_raw = rng.normal(loc=0.0, scale=1.0, size=(config.n, config.d)).astype(float)
    skills = _normalize_rows(skills_raw)

    b_upper = rng.normal(loc=0.0, scale=0.5, size=(config.n, config.n)).astype(float)
    b = np.triu(b_upper, k=1)
    b = b + b.T

    return PlayerParams(a=a, c=c, skills=skills, b=b)

