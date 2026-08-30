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

- `_des_core`: Shared singleton owning the static intern table, SIMD intrinsics, and scratchpad arenas.
- `fast_parse.h`: C `des_err` Result codes and integer / hex parsers.
- `simd_ops.c`: Vectorized ASCII lowercasing, CRLF scanning, and URL validation.
- `scratchpad.c`: 64-byte cacheline aligned bump allocator for standard request lifecycles.
