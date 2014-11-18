#!/usr/bin/python

import os;
import sys;
import re;
from pyparsing import Word, alphas, printables, ParseException, SkipTo, Literal, Combine, Optional, nums, Or, Forward, ZeroOrMore, OneOrMore, StringEnd, StringStart, alphanums
import dateutil.parser;
from ete2 import Tree

class TreeBuilder:
	def __init__(self, num_level):
		self.tree = [[] for i in range(num_level)]

	def prefix(self, levelfrom, levelto):
		prefixs = [self.tree[l][-1]["name"] for l in range(levelfrom, levelto)];
		return "-".join(prefixs);

	def take(self, level, name):
		self.tree[level].append({"name" : name, "children": []});
		if level > 0:
			self.tree[level - 1][-1]["children"].append(len(self.tree[level]) - 1);

	def post_traverse(self, level=0, index=0):
		# post_traverse node at level with index 
		child_str = "";
		children = self.tree[level][index]["children"];
		if children:
			child_str = [self.post_traverse(level + 1, child) for child in children];
			child_str = "(" + ",".join(child_str) + ")";

		return child_str + self.tree[level][index]["name"];

def label_has(labels, keywords):
	if isinstance(keywords, list):
		return any([label in keywords for label in labels]);
	else:
		return any([label == keywords for label in labels]);

def get_schedule_item(work, labels, prev_works):
	if label_has(labels, ["done", "notyet", "cancelled", "cancel", "hashtag"]): return [];

	output_lines = [];	
	output_lines.append(work + " :");
	if label_has(labels, ["seq"]) and prev_works:
		output_lines.append("  prereqs: " + ",".join(prev_works));
		labels = [label for label in labels if label != "seq"];
	output_lines.append("  labels: " + "".join(labels));
	return output_lines;

s = {};
def set_label(string, loc, toks): s["label"].append(toks[1].lower())
def set_content(string, loc, toks): s["content"] = toks[0].replace(" ", "-")
def set_hashtag(string, loc, toks): s["content"] = toks[1]; s["label"].append("hashtag");

def set_node(string, loc, toks, level): s["level"] = level;
def setter(level): return lambda s, l, t: set_node(s, l, t, level)

Label = (Literal("[") + SkipTo(']') + "]").setParseAction(set_label);
Sentence = (Word(alphanums + " .-\"'")).setParseAction(set_content);
Hashtag = (Literal("#") + Word(alphanums)).setParseAction(set_hashtag)

Title = (Literal("*") + Sentence).setParseAction(setter(1))
Hashtagline = (Hashtag + ZeroOrMore(Label) + Optional(Sentence)).setParseAction(setter(2))
Headline = (Word(nums) + Literal(".") + ZeroOrMore(Label) + Sentence).setParseAction(setter(2))
Sub1head = (Literal("+") + ZeroOrMore(Label) + Sentence).setParseAction(setter(3))
Sub2head = (Literal("  +") + ZeroOrMore(Label) + Sentence).setParseAction(setter(4))
Sub3head = (Literal("    +") + ZeroOrMore(Label) + Sentence).setParseAction(setter(5))
Sub4head = (Literal("      +") + ZeroOrMore(Label) + Sentence).setParseAction(setter(6))

Line = StringStart() + (Sub1head | Sub2head | Sub3head | Sub4head | Headline | Title | Hashtagline | Sentence);

# Read a todo list, generate a schedule for the scheduler to optimize.
node_table = {};
tree_builder = TreeBuilder(7);
tree_builder.take(0, "_Root");

for line in open(sys.argv[1], "r"):
	# Schedule to here.
	if line.startswith("###"): break;
	# print line

	s.clear();
	s["label"] = [];
	s["level"] = 0;
	s["notes"] = "";

	try: 
		L = Line.parseString(line);
	except ParseException, err:
		continue;

	# print s;

	if s["level"] >= 3:
		s["level"] = line.find("+") / 2 + 3;

	if s["level"] == 0:
		# Text.
		node_table[entry]["notes"] += s["content"];
	else:
		entry = tree_builder.prefix(1, s["level"]) + "-" + s["content"];
		s["entry"] = entry;
		tree_builder.take(s["level"], s["content"]);
		node_table.update({s["entry"] : dict(s)});

tree_str = tree_builder.post_traverse();
#print tree_str;
tree = Tree(tree_str + ";", format=1);
#print tree

# Get all the leafs.
def get_node_info(node):
	names = [pa.name for pa in reversed(node.get_ancestors())];
	key = "-".join(names[1:]) + "-" + node.name;
	if not key in node_table: return None;
	return node_table[key];

def leaf_fun(node): 
	if node.name == "_Root": return False;
	if node.is_leaf(): return True;

	s = get_node_info(node);
	if s is None: return True;
	return label_has(s["label"], ["done", "notyet", "cancel", "cancelled", "covered", "hashtag"]);

# Get all the not yet terms.
not_done_entries = set();
for subtree in tree.children[:-1]:
	for node in subtree.iter_leaves(is_leaf_fn=leaf_fun):
		s = get_node_info(node);
		if s is None: continue;
		if not label_has(s["label"], ["done", "cancel", "cancelled", "covered", "hashtag"]):
			not_done_entries.add(s["entry"]);

print "-------- Not done list --------";
not_done_entries = list(not_done_entries);
not_done_entries.sort();

print "\n".join(not_done_entries);
print "-------------------------------";

items = [];
output_lines = [];

# Get the last headline node.
output_lines.append("_End_Time_: " + "23:59/" + get_node_info(tree.children[-1])["content"]);
prev_works = [];
for leaf in tree.children[-1].iter_leaves(is_leaf_fn=leaf_fun):
	s = get_node_info(leaf);
	if s is None: continue;

	work_to_do = get_schedule_item(s["entry"], s["label"], prev_works)
	if work_to_do:
		items.append(leaf.name);
		output_lines += work_to_do;
	prev_works = [s["entry"]];

regulars = [
  "Onboardmeeting 15:00/Thu~30m",
  "Breakfast+Commute 8:50am!20m~45m*1d$mustdo",
  "Lunch 12:00pm!30m~1h*1d$mustdo",
  "Dinner 6:30pm!30m~45m*1d$mustdo",
  "Shower 22:00!1h30m~15m*1d$mustdo",
  "Sleep 23:30!30m~7h45m*1d$mustdo",
  "Jogging 22:00!30m~1h*2d$1"
]

# Finally check items.
for regular in regulars:
	task_name, task_spec = regular.split(" ")
	# print task_name, task_spec
	if any([k.lower().find(task_name.lower()) >= 0 for k in items]): continue;
	output_lines.append(task_name + ": ");
	output_lines.append("  labels: " + task_spec);

open(sys.argv[2], "w").write("\n".join(output_lines));