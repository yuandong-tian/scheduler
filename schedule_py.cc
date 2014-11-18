#include "schedule_lib.h"

#include <boost/python.hpp>

#include <google/protobuf/text_format.h>

#include <boost/foreach.hpp>
#include <boost/python/class.hpp>
#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <boost/python/list.hpp>
#include <boost/python/extract.hpp>
#include <boost/python/object.hpp>
#include <boost/python/stl_iterator.hpp>
#include <boost/python/handle.hpp>

namespace py = boost::python;
using namespace std;
using namespace schedule;

class SchedulerWrapper {
public:
	string MakeSchedule(const string& tasks_str) {
		Tasks tasks;
		Schedules schedules;

		string schedules_str;
		tasks.ParseFromString(tasks_str);
		if (make_schedule(tasks, &schedules)) {
			schedules.SerializeToString(&schedules_str);
			return schedules_str;
		} else {
			return "";
		}
	}
};

BOOST_PYTHON_MODULE(schedule_pylib) {
	// below, we prepend an underscore to methods that will be replaced
	// in Python
	py::class_<SchedulerWrapper>("Scheduler")
	   .def("MakeSchedule", &SchedulerWrapper::MakeSchedule)
	;
}