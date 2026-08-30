#define DES_BUILDING_CORE 1

#include "simd_ops.h"
#include <string.h>

#if defined(_MSC_VER) && !defined(__clang__)
    #include <intrin.h>
    static inline int __des_ctz(uint32_t mask) {
        unsigned long index;
        _BitScanForward(&index, mask);
        return (int)index;
    }
    #define __builtin_ctz(x) __des_ctz(x)
#endif

#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__) || defined(_M_IX86)
    #include <immintrin.h>
    #include <emmintrin.h>
    #define X86_TARGETS_AVAILABLE 1
#elif defined(__ARM_NEON) || defined(__aarch64__) || defined(_M_ARM64)
    #if defined(_MSC_VER) && !defined(__clang__)
        #include <arm64_neon.h>
    #else
        #include <arm_neon.h>
    #endif
    #define ARM_NEON_AVAILABLE 1
#endif

/* ========================================================================= */
/* 1. SCALAR KERNELS (Portable C)                                            */
/* ========================================================================= */

static int64_t simd_find_crlf_scalar(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length < 2)) {
        return -1;
    }
    for (size_t i = 0; i + 1 < length; ++i) {
        if (buffer[i] == '\r' && buffer[i + 1] == '\n') {
            return (int64_t)i;
        }
    }
    return -1;
}

static int64_t simd_find_crlf_crlf_scalar(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length < 4)) {
        return -1;
    }
    for (size_t i = 0; i + 3 < length; ++i) {
        if (buffer[i] == '\r' &&
            buffer[i + 1] == '\n' &&
            buffer[i + 2] == '\r' &&
            buffer[i + 3] == '\n') {
            return (int64_t)i;
        }
    }
    return -1;
}

static int64_t simd_find_path_separator_scalar(const char * __restrict__ buffer, size_t length, size_t start_pos) {
    if (DES_UNLIKELY(buffer == NULL || start_pos >= length)) {
        return -1;
    }
    for (size_t i = start_pos; i < length; ++i) {
        char c = buffer[i];
        if (c == '/' || c == '?' || c == '#' || c == ' ') {
            return (int64_t)i;
        }
    }
    return -1;
}

static int simd_validate_url_ascii_scalar(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL)) {
        return 0;
    }
    for (size_t i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)buffer[i];
        if (DES_UNLIKELY(c < 32 || c > 126)) {
            return 0;
        }
    }
    return 1;
}

static uint32_t simd_fast_hash_scalar(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length == 0)) {
        return 0;
    }
    uint32_t hash = 2166136261u;
    size_t i = 0;
    while (i + 4 <= length) {
        uint32_t val;
        memcpy(&val, buffer + i, 4);
        hash = (hash ^ (val & 0xFF)) * 16777619u;
        hash = (hash ^ ((val >> 8) & 0xFF)) * 16777619u;
        hash = (hash ^ ((val >> 16) & 0xFF)) * 16777619u;
        hash = (hash ^ ((val >> 24) & 0xFF)) * 16777619u;
        i += 4;
    }
    for (; i < length; ++i) {
        hash = (hash ^ ((unsigned char)buffer[i])) * 16777619u;
    }
    return hash;
}

static void simd_lowercase_ascii_scalar(const char * __restrict__ src, char * __restrict__ dst, size_t length) {
    if (DES_UNLIKELY(src == NULL || dst == NULL || length == 0)) {
        return;
    }
    size_t i = 0;
    while (i + 8 <= length) {
        uint64_t v;
        memcpy(&v, src + i, 8);
        for (int k = 0; k < 8; ++k) {
            unsigned char c = (unsigned char)((v >> (k * 8)) & 0xFF);
            if (c >= 'A' && c <= 'Z') {
                c = (unsigned char)(c + 32);
            }
            dst[i + k] = (char)c;
        }
        i += 8;
    }
    for (; i < length; ++i) {
        unsigned char c = (unsigned char)src[i];
        if (c >= 'A' && c <= 'Z') {
            c = (unsigned char)(c + 32);
        }
        dst[i] = (char)c;
    }
}

static int simd_is_ascii_lowercase_scalar(const char * __restrict__ s, size_t length) {
    if (DES_UNLIKELY(s == NULL || length == 0)) {
        return 1;
    }
    for (size_t i = 0; i < length; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (DES_UNLIKELY(c >= 'A' && c <= 'Z')) {
            return 0;
        }
    }
    return 1;
}


/* ========================================================================= */
/* 2. SSE2 KERNELS (x86_64 Baseline / Target SSE2)                           */
/* ========================================================================= */

