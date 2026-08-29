# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: initializedcheck=False
# cython: language_level=3
# Copyright (C) 2018-present Roberto Prevato
#
# This module is part of Dreaming Electric Sheep and is released under
# the MIT License https://opensource.org/licenses/MIT

import re
from urllib.parse import unquote
from libc.stdint cimport uint32_t, int64_t

cdef extern from "simd_ops.h" nogil:
    uint32_t simd_fast_hash(const char *buffer, size_t length)
    int64_t simd_find_path_separator(const char *buffer, size_t length, size_t start_pos)


cdef class RouteMatch:
    def __init__(self, object route, dict values=None):
        self.route = route
        self.handler = route.handler
        self.pattern = route.pattern
        self._values = (
            {
                k: unquote(v.decode("utf8")) if isinstance(v, bytes) else (unquote(v) if isinstance(v, str) and "%" in v else v)
                for k, v in values.items()
            }
            if values
            else None
        )

    @property
    def values(self) -> dict:
        return self._values

    def __repr__(self):
        return f"<RouteMatch {self.pattern}>"


_INT_RX = re.compile(rb"^\d+$")
_FLOAT_RX = re.compile(rb"^\d+(?:\.\d+)?$")
_UUID_RX = re.compile(
    rb"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
)


cdef inline str _fast_unquote(bytes val):
    cdef str decoded = val.decode("utf8", errors="replace")
    if "%" in decoded:
        return unquote(decoded)
    return decoded


cdef class RadixNode:

    def __init__(self, bytes segment=b""):
        self.segment = segment
        self.route = None
        self.children = {}
        self.param_child = None
        self.param_name = None
        self.param_names = None
        self.param_validator = None
        self.wildcard_child = None
        self.wildcard_name = None
        self.wildcard_suffix = None
        self.is_leaf = False


