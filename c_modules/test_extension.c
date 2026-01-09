#include <Python.h>

static PyObject* test_hello(PyObject* self, PyObject* args) {
    return Py_BuildValue("s", "Hello from C!");
}

static PyMethodDef TestMethods[] = {
    {"hello", test_hello, METH_VARARGS, "Return a hello string."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef testmodule = {
    PyModuleDef_HEAD_INIT,
    "test_extension",
    NULL,
    -1,
    TestMethods
};

PyMODINIT_FUNC PyInit_test_extension(void) {
    return PyModule_Create(&testmodule);
}
