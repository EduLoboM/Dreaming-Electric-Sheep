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
 */
int scratchpad_init(ScratchpadArena *arena, size_t capacity);

/*
 * Allocates aligned memory from the scratchpad arena.
 * Returns pointer to allocated memory, or NULL on out-of-memory.
 */
void *scratchpad_alloc(ScratchpadArena *arena, size_t size, size_t alignment);

/*
 * Resets the scratchpad arena in O(1) time by rewinding the offset to 0.
 */
static inline void scratchpad_reset(ScratchpadArena *arena) {
    if (arena != NULL) {
        arena->offset = 0;
    }
}

/*
 * Destroys and frees the scratchpad arena buffer.
 */
void scratchpad_destroy(ScratchpadArena *arena);

#ifdef __cplusplus
}
#endif

#endif /* DREAMING_ELECTRIC_SHEEP_SCRATCHPAD_H */
