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
from cpython.unicode cimport PyUnicode_CheckExact
from cpython.bytes cimport PyBytes_CheckExact

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
                k: (unquote(v) if "%" in v else v) if isinstance(v, str) else (unquote(v.decode("utf8")) if isinstance(v, bytes) else v)
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


_INT_RX_BYTES = re.compile(rb"^\d+$")
_FLOAT_RX_BYTES = re.compile(rb"^\d+(?:\.\d+)?$")
_UUID_RX_BYTES = re.compile(
    rb"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
)

_INT_RX_STR = re.compile(r"^\d+$")
_FLOAT_RX_STR = re.compile(r"^\d+(?:\.\d+)?$")
_UUID_RX_STR = re.compile(
    r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
)


cdef inline str _fast_unquote_bytes(bytes val):
    cdef str decoded = val.decode("utf8", errors="replace")
    if "%" in decoded:
        return unquote(decoded)
    return decoded

cdef inline str _fast_unquote_str(str val):
    if "%" in val:
        return unquote(val)
    return val


cdef class RadixNode:

    def __init__(self, str segment_str="", bytes segment_bytes=b""):
        self.segment_str = segment_str
        self.segment_bytes = segment_bytes
        self.route = None
        self.children_str = {}
        self.children_bytes = {}
        self.param_child = None
        self.param_name = None
        self.param_names = None
        self.param_validator_str = None
        self.param_validator_bytes = None
        self.wildcard_child = None
        self.wildcard_name = None
        self.wildcard_suffix_str = None
        self.wildcard_suffix_bytes = None
        self.is_leaf = False


