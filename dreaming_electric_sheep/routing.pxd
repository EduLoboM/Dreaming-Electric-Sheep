cdef class RouteMatch:
    cdef public object handler
    cdef public object pattern
    cdef public dict _values
    cdef public object route


cdef class RadixNode:
    cdef public str segment_str
    cdef public bytes segment_bytes
    cdef public object route
    cdef public dict children_str
    cdef public dict children_bytes
    cdef public RadixNode param_child
    cdef public str param_name
    cdef public list param_names
    cdef public object param_validator_str
    cdef public object param_validator_bytes
    cdef public RadixNode wildcard_child
    cdef public str wildcard_name
    cdef public str wildcard_suffix_str
    cdef public bytes wildcard_suffix_bytes
    cdef public bint is_leaf


cdef class RadixTree:
    cdef public RadixNode root
    cdef public dict static_routes_str
    cdef public dict static_routes_bytes
    cpdef void insert(self, object pattern, object route, list param_names=*)
    cdef tuple _parse_param_segment(self, str seg)
    cpdef tuple match(self, object path)
    cdef tuple _match_str(self, str path)
    cdef tuple _match_bytes(self, bytes path)
    cdef tuple _match_recursive_str(self, RadixNode current, list segments, int index, dict params)
    cdef tuple _match_recursive_bytes(self, RadixNode current, list segments, int index, dict params)


cdef class CythonRadixRouter:
    cdef public dict trees
    cpdef void add_route(self, object method, object pattern, object route, list param_names=*)
    cpdef tuple get_match(self, object method, object path)
    cpdef void freeze(self)
