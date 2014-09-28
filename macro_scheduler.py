#!/usr/bin/python

import os;
import sys;
import re;
from pyparsing import Word, alphas, printables, ParseException, SkipTo, Literal, Combine, Optional, nums, Or, Forward, ZeroOrMore, OneOrMore, StringEnd, StringStart, alphanums
import dateutil.parser;

regulars = [
  "set_ *1d$mustdo",
  "Breakfast+Commute 8:50am!20m~45m",
  "Lunch 12:00pm!30m~1h",
  "Dinner 6:30pm!30m~45m",
  "Shower 22:00!1h30m~15m",
  "Sleep 23:30!30m~7h45m",
  "set_ *2d$1",
  "Jogging 22:00!30m~1h"
]

def label_has(labels, keyword):
	return any([label == keyword for label in labels]);

type_head = 0;
type_subhead = 1;
type_title = 2;

s = {};
def set_label(string, loc, toks): s["label"].append(toks[1])
def set_content(string, loc, toks): s["content"] = toks[0]
def set_head(string, loc, toks): s["type"] = type_head;
def set_subhead(string, loc, toks): s["type"] = type_subhead;
def set_title(string, loc, toks): s["type"] = type_title;

Label = (Literal("[") + SkipTo(']') + "]").setParseAction(set_label);
Sentence = (Word(alphanums + " ")).setParseAction(set_content);
Subhead = (Literal("+") + ZeroOrMore(Label) + Sentence).setParseAction(set_subhead)
Headline = (Word(nums) + Literal(".") + ZeroOrMore(Label) + Sentence).setParseAction(set_head)
Title = (Literal("*") + Sentence).setParseAction(set_title)

Line = StringStart() + (Subhead | Headline | Title);

# Read a todo list, generate a schedule for the scheduler to optimize.
curr_headline = "";

items = [];

for line in open(sys.argv[1], "r"):
	s.clear();
	s["label"] = [];

	try: 
		L=Line.parseString(line);
	except ParseException,err:
		continue;

	labels = [label.lower() for label in s["label"]];
	work = s["content"].replace(" ", "-");

	if s["type"] == type_title:
		print "_End_Time_: " + "23:59/" + s["content"];		
		continue;

	if s["type"] == type_head:
		current_headline = s["content"].strip();
#		print "Head = ", current_headline
		continue;

	if label_has(labels, "done") or label_has(labels, "notyet"): continue;
	items.append(work);
	if label_has(labels, "coding"):
		# For coding, we need multiple cycles.
		print work + " :"
		print "  -", work + "-1 2h+1h"
		print "  -", work + "-2 20m+1h"
		print "  -", work + "-3 10m+1h"

	elif label_has(labels, "plan"):
		print work + ":";
		print "  -", work, "30m"
	else:
		if current_headline.lower() == "research":
			labels = ["1h30m"];
		elif current_headline.lower() == "reading":
			labels = ["30m"]

		print work + ":";
		print "  -", work, "".join(labels);

# Finally check items.
print "Calender_: "
for regular in regulars:
	task_name, task_spec = regular.split(" ")
	# print task_name, task_spec
	if any([k.lower().find(task_name.lower()) >= 0 for k in items]): continue;
	print "  - " + task_name + " " + task_spec;
