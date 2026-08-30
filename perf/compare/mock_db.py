"""
Shared in-memory mock database fixtures and deterministic data accessors.
Provides uniform data structures and logic across all benchmarked frameworks.
Localhost framework overhead test fixtures (not Postgres / not TechEmpower).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, List, Dict

# Pre-generate 10,000 World records
_INITIAL_WORLDS: Dict[int, int] = {
    i: random.randint(1, 10000) for i in range(1, 10001)
}

_WORLD_DATA: Dict[int, int] = dict(_INITIAL_WORLDS)

# Canonical 12 Fortunes
_INITIAL_FORTUNES: List[tuple[int, str]] = [
    (1, "fortune: No such file or directory"),
    (2, "A computer program does what you tell it to do, not what you want it to do."),
    (3, "Emacs is a nice operating system, but it lacks a good text editor."),
    (4, "Any program that runs right is obsolete."),
    (5, "A list is only as strong as its weakest link. — Donald Knuth"),
    (6, "Feature: A bug with seniority."),
    (7, "Computers make very fast, very accurate mistakes."),
    (8, '<script>alert("This should not be displayed in a browser alert box.");</script>'),
    (9, "フレームワークのベンチマーク"),
    (10, "An ounce of practice is worth a pound of theory."),
    (11, "Programmers are tools for converting caffeine into code."),
    (12, "About astrology: Most software designers are definitely not Pisces."),
]


@dataclass
class FortuneItem:
    id: int
    message: str


_STATIC_FORTUNES: List[FortuneItem] = [
    FortuneItem(id=fid, message=msg) for fid, msg in _INITIAL_FORTUNES
]


def clamp_queries(raw: Any) -> int:
    """Clamps queries query-param between 1 and 500."""
    if raw is None:
        return 1
    try:
        if isinstance(raw, (list, tuple)):
            raw = raw[0] if raw else 1
        val = int(raw)
        if val < 1:
            return 1
        if val > 500:
            return 500
        return val
    except (ValueError, TypeError):
        return 1


def get_single_world() -> Dict[str, int]:
    """Fetch one random world record."""
    wid = random.randint(1, 10000)
    return {"id": wid, "randomNumber": _WORLD_DATA.get(wid, wid)}


def get_multiple_worlds(count: int) -> List[Dict[str, int]]:
    """Fetch `count` random world records."""
    res = []
    for _ in range(count):
        wid = random.randint(1, 10000)
        res.append({"id": wid, "randomNumber": _WORLD_DATA.get(wid, wid)})
    return res


def get_fortunes_sorted() -> List[FortuneItem]:
    """Get 12 static fortunes + 1 dynamic fortune, sorted by message."""
    fortunes = list(_STATIC_FORTUNES)
    fortunes.append(FortuneItem(id=0, message="Additional fortune added at request time."))
    fortunes.sort(key=lambda x: x.message)
    return fortunes


def update_multiple_worlds(count: int) -> List[Dict[str, int]]:
    """Fetch `count` records, update random number, save and return."""
    res = []
    for _ in range(count):
        wid = random.randint(1, 10000)
        new_rand = random.randint(1, 10000)
        _WORLD_DATA[wid] = new_rand
        res.append({"id": wid, "randomNumber": new_rand})
    return res


FORTUNES_HTML_TEMPLATE = """<!DOCTYPE html><html><head><title>Fortunes</title></head><body><table><tr><th>id</th><th>message</th></tr>{% for fortune in fortunes %}<tr><td>{{ fortune.id }}</td><td>{{ fortune.message }}</td></tr>{% endfor %}</table></body></html>"""
