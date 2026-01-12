from __future__ import annotations

from collections.abc import Iterable


def iter_bits(mask: int) -> Iterable[int]:
    while mask:
        lsb = mask & -mask
        idx = (lsb.bit_length() - 1)
        yield idx
        mask ^= lsb


def popcount(mask: int) -> int:
    return mask.bit_count()


def lowest_bit_index(mask: int) -> int:
    if mask == 0:
        raise ValueError("mask must be non-zero")
    return (mask & -mask).bit_length() - 1


def members_list(mask: int) -> list[int]:
    return list(iter_bits(mask))

