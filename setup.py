"""
This file is used to specify Python extensions, which are used when using Cython.
Extensions are used only if the current runtime is CPython and only if there is not an
environment variable: `DREAMING_ELECTRIC_SHEEP_NO_EXTENSIONS=1`.
The logic is to support PyPy.
"""

import os
from setuptools import Extension, setup
import platform

COMPILE_ARGS = ["-O2"]

# Check for environment variable to skip extensions
skip_ext = (
    os.environ.get("DREAMING_ELECTRIC_SHEEP_NO_EXTENSIONS", "0") == "1"
    or os.environ.get("BLACKSHEEP_NO_EXTENSIONS", "0") == "1"
)


if platform.python_implementation() == "CPython" and not skip_ext:
    ext_modules = [
        Extension(
            "dreaming_electric_sheep.url",
            ["dreaming_electric_sheep/url.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.exceptions",
            ["dreaming_electric_sheep/exceptions.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.headers",
            ["dreaming_electric_sheep/headers.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.cookies",
            ["dreaming_electric_sheep/cookies.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.contents",
            ["dreaming_electric_sheep/contents.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.messages",
            ["dreaming_electric_sheep/messages.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.scribe",
            ["dreaming_electric_sheep/scribe.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.baseapp",
            ["dreaming_electric_sheep/baseapp.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
    ]
else:
    ext_modules = []

setup(ext_modules=ext_modules)

