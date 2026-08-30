"""
RSGI (Rust Server Gateway Interface) support for Dreaming Electric Sheep.
Enables direct protocol integration with Granian RSGI interface.
"""
from __future__ import annotations

import logging
from typing import Any, List, Tuple

from dreaming_electric_sheep.scribe import (
    extract_rsgi_headers,
    instantiate_rsgi_request,
    send_rsgi_response,
    send_rsgi_response_sync,
)

logger = logging.getLogger("dreaming_electric_sheep.server")

__all__ = [
    "extract_rsgi_headers",
    "instantiate_rsgi_request",
    "send_rsgi_response",
    "send_rsgi_response_sync",
]
