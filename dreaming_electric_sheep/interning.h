/*
 * Static PyObject* Interning Table for Dreaming Electric Sheep.
 * Pre-allocates and interns common HTTP methods, headers, and MIME types
 * to ensure O(1) pointer equality and eliminate per-request string/bytes allocation.
 */

#ifndef DREAMING_ELECTRIC_SHEEP_INTERNING_H
#define DREAMING_ELECTRIC_SHEEP_INTERNING_H

#include <Python.h>
#include <stddef.h>
#include "fast_parse.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct DES_CACHE_ALIGNED {
    // Unicode HTTP Methods
    PyObject *method_get_str;
    PyObject *method_post_str;
    PyObject *method_put_str;
    PyObject *method_delete_str;
    PyObject *method_patch_str;
    PyObject *method_head_str;
    PyObject *method_options_str;
    PyObject *method_trace_str;
    PyObject *method_connect_str;

    // Bytes HTTP Methods
    PyObject *method_get_bytes;
    PyObject *method_post_bytes;
    PyObject *method_put_bytes;
    PyObject *method_delete_bytes;
    PyObject *method_patch_bytes;
    PyObject *method_head_bytes;
    PyObject *method_options_bytes;
    PyObject *method_trace_bytes;
    PyObject *method_connect_bytes;

    // Common Bytes Headers (lowercase)
    PyObject *header_content_type;
    PyObject *header_content_length;
    PyObject *header_host;
    PyObject *header_cookie;
    PyObject *header_set_cookie;
    PyObject *header_accept;
    PyObject *header_accept_encoding;
    PyObject *header_accept_language;
    PyObject *header_user_agent;
    PyObject *header_server;
    PyObject *header_date;
    PyObject *header_connection;
    PyObject *header_transfer_encoding;
    PyObject *header_authorization;
    PyObject *header_location;
    PyObject *header_etag;
    PyObject *header_if_none_match;
    PyObject *header_origin;
    PyObject *header_cors_allow_origin;
    PyObject *header_cors_request_method;

    // Common Unicode Headers (lowercase str)
    PyObject *header_content_type_str;
    PyObject *header_content_length_str;
    PyObject *header_host_str;
    PyObject *header_cookie_str;
    PyObject *header_set_cookie_str;
    PyObject *header_accept_str;
    PyObject *header_accept_encoding_str;
    PyObject *header_accept_language_str;
    PyObject *header_user_agent_str;
    PyObject *header_server_str;
    PyObject *header_date_str;
    PyObject *header_connection_str;
    PyObject *header_transfer_encoding_str;
    PyObject *header_authorization_str;
    PyObject *header_location_str;
    PyObject *header_etag_str;
    PyObject *header_if_none_match_str;
    PyObject *header_origin_str;
    PyObject *header_cors_allow_origin_str;
    PyObject *header_cors_request_method_str;

    // Common Content-Types / Transfer values (bytes)
    PyObject *ct_application_json;
    PyObject *ct_text_plain;
    PyObject *ct_text_html;
    PyObject *ct_application_octet_stream;
    PyObject *ct_form_urlencoded;
    PyObject *ct_multipart_form;
    PyObject *val_chunked;
    PyObject *val_zero;
} StaticInternTable;

extern DES_API StaticInternTable g_des_intern_table;

/*
 * Initializes and interns all static PyObjects in the global table.
 * Safe to call multiple times (idempotent, thread/GIL-safe).
 * Process-lifetime ownership is held by g_des_intern_table.
 */
DES_API int init_static_interning(void);

/*
 * Returns a BORROWED reference to interned Unicode method object or NULL if not in static table.
 * The caller does not steal reference; Cython auto-increfs when assigning to PyObject/object.
 */
DES_API PyObject *get_interned_method_str(const char * __restrict__ method_str, size_t len);

/*
 * Returns a BORROWED reference to interned Bytes method object or NULL if not in static table.
 */
DES_API PyObject *get_interned_method_bytes(const char * __restrict__ method_str, size_t len);

/*
 * Returns a BORROWED reference to interned Bytes header name or NULL if not in static table.
 */
DES_API PyObject *get_interned_header_name_bytes(const char * __restrict__ name_str, size_t len);

/*
 * Returns a BORROWED reference to interned Unicode header name or NULL if not in static table.
 */
DES_API PyObject *get_interned_header_name_str(const char * __restrict__ name_str, size_t len);

/*
 * Returns a BORROWED reference to interned Bytes content type or NULL if not in static table.
 */
DES_API PyObject *get_interned_content_type_bytes(const char * __restrict__ type_str, size_t len);

#ifdef __cplusplus
}
#endif

#endif /* DREAMING_ELECTRIC_SHEEP_INTERNING_H */
