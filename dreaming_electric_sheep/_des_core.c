/*
 * dreaming_electric_sheep._des_core
 * Unified C extension core for Dreaming Electric Sheep.
 * Owns the static intern table, SIMD operations, and scratchpad memory arena.
 */

#define DES_BUILDING_CORE 1

#include <Python.h>
#include "fast_parse.h"
#include "interning.h"
#include "scratchpad.h"
#include "simd_ops.h"

static PyObject *py_init_static_interning(PyObject *self, PyObject *args) {
    int res = init_static_interning();
    return PyLong_FromLong(res);
}

static PyObject *py_get_intern_table_address(PyObject *self, PyObject *args) {
    return PyLong_FromVoidPtr((void *)&g_des_intern_table);
}

static PyObject *py_get_simd_isa_info(PyObject *self, PyObject *args) {
#if defined(HAS_AVX2)
    return PyUnicode_FromString("AVX2");
#elif defined(HAS_SSE2)
    return PyUnicode_FromString("SSE2");
#elif defined(HAS_NEON)
    return PyUnicode_FromString("NEON");
#else
    return PyUnicode_FromString("SCALAR");
#endif
}

static PyMethodDef DesCoreMethods[] = {
    {"init_static_interning", py_init_static_interning, METH_NOARGS, "Initialize static PyObject interning table"},
    {"get_intern_table_address", py_get_intern_table_address, METH_NOARGS, "Get memory address of g_des_intern_table"},
    {"get_simd_isa_info", py_get_simd_isa_info, METH_NOARGS, "Get active compiled SIMD ISA info"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef des_core_module = {
    PyModuleDef_HEAD_INIT,
    "_des_core",
    "Dreaming Electric Sheep core compiled C intrinsics, arenas, and intern table",
    -1,
    DesCoreMethods
};

PyMODINIT_FUNC PyInit__des_core(void) {
    PyObject *m = PyModule_Create(&des_core_module);
    if (m == NULL) {
        return NULL;
    }

    if (init_static_interning() != 0) {
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
