"""
Command-line interface package for Dreaming Electric Sheep.
"""


def main():
    from dreaming_electric_sheep.cli.main import main as _main

    return _main()


__all__ = ["main"]