#if defined(X86_TARGETS_AVAILABLE) && (defined(__GNUC__) || defined(__clang__))
#define DES_TARGET_SSE2 __attribute__((target("sse2")))
#define DES_TARGET_AVX2 __attribute__((target("avx2")))
#else
#define DES_TARGET_SSE2
#define DES_TARGET_AVX2
#endif

#if defined(X86_TARGETS_AVAILABLE)

DES_TARGET_SSE2
static int64_t simd_find_crlf_sse2(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length < 2)) {
        return -1;
    }
    size_t i = 0;
    __m128i cr = _mm_set1_epi8('\r');
    while (i + 16 <= length) {
        DES_PREFETCH(buffer + i + 32, 0, 3);
        __m128i chunk = _mm_loadu_si128((const __m128i *)(buffer + i));
        __m128i cmp = _mm_cmpeq_epi8(chunk, cr);
        uint32_t mask = (uint32_t)_mm_movemask_epi8(cmp);

        while (mask != 0) {
            int bit = __builtin_ctz(mask);
            size_t pos = i + (size_t)bit;
            if (pos + 1 < length && buffer[pos + 1] == '\n') {
                return (int64_t)pos;
            }
            mask &= mask - 1;
        }
        i += 16;
    }
    for (; i + 1 < length; ++i) {
        if (buffer[i] == '\r' && buffer[i + 1] == '\n') {
            return (int64_t)i;
        }
    }
    return -1;
}

DES_TARGET_SSE2
static int64_t simd_find_crlf_crlf_sse2(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length < 4)) {
        return -1;
    }
    size_t i = 0;
    __m128i cr = _mm_set1_epi8('\r');
    while (i + 16 <= length) {
        DES_PREFETCH(buffer + i + 32, 0, 3);
        __m128i chunk = _mm_loadu_si128((const __m128i *)(buffer + i));
        __m128i cmp = _mm_cmpeq_epi8(chunk, cr);
        uint32_t mask = (uint32_t)_mm_movemask_epi8(cmp);

        while (mask != 0) {
            int bit = __builtin_ctz(mask);
            size_t pos = i + (size_t)bit;
            if (pos + 3 < length &&
                buffer[pos + 1] == '\n' &&
                buffer[pos + 2] == '\r' &&
                buffer[pos + 3] == '\n') {
                return (int64_t)pos;
            }
            mask &= mask - 1;
        }
        i += 16;
    }
    for (; i + 3 < length; ++i) {
        if (buffer[i] == '\r' &&
            buffer[i + 1] == '\n' &&
            buffer[i + 2] == '\r' &&
            buffer[i + 3] == '\n') {
            return (int64_t)i;
        }
    }
    return -1;
}

DES_TARGET_SSE2
static int64_t simd_find_path_separator_sse2(const char * __restrict__ buffer, size_t length, size_t start_pos) {
    if (DES_UNLIKELY(buffer == NULL || start_pos >= length)) {
        return -1;
    }
    size_t i = start_pos;
    __m128i slash = _mm_set1_epi8('/');
    __m128i quest = _mm_set1_epi8('?');
    __m128i hash  = _mm_set1_epi8('#');
    __m128i space = _mm_set1_epi8(' ');

    while (i + 16 <= length) {
        DES_PREFETCH(buffer + i + 32, 0, 3);
        __m128i chunk = _mm_loadu_si128((const __m128i *)(buffer + i));
        __m128i m1 = _mm_cmpeq_epi8(chunk, slash);
        __m128i m2 = _mm_cmpeq_epi8(chunk, quest);
        __m128i m3 = _mm_cmpeq_epi8(chunk, hash);
        __m128i m4 = _mm_cmpeq_epi8(chunk, space);
        __m128i matched = _mm_or_si128(_mm_or_si128(m1, m2), _mm_or_si128(m3, m4));
        uint32_t mask = (uint32_t)_mm_movemask_epi8(matched);

        if (mask != 0) {
            int bit = __builtin_ctz(mask);
            return (int64_t)(i + (size_t)bit);
        }
        i += 16;
    }
    for (; i < length; ++i) {
        char c = buffer[i];
        if (c == '/' || c == '?' || c == '#' || c == ' ') {
            return (int64_t)i;
        }
    }
    return -1;
}

