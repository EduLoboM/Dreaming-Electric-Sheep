"""
High-performance data structures for Dreaming Electric Sheep.
"""

from typing import TypeVar

import msgspec

T = TypeVar("T")


class Struct(msgspec.Struct, frozen=True):
    """
    Base Struct class for Dreaming Electric Sheep.

    By default, it uses `frozen=True` to minimize memory footprint in C (~48 bytes),
    enable aggressive compiler register optimizations, provide native immutability,
    and make instances hashable.
    """

    pass


def struct(cls=None, *, frozen: bool = True, omit_defaults: bool = False, rename=None):
    """
    Decorator or helper to define a msgspec Struct with `frozen=True` by default.
    """

    def decorator(c):
        return msgspec.defstruct(
            c.__name__,
            [
                (f, getattr(c, f, msgspec.NODEFAULT))
                for f in getattr(c, "__annotations__", {})
            ],
            frozen=frozen,
            omit_defaults=omit_defaults,
            rename=rename,
        )

    if cls is not None:
        return decorator(cls)
    return decorator
