"""
Raw ASGI benchmark application running directly on Uvicorn (uvloop + httptools).
Measures the pure Uvicorn ASGI server ceiling.
"""
from perf.compare.granian_raw_app import app

__all__ = ["app"]
