#include "interning.h"
#include <string.h>

StaticInternTable g_des_intern_table = {0};
static int g_interning_initialized = 0;

static inline PyObject *create_interned_str(const char *s) {
    PyObject *u = PyUnicode_FromString(s);
    if (u != NULL) {
        PyUnicode_InternInPlace(&u);
    }
    return u;
}

static inline PyObject *create_bytes(const char *s) {
    return PyBytes_FromString(s);
}

int init_static_interning(void) {
    if (DES_LIKELY(g_interning_initialized)) {
        return 0;
    }

    PyGILState_STATE gstate = PyGILState_Ensure();
    if (g_interning_initialized) {
        PyGILState_Release(gstate);
        return 0;
    }

    // Methods (Unicode)
    g_des_intern_table.method_get_str     = create_interned_str("GET");
    g_des_intern_table.method_post_str    = create_interned_str("POST");
    g_des_intern_table.method_put_str     = create_interned_str("PUT");
    g_des_intern_table.method_delete_str  = create_interned_str("DELETE");
    g_des_intern_table.method_patch_str   = create_interned_str("PATCH");
    g_des_intern_table.method_head_str    = create_interned_str("HEAD");
    g_des_intern_table.method_options_str = create_interned_str("OPTIONS");
    g_des_intern_table.method_trace_str   = create_interned_str("TRACE");
    g_des_intern_table.method_connect_str = create_interned_str("CONNECT");

    // Methods (Bytes)
    g_des_intern_table.method_get_bytes     = create_bytes("GET");
    g_des_intern_table.method_post_bytes    = create_bytes("POST");
    g_des_intern_table.method_put_bytes     = create_bytes("PUT");
    g_des_intern_table.method_delete_bytes  = create_bytes("DELETE");
    g_des_intern_table.method_patch_bytes   = create_bytes("PATCH");
    g_des_intern_table.method_head_bytes    = create_bytes("HEAD");
    g_des_intern_table.method_options_bytes = create_bytes("OPTIONS");
    g_des_intern_table.method_trace_bytes   = create_bytes("TRACE");
    g_des_intern_table.method_connect_bytes = create_bytes("CONNECT");

    // Common Headers (Bytes, lowercase)
    g_des_intern_table.header_content_type       = create_bytes("content-type");
    g_des_intern_table.header_content_length     = create_bytes("content-length");
    g_des_intern_table.header_host               = create_bytes("host");
    g_des_intern_table.header_cookie             = create_bytes("cookie");
    g_des_intern_table.header_set_cookie         = create_bytes("set-cookie");
    g_des_intern_table.header_accept             = create_bytes("accept");
    g_des_intern_table.header_accept_encoding    = create_bytes("accept-encoding");
    g_des_intern_table.header_accept_language    = create_bytes("accept-language");
    g_des_intern_table.header_user_agent         = create_bytes("user-agent");
    g_des_intern_table.header_server             = create_bytes("server");
    g_des_intern_table.header_date               = create_bytes("date");
    g_des_intern_table.header_connection         = create_bytes("connection");
    g_des_intern_table.header_transfer_encoding  = create_bytes("transfer-encoding");
    g_des_intern_table.header_authorization      = create_bytes("authorization");
    g_des_intern_table.header_location           = create_bytes("location");
    g_des_intern_table.header_etag               = create_bytes("etag");
    g_des_intern_table.header_if_none_match      = create_bytes("if-none-match");
    g_des_intern_table.header_origin             = create_bytes("origin");
    g_des_intern_table.header_cors_allow_origin  = create_bytes("access-control-allow-origin");
    g_des_intern_table.header_cors_request_method = create_bytes("access-control-request-method");

    // Content types and common values (Bytes)
    g_des_intern_table.ct_application_json         = create_bytes("application/json");
    g_des_intern_table.ct_text_plain               = create_bytes("text/plain");
    g_des_intern_table.ct_text_html                = create_bytes("text/html");
    g_des_intern_table.ct_application_octet_stream = create_bytes("application/octet-stream");
    g_des_intern_table.ct_form_urlencoded          = create_bytes("application/x-www-form-urlencoded");
    g_des_intern_table.ct_multipart_form           = create_bytes("multipart/form-data");
    g_des_intern_table.val_chunked                 = create_bytes("chunked");
    g_des_intern_table.val_zero                    = create_bytes("0");

    g_interning_initialized = 1;
    PyGILState_Release(gstate);
    return 0;
}

PyObject *get_interned_method_str(const char * __restrict__ method_str, size_t len) {
    if (DES_UNLIKELY(!g_interning_initialized)) {
        init_static_interning();
    }
    if (DES_UNLIKELY(method_str == NULL)) {
        return NULL;
    }

    switch (len) {
        case 3:
            if (memcmp(method_str, "GET", 3) == 0) return g_des_intern_table.method_get_str;
            if (memcmp(method_str, "PUT", 3) == 0) return g_des_intern_table.method_put_str;
            break;
        case 4:
            if (memcmp(method_str, "POST", 4) == 0) return g_des_intern_table.method_post_str;
            if (memcmp(method_str, "HEAD", 4) == 0) return g_des_intern_table.method_head_str;
            break;
        case 5:
            if (memcmp(method_str, "PATCH", 5) == 0) return g_des_intern_table.method_patch_str;
            if (memcmp(method_str, "TRACE", 5) == 0) return g_des_intern_table.method_trace_str;
            break;
        case 6:
            if (memcmp(method_str, "DELETE", 6) == 0) return g_des_intern_table.method_delete_str;
            break;
        case 7:
            if (memcmp(method_str, "OPTIONS", 7) == 0) return g_des_intern_table.method_options_str;
            if (memcmp(method_str, "CONNECT", 7) == 0) return g_des_intern_table.method_connect_str;
            break;
        default:
            break;
    }
    return NULL;
}

