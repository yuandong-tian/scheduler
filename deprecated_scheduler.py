#!/usr/bin/python

# Each task is like:
# "Task1-Stage2" : {
#   "PreReq" : {
#      task_key1 : delay1 (in timedelta)
#      task_key2 : delay2
#   }
#   "Duration" : timedelta
#   "FixedStart": datetime
#   "FixedEnd": datetime
#   "FixedTolerance" : timedelta
#   "Deadline" : datetime
# }

# Start task
# Return schedule:
# "Task1-Stage2" : {
#   "Start" : datetime, 
#   "End" : datetime
# }

# Old scheduler (Python-based.)

def get_earliest_start_time(task, start_time):
	time = task.time;

	# Deadline is violated.
	if time.HasField("deadline") and start_time + time.duration > time.deadline:
		return None, None;

	# Check time intervals:
	start_time_fitin = False;
	for start1, start2 in zip(time.earliest_starts, time.latest_starts):
		if start_time <= start2:
			start_time = max(start_time, start1);
			start_time_fitin = True;
			break;

	if not start_time_fitin: return None, None;
	return (start_time, start_time + time.duration);

def check_criterion(task, cool_down_table, schedule, start_time):
	""" Check whether the task can be scheduled given the current schedule."""
	""" If so, return a new task status, else return None"""
	# Step 1, check PreReq
	if schedule:
		start_time = max([end_time for k, end_time in schedule.iteritems()]);
	start_time += time_to_rest;

	for prev_task in task.pre_req_ids:
		if not prev_task in schedule: return None;
		start_time = max(start_time, schedule[prev_task] + cool_down_table[prev_task]);

	start_time, end_time = get_earliest_start_time(task, start_time);
	if start_time is None: return None;
	return end_time;

# start_timestamp: Start of this schedule
# end_timestamp: End of this schedule.
def get_estimation(tasks, schedule, start_timestamp):
	# Get the lower bound estimation of the time spent.
	if schedule:
		start_time = max([end_time for k, end_time in schedule.iteritems()]);
	else:
		start_time = start_timestamp;

	lower_bound = 0;
	for task in tasks.tasks:
		if task.id in schedule: continue;
		earliest_start_time, end_time = get_earliest_start_time(task, start_time);
		if earliest_start_time is None: 
			return None;
			#lower_bound += task.time.duration * 100;
		else: 
			lower_bound += task.time.duration + time_to_rest;

	return start_time + lower_bound;

def make_schedule(tasks, start_time):
	""" Schedule all tasks from start_time, and return the schedule. Use A* algorithm"""
	queue = PriorityQueue();

	# Lower bound.
	cool_down_table = {task.id : task.time.cool_down for task in tasks.tasks};	

	num_iteration = 0;
	best_schedule = {};
	best_penalty = 0;

	start_timestamp = int(start_time.strftime("%s"));
	queue.put((0, {}));
	while not queue.empty():
		penalty, schedule = queue.get();
		num_iteration += 1;

   	    # Best solution
		if len(schedule) > len(best_schedule):
			best_schedule = schedule;
			best_penalty = penalty;
		if len(best_schedule) == len(tasks.tasks): break;

		# Expand the schedule and put them to the queue.
		for task in tasks.tasks:
			if task.id in schedule: continue;
			new_end_time = check_criterion(task, cool_down_table, schedule, start_timestamp);
			if new_end_time:
				updated_schedule = dict(schedule);
				updated_schedule.update({ task.id : new_end_time });
				estimated_penalty = get_estimation(tasks, updated_schedule, start_timestamp);
				if estimated_penalty:
					queue.put((estimated_penalty, updated_schedule));

	if len(best_schedule) < len(tasks.tasks):
		print "Solution incomplete!";
		for task in tasks.tasks:
			if not task.id in best_schedule:
				print "Task " + task.id + " not listed!";

	print "Solution found with penalty = %d, #Steps = %d" % (best_penalty, num_iteration);

	task_table = {task.id : (task.group, task.time.duration) for task in tasks.tasks};	
	return {k : {"Group" : task_table[k][0], "Start" : end_time - task_table[k][1], "End" : end_time } for k, end_time in best_schedule.iteritems() };


# Old parser.
def parse_fixed_task(task_name, argument):
	start, tol, duration = argument.split(",");
	task = { "FixedStart" : parse_time(start), "FixedTolerance" : parse_duration(tol), "Duration" : parse_duration(duration) };
	return {task_name : task};

