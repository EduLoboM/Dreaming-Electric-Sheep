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

import sysconfig
import shutil
from setuptools.command.build_ext import build_ext as _build_ext

if sys.platform == "win32":
    COMPILE_ARGS = ["/O2", "/GL"]
    LINK_ARGS = ["/LTCG"]
    CYTHON_LINK_ARGS = LINK_ARGS
else:
    COMPILE_ARGS = ["-O3", "-fPIC", "-fstrict-aliasing", "-flto", "-fuse-linker-plugin"]
    LINK_ARGS = ["-flto", "-fuse-linker-plugin"]
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    CYTHON_LINK_ARGS = LINK_ARGS + [
        "-Wl,-rpath,$ORIGIN",
        "-Ldreaming_electric_sheep",
        f"-l:_des_core{ext_suffix}",
    ]

class CustomBuildExt(_build_ext):
    def build_extensions(self):
        core_ext = next((e for e in self.extensions if e.name.endswith("._des_core")), None)
        other_exts = [e for e in self.extensions if not e.name.endswith("._des_core")]
        if core_ext:
            self.build_extension(core_ext)
            core_so_path = self.get_ext_fullpath(core_ext.name)
            target_dir = os.path.abspath("dreaming_electric_sheep")
            if os.path.exists(core_so_path):
                shutil.copy(core_so_path, target_dir)
            build_target_dir = os.path.abspath(os.path.dirname(core_so_path))
            for e in other_exts:
                if target_dir not in e.library_dirs:
                    e.library_dirs.append(target_dir)
                if build_target_dir not in e.library_dirs:
                    e.library_dirs.append(build_target_dir)
        for ext in other_exts:
            self.build_extension(ext)

# Check for environment variable to skip extensions
skip_ext = (
    os.environ.get("DREAMING_ELECTRIC_SHEEP_NO_EXTENSIONS", "0") == "1"
    or os.environ.get("BLACKSHEEP_NO_EXTENSIONS", "0") == "1"
)

ext = ".pyx" if USE_CYTHON else ".c"

ext_modules = []
if not skip_ext:
    # 1. Unified compiled core owning intern table, SIMD intrinsics, and memory arenas
    des_core_ext = Extension(
        "dreaming_electric_sheep._des_core",
        [
            "dreaming_electric_sheep/_des_core.c",
            "dreaming_electric_sheep/interning.c",
            "dreaming_electric_sheep/scratchpad.c",
            "dreaming_electric_sheep/simd_ops.c",
        ],
        include_dirs=["dreaming_electric_sheep"],
        extra_compile_args=COMPILE_ARGS,
        extra_link_args=LINK_ARGS,
    )

    # 2. Cython extensions (linking against unified core)
    cython_extensions = [
        Extension(
            "dreaming_electric_sheep.url",
            [f"dreaming_electric_sheep/url{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.exceptions",
            [f"dreaming_electric_sheep/exceptions{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.headers",
            [f"dreaming_electric_sheep/headers{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.cookies",
            [f"dreaming_electric_sheep/cookies{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.contents",
            [f"dreaming_electric_sheep/contents{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.messages",
            [f"dreaming_electric_sheep/messages{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.scribe",
            [f"dreaming_electric_sheep/scribe{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.baseapp",
            [f"dreaming_electric_sheep/baseapp{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
        Extension(
            "dreaming_electric_sheep.routing",
            [f"dreaming_electric_sheep/routing{ext}"],
            include_dirs=["dreaming_electric_sheep"],
            extra_compile_args=COMPILE_ARGS,
            extra_link_args=CYTHON_LINK_ARGS,
        ),
    ]

    if USE_CYTHON:
        cython_extensions = cythonize(
            cython_extensions,
            compiler_directives={"language_level": "3"},
        )

    ext_modules = [des_core_ext] + cython_extensions

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": CustomBuildExt},
)