PyObject *get_interned_method_bytes(const char * __restrict__ method_str, size_t len) {
    if (DES_UNLIKELY(!g_interning_initialized)) {
        init_static_interning();
    }
    if (DES_UNLIKELY(method_str == NULL)) {
        return NULL;
    }

    switch (len) {
        case 3:
            if (memcmp(method_str, "GET", 3) == 0) return g_des_intern_table.method_get_bytes;
            if (memcmp(method_str, "PUT", 3) == 0) return g_des_intern_table.method_put_bytes;
            break;
        case 4:
            if (memcmp(method_str, "POST", 4) == 0) return g_des_intern_table.method_post_bytes;
            if (memcmp(method_str, "HEAD", 4) == 0) return g_des_intern_table.method_head_bytes;
            break;
        case 5:
            if (memcmp(method_str, "PATCH", 5) == 0) return g_des_intern_table.method_patch_bytes;
            if (memcmp(method_str, "TRACE", 5) == 0) return g_des_intern_table.method_trace_bytes;
            break;
        case 6:
            if (memcmp(method_str, "DELETE", 6) == 0) return g_des_intern_table.method_delete_bytes;
            break;
        case 7:
            if (memcmp(method_str, "OPTIONS", 7) == 0) return g_des_intern_table.method_options_bytes;
            if (memcmp(method_str, "CONNECT", 7) == 0) return g_des_intern_table.method_connect_bytes;
            break;
        default:
            break;
    }
    return NULL;
}

PyObject *get_interned_header_name_bytes(const char * __restrict__ name_str, size_t len) {
    if (DES_UNLIKELY(!g_interning_initialized)) {
        init_static_interning();
    }
    if (DES_UNLIKELY(name_str == NULL)) {
        return NULL;
    }

    switch (len) {
        case 4:
            if (memcmp(name_str, "host", 4) == 0) return g_des_intern_table.header_host;
            if (memcmp(name_str, "date", 4) == 0) return g_des_intern_table.header_date;
            if (memcmp(name_str, "etag", 4) == 0) return g_des_intern_table.header_etag;
            break;
        case 6:
            if (memcmp(name_str, "accept", 6) == 0) return g_des_intern_table.header_accept;
            if (memcmp(name_str, "cookie", 6) == 0) return g_des_intern_table.header_cookie;
            if (memcmp(name_str, "server", 6) == 0) return g_des_intern_table.header_server;
            if (memcmp(name_str, "origin", 6) == 0) return g_des_intern_table.header_origin;
            break;
        case 8:
            if (memcmp(name_str, "location", 8) == 0) return g_des_intern_table.header_location;
            break;
        case 10:
            if (memcmp(name_str, "set-cookie", 10) == 0) return g_des_intern_table.header_set_cookie;
            if (memcmp(name_str, "user-agent", 10) == 0) return g_des_intern_table.header_user_agent;
            if (memcmp(name_str, "connection", 10) == 0) return g_des_intern_table.header_connection;
            break;
        case 12:
            if (memcmp(name_str, "content-type", 12) == 0) return g_des_intern_table.header_content_type;
            break;
        case 13:
            if (memcmp(name_str, "authorization", 13) == 0) return g_des_intern_table.header_authorization;
            if (memcmp(name_str, "if-none-match", 13) == 0) return g_des_intern_table.header_if_none_match;
            break;
        case 14:
            if (memcmp(name_str, "content-length", 14) == 0) return g_des_intern_table.header_content_length;
            break;
        case 15:
            if (memcmp(name_str, "accept-encoding", 15) == 0) return g_des_intern_table.header_accept_encoding;
            if (memcmp(name_str, "accept-language", 15) == 0) return g_des_intern_table.header_accept_language;
            break;
        case 17:
            if (memcmp(name_str, "transfer-encoding", 17) == 0) return g_des_intern_table.header_transfer_encoding;
            break;
        case 27:
            if (memcmp(name_str, "access-control-allow-origin", 27) == 0) return g_des_intern_table.header_cors_allow_origin;
            break;
        case 28:
            if (memcmp(name_str, "access-control-request-method", 28) == 0) return g_des_intern_table.header_cors_request_method;
            break;
        default:
            break;
    }
    return NULL;
}

PyObject *get_interned_content_type_bytes(const char * __restrict__ type_str, size_t len) {
    if (DES_UNLIKELY(!g_interning_initialized)) {
        init_static_interning();
    }
    if (DES_UNLIKELY(type_str == NULL)) {
        return NULL;
    }

    switch (len) {
        case 9:
            if (memcmp(type_str, "text/html", 9) == 0) return g_des_intern_table.ct_text_html;
            break;
        case 10:
            if (memcmp(type_str, "text/plain", 10) == 0) return g_des_intern_table.ct_text_plain;
            break;
        case 16:
            if (memcmp(type_str, "application/json", 16) == 0) return g_des_intern_table.ct_application_json;
            break;
        case 19:
            if (memcmp(type_str, "multipart/form-data", 19) == 0) return g_des_intern_table.ct_multipart_form;
            break;
        case 24:
            if (memcmp(type_str, "application/octet-stream", 24) == 0) return g_des_intern_table.ct_application_octet_stream;
            break;
        case 33:
            if (memcmp(type_str, "application/x-www-form-urlencoded", 33) == 0) return g_des_intern_table.ct_form_urlencoded;
            break;
        default:
            break;
    }
    return NULL;
}