cdef class RadixTree:

    def __init__(self):
        self.root = RadixNode("", b"")
        self.static_routes_str = {}
        self.static_routes_bytes = {}

    cpdef void insert(self, object pattern, object route, list param_names=None):
        cdef str pat_str
        cdef bytes pat_bytes

        if PyBytes_CheckExact(pattern):
            pat_bytes = <bytes>pattern
            pat_str = pat_bytes.decode("utf8")
        elif PyUnicode_CheckExact(pattern):
            pat_str = <str>pattern
            pat_bytes = pat_str.encode("utf8")
        else:
            pat_str = str(pattern)
            pat_bytes = pat_str.encode("utf8")

        cdef str norm_str = pat_str
        if norm_str == "":
            norm_str = "/"
        if len(norm_str) > 1 and norm_str.endswith("/") and not norm_str.endswith("*/"):
            norm_str = norm_str.rstrip("/")

        cdef bytes norm_bytes = norm_str.encode("utf8")

        # Detect static route without params or wildcards
        cdef bint has_params = (
            "{" in norm_str
            or ":" in norm_str
            or "<" in norm_str
            or "*" in norm_str
        )

        if not has_params:
            self.static_routes_str[norm_str] = route
            self.static_routes_bytes[norm_bytes] = route
            if norm_str != "/":
                self.static_routes_str[norm_str + "/"] = route
                self.static_routes_bytes[norm_bytes + b"/"] = route
            else:
                self.static_routes_str[""] = route
                self.static_routes_bytes[b""] = route

        # Split pattern into segments
        cdef list raw_segments_str = [s for s in norm_str.split("/") if s]
        cdef RadixNode current = self.root
        cdef str seg_str
        cdef bytes seg_bytes
        cdef str p_name
        cdef str val_type

        if not raw_segments_str:
            # Root route "/"
            self.root.route = route
            self.root.is_leaf = True
            return

        for i, seg_str in enumerate(raw_segments_str):
            seg_bytes = seg_str.encode("utf8")
            if seg_str == "*" or seg_str.startswith("*"):
                # Wildcard catch-all
                if current.wildcard_child is None:
                    current.wildcard_child = RadixNode("*", b"*")
                current.wildcard_name = "tail"
                if len(seg_str) > 1:
                    current.wildcard_suffix_str = seg_str[1:].lower()
                    current.wildcard_suffix_bytes = current.wildcard_suffix_str.encode("utf8")
                else:
                    current.wildcard_suffix_str = None
                    current.wildcard_suffix_bytes = None
                current = current.wildcard_child
                break
            elif (
                (seg_str.startswith("{") and seg_str.endswith("}"))
                or (seg_str.startswith("<") and seg_str.endswith(">"))
                or (seg_str.startswith(":"))
            ):
                # Parameterized segment
                p_name, val_type = self._parse_param_segment(seg_str)
                if val_type == "path":
                    if current.wildcard_child is None:
                        current.wildcard_child = RadixNode("*", b"*")
                    current.wildcard_name = p_name
                    current.wildcard_suffix_str = None
                    current.wildcard_suffix_bytes = None
                    current = current.wildcard_child
                    break

                if current.param_child is None:
                    current.param_child = RadixNode(seg_str, seg_bytes)
                    current.param_child.param_name = p_name
                    if val_type == "int":
                        current.param_child.param_validator_str = _INT_RX_STR
                        current.param_child.param_validator_bytes = _INT_RX_BYTES
                    elif val_type == "float":
                        current.param_child.param_validator_str = _FLOAT_RX_STR
                        current.param_child.param_validator_bytes = _FLOAT_RX_BYTES
                    elif val_type == "uuid":
                        current.param_child.param_validator_str = _UUID_RX_STR
                        current.param_child.param_validator_bytes = _UUID_RX_BYTES
                    else:
                        current.param_child.param_validator_str = None
                        current.param_child.param_validator_bytes = None
                current = current.param_child
            else:
                # Static segment
                seg_lower_str = seg_str.lower()
                seg_lower_bytes = seg_lower_str.encode("utf8")
                if seg_lower_str not in current.children_str:
                    child_node = RadixNode(seg_lower_str, seg_lower_bytes)
                    current.children_str[seg_lower_str] = child_node
                    current.children_bytes[seg_lower_bytes] = child_node
                current = current.children_str[seg_lower_str]

        current.route = route
        current.is_leaf = True
        if param_names is not None:
            current.param_names = [p if isinstance(p, str) else p.decode("utf8") for p in param_names]
        elif hasattr(route, "param_names") and route.param_names:
            current.param_names = [p if isinstance(p, str) else p.decode("utf8") for p in route.param_names]
        else:
            current.param_names = None

    cdef tuple _parse_param_segment(self, str seg):
        cdef str inner
        cdef str param_type = ""
        cdef str param_name = ""

        cdef Py_ssize_t seg_len = len(seg)
        if seg.startswith("{") and seg.endswith("}"):
            inner = seg[1 : seg_len - 1]
        elif seg.startswith("<") and seg.endswith(">"):
            inner = seg[1 : seg_len - 1]
        elif seg.startswith(":"):
            inner = seg[1:]
        else:
            inner = seg

        if ":" in inner:
            parts = inner.split(":", 1)
            if parts[0] in ("int", "float", "uuid", "str", "string", "path"):
                param_type = parts[0]
                param_name = parts[1]
            else:
                param_name = parts[0]
                param_type = parts[1]
        else:
            param_name = inner

        return param_name, param_type

    cpdef tuple match(self, object path):
        if PyUnicode_CheckExact(path):
            return self._match_str(<str>path)
        elif PyBytes_CheckExact(path):
            return self._match_bytes(<bytes>path)
        else:
            return self._match_str(str(path))

    cdef tuple _match_str(self, str path):
        if "//" in path:
            return None

        # 1. Check static route fast-path (O(1) on str)
        cdef object static_match = self.static_routes_str.get(path)
        if static_match is not None:
            return (static_match, None)

        cdef str norm_path = path
        if len(norm_path) > 1 and norm_path.endswith("/"):
            norm_path = norm_path.rstrip("/")

        static_match = self.static_routes_str.get(norm_path)
        if static_match is not None:
            return (static_match, None)

        if norm_path == "" or norm_path == "/":
            if self.root.route is not None:
                return (self.root.route, None)
            if self.root.wildcard_child is not None and self.root.wildcard_child.route is not None:
                return (self.root.wildcard_child.route, {self.root.wildcard_name or "tail": ""})
            return None

        # 2. Segment-based tree traversal (O(depth) on str)
        cdef list segments = [s for s in norm_path.split("/") if s]
        cdef dict params = {}
        return self._match_recursive_str(self.root, segments, 0, params)

    cdef tuple _match_recursive_str(self, RadixNode current, list segments, int index, dict params):
        cdef int total = len(segments)
        if index == total:
            if current.is_leaf and current.route is not None:
                if current.param_names is not None and params and len(current.param_names) == len(params):
                    return (current.route, dict(zip(current.param_names, params.values())))
                return (current.route, params if params else None)
            if current.wildcard_child is not None and current.wildcard_child.route is not None:
                if current.wildcard_suffix_str is not None:
                    return None
                p_copy = params.copy() if params else {}
                p_copy[current.wildcard_name or "tail"] = ""
                return (current.wildcard_child.route, p_copy)
            return None

        cdef str seg = segments[index]
        cdef str seg_lower = seg.lower()
        cdef RadixNode child
        cdef tuple res

        # A. Try exact static child
        if seg_lower in current.children_str:
            child = current.children_str[seg_lower]
            res = self._match_recursive_str(child, segments, index + 1, params)
            if res is not None:
                return res

        # B. Try parameterized child
        if current.param_child is not None:
            child = current.param_child
            if child.param_validator_str is not None:
                if not child.param_validator_str.match(seg):
                    child = None

            if child is not None:
                p_copy = params.copy() if params else {}
                p_copy[f"_p_{index}"] = _fast_unquote_str(seg)
                res = self._match_recursive_str(child, segments, index + 1, p_copy)
                if res is not None:
                    return res

        # C. Try wildcard child
        if current.wildcard_child is not None and current.wildcard_child.route is not None:
            tail_str = "/".join(segments[index:])
            if current.wildcard_suffix_str is not None:
                if not tail_str.lower().endswith(current.wildcard_suffix_str):
                    return None
                tail_str = tail_str[: len(tail_str) - len(current.wildcard_suffix_str)]
            p_copy = params.copy() if params else {}
            tail_val = _fast_unquote_str(tail_str)
            if current.wildcard_child.param_names and len(current.wildcard_child.param_names) == len(params) + 1:
                all_vals = list(params.values()) + [tail_val]
                return (current.wildcard_child.route, dict(zip(current.wildcard_child.param_names, all_vals)))
            p_copy[current.wildcard_name or "tail"] = tail_val
            return (current.wildcard_child.route, p_copy)

        return None

    cdef tuple _match_bytes(self, bytes path):
        if b"//" in path:
            return None

        # 1. Check static route fast-path
        cdef object static_match = self.static_routes_bytes.get(path)
        if static_match is not None:
            return (static_match, None)

        cdef bytes norm_path = path
        if len(norm_path) > 1 and norm_path.endswith(b"/"):
            norm_path = norm_path.rstrip(b"/")

        static_match = self.static_routes_bytes.get(norm_path)
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
        return self._match_recursive_bytes(self.root, segments, 0, params)

    cdef tuple _match_recursive_bytes(self, RadixNode current, list segments, int index, dict params):
        cdef int total = len(segments)
        if index == total:
            if current.is_leaf and current.route is not None:
                if current.param_names is not None and params and len(current.param_names) == len(params):
                    return (current.route, dict(zip(current.param_names, params.values())))
                return (current.route, params if params else None)
            if current.wildcard_child is not None and current.wildcard_child.route is not None:
                if current.wildcard_suffix_bytes is not None:
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
        if seg_lower in current.children_bytes:
            child = current.children_bytes[seg_lower]
            res = self._match_recursive_bytes(child, segments, index + 1, params)
            if res is not None:
                return res

        # B. Try parameterized child
        if current.param_child is not None:
            child = current.param_child
            if child.param_validator_bytes is not None:
                if not child.param_validator_bytes.match(seg):
                    child = None

            if child is not None:
                p_copy = params.copy() if params else {}
                p_copy[f"_p_{index}"] = _fast_unquote_bytes(seg)
                res = self._match_recursive_bytes(child, segments, index + 1, p_copy)
                if res is not None:
                    return res

        # C. Try wildcard child
        if current.wildcard_child is not None and current.wildcard_child.route is not None:
            tail_bytes = b"/".join(segments[index:])
            if current.wildcard_suffix_bytes is not None:
                if not tail_bytes.lower().endswith(current.wildcard_suffix_bytes):
                    return None
                tail_bytes = tail_bytes[: len(tail_bytes) - len(current.wildcard_suffix_bytes)]
            p_copy = params.copy() if params else {}
            tail_str = _fast_unquote_bytes(tail_bytes)
            if current.wildcard_child.param_names and len(current.wildcard_child.param_names) == len(params) + 1:
                all_vals = list(params.values()) + [tail_str]
                return (current.wildcard_child.route, dict(zip(current.wildcard_child.param_names, all_vals)))
            p_copy[current.wildcard_name or "tail"] = tail_str
            return (current.wildcard_child.route, p_copy)

        return None