DES_TARGET_SSE2
static int simd_validate_url_ascii_sse2(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL)) {
        return 0;
    }
    size_t i = 0;
    __m128i min_val = _mm_set1_epi8(32);
    __m128i max_val = _mm_set1_epi8(126);

    while (i + 16 <= length) {
        DES_PREFETCH(buffer + i + 32, 0, 3);
        __m128i chunk = _mm_loadu_si128((const __m128i *)(buffer + i));
        __m128i lt = _mm_cmpgt_epi8(min_val, chunk);
        __m128i gt = _mm_cmpgt_epi8(chunk, max_val);
        __m128i invalid = _mm_or_si128(lt, gt);
        if (DES_UNLIKELY(_mm_movemask_epi8(invalid) != 0)) {
            return 0;
        }
        i += 16;
    }
    for (; i < length; ++i) {
        unsigned char c = (unsigned char)buffer[i];
        if (DES_UNLIKELY(c < 32 || c > 126)) {
            return 0;
        }
    }
    return 1;
}

DES_TARGET_SSE2
static void simd_lowercase_ascii_sse2(const char * __restrict__ src, char * __restrict__ dst, size_t length) {
    if (DES_UNLIKELY(src == NULL || dst == NULL || length == 0)) {
        return;
    }
    size_t i = 0;
    __m128i a_minus_1 = _mm_set1_epi8('A' - 1);
    __m128i z_plus_1 = _mm_set1_epi8('Z' + 1);
    __m128i diff = _mm_set1_epi8(32);

    while (i + 16 <= length) {
        DES_PREFETCH(src + i + 32, 0, 3);
        __m128i chunk = _mm_loadu_si128((const __m128i *)(src + i));
        __m128i ge_a = _mm_cmpgt_epi8(chunk, a_minus_1);
        __m128i le_z = _mm_cmpgt_epi8(z_plus_1, chunk);
        __m128i is_upper = _mm_and_si128(ge_a, le_z);
        __m128i to_add = _mm_and_si128(is_upper, diff);
        __m128i result = _mm_add_epi8(chunk, to_add);
        _mm_storeu_si128((__m128i *)(dst + i), result);
        i += 16;
    }
    simd_lowercase_ascii_scalar(src + i, dst + i, length - i);
}

DES_TARGET_SSE2
static int simd_is_ascii_lowercase_sse2(const char * __restrict__ s, size_t length) {
    if (DES_UNLIKELY(s == NULL || length == 0)) {
        return 1;
    }
    size_t i = 0;
    __m128i a_minus_1 = _mm_set1_epi8('A' - 1);
    __m128i z_plus_1 = _mm_set1_epi8('Z' + 1);

    while (i + 16 <= length) {
        __m128i chunk = _mm_loadu_si128((const __m128i *)(s + i));
        __m128i ge_a = _mm_cmpgt_epi8(chunk, a_minus_1);
        __m128i le_z = _mm_cmpgt_epi8(z_plus_1, chunk);
        __m128i is_upper = _mm_and_si128(ge_a, le_z);
        if (DES_UNLIKELY(_mm_movemask_epi8(is_upper) != 0)) {
            return 0;
        }
        i += 16;
    }
    return simd_is_ascii_lowercase_scalar(s + i, length - i);
}


/* ========================================================================= */
/* 3. AVX2 KERNELS (Target AVX2)                                             */
/* ========================================================================= */

DES_TARGET_AVX2
static int64_t simd_find_crlf_avx2(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length < 2)) {
        return -1;
    }
    size_t i = 0;
    __m256i cr = _mm256_set1_epi8('\r');
    while (i + 32 <= length) {
        DES_PREFETCH(buffer + i + 64, 0, 3);
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(buffer + i));
        __m256i cmp = _mm256_cmpeq_epi8(chunk, cr);
        uint32_t mask = (uint32_t)_mm256_movemask_epi8(cmp);

        while (mask != 0) {
            int bit = __builtin_ctz(mask);
            size_t pos = i + (size_t)bit;
            if (pos + 1 < length && buffer[pos + 1] == '\n') {
                return (int64_t)pos;
            }
            mask &= mask - 1;
        }
        i += 32;
    }
    return simd_find_crlf_sse2(buffer + i, length - i) == -1 ? -1 : (int64_t)i + simd_find_crlf_sse2(buffer + i, length - i);
}

DES_TARGET_AVX2
static int64_t simd_find_crlf_crlf_avx2(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL || length < 4)) {
        return -1;
    }
    size_t i = 0;
    __m256i cr = _mm256_set1_epi8('\r');
    while (i + 32 <= length) {
        DES_PREFETCH(buffer + i + 64, 0, 3);
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(buffer + i));
        __m256i cmp = _mm256_cmpeq_epi8(chunk, cr);
        uint32_t mask = (uint32_t)_mm256_movemask_epi8(cmp);

        while (mask != 0) {
            int bit = __builtin_ctz(mask);
            size_t pos = i + (size_t)bit;
            if (pos + 3 < length &&
                buffer[pos + 1] == '\n' &&
                buffer[pos + 2] == '\r' &&
                buffer[pos + 3] == '\n') {
                return (int64_t)pos;
            }
            mask &= mask - 1;
        }
        i += 32;
    }
    return simd_find_crlf_crlf_sse2(buffer + i, length - i) == -1 ? -1 : (int64_t)i + simd_find_crlf_crlf_sse2(buffer + i, length - i);
}

