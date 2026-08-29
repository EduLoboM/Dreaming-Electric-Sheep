#include "scratchpad.h"
#include <string.h>

int scratchpad_init(ScratchpadArena *arena, size_t capacity) {
    if (arena == NULL) {
        return -1;
    }
    if (capacity == 0) {
        capacity = DEFAULT_SCRATCHPAD_CAPACITY;
    }
    arena->buffer = (char *)malloc(capacity);
    if (arena->buffer == NULL) {
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

void *scratchpad_alloc(ScratchpadArena *arena, size_t size, size_t alignment) {
    if (arena == NULL || arena->buffer == NULL || size == 0) {
        return NULL;
    }

    if (alignment == 0) {
        alignment = sizeof(void *);
    }

    // Align offset
    size_t current_addr = (size_t)(arena->buffer + arena->offset);
    size_t aligned_addr = (current_addr + (alignment - 1)) & ~(alignment - 1);
    size_t new_offset = (aligned_addr - (size_t)arena->buffer) + size;

    if (new_offset > arena->capacity) {
        // Arena overflow: attempt geometric resize if dynamically allocated
        if (arena->is_dynamic) {
            size_t new_capacity = arena->capacity * 2;
            if (new_capacity < new_offset) {
                new_capacity = new_offset + DEFAULT_SCRATCHPAD_CAPACITY;
            }
            char *new_buf = (char *)realloc(arena->buffer, new_capacity);
            if (new_buf == NULL) {
                return NULL;
            }
            arena->buffer = new_buf;
            arena->capacity = new_capacity;

            current_addr = (size_t)(arena->buffer + arena->offset);
            aligned_addr = (current_addr + (alignment - 1)) & ~(alignment - 1);
            new_offset = (aligned_addr - (size_t)arena->buffer) + size;
        } else {
            return NULL;
        }
    }

    void *ptr = (void *)aligned_addr;
    arena->offset = new_offset;
    return ptr;
}

void scratchpad_destroy(ScratchpadArena *arena) {
    if (arena != NULL) {
        if (arena->buffer != NULL && arena->is_dynamic) {
            free(arena->buffer);
            arena->buffer = NULL;
        }
        arena->capacity = 0;
        arena->offset = 0;
        arena->is_dynamic = 0;
    }
}
