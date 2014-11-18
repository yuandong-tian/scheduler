#include <iostream>
#include "schedule_lib.h"

using namespace std;
using namespace schedule;

Task make_task(const string& name, time_t duration, const string& pre_id, time_t delay) {
	Task task;
	task.set_id(name);
	task.set_duration(duration);
	if (pre_id != "") {
		TaskPreReq* pre_req = task.add_pre_req();
		pre_req->set_id(pre_id);
		pre_req->set_delay(delay);
	}
	return task;
}

void test() {
	Tasks tasks;
	tasks.set_global_start_time(0);
	tasks.set_rest_time(5);

	*tasks.add_tasks() = make_task("Research0-1", 20, "", 0);
	*tasks.add_tasks() = make_task("Research0-2", 20, "Research0-1", 60);
	*tasks.add_tasks() = make_task("Research0-3", 20, "Research0-2", 20);
	*tasks.add_tasks() = make_task("Work-1", 30, "", 0);
	*tasks.add_tasks() = make_task("Work-2", 30, "Work-1", 20);
	*tasks.add_tasks() = make_task("Work-3", 10, "Work-2", 20);

	Schedules schedules;
	if (make_schedule(tasks, &schedules)) {
		// print schedules
		cout << "#steps = " << schedules.search_steps() << endl;
		for (int i = 0; i < schedules.schedules_size(); ++i) {
			const Schedule& schedule = schedules.schedules(i);
			cout << schedule.id() << "  From: " << schedule.start() << "  To: " << schedule.end() << endl;
		}
	}
}

int main() {
	// Schedule
	test();
	return 0;
}