from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Node:
    """ネットワークノード。

    Attributes
    ----------
    id:
        ノード ID (1..n)。
    x, y:
        ノード座標。震源距離計算等に使用する。
    """

    id: int
    x: float
    y: float


@dataclass
class Edge:
    """ネットワークリンク。

    Attributes
    ----------
    u, v:
        接続するノード ID。
    directed:
        有向エッジかどうか。現状は False を基本とする。
    """

    u: int
    v: int
    directed: bool = False


@dataclass
class Graph:
    """ライフラインネットワークのグラフ表現。"""

    nodes: List[Node]
    edges: List[Edge]
    source_node_id: int
    sink_node_id: int

