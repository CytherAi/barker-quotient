"""
barker.known_configs
=====================
Single source of truth for all known minimal covering hard-prime configurations.

Every module that needs the known-config list imports from here.
"""

from __future__ import annotations

KNOWN_MINIMAL_COVERING_TRIPLES: list[tuple[int, ...]] = [
    (73, 233, 1721),
    (73, 1609, 1801),
    (89, 601, 2969),
    (233, 337, 2969),
    (937, 1609, 4057),
    (1289, 1433, 1609),
    (1913, 2089, 3257),
]

KNOWN_MINIMAL_COVERING_4SETS: list[tuple[int, ...]] = [
    (337, 937, 1433, 1721),
]

KNOWN_MINIMAL_COVERING_5SETS: list[tuple[int, ...]] = [
    (89, 1721, 4177, 6553, 7529),
    (233, 881, 4201, 6553, 6857),
    (1913, 4057, 6089, 6353, 7753),
    (4297, 4409, 5689, 6553, 7753),
]

ALL_KNOWN_MINIMAL_COVERING: list[frozenset[int]] = [
    frozenset(s) for s in (
        KNOWN_MINIMAL_COVERING_TRIPLES
        + KNOWN_MINIMAL_COVERING_4SETS
        + KNOWN_MINIMAL_COVERING_5SETS
    )
]
