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
    #if defined(__AVX2__)
        #include <immintrin.h>
        #define HAS_AVX2 1
    #elif defined(__SSE4_2__) || defined(__SSE2__) || defined(_M_X64) || (defined(_M_IX86_FP) && _M_IX86_FP >= 2)
        #include <emmintrin.h>
        #define HAS_SSE2 1
    #endif
#elif defined(__ARM_NEON) || defined(__aarch64__) || defined(_M_ARM64)
    #if defined(_MSC_VER) && !defined(__clang__)
        #include <arm64_neon.h>
    #else
        #include <arm_neon.h>
    #endif
    #define HAS_NEON 1
#endif

int64_t simd_find_crlf(const char * __restrict__ buffer, size_t length) {
    if (buffer == NULL || length < 2) {
        return -1;
    }

    size_t i = 0;

#if defined(HAS_AVX2)
    // 32-byte chunks with AVX2
    __m256i cr = _mm256_set1_epi8('\r');
    while (i + 32 <= length) {
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(buffer + i));
        __m256i cmp = _mm256_cmpeq_epi8(chunk, cr);
        uint32_t mask = (uint32_t)_mm256_movemask_epi8(cmp);

        while (mask != 0) {
            int bit = __builtin_ctz(mask);
            size_t pos = i + (size_t)bit;
            if (pos + 1 < length && buffer[pos + 1] == '\n') {
                return (int64_t)pos;
            }
            mask &= mask - 1; // Clear lowest set bit
        }
        i += 32;
    }
#elif defined(HAS_SSE2)
    // 16-byte chunks with SSE2
    __m128i cr = _mm_set1_epi8('\r');
    while (i + 16 <= length) {
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
#endif

    // Scalar fallback
    for (; i + 1 < length; ++i) {
        if (buffer[i] == '\r' && buffer[i + 1] == '\n') {
            return (int64_t)i;
        }
    }

    return -1;
}

int64_t simd_find_crlf_crlf(const char * __restrict__ buffer, size_t length) {
    if (buffer == NULL || length < 4) {
        return -1;
    }

    size_t i = 0;

#if defined(HAS_AVX2)
    __m256i cr = _mm256_set1_epi8('\r');
    while (i + 32 <= length) {
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
#elif defined(HAS_SSE2)
    __m128i cr = _mm_set1_epi8('\r');
    while (i + 16 <= length) {
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
#endif

    // Scalar loop
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

int64_t simd_find_path_separator(const char * __restrict__ buffer, size_t length, size_t start_pos) {
    if (buffer == NULL || start_pos >= length) {
        return -1;
    }

    size_t i = start_pos;

#if defined(HAS_AVX2)
    __m256i slash = _mm256_set1_epi8('/');
    __m256i quest = _mm256_set1_epi8('?');
    __m256i hash  = _mm256_set1_epi8('#');
    __m256i space = _mm256_set1_epi8(' ');

    while (i + 32 <= length) {
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
#elif defined(HAS_SSE2)
    __m128i slash = _mm_set1_epi8('/');
    __m128i quest = _mm_set1_epi8('?');
    __m128i hash  = _mm_set1_epi8('#');
    __m128i space = _mm_set1_epi8(' ');

    while (i + 16 <= length) {
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
#endif

    // Scalar fallback
    for (; i < length; ++i) {
        char c = buffer[i];
        if (c == '/' || c == '?' || c == '#' || c == ' ') {
            return (int64_t)i;
        }
    }

    return -1;
}

int simd_validate_url_ascii(const char * __restrict__ buffer, size_t length) {
    if (buffer == NULL) {
        return 0;
    }

    size_t i = 0;

#if defined(HAS_AVX2)
    __m256i min_val = _mm256_set1_epi8(32);  // ' ' space is 32
    __m256i max_val = _mm256_set1_epi8(126); // '~' is 126

    while (i + 32 <= length) {
        __m256i chunk = _mm256_loadu_si256((const __m256i *)(buffer + i));
        // Check if any byte < 32 or > 126
        __m256i lt = _mm256_cmpgt_epi8(min_val, chunk);
        __m256i gt = _mm256_cmpgt_epi8(chunk, max_val);
        __m256i invalid = _mm256_or_si256(lt, gt);
        if (_mm256_movemask_epi8(invalid) != 0) {
            return 0;
        }
        i += 32;
    }
#elif defined(HAS_SSE2)
    __m128i min_val = _mm_set1_epi8(32);
    __m128i max_val = _mm_set1_epi8(126);

    while (i + 16 <= length) {
        __m128i chunk = _mm_loadu_si128((const __m128i *)(buffer + i));
        __m128i lt = _mm_cmpgt_epi8(min_val, chunk);
        __m128i gt = _mm_cmpgt_epi8(chunk, max_val);
        __m128i invalid = _mm_or_si128(lt, gt);
        if (_mm_movemask_epi8(invalid) != 0) {
            return 0;
        }
        i += 16;
    }
#endif

    for (; i < length; ++i) {
        unsigned char c = (unsigned char)buffer[i];
        if (c < 32 || c > 126) {
            return 0;
        }
    }

    return 1;
}

uint32_t simd_fast_hash(const char * __restrict__ buffer, size_t length) {
    if (buffer == NULL || length == 0) {
        return 0;
    }

    // FNV-1a with 32-bit prime, unrolled in 4-byte steps
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
