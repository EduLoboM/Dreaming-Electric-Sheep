/*
 * Fast Parsing, Cursor Operations, and Compiler Intrinsics for Dreaming Electric Sheep.
 * Implements forced inlining (__attribute__((always_inline))), strict aliasing (__restrict__),
 * cache-line alignment (_Alignas(64)), branch hints (__builtin_expect), and software prefetching.
 */

#ifndef DREAMING_ELECTRIC_SHEEP_FAST_PARSE_H
#define DREAMING_ELECTRIC_SHEEP_FAST_PARSE_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#if defined(_MSC_VER) && !defined(__clang__)
    #define DES_ALWAYS_INLINE __forceinline
    #define DES_CACHE_ALIGNED __declspec(align(64))
    #define __restrict__ __restrict
    #define DES_LIKELY(x) (x)
    #define DES_UNLIKELY(x) (x)
    #define DES_PREFETCH(ptr, rw, loc)
#else
    #define DES_ALWAYS_INLINE __attribute__((always_inline)) inline
    #define DES_CACHE_ALIGNED __attribute__((aligned(64)))
    #define DES_LIKELY(x) __builtin_expect(!!(x), 1)
    #define DES_UNLIKELY(x) __builtin_expect(!!(x), 0)
    #define DES_PREFETCH(ptr, rw, loc) __builtin_prefetch((ptr), (rw), (loc))
#endif

#ifndef DES_API
    #if defined(_WIN32) || defined(__CYGWIN__)
        #if defined(DES_BUILDING_CORE)
            #define DES_API __declspec(dllexport)
        #else
            #define DES_API __declspec(dllimport)
        #endif
    #else
        #if defined(__GNUC__) && __GNUC__ >= 4
            #define DES_API __attribute__((visibility("default")))
        #else
            #define DES_API
        #endif
    #endif
#endif

typedef enum {
    DES_OK = 0,
    DES_ERR_NULL_ARG = 1,
    DES_ERR_OVERFLOW = 2,
    DES_ERR_INVALID = 3,
    DES_ERR_NOMEM = 4,
    DES_ERR_NOT_FOUND = 5,
} des_err;

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Fast parsing of unsigned 64-bit integer from ASCII byte buffer with forced inlining.
 * Returns 1 on success, 0 on invalid characters or overflow.
 */
static DES_ALWAYS_INLINE int fast_parse_uint64(
    const char * __restrict__ s,
    size_t len,
    uint64_t * __restrict__ out
) {
    if (DES_UNLIKELY(s == NULL || len == 0 || out == NULL)) {
        return 0;
    }

    uint64_t val = 0;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (DES_UNLIKELY(c < '0' || c > '9')) {
            return 0;
        }
        uint64_t digit = (uint64_t)(c - '0');
        if (DES_UNLIKELY(val > (UINT64_MAX - digit) / 10)) {
            return 0; // Overflow
        }
        val = val * 10 + digit;
    }

    *out = val;
    return 1;
}

/*
 * Fast parsing of signed 64-bit integer from ASCII byte buffer with forced inlining.
 * Returns 1 on success, 0 on invalid characters or overflow.
 */
static DES_ALWAYS_INLINE int fast_parse_int64(
    const char * __restrict__ s,
    size_t len,
    int64_t * __restrict__ out
) {
    if (DES_UNLIKELY(s == NULL || len == 0 || out == NULL)) {
        return 0;
    }

    int negative = 0;
    size_t start = 0;

    if (s[0] == '-') {
        negative = 1;
        start = 1;
        if (DES_UNLIKELY(len == 1)) {
            return 0;
        }
    } else if (s[0] == '+') {
        start = 1;
        if (DES_UNLIKELY(len == 1)) {
            return 0;
        }
    }

    uint64_t uval = 0;
    for (size_t i = start; i < len; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (DES_UNLIKELY(c < '0' || c > '9')) {
            return 0;
        }
        uint64_t digit = (uint64_t)(c - '0');
        if (DES_UNLIKELY(uval > (UINT64_MAX - digit) / 10)) {
            return 0;
        }
        uval = uval * 10 + digit;
    }

    if (negative) {
        if (DES_UNLIKELY(uval > (uint64_t)INT64_MAX + 1)) {
            return 0;
        }
        *out = -(int64_t)uval;
    } else {
        if (DES_UNLIKELY(uval > (uint64_t)INT64_MAX)) {
            return 0;
        }
        *out = (int64_t)uval;
    }

    return 1;
}

/*
 * Fast parsing of hexadecimal unsigned 64-bit integer (e.g. for HTTP chunked transfer sizes).
 * Returns 1 on success, 0 on invalid characters or overflow.
 */
static DES_ALWAYS_INLINE int fast_parse_hex_uint64(
    const char * __restrict__ s,
    size_t len,
    uint64_t * __restrict__ out
) {
    if (DES_UNLIKELY(s == NULL || len == 0 || out == NULL)) {
        return 0;
    }

    uint64_t val = 0;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)s[i];
        uint64_t digit;

        if (c >= '0' && c <= '9') {
            digit = (uint64_t)(c - '0');
        } else if (c >= 'a' && c <= 'f') {
            digit = (uint64_t)(c - 'a' + 10);
        } else if (c >= 'A' && c <= 'F') {
            digit = (uint64_t)(c - 'A' + 10);
        } else {
            return 0;
        }

        if (DES_UNLIKELY(val > (UINT64_MAX >> 4))) {
            return 0; // Overflow
        }
        val = (val << 4) | digit;
    }

    *out = val;
    return 1;
}

/*
 * Cursor navigation: skips whitespace (' ' and '\t') in buffer with forced inlining.
 */
static DES_ALWAYS_INLINE void cursor_skip_spaces(
    const char * __restrict__ buffer,
    size_t length,
    size_t * __restrict__ cursor
) {
    if (DES_UNLIKELY(buffer == NULL || cursor == NULL)) {
        return;
    }
    size_t c = *cursor;
    while (c < length && (buffer[c] == ' ' || buffer[c] == '\t')) {
        c++;
    }
    *cursor = c;
}

/*
 * Cursor navigation: matches an expected byte character and advances cursor.
 * Returns 1 if matched and advanced, 0 otherwise.
 */
static DES_ALWAYS_INLINE int cursor_match_byte(
    const char * __restrict__ buffer,
    size_t length,
    size_t * __restrict__ cursor,
    char expected
) {
    if (DES_UNLIKELY(buffer == NULL || cursor == NULL)) {
        return 0;
    }
    size_t c = *cursor;
    if (c < length && buffer[c] == expected) {
        *cursor = c + 1;
        return 1;
    }
    return 0;
}

#ifdef __cplusplus
}
#endif

#endif /* DREAMING_ELECTRIC_SHEEP_FAST_PARSE_H */