DES_TARGET_AVX2
static int64_t simd_find_path_separator_avx2(const char * __restrict__ buffer, size_t length, size_t start_pos) {
    if (DES_UNLIKELY(buffer == NULL || start_pos >= length)) {
        return -1;
    }
    size_t i = start_pos;
    __m256i slash = _mm256_set1_epi8('/');
    __m256i quest = _mm256_set1_epi8('?');
    __m256i hash  = _mm256_set1_epi8('#');
    __m256i space = _mm256_set1_epi8(' ');

    while (i + 32 <= length) {
        DES_PREFETCH(buffer + i + 64, 0, 3);
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(buffer + i));
        __m256i m1 = _mm256_cmpeq_epi8(chunk, slash);
        __m256i m2 = _mm256_cmpeq_epi8(chunk, quest);
        __m256i m3 = _mm256_cmpeq_epi8(chunk, hash);
        __m256i m4 = _mm256_cmpeq_epi8(chunk, space);
        __m256i matched = _mm256_or_si256(_mm256_or_si256(m1, m2), _mm256_or_si256(m3, m4));
        uint32_t mask = (uint32_t)_mm256_movemask_epi8(matched);

        if (mask != 0) {
            int bit = __builtin_ctz(mask);
            return (int64_t)(i + (size_t)bit);
        }
        i += 32;
    }
    return simd_find_path_separator_sse2(buffer, length, i);
}

DES_TARGET_AVX2
static int simd_validate_url_ascii_avx2(const char * __restrict__ buffer, size_t length) {
    if (DES_UNLIKELY(buffer == NULL)) {
        return 0;
    }
    size_t i = 0;
    __m256i min_val = _mm256_set1_epi8(32);
    __m256i max_val = _mm256_set1_epi8(126);

    while (i + 32 <= length) {
        DES_PREFETCH(buffer + i + 64, 0, 3);
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(buffer + i));
        __m256i lt = _mm256_cmpgt_epi8(min_val, chunk);
        __m256i gt = _mm256_cmpgt_epi8(chunk, max_val);
        __m256i invalid = _mm256_or_si256(lt, gt);
        if (DES_UNLIKELY(_mm256_movemask_epi8(invalid) != 0)) {
            return 0;
        }
        i += 32;
    }
    return simd_validate_url_ascii_sse2(buffer + i, length - i);
}

DES_TARGET_AVX2
static void simd_lowercase_ascii_avx2(const char * __restrict__ src, char * __restrict__ dst, size_t length) {
    if (DES_UNLIKELY(src == NULL || dst == NULL || length == 0)) {
        return;
    }
    size_t i = 0;
    __m256i a_minus_1 = _mm256_set1_epi8('A' - 1);
    __m256i z_plus_1 = _mm256_set1_epi8('Z' + 1);
    __m256i diff = _mm256_set1_epi8(32);

    while (i + 32 <= length) {
        DES_PREFETCH(src + i + 64, 0, 3);
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(src + i));
        __m256i ge_a = _mm256_cmpgt_epi8(chunk, a_minus_1);
        __m256i le_z = _mm256_cmpgt_epi8(z_plus_1, chunk);
        __m256i is_upper = _mm256_and_si256(ge_a, le_z);
        __m256i to_add = _mm256_and_si256(is_upper, diff);
        __m256i result = _mm256_add_epi8(chunk, to_add);
        _mm256_storeu_si256((__m256i *)(dst + i), result);
        i += 32;
    }
    simd_lowercase_ascii_sse2(src + i, dst + i, length - i);
}

DES_TARGET_AVX2
static int simd_is_ascii_lowercase_avx2(const char * __restrict__ s, size_t length) {
    if (DES_UNLIKELY(s == NULL || length == 0)) {
        return 1;
    }
    size_t i = 0;
    __m256i a_minus_1 = _mm256_set1_epi8('A' - 1);
    __m256i z_plus_1 = _mm256_set1_epi8('Z' + 1);

    while (i + 32 <= length) {
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(s + i));
        __m256i ge_a = _mm256_cmpgt_epi8(chunk, a_minus_1);
        __m256i le_z = _mm256_cmpgt_epi8(z_plus_1, chunk);
        __m256i is_upper = _mm256_and_si256(ge_a, le_z);
        if (DES_UNLIKELY(_mm256_movemask_epi8(is_upper) != 0)) {
            return 0;
        }
        i += 32;
    }
    return simd_is_ascii_lowercase_sse2(s + i, length - i);
}