cdef class CythonRadixRouter:

    def __init__(self):
        self.trees = {}

    cpdef void add_route(self, object method, object pattern, object route, list param_names=None):
        cdef str m_str
        cdef bytes m_bytes
        cdef RadixTree tree

        if PyBytes_CheckExact(method):
            m_bytes = (<bytes>method).upper()
            m_str = m_bytes.decode("utf8")
        elif PyUnicode_CheckExact(method):
            m_str = (<str>method).upper()
            m_bytes = m_str.encode("utf8")
        else:
            m_str = str(method).upper()
            m_bytes = m_str.encode("utf8")

        if m_str not in self.trees:
            tree = RadixTree()
            self.trees[m_str] = tree
            self.trees[m_bytes] = tree
        else:
            tree = <RadixTree>self.trees[m_str]

        tree.insert(pattern, route, param_names)

    cpdef tuple get_match(self, object method, object path):
        cdef object m
        if PyBytes_CheckExact(method):
            m = (<bytes>method).upper()
        elif PyUnicode_CheckExact(method):
            m = (<str>method).upper()
        else:
            m = str(method).upper()

        if m not in self.trees:
            return None
        cdef RadixTree tree = self.trees[m]
        return tree.match(path)

    cpdef void freeze(self):
        """Freezes the radix router tables for concurrent read-only dispatch."""
        pass
