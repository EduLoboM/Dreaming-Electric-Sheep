"""
High-performance C/Cython extensions build configuration for Dreaming Electric Sheep.
Optimized exclusively for modern CPython (>= 3.11) with SIMD vectorization,
PEP 590 Vectorcall, and C-level memory arenas.
"""

import os
import sys
from setuptools import Extension, setup

COMPILE_ARGS = ["-O3", "-fPIC"]

if sys.platform != "win32":
    # On GCC/Clang enable pointer aliasing and math optimizations
    COMPILE_ARGS.extend(["-fstrict-aliasing"])

# Check for environment variable to skip extensions
skip_ext = (
    os.environ.get("DREAMING_ELECTRIC_SHEEP_NO_EXTENSIONS", "0") == "1"
    or os.environ.get("BLACKSHEEP_NO_EXTENSIONS", "0") == "1"
)

ext_modules = []
if not skip_ext:
    ext_modules = [
        Extension(
            "dreaming_electric_sheep.url",
            [
                "dreaming_electric_sheep/url.c",
                "dreaming_electric_sheep/simd_ops.c",
            ],
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
            [
                "dreaming_electric_sheep/messages.c",
                "dreaming_electric_sheep/scratchpad.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.scribe",
            [
                "dreaming_electric_sheep/scribe.c",
                "dreaming_electric_sheep/simd_ops.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.baseapp",
            ["dreaming_electric_sheep/baseapp.c"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.routing",
            [
                "dreaming_electric_sheep/routing.c",
                "dreaming_electric_sheep/simd_ops.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
    ]

setup(ext_modules=ext_modules)

