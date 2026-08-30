# Development & C Core Engineering Guide

This document describes how to develop, test, and profile **Dreaming Electric Sheep** with C-level sanitizers and optimizations.

---

## 1. Local Development Setup

Ensure you have Python 3.13 or 3.14 installed with development headers, a modern C compiler (`gcc` or `clang` with AVX2 / SSE4.2 support), and Cython:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make compile
pytest tests/
```

---

## 2. AddressSanitizer (ASAN) and UndefinedBehaviorSanitizer (UBSAN)

The C core (`_des_core.so`) and Cython extensions can be compiled with LLVM/GCC sanitizers to catch memory corruption, out-of-bounds access, use-after-free, and integer overflows.

### Running with Make

```bash
make asan
```

### Manual In-Tree Build & Run

```bash
# 1. Clean previous build artifacts
make clean

# 2. Build extensions with ASAN/UBSAN instrumentation
CFLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
LDFLAGS="-fsanitize=address,undefined" \
python3 setup.py build_ext --inplace

# 3. Execute test suite with ASAN & UBSAN environment flags
ASAN_OPTIONS="detect_leaks=0:symbolize=1:abort_on_error=1" \
UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1" \
LD_PRELOAD="$(gcc -print-file-name=libasan.so)" \
pytest tests/
```

> **Note**: CPython itself performs internal memory arena management. `detect_leaks=0` is recommended so CPython's own static allocations do not trigger false leak reports, while ASAN memory bounds and use-after-free checks remain fully active.

---

## 3. Profile-Guided Optimization (PGO)

Profile-Guided Optimization provides a 5–15% throughput increase on hot paths by compiling extensions with branch-prediction and layout data gathered from real workloads.

### Running 2-Stage PGO Build

```bash
make pgo
```

### Manual Steps:
1. **Instrumented Build**:
   ```bash
   CFLAGS="-fprofile-generate -O3" LDFLAGS="-fprofile-generate" python3 setup.py build_ext --inplace
   ```
2. **Train on Benchmark / Workload**:
   ```bash
   pytest tests/test_c_resilience_and_optimizations.py tests/test_des_core_intern.py tests/test_des_simd_scratchpad.py tests/test_des_core_errors.py
   ```
3. **Profile-Optimized Build**:
   ```bash
   CFLAGS="-fprofile-use -fprofile-correction -O3" LDFLAGS="-fprofile-use" python3 setup.py build_ext --inplace
   ```

---

## 4. Architecture & Hot Path Components

- `_des_core`: Shared singleton owning the static intern table, SIMD runtime dispatch, and scratchpad arenas.
- `fast_parse.h`: C `des_err` Result codes and integer / hex parsers.
- `simd_ops.c`: Multi-ISA vectorization kernels (`AVX2`, `SSE2`, `NEON`, `SCALAR`) with runtime CPUID dispatch.
- `scratchpad.c`: 64-byte cacheline aligned bump allocator for standard request lifecycles.

---

## 5. SIMD Runtime CPUID Dispatch & Portable Wheels

To guarantee that binary wheels remain universally portable across all x86_64 machines without causing `SIGILL` on older CPUs, `setup.py` compiles with generic baseline flags (no global `-mavx2` or `-march=native`).

Multi-ISA dispatch is implemented inside `simd_ops.c`:
1. **Multiple Kernel Targets**: Functions are compiled with GCC/Clang target attributes (`__attribute__((target("avx2")))`, `__attribute__((target("sse2")))`, portable scalar SWAR, and ARM NEON).
2. **CPUID Initialization**: When `_des_core` initializes, `__builtin_cpu_init()` checks host CPU features (`__builtin_cpu_supports("avx2")`) and fills the global `DesSimdOps` function pointer table once.
3. **Zero-Overhead Call Sites**: Cython and C call sites dispatch directly through the resolved function pointers without per-request CPUID checks.

---

## 6. Honest Comparative Benchmarks (`perf/compare`)

To measure framework overhead accurately against FastAPI and Litestar:

```bash
# Install comparison dependencies (Granian, FastAPI, Litestar, oha)
pip install -r perf/requirements-bench.txt

# Run the automated benchmark harness
./perf/compare/run.sh
```

- **Tooling**: Uses `oha` (Rust HTTP load generator) across identical Granian (Rust ASGI) server configurations (1 worker, 50 concurrency, 10s duration).
- **Smoke Tests**: The `des bench` CLI command is a lightweight development and smoke-testing tool. Published comparison numbers come strictly from `perf/compare/run.sh` with `oha`.
