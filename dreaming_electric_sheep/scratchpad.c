#include "scratchpad.h"
#include <string.h>

int scratchpad_init(ScratchpadArena * __restrict__ arena, size_t capacity) {
    if (DES_UNLIKELY(arena == NULL)) {
        return -1;
    }
    if (capacity == 0) {
        capacity = DEFAULT_SCRATCHPAD_CAPACITY;
    }
    // Bypass zero-initialization: malloc without memset(0)
    arena->buffer = (char *)malloc(capacity);
    if (DES_UNLIKELY(arena->buffer == NULL)) {
        arena->capacity = 0;
        arena->offset = 0;
        arena->is_dynamic = 0;
        return -1;
    }
    arena->capacity = capacity;
    arena->offset = 0;
    arena->is_dynamic = 1;
    return 0;
}

void *scratchpad_alloc(ScratchpadArena * __restrict__ arena, size_t size, size_t alignment) {
    if (DES_UNLIKELY(arena == NULL || arena->buffer == NULL || size == 0)) {
        return NULL;
    }

    if (alignment == 0) {
        alignment = sizeof(void *);
    }

    // Align offset
    uintptr_t current_addr = (uintptr_t)(arena->buffer + arena->offset);
    uintptr_t aligned_addr = (current_addr + (alignment - 1)) & ~(uintptr_t)(alignment - 1);
    size_t new_offset = (size_t)(aligned_addr - (uintptr_t)arena->buffer) + size;

    if (DES_UNLIKELY(new_offset > arena->capacity)) {
        // Arena overflow: attempt geometric resize if dynamically allocated
        if (DES_LIKELY(arena->is_dynamic)) {
            size_t new_capacity = arena->capacity * 2;
            if (new_capacity < new_offset) {
                new_capacity = new_offset + DEFAULT_SCRATCHPAD_CAPACITY;
            }
            char *new_buf = (char *)realloc(arena->buffer, new_capacity);
            if (DES_UNLIKELY(new_buf == NULL)) {
                return NULL;
            }
            arena->buffer = new_buf;
            arena->capacity = new_capacity;

            current_addr = (uintptr_t)(arena->buffer + arena->offset);
            aligned_addr = (current_addr + (alignment - 1)) & ~(uintptr_t)(alignment - 1);
            new_offset = (size_t)(aligned_addr - (uintptr_t)arena->buffer) + size;
        } else {
            return NULL;
        }
    }

    void *ptr = (void *)aligned_addr;
    arena->offset = new_offset;
    return ptr;
}

void scratchpad_destroy(ScratchpadArena * __restrict__ arena) {
    if (DES_LIKELY(arena != NULL)) {
        if (arena->buffer != NULL && arena->is_dynamic) {
            free(arena->buffer);
            arena->buffer = NULL;
        }
        arena->capacity = 0;
        arena->offset = 0;
        arena->is_dynamic = 0;
    }
}
