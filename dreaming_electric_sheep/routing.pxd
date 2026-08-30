cdef class RouteMatch:
    cdef public object handler
    cdef public object pattern
    cdef public dict _values
    cdef public object route


cdef class RadixNode:
    cdef public bytes segment
    cdef public object route
    cdef public dict children
    cdef public RadixNode param_child
    cdef public str param_name
    cdef public list param_names
    cdef public object param_validator
    cdef public RadixNode wildcard_child
    cdef public str wildcard_name
    cdef public bytes wildcard_suffix
    cdef public bint is_leaf


cdef class RadixTree:
    cdef public RadixNode root
    cdef public dict static_routes
    cpdef void insert(self, bytes pattern, object route, list param_names=*)
    cdef tuple _parse_param_segment(self, bytes seg)
    cpdef tuple match(self, bytes path)
    cdef tuple _match_recursive(self, RadixNode current, list segments, int index, dict params)


cdef class CythonRadixRouter:
    cdef public dict trees
    cpdef void add_route(self, bytes method, bytes pattern, object route, list param_names=*)
    cpdef tuple get_match(self, bytes method, bytes path)
    cpdef void freeze(self)
