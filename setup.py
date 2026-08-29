"""
High-performance C/Cython extensions build configuration for Dreaming Electric Sheep.
Optimized exclusively for modern CPython (>= 3.13) with SIMD vectorization,
PEP 590 Vectorcall, and C-level memory arenas.
"""

import os
import sys
from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

if sys.platform == "win32":
    COMPILE_ARGS = ["/O2"]
else:
    COMPILE_ARGS = ["-O3", "-fPIC", "-fstrict-aliasing"]

# Check for environment variable to skip extensions
skip_ext = (
    os.environ.get("DREAMING_ELECTRIC_SHEEP_NO_EXTENSIONS", "0") == "1"
    or os.environ.get("BLACKSHEEP_NO_EXTENSIONS", "0") == "1"
)

ext = ".pyx" if USE_CYTHON else ".c"

ext_modules = []
if not skip_ext:
    ext_modules = [
        Extension(
            "dreaming_electric_sheep.url",
            [
                f"dreaming_electric_sheep/url{ext}",
                "dreaming_electric_sheep/simd_ops.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.exceptions",
            [f"dreaming_electric_sheep/exceptions{ext}"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.headers",
            [f"dreaming_electric_sheep/headers{ext}"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.cookies",
            [f"dreaming_electric_sheep/cookies{ext}"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.contents",
            [f"dreaming_electric_sheep/contents{ext}"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.messages",
            [
                f"dreaming_electric_sheep/messages{ext}",
                "dreaming_electric_sheep/scratchpad.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.scribe",
            [
                f"dreaming_electric_sheep/scribe{ext}",
                "dreaming_electric_sheep/simd_ops.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.baseapp",
            [f"dreaming_electric_sheep/baseapp{ext}"],
            extra_compile_args=COMPILE_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.routing",
            [
                f"dreaming_electric_sheep/routing{ext}",
                "dreaming_electric_sheep/simd_ops.c",
            ],
            extra_compile_args=COMPILE_ARGS,
        ),
    ]

    if USE_CYTHON:
        ext_modules = cythonize(
            ext_modules,
            compiler_directives={"language_level": "3"},
        )

setup(ext_modules=ext_modules)

