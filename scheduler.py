#!/usr/bin/python
import re;
import os;
import sys;
from datetime import timedelta, datetime;
from Queue import PriorityQueue;
import dateutil.parser;
from prettytable import PrettyTable
import yaml;
import re
from pyparsing import Word, alphas, ParseException, Literal, Combine, Optional, nums, Or, Forward, ZeroOrMore, OneOrMore, StringEnd, StringStart, alphanums

import task_pb2;
import schedule_pylib

regex = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
def parse_duration(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def parse_time(time_str, start_time=datetime.now()):
	return dateutil.parser.parse(time_str, default=start_time)

def util_dt_time(datetime_obj):
	return int(datetime_obj.strftime("%s"));

def util_dt_duration(timedelta_obj):
	return int(timedelta_obj.total_seconds());

def util_timestamp(time_str, start_time=datetime.now()):
	return int(parse_time(time_str, start_time=start_time).strftime("%s"));

def util_duration(time_str):
	return int(parse_duration(time_str).total_seconds());

time_to_rest = util_duration("5m");

def ConvertSchedule(schedules):
	print "num of steps = %d" % schedules.search_steps;
	used_ratio = float(schedules.used_duration) / schedules.total_duration;
	print "Used/Total: %d / %d (%f%%)" % (schedules.used_duration, schedules.total_duration, used_ratio * 100);
	print "Search status: ", schedules.status
	if schedules.status == task_pb2.Schedules.INCOMPLETE:
		print "Incomplete tasks:"
		print schedules.incomplete_tasks
	table = {}
	for schedule in schedules.schedules:
		table.update({ schedule.id : {"Group": "", "Start" : schedule.start, "End" : schedule.end } });
	return table;

def print_schedule(schedule):
	# print the schedule sorted by their starting time.
	sorted_schedule = [(v["Start"], key) for key, v in schedule.iteritems()];
	sorted_schedule.sort(key=lambda x: x[0]);

	table = PrettyTable(["Task", "Group", "Start", "End"]);
	table.align["Task"] = "l";
	table.padding_width = 1;

	for start_time, key in sorted_schedule:
		start_string = datetime.fromtimestamp(schedule[key]["Start"]).strftime("%X %x %a");
		end_string = datetime.fromtimestamp(schedule[key]["End"]).strftime("%X %x %a");
		table.add_row([key, schedule[key]["Group"], start_string, end_string]);
	print table

# Specification of time segment:
# 8:50am!20m~45m
# This event starts at 8:50am with 20m tolerance of starting time, and will last for 45m.
#
# 1h+30m>15:00<22:00
# This event lasts for 1 hour, and has cool_down time of 30m (any task depent on it must starts after 30m of its completion). 
# Also, this event should be scheduled between 15:00 and 22:00.
# 
# 1h<<16:00
# This event lasts for 1 hour and should be finished before 16:00.
# 
# 8:50am/Sun~45m*1d
# This event starts from 8:50am Sunday, lasts for 45m and will repeat every day.
# 
# 1h>15:00<23:00^1d
# This event lasts for 1 hour and should be scheduled anyday after 15:00 and before 23:00.

def convert_time_seg(time_seg, start_time, end_time):
	# From table to Task
	percent = time_seg.get("percent", 0);
	if percent == 100: return [];

	# print start_time, end_time;

	time = task_pb2.TimeSegment()
	if "priority" in time_seg:
		time.priority = time_seg["priority"];

	if "duration" in time_seg:
		time.duration = util_dt_duration(time_seg["duration"]) * (100 - percent) / 100;

	if "deadline" in time_seg:
		time.deadline = util_dt_time(time_seg["deadline"]);

	if "cool_down" in time_seg:
		time.cool_down = util_dt_duration(time_seg["cool_down"]);

	if "start" in time_seg:
		st = time_seg["start"];
		tol = time_seg.get("start_tol", timedelta(0));
		earliest_start_time = st - tol;
		latest_start_time = st + tol;

		if "end" in time_seg:
			time.duration = util_dt_duration(time_seg["end"] - st);
	else:
		latest_start_time = time_seg.get("start_before", end_time);
		earliest_start_time = time_seg.get("start_after", start_time);

	# print "----"
	# print start_time, end_time;

	# Deal with repeated tasks.
	times = [];

	repeat_duration = time_seg.get("rep", None);
	alternative_duration = time_seg.get("alternative", None)

	while earliest_start_time < end_time:
		latest_start_time_this = latest_start_time;
		earliest_start_time_this = earliest_start_time;

		this_end_time = end_time;
		if repeat_duration: 
			this_end_time = earliest_start_time + repeat_duration - time_seg["duration"]

		# print "timestamp_this:";
		# print earliest_start_time_this, latest_start_time_this

		if latest_start_time_this >= earliest_start_time_this:
			time_this = task_pb2.TimeSegment();
			time_this.CopyFrom(time);
			while earliest_start_time_this < this_end_time:
				latest_start_time_ii = min(latest_start_time_this, end_time)
				earliest_start_time_ii = max(earliest_start_time_this, start_time)

				if latest_start_time_ii >= earliest_start_time_ii:
					# print "timestamp_ii:";
					# print earliest_start_time_ii, latest_start_time_ii;
					time_this.earliest_starts.append(util_dt_time(earliest_start_time_ii));
					time_this.latest_starts.append(util_dt_time(latest_start_time_ii));

				if not alternative_duration: break;
				earliest_start_time_this += alternative_duration;
				latest_start_time_this += alternative_duration;

			if len(time_this.earliest_starts) > 0:
				times.append(time_this);

		if not repeat_duration: break;
		# print "-----";
		earliest_start_time += repeat_duration;
		latest_start_time += repeat_duration;

	return times;

def parse_time_seg(scheduling_str, additional={}, start_time=datetime.now()):
	# 8:50am+-20m~45m>15:00<22:00<<deadline%80+cooldown*RepPattern
	# 1h+30m...
	s = dict(additional);

	def set_timestamp(string, loc, toks, key): s[key] = parse_time(toks[-1], start_time);
	def set_duration(string, loc, toks, key): s[key] = parse_duration(toks[-1]);
	def set_percent(string, loc, toks): 
		if toks[-1].lower() == "done" or toks[-1].lower() == "canceled":
			s["percent"] = 100;			
		else:
			s["percent"] = int(toks[-1]);
	def set_priority(string, loc, toks): 
		if toks[-1].lower() == "mustdo" or toks[-1].lower() == "highest":
			s["priority"] = 100;			
		else:
			s["priority"] = int(toks[-1]);			

	atom_time_comp1 = Literal(":") + Word(nums);
	atom_time_comp2 = Literal("am") | Literal("pm")
	atom_time_comp3 = Literal("/") + Word(alphas)
	atom_time = Combine(Word(nums) + OneOrMore(atom_time_comp1 | atom_time_comp2 | atom_time_comp3))
	atom_days = Word(nums) + "d";
	atom_hours = Word(nums) + "h";
	atom_minutes = Word(nums) + "m";
	atom_seconds = Word(nums) + "s";
	atom_duration_ele = atom_days | atom_hours | atom_minutes | atom_seconds;
	atom_duration = Combine(OneOrMore(atom_duration_ele));
	tok_start_time1 = (StringStart() + atom_time).setParseAction(lambda s, l, t: set_timestamp(s, l, t, "start"));
	tok_duration1 = (StringStart() + atom_duration).setParseAction(lambda s, l, t: set_duration(s, l, t, "duration"))
	tok_start_time2 = (Literal("=") + atom_time).setParseAction(lambda s, l, t: set_timestamp(s, l, t, "start"));
	tok_duration2 = (Literal("~") + atom_duration).setParseAction(lambda s, l, t: set_duration(s, l, t, "duration"));
	tok_end_time = (Literal("-") + atom_time).setParseAction(lambda s, l, t: set_timestamp(s, l, t, "end"));
	tok_time_tol = (Literal("!") + atom_duration).setParseAction(lambda s, l, t: set_duration(s, l, t, "start_tol"));
	tok_start_before = (Literal("<") + atom_time).setParseAction(lambda s, l, t: set_timestamp(s, l, t, "start_before"));
	tok_start_after = (Literal(">") + atom_time).setParseAction(lambda s, l, t: set_timestamp(s, l, t, "start_after"));
	tok_deadline = (Literal("<<") + atom_time).setParseAction(lambda s, l, t: set_timestamp(s, l, t, "deadline"))
	tok_complete_percent = (Literal("%") + Word(alphanums)).setParseAction(set_percent);
	tok_cool_down = (Literal("+") + atom_duration).setParseAction(lambda s, l, t: set_duration(s, l, t, "cool_down"))
	tok_rep = (Literal("*") + atom_duration).setParseAction(lambda s, l, t: set_duration(s, l, t, "rep"));
	tok_alternative = (Literal("^") + atom_duration).setParseAction(lambda s, l, t: set_duration(s, l, t, "alternative"));
	tok_priority = (Literal("$") + Word(alphanums)).setParseAction(set_priority);

	tok_first = tok_start_time1 | tok_duration1;
	tok_any = tok_start_time2 | tok_end_time | tok_duration2 | tok_time_tol | tok_start_before | tok_start_after | tok_deadline | tok_complete_percent | tok_cool_down | tok_rep | tok_alternative | tok_priority;
	parse = Optional(tok_first) + ZeroOrMore(tok_any)

	try: 
		L=parse.parseString(scheduling_str);
	except ParseException,err:
		return None;
	return s;

def process_tasks_yaml(file_name, start_time):
	config = yaml.load(open(file_name, "r"));
	# From the config file, prepare the task.
	end_time = parse_time(config["_End_Time_"]);

	tasks = task_pb2.Tasks()
	for group, content in config.iteritems():
		if not isinstance(content, list): continue;

		is_sequence = group[-1] != "_";
		prev_task_id = "";
		global_segment = {};
		prereq = None;
		for task_item in content:
			# print task_item
			task_id, spec = task_item.split(" ", 2);
			if task_id == "set_":
				global_segment = parse_time_seg(spec, start_time=start_time);
				continue;
			if task_id == "pre_req_":
				prereq = spec.split(",");
				continue;				

			segment = parse_time_seg(spec, additional=global_segment, start_time=start_time);
			# print segment
			this_times = convert_time_seg(segment, start_time, end_time);

			for idx, time in enumerate(this_times):
				task = tasks.tasks.add();
				if idx > 0: 
					task.id = task_id + "-" + str(idx);
				else:
					task.id = task_id;
				task.group = group;
				task.time.CopyFrom(time);
				if prereq:
					task.pre_req_ids.extend(prereq);
				if is_sequence and prev_task_id:
					task.pre_req_ids.append(prev_task_id)
				
				prev_task_id = task_id;

	tasks.global_start_time = util_dt_time(start_time);
	tasks.rest_time = time_to_rest;
	tasks.max_heap_size = 100;
	return tasks;

if __name__ == '__main__':
	# Load the task.
	# now = parse_time("16:00 09/27/2014")
	now = datetime.now();
	tasks = process_tasks_yaml(sys.argv[1], now)
	# print tasks;

	schedules_string = schedule_pylib.MakeSchedule(tasks.SerializeToString())

	if schedules_string:
		schedules = task_pb2.Schedules.FromString(schedules_string);
		schedule = ConvertSchedule(schedules)
		print_schedule(schedule);
