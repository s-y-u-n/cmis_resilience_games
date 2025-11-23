from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt
from typing import Dict, Iterable, Set

import numpy as np
from scipy.stats import multivariate_normal, norm

from .fragility import FragilityParam
from .graph import Graph
from .hazard import GmpeParam, HazardScenario
from .reinforcement import ReinforcementModel


@dataclass
class SimulationConfig:
    """モンテカルロシミュレーション設定。"""

    num_samples: int
    random_seed: int = 0
    use_quasi_mc: bool = False


def _compute_source_distance(
    graph: Graph,
    hazard: HazardScenario,
) -> Dict[int, float]:
    """各ノードの震源距離 R_i を計算する。"""
    ex = hazard.epicenter_x
    ey = hazard.epicenter_y
    distances: Dict[int, float] = {}
    for node in graph.nodes:
        dx = node.x - ex
        dy = node.y - ey
        distances[node.id] = sqrt(dx * dx + dy * dy)
    return distances


def _gmpe_mean_log_pga(
    gmpe: GmpeParam,
    magnitude: float,
    distance: float,
) -> float:
    """GMPE に基づく log PGA の平均値 μ_i を計算する簡易版。

    実際の論文式(17)の係数構造はここでは抽象化し、
    a + b M + c log(R + h) + d R のような形を想定する。
    """
    r_h = distance + gmpe.h
    return gmpe.a + gmpe.b * magnitude + gmpe.c * log(r_h) + gmpe.d * distance


def sample_pga_for_all_nodes(
    graph: Graph,
    hazard: HazardScenario,
    gmpe: GmpeParam,
    rng: np.random.Generator,
) -> Dict[int, float]:
    """各ノード i について PGA_i を 1 サンプル生成する。

    初期実装では空間相関を「対角共分散行列」による独立近似としつつ、
    インターフェースとしては多変量正規乱数に基づく実装とする。
    """
    distances = _compute_source_distance(graph, hazard)
    node_ids = [node.id for node in graph.nodes]
    n = len(node_ids)

    means = np.zeros(n)
    for idx, node_id in enumerate(node_ids):
        means[idx] = _gmpe_mean_log_pga(
            gmpe=gmpe,
            magnitude=hazard.magnitude,
            distance=distances[node_id],
        )

    # total sigma (between-event + within-event)
    sigma_total = sqrt(gmpe.sigma_inter**2 + gmpe.sigma_intra**2)
    cov = np.eye(n) * sigma_total**2  # TODO: 空間相関モデルによる共分散構成

    mvn = multivariate_normal(mean=means, cov=cov)
    z = mvn.rvs(random_state=rng)
    if n == 1:
        z = np.array([z], dtype=float)

    pga_samples: Dict[int, float] = {}
    for idx, node_id in enumerate(node_ids):
        log_pga = z[idx]
        pga_samples[node_id] = float(np.exp(log_pga))
    return pga_samples


def compute_failure_prob_for_node(
    pga: float,
    frag: FragilityParam,
) -> float:
    """fragility 曲線に基づき、P(E_i | PGA_i) を返す。"""
    if pga <= 0.0 or frag.alpha <= 0.0 or frag.beta <= 0.0:
        return 0.0
    x = (log(pga) - log(frag.alpha)) / frag.beta
    return float(norm.cdf(x))


def sample_node_failures(
    pga_samples: Dict[int, float],
    frag_params: Dict[int, FragilityParam],
    rng: np.random.Generator,
) -> Dict[int, bool]:
    """各ノードについて Bernoulli 試行で故障/生存をサンプリングする。"""
    failures: Dict[int, bool] = {}
    for node_id, pga in pga_samples.items():
        frag = frag_params[node_id]
        p_fail = compute_failure_prob_for_node(pga, frag)
        failures[node_id] = bool(rng.random() < p_fail)
    return failures


def check_system_failure(
    graph: Graph,
    node_failed: Dict[int, bool],
) -> bool:
    """ソースとシンクの非連結性に基づくシステム失敗判定。

    現時点では簡易 BFS 実装を用いる。
    """
    from collections import deque

    source = graph.source_node_id
    sink = graph.sink_node_id
    if node_failed.get(source, False) or node_failed.get(sink, False):
        return True

    adjacency: Dict[int, Set[int]] = {}
    for node in graph.nodes:
        adjacency[node.id] = set()
    for edge in graph.edges:
        if node_failed.get(edge.u, False) or node_failed.get(edge.v, False):
            continue
        adjacency[edge.u].add(edge.v)
        if not edge.directed:
            adjacency[edge.v].add(edge.u)

    visited: Set[int] = set()
    queue: deque[int] = deque([source])
    visited.add(source)

    while queue:
        current = queue.popleft()
        if current == sink:
            return False
        for neighbor in adjacency.get(current, ()):
            if neighbor not in visited and not node_failed.get(neighbor, False):
                visited.add(neighbor)
                queue.append(neighbor)

    return True


def build_reinforced_fragility_params(
    coalition_S: Iterable[int],
    base_frag_params: Dict[int, FragilityParam],
    reinforce: ReinforcementModel,
) -> Dict[int, FragilityParam]:
    """補強状態 S を反映した fragility パラメータ辞書を生成する。"""
    coalition_set = set(coalition_S)
    updated: Dict[int, FragilityParam] = {}
    for node_id, frag in base_frag_params.items():
        if node_id in coalition_set:
            updated[node_id] = FragilityParam(
                node_id=node_id,
                alpha=frag.alpha * reinforce.alpha_factor,
                beta=frag.beta * reinforce.beta_factor,
            )
        else:
            updated[node_id] = frag
    return updated


def estimate_system_failure_probability(
    coalition_S: Set[int],
    graph: Graph,
    base_frag_params: Dict[int, FragilityParam],
    hazard: HazardScenario,
    gmpe: GmpeParam,
    reinforce: ReinforcementModel,
    config: SimulationConfig,
) -> float:
    """提携 S を補強した状態におけるシステム失敗確率 P_sys(S) を推定する。"""
    frag_params = build_reinforced_fragility_params(
        coalition_S=coalition_S,
        base_frag_params=base_frag_params,
        reinforce=reinforce,
    )

    rng = np.random.default_rng(config.random_seed)
    num_fail = 0

    for _ in range(config.num_samples):
        pga_samples = sample_pga_for_all_nodes(graph, hazard, gmpe, rng)
        node_failed = sample_node_failures(pga_samples, frag_params, rng)
        if check_system_failure(graph, node_failed):
            num_fail += 1

    return num_fail / float(config.num_samples)

