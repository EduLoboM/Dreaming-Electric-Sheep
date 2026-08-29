/*
 * SIMD vectorization and fast memory operations for Dreaming Electric Sheep.
 * Supports AVX2 (x86_64), SSE4.2 (x86), ARM NEON (aarch64), and portable scalar SWAR.
 */

#ifndef DREAMING_ELECTRIC_SHEEP_SIMD_OPS_H
#define DREAMING_ELECTRIC_SHEEP_SIMD_OPS_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Finds the offset of the first occurrence of "\r\n" in buffer.
 * Returns -1 if not found.
 */
int64_t simd_find_crlf(const char * __restrict__ buffer, size_t length);

/*
 * Finds the offset of the first occurrence of "\r\n\r\n" (end of HTTP headers).
 * Returns -1 if not found.
 */
int64_t simd_find_crlf_crlf(const char * __restrict__ buffer, size_t length);

/*
 * Finds the offset of the next path separator ('/', '?', '#', ' ') starting from start_pos.
 * Returns -1 if not found.
 */
int64_t simd_find_path_separator(const char * __restrict__ buffer, size_t length, size_t start_pos);

/*
 * Validates that all bytes in the buffer are valid ASCII URL characters without control chars.
 * Returns 1 if valid, 0 if invalid character found.
 */
int simd_validate_url_ascii(const char * __restrict__ buffer, size_t length);

/*
 * Computes a fast 32-bit hash of a byte buffer using SWAR / SIMD unrolling.
 */
uint32_t simd_fast_hash(const char * __restrict__ buffer, size_t length);

#ifdef __cplusplus
}
#endif

#endif /* DREAMING_ELECTRIC_SHEEP_SIMD_OPS_H */
