#include "schedule_lib.h"

#include "Python.h"

using namespace std;
using namespace schedule;

PyMODINIT_FUNC initschedule_pylib(void); /* Forward */

int main(int argc, char **argv) {
    /* Pass argv[0] to the Python interpreter */
    Py_SetProgramName(argv[0]);

    /* Initialize the Python interpreter.  Required. */
    Py_Initialize();

    /* Add a static module */
    initschedule_pylib();

    /* Exit, cleaning up the interpreter */
    Py_Exit(0);

    /*NOTREACHED*/
    return 0;
}

/* 'self' is not used */
static PyObject * schedule_pylib_make_schedule(PyObject *self, PyObject* args) {
    const char *tasks_string;

    if (!PyArg_ParseTuple(args, "s", &tasks_string))
        return NULL;

    string tasks_str = tasks_string;

    Tasks tasks;
    Schedules schedules;

    string schedules_str;
    tasks.ParseFromString(tasks_str);
    if (make_schedule(tasks, &schedules)) {
    	schedules.SerializeToString(&schedules_str);
    }

    return Py_BuildValue("s#", schedules_str.c_str(), schedules_str.size());
}

static PyMethodDef schedule_pylib_methods[] = {
        {"MakeSchedule", schedule_pylib_make_schedule, METH_VARARGS,
         "Make a schedule for you."},
        {NULL, NULL, 0, NULL}           /* sentinel */
};

PyMODINIT_FUNC initschedule_pylib(void)
{
        PyImport_AddModule("schedule_pylib");
        Py_InitModule("schedule_pylib", schedule_pylib_methods);
}
