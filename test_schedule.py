#!/usr/bin/python

import schedule_pylib;
import task_pb2;
from prettytable import PrettyTable

start_time = 0;
end_time = 1000;

def AddTask(task_name, duration, delay, pre_req_id):
	task = task_pb2.Task();
	task.id = task_name;
	task.time.duration = duration;
	task.time.cool_down = delay
	task.time.earliest_starts.append(start_time);
	task.time.latest_starts.append(end_time);

	if pre_req_id:
		task.pre_req_ids.append(pre_req_id);
	return task;

def PrintSchedule(schedules):
	print "num of steps = %d" % schedules.search_steps;
	table = PrettyTable(["Task", "Start", "End"]);
	table.align["Task"] = "l";
	table.padding_width = 1;

	for schedule in schedules.schedules:
		table.add_row([schedule.id, schedule.start, schedule.end]);
	print table;

tasks = task_pb2.Tasks();
tasks.tasks.extend([
	AddTask("Work-1", 30, 0, ""),
	AddTask("Work-2", 20, 30, "Work-1"),
	AddTask("Work-3", 40, 10, "Work-2"),
	AddTask("Work-4", 40, 20, "Work-3"),	
	AddTask("Work-5", 40, 40, "Work-4"),
	AddTask("Work-6", 40, 10, "Work-5"),	
	AddTask("Research-1", 20, 0, ""),
	AddTask("Research-2", 20, 90, "Research-1"),
	AddTask("Research-3", 30, 10, "Research-2"),
	AddTask("Research-4", 70, 20, "Research-3"),
	AddTask("Research-5", 20, 60, "Research-4"),
	AddTask("Research-6", 30, 50, "Research-5")		
]);

scheduler = schedule_pylib.Scheduler();
schedules_string = scheduler.MakeSchedule(tasks.SerializeToString())

if schedules_string:
	schedules = task_pb2.Schedules.FromString(schedules_string);
	PrintSchedule(schedules);
else:
	print "No available schedule!"