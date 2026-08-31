/*
 * Per-request Scratchpad Memory Arena for Dreaming Electric Sheep.
 * Provides O(1) allocation and O(1) bulk reset on request completion,
 * mitigating heap fragmentation and avoiding per-request malloc/free calls.
 */

#ifndef DREAMING_ELECTRIC_SHEEP_SCRATCHPAD_H
#define DREAMING_ELECTRIC_SHEEP_SCRATCHPAD_H

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include "fast_parse.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DEFAULT_SCRATCHPAD_CAPACITY (64 * 1024) // 64 KB per request arena

typedef struct {
    char *buffer;
    size_t capacity;
    size_t offset;
    int is_dynamic;
} ScratchpadArena;

/*
 * Initializes a scratchpad arena with the specified capacity.
 * Returns DES_OK on success, or des_err on failure.
 */
DES_API des_err scratchpad_init(ScratchpadArena * __restrict__ arena, size_t capacity);

/*
 * Allocates aligned memory from the scratchpad arena.
 * Returns DES_OK on success with *out_ptr set to allocated buffer, or des_err on failure.
 */
DES_API des_err scratchpad_alloc(
    ScratchpadArena * __restrict__ arena,
    size_t size,
    size_t alignment,
    void ** __restrict__ out_ptr
);

/*
 * Resets the scratchpad arena in O(1) time by rewinding the offset to 0 with forced inlining.
 */
static DES_ALWAYS_INLINE void scratchpad_reset(ScratchpadArena * __restrict__ arena) {
    if (DES_LIKELY(arena != NULL)) {
        arena->offset = 0;
    }
}

/*
 * Destroys and frees the scratchpad arena buffer.
 */
DES_API void scratchpad_destroy(ScratchpadArena * __restrict__ arena);

#ifdef __cplusplus
}
#endif

#endif /* DREAMING_ELECTRIC_SHEEP_SCRATCHPAD_H */
