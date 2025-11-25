from __future__ import annotations

from enum import Enum
from typing import Protocol

import numpy as np


class GameType(Enum):
    PROTECTION = "protection"
    DAMAGE_REDUCTION = "damage_reduction"
    CREDIT_ALLOCATION = "credit_allocation"


class ValueFunction(Protocol):
    """
    Protocol for cooperative-game characteristic functions v(S).
    """

    game_type: GameType

    def evaluate(self, coalition: np.ndarray) -> float:
        """
        Evaluate v(S) for a given coalition mask.

        Parameters
        ----------
        coalition : np.ndarray of shape (N,), bool
            coalition[i] is True if player i is in S.
        """

