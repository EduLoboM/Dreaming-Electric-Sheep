/*
 * SIMD vectorization and fast memory operations for Dreaming Electric Sheep.
 * Supports AVX2 (x86_64), SSE4.2 (x86), ARM NEON (aarch64), and portable scalar SWAR.
 */

#ifndef DREAMING_ELECTRIC_SHEEP_SIMD_OPS_H
#define DREAMING_ELECTRIC_SHEEP_SIMD_OPS_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include "fast_parse.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Finds the offset of the first occurrence of "\r\n" in buffer.
 * Returns -1 if not found.
 */
DES_API int64_t simd_find_crlf(const char * __restrict__ buffer, size_t length);

/*
 * Finds the offset of the first occurrence of "\r\n\r\n" (end of HTTP headers).
 * Returns -1 if not found.
 */
DES_API int64_t simd_find_crlf_crlf(const char * __restrict__ buffer, size_t length);

/*
 * Finds the offset of the next path separator ('/', '?', '#', ' ') starting from start_pos.
 * Returns -1 if not found.
 */
DES_API int64_t simd_find_path_separator(const char * __restrict__ buffer, size_t length, size_t start_pos);

/*
 * Validates that all bytes in the buffer are valid ASCII URL characters without control chars.
 * Returns 1 if valid, 0 if invalid character found.
 */
DES_API int simd_validate_url_ascii(const char * __restrict__ buffer, size_t length);

/*
 * Computes a fast 32-bit hash of a byte buffer using SWAR / SIMD unrolling.
 */
/*
 * Converts an ASCII string to lowercase using SIMD vectorization.
 * Supports in-place conversion (src == dst) or distinct destination buffer.
 */
DES_API void simd_lowercase_ascii(const char * __restrict__ src, char * __restrict__ dst, size_t length);

/*
 * Checks if an ASCII string is entirely lowercase (contains no uppercase 'A'-'Z').
 * Returns 1 if all characters are lowercase / non-uppercase, 0 if uppercase exists.
 */
DES_API int simd_is_ascii_lowercase(const char * __restrict__ s, size_t length);

#ifdef __cplusplus
}
#endif

#endif /* DREAMING_ELECTRIC_SHEEP_SIMD_OPS_H */