def parse_interval_task(task_name, deadline, argument):
	intervals = [parse_duration(interval) for interval in argument.split(",")];
	if deadline: deadline = parse_time(deadline);

	task = { "Duration" : intervals[0] };
	if deadline:
		this_deadline = deadline;
		for j in range(1, len(intervals)):
			this_deadline -= intervals[j];
		task.update({"Deadline" : this_deadline});
	tasks = { task_name + "-0" : task };

	for i in range(1, len(intervals), 2):
		this_task = "%s-%d" % (task_name, i / 2 + 1);
		prev_task = "%s-%d" % (task_name, i / 2);
		task = { "Duration" : intervals[i + 1], "PreReq" : { prev_task : intervals[i] } };

		if deadline:
			# Not efficient here.
			this_deadline = deadline;
			for j in range(i + 2, len(intervals)):
				this_deadline -= intervals[j];
			task.update({"Deadline" : this_deadline});

		tasks.update({this_task : task});
	return tasks;

def parse_seq_task(task_name, deadline, argument):
	intervals = [parse_duration(interval) for interval in argument.split(",")];
	if deadline: deadline = parse_time(deadline);

	task = { "Duration" : intervals[0] };
	if deadline:
		this_deadline = deadline;
		for j in range(1, len(intervals)):
			this_deadline -= intervals[j];
		task.update({"Deadline" : this_deadline});
	tasks = { task_name + "-0" : task };

	zero_duration = parse_duration("0s");
	for i in range(1, len(intervals)):
		this_task = "%s-%d" % (task_name, i);
		prev_task = "%s-%d" % (task_name, i - 1);
		task = { "Duration" : intervals[i], "PreReq" : { prev_task : zero_duration } };

		if deadline:
		    # Not efficient here.
		    this_deadline = deadline;
		    for j in range(i + 1, len(intervals)):
		    	this_deadline -= intervals[j];
		    task.update({"Deadline" : this_deadline});

		tasks.update({this_task : task});

	return tasks;

# Deprecated timer parser.
def parse_time_seg(seg_str, curr_datetime):
	weekday_table = { 
	    "Mon" : {0}, "Tue" : {1}, "Wed" : {2}, 
	    "Thu" : {3}, "Fri" : {4}, "Sat" : {5}, "Sun" : {6},  
	    "Weekday" : {0, 1, 2, 3, 4}, 
	    "Weekend" : {5, 6},
	    "Every2" : {1, 3, 5}
	};

	# Parse time segment
	segment = task_pb2.TimeSegment();
	tokens = seg_str.split("+");
	if len(tokens) == 2:
		segment.cool_down = util_duration(tokens[1])
		seg_str = tokens[0];

	tokens = seg_str.split("/");
	if len(tokens) == 4:
		# Check workday.
		if not tokens[1] in weekday_table: return None;
		if not curr_datetime.weekday() in weekday_table[tokens[1]]: return None;

		segment.start = util_timestamp(tokens[0])
		segment.start_tol = util_duration(tokens[2])
		segment.duration = util_duration(tokens[3])
	elif len(tokens) == 3:
		segment.start = util_timestamp(tokens[0])
		segment.start_tol = util_duration(tokens[1])
		segment.duration = util_duration(tokens[2])
	elif len(tokens) == 2:
		segment.start = util_timestamp(tokens[0])		
		segment.duration = util_duration(tokens[1])		
	elif len(tokens) == 1:
		segment.duration = util_duration(tokens[0])
	else:
		return None;

	return segment;

def process_tasks(file_name):
	tasks = {};
	zero_duration = parse_duration("0s");

	for line in open(file_name, "r"):
		if line.startswith("#"): continue;

		tokens = [token.strip() for token in line.split("|")];
		if len(tokens[1:-1]) != 6: continue;
		task_name, type_of_task, prereq, deadline, argument, is_done = tuple(tokens[1:-1]);

		if is_done == "Done": continue;

		if type_of_task == "Interval": 
			this_tasks = parse_interval_task(task_name, deadline, argument);
		elif type_of_task == "Fixed":
			this_tasks = parse_fixed_task(task_name, argument);			
		elif type_of_task == "Seq":
			this_tasks = parse_seq_task(task_name, deadline, argument);			
		else:
			raise RuntimeError("Unknown type of task " + type_of_task + "for task " + task_name);

		if prereq:
			for key, content in this_tasks.iteritems():
				content.update({"PreReq" : { prereq: zero_duration }});

		tasks.update(this_tasks);

	return tasks;