cdef class RadixTree:

    def __init__(self):
        self.root = RadixNode(b"")
        self.static_routes = {}

    cpdef void insert(self, bytes pattern, object route, list param_names=None):
        cdef bytes norm_pattern = pattern
        if norm_pattern == b"":
            norm_pattern = b"/"
        if len(norm_pattern) > 1 and norm_pattern.endswith(b"/") and not norm_pattern.endswith(b"*/"):
            norm_pattern = norm_pattern.rstrip(b"/")

        # Detect static route without params or wildcards
        cdef bint has_params = (
            b"{" in norm_pattern
            or b":" in norm_pattern
            or b"<" in norm_pattern
            or b"*" in norm_pattern
        )

        if not has_params:
            self.static_routes[norm_pattern] = route
            # Also insert with trailing slash for fast lookup
            if norm_pattern != b"/":
                self.static_routes[norm_pattern + b"/"] = route
            else:
                self.static_routes[b""] = route

        # Split pattern into segments
        cdef list raw_segments = [s for s in norm_pattern.split(b"/") if s]
        cdef RadixNode current = self.root
        cdef bytes seg
        cdef str p_name
        cdef object validator

        if not raw_segments:
            # Root route "/"
            self.root.route = route
            self.root.is_leaf = True
            return

        for i, seg in enumerate(raw_segments):
            if seg == b"*" or seg.startswith(b"*"):
                # Wildcard catch-all
                if current.wildcard_child is None:
                    current.wildcard_child = RadixNode(b"*")
                current.wildcard_name = "tail"
                if len(seg) > 1:
                    current.wildcard_suffix = seg[1:].lower()
                else:
                    current.wildcard_suffix = None
                current = current.wildcard_child
                break
            elif (
                (seg.startswith(b"{") and seg.endswith(b"}"))
                or (seg.startswith(b"<") and seg.endswith(b">"))
                or (seg.startswith(b":"))
            ):
                # Parameterized segment
                p_name, validator = self._parse_param_segment(seg)
                if validator == "path":
                    # Path wildcard
                    if current.wildcard_child is None:
                        current.wildcard_child = RadixNode(b"*")
                    current.wildcard_name = p_name
                    current.wildcard_suffix = None
                    current = current.wildcard_child
                    break

                if current.param_child is None:
                    current.param_child = RadixNode(seg)
                    current.param_child.param_name = p_name
                    current.param_child.param_validator = validator
                current = current.param_child
            else:
                # Static segment
                seg_lower = seg.lower()
                if seg_lower not in current.children:
                    current.children[seg_lower] = RadixNode(seg_lower)
                current = current.children[seg_lower]

        current.route = route
        current.is_leaf = True
        if param_names is not None:
            current.param_names = [p if isinstance(p, str) else p.decode("utf8") for p in param_names]
        elif hasattr(route, "param_names") and route.param_names:
            current.param_names = [p if isinstance(p, str) else p.decode("utf8") for p in route.param_names]
        else:
            current.param_names = None

    cdef tuple _parse_param_segment(self, bytes seg):
        cdef str inner
        cdef str param_type = ""
        cdef str param_name = ""
        cdef object validator = None

        cdef Py_ssize_t seg_len = len(seg)
        if seg.startswith(b"{") and seg.endswith(b"}"):
            inner = seg[1 : seg_len - 1].decode("utf8")
        elif seg.startswith(b"<") and seg.endswith(b">"):
            inner = seg[1 : seg_len - 1].decode("utf8")
        elif seg.startswith(b":"):
            inner = seg[1:].decode("utf8")
        else:
            inner = seg.decode("utf8")

        if ":" in inner:
            parts = inner.split(":", 1)
            # Support both {int:id} and {id:int}
            if parts[0] in ("int", "float", "uuid", "str", "string", "path"):
                param_type = parts[0]
                param_name = parts[1]
            else:
                param_name = parts[0]
                param_type = parts[1]
        else:
            param_name = inner

        if param_type == "int":
            validator = _INT_RX
        elif param_type == "float":
            validator = _FLOAT_RX
        elif param_type == "uuid":
            validator = _UUID_RX
        elif param_type == "path":
            validator = "path"

        return param_name, validator

    cpdef tuple match(self, bytes path):
        if b"//" in path:
            return None

        # 1. Check static route fast-path
        cdef object static_match = self.static_routes.get(path)
        if static_match is not None:
            return (static_match, None)

        cdef bytes norm_path = path
        if len(norm_path) > 1 and norm_path.endswith(b"/"):
            norm_path = norm_path.rstrip(b"/")

        static_match = self.static_routes.get(norm_path)
        if static_match is not None:
            return (static_match, None)

        if norm_path == b"" or norm_path == b"/":
            if self.root.route is not None:
                return (self.root.route, None)
            if self.root.wildcard_child is not None and self.root.wildcard_child.route is not None:
                return (self.root.wildcard_child.route, {self.root.wildcard_name or "tail": ""})
            return None

        # 2. Segment-based tree traversal
        cdef list segments = [s for s in norm_path.split(b"/") if s]
        cdef dict params = {}
        cdef tuple result = self._match_recursive(self.root, segments, 0, params)
        return result

    cdef tuple _match_recursive(self, RadixNode current, list segments, int index, dict params):
        cdef int total = len(segments)
        if index == total:
            if current.is_leaf and current.route is not None:
                if current.param_names is not None and params and len(current.param_names) == len(params):
                    return (current.route, dict(zip(current.param_names, params.values())))
                return (current.route, params if params else None)
            if current.wildcard_child is not None and current.wildcard_child.route is not None:
                if current.wildcard_suffix is not None:
                    return None
                p_copy = params.copy() if params else {}
                p_copy[current.wildcard_name or "tail"] = ""
                return (current.wildcard_child.route, p_copy)
            return None

        cdef bytes seg = segments[index]
        cdef bytes seg_lower = seg.lower()
        cdef RadixNode child
        cdef tuple res

        # A. Try exact static child
        if seg_lower in current.children:
            child = current.children[seg_lower]
            res = self._match_recursive(child, segments, index + 1, params)
            if res is not None:
                return res

        # B. Try parameterized child
        if current.param_child is not None:
            child = current.param_child
            # Check validator regex if present
            if child.param_validator is not None:
                if not child.param_validator.match(seg):
                    child = None

            if child is not None:
                p_copy = params.copy() if params else {}
                p_copy[f"_p_{index}"] = _fast_unquote(seg)
                res = self._match_recursive(child, segments, index + 1, p_copy)
                if res is not None:
                    return res

        # C. Try wildcard child
        if current.wildcard_child is not None and current.wildcard_child.route is not None:
            tail_bytes = b"/".join(segments[index:])
            if current.wildcard_suffix is not None:
                if not tail_bytes.lower().endswith(current.wildcard_suffix):
                    return None
                tail_bytes = tail_bytes[: len(tail_bytes) - len(current.wildcard_suffix)]
            p_copy = params.copy() if params else {}
            tail_str = _fast_unquote(tail_bytes)
            if current.wildcard_child.param_names and len(current.wildcard_child.param_names) == len(params) + 1:
                all_vals = list(params.values()) + [tail_str]
                return (current.wildcard_child.route, dict(zip(current.wildcard_child.param_names, all_vals)))
            p_copy[current.wildcard_name or "tail"] = tail_str
            return (current.wildcard_child.route, p_copy)

        return None


cdef class CythonRadixRouter:

    def __init__(self):
        self.trees = {}

    cpdef void add_route(self, bytes method, bytes pattern, object route, list param_names=None):
        cdef bytes m = method.upper()
        if m not in self.trees:
            self.trees[m] = RadixTree()
        cdef RadixTree tree = self.trees[m]
        tree.insert(pattern, route, param_names)

    cpdef tuple get_match(self, bytes method, bytes path):
        cdef bytes m = method.upper()
        if m not in self.trees:
            return None
        cdef RadixTree tree = self.trees[m]
        return tree.match(path)