#endif /* X86_TARGETS_AVAILABLE */


/* ========================================================================= */
/* 4. RUNTIME DISPATCH TABLE INITIALIZATION                                  */
/* ========================================================================= */

DesSimdOps g_des_simd_ops = {
    .isa_name = "SCALAR",
    .find_crlf = simd_find_crlf_scalar,
    .find_crlf_crlf = simd_find_crlf_crlf_scalar,
    .find_path_separator = simd_find_path_separator_scalar,
    .validate_url_ascii = simd_validate_url_ascii_scalar,
    .fast_hash = simd_fast_hash_scalar,
    .lowercase_ascii = simd_lowercase_ascii_scalar,
    .is_ascii_lowercase = simd_is_ascii_lowercase_scalar,
};

static int g_simd_dispatch_initialized = 0;

void init_simd_dispatch(void) {
    if (g_simd_dispatch_initialized) {
        return;
    }

#if defined(X86_TARGETS_AVAILABLE) && (defined(__GNUC__) || defined(__clang__))
    __builtin_cpu_init();
    if (__builtin_cpu_supports("avx2")) {
        g_des_simd_ops.isa_name = "AVX2";
        g_des_simd_ops.find_crlf = simd_find_crlf_avx2;
        g_des_simd_ops.find_crlf_crlf = simd_find_crlf_crlf_avx2;
        g_des_simd_ops.find_path_separator = simd_find_path_separator_avx2;
        g_des_simd_ops.validate_url_ascii = simd_validate_url_ascii_avx2;
        g_des_simd_ops.fast_hash = simd_fast_hash_scalar;
        g_des_simd_ops.lowercase_ascii = simd_lowercase_ascii_avx2;
        g_des_simd_ops.is_ascii_lowercase = simd_is_ascii_lowercase_avx2;
    } else if (__builtin_cpu_supports("sse2")) {
        g_des_simd_ops.isa_name = "SSE2";
        g_des_simd_ops.find_crlf = simd_find_crlf_sse2;
        g_des_simd_ops.find_crlf_crlf = simd_find_crlf_crlf_sse2;
        g_des_simd_ops.find_path_separator = simd_find_path_separator_sse2;
        g_des_simd_ops.validate_url_ascii = simd_validate_url_ascii_sse2;
        g_des_simd_ops.fast_hash = simd_fast_hash_scalar;
        g_des_simd_ops.lowercase_ascii = simd_lowercase_ascii_sse2;
        g_des_simd_ops.is_ascii_lowercase = simd_is_ascii_lowercase_sse2;
    } else {
        g_des_simd_ops.isa_name = "SCALAR";
    }
#elif defined(ARM_NEON_AVAILABLE)
    g_des_simd_ops.isa_name = "NEON";
#else
    g_des_simd_ops.isa_name = "SCALAR";
#endif

    g_simd_dispatch_initialized = 1;
}

const char *get_active_simd_isa(void) {
    if (!g_simd_dispatch_initialized) {
        init_simd_dispatch();
    }
    return g_des_simd_ops.isa_name;
}

/* ========================================================================= */
/* 5. PUBLIC CALL SITES FORWARDING                                           */
/* ========================================================================= */

int64_t simd_find_crlf(const char * __restrict__ buffer, size_t length) {
    return g_des_simd_ops.find_crlf(buffer, length);
}

int64_t simd_find_crlf_crlf(const char * __restrict__ buffer, size_t length) {
    return g_des_simd_ops.find_crlf_crlf(buffer, length);
}

int64_t simd_find_path_separator(const char * __restrict__ buffer, size_t length, size_t start_pos) {
    return g_des_simd_ops.find_path_separator(buffer, length, start_pos);
}

int simd_validate_url_ascii(const char * __restrict__ buffer, size_t length) {
    return g_des_simd_ops.validate_url_ascii(buffer, length);
}

uint32_t simd_fast_hash(const char * __restrict__ buffer, size_t length) {
    return g_des_simd_ops.fast_hash(buffer, length);
}

void simd_lowercase_ascii(const char * __restrict__ src, char * __restrict__ dst, size_t length) {
    g_des_simd_ops.lowercase_ascii(src, dst, length);
}

int simd_is_ascii_lowercase(const char * __restrict__ s, size_t length) {
    return g_des_simd_ops.is_ascii_lowercase(s, length);
}
