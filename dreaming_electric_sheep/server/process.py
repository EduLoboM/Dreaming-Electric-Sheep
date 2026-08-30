"""
Provides functions related to the server process.
"""

import os
import signal
import warnings
from typing import TYPE_CHECKING

from dreaming_electric_sheep.utils import truthy

if TYPE_CHECKING:
    from dreaming_electric_sheep.server.application import Application

_STOPPING = False


def is_stopping() -> bool:
    """
    Returns a value indicating whether the server process received a SIGINT or a SIGTERM
    signal, and therefore the application is stopping.
    """
    if not truthy(os.environ.get("APP_SIGNAL_HANDLER", "")):
        warnings.warn(
            "This function can only be used if the env variable `APP_SIGNAL_HANDLER=1`"
            " is set.",
            UserWarning,
        )
        return False  # Return a default value since the function cannot proceed
    return _STOPPING


def _iter_supported_signals():
    for signal_name in ("SIGINT", "SIGTERM"):
        signal_type = getattr(signal, signal_name, None)
        if signal_type is None:
            continue
        try:
            signal.getsignal(signal_type)
        except (AttributeError, ValueError, OSError):
            continue
        yield signal_type


def use_shutdown_handler(app: "Application"):
    """
    Configures an application start event handler that listens to SIGTERM and SIGINT
    to know when the process is stopping.
    """

    @app.on_start
    async def configure_shutdown_handler():
        # See the conversation here:
        # https://github.com/encode/uvicorn/issues/1579#issuecomment-1419635974
        for signal_type in _iter_supported_signals():
            current_handler = signal.getsignal(signal_type)

            def terminate_now(signum, frame, current_handler=current_handler):
                global _STOPPING
                _STOPPING = True

                if callable(current_handler):
                    current_handler(signum, frame)  # type: ignore

            try:
                signal.signal(signal_type, terminate_now)
            except (ValueError, OSError):
                continue
