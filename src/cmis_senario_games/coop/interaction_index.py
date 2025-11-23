from __future__ import annotations

from typing import Dict, Iterable, Set

from ..core.game import ResilienceGame


def interaction_index(
    game: ResilienceGame,
    coalition_T: Set[int],
) -> float:
    """シナジー指標 / 相互作用指標 I(T) を計算するための骨組み関数。

    ここではインターフェースのみ定義し、具体的な算出式は
    論文の定義に基づき後続フェーズで実装する。
    """
    # TODO: 論文で定義された I(T) の実装
    raise NotImplementedError("interaction_index is not implemented yet.")

