#!/usr/bin/python

from schedule import *
import unittest

class ParseTest(unittest.TestCase):
	def assertTimeEqual(self, dt1, dt2):
		diff = dt1 - dt2;
		if abs(diff.total_seconds()) >= 1:
			print "Assert failed:", dt1, "!=", dt2
			self.assertLess(abs(diff.total_seconds()), 1);

	def _check_start_end(self, task, index, s1_str, s2_str):
		# self.assertAlmostEqual(datetime.fromtimestamp(task.earliest_starts[index]), parse_time(s1_str));
		# self.assertAlmostEqual(datetime.fromtimestamp(task.latest_starts[index]), parse_time(s2_str));
		#self.assertEqual(datetime.fromtimestamp(task.earliest_starts[index]), parse_time(s1_str));
		#self.assertEqual(datetime.fromtimestamp(task.latest_starts[index]), parse_time(s2_str));
		self.assertTimeEqual(datetime.fromtimestamp(task.earliest_starts[index]), parse_time(s1_str));
		self.assertTimeEqual(datetime.fromtimestamp(task.latest_starts[index]), parse_time(s2_str));

	def test_parse_time_seg(self):
		start_time = parse_time("22:00 09/26/2014")
		task = parse_time_seg(">15:00", start_time=start_time);
		self.assertEqual(task["start_after"], parse_time("15:00", start_time=start_time));
		self.assertEqual(len(task), 1);

		task = parse_time_seg("*1d", start_time=start_time);
		self.assertEqual(task["rep"], parse_duration("1d"));
		self.assertEqual(len(task), 1);

		task = parse_time_seg("8:50am!20m~45m>15:00<22:00<<22:30/Fri%80+1h*7d$50", start_time=start_time);
		self.assertEqual(task["rep"], parse_duration("7d"));
		self.assertEqual(task["start"], parse_time("8:50am", start_time=start_time));
		self.assertEqual(task["start_tol"], parse_duration("20m"));
		self.assertEqual(task["duration"], parse_duration("45m"));
		self.assertEqual(task["start_before"], parse_time("22:00", start_time=start_time));
		self.assertEqual(task["start_after"], parse_time("15:00", start_time=start_time));
		self.assertEqual(task["deadline"], parse_time("22:30/Fri", start_time=start_time));
		self.assertEqual(task["percent"], 80);
		self.assertEqual(task["cool_down"], parse_duration("1h"));
		self.assertEqual(task["rep"], parse_duration("7d"));
		self.assertEqual(task["priority"], 50);

		task = parse_time_seg("1h30m+5h<<16:00$mustdo", start_time=start_time);
		self.assertEqual(task["duration"], parse_duration("1h30m"));
		self.assertEqual(task["cool_down"], parse_duration("5h"));
		self.assertEqual(task["deadline"], parse_time("16:00", start_time=start_time));
		self.assertEqual(task["priority"], 100);		

		task = parse_time_seg("8:15-8:25!20m+90m", start_time=start_time);
		self.assertEqual(task["cool_down"], parse_duration("90m"));
		self.assertEqual(task["start"], parse_time("8:15", start_time=start_time));
		self.assertEqual(task["end"], parse_time("8:25", start_time=start_time));
		self.assertEqual(task["start_tol"], parse_duration("20m"));

	def test_convert_time_seg(self):
		args = {};
		args["start_time"] = parse_time("22:00 09/26/2014")
		args["end_time"] = parse_time("22:00 09/29/2014")

		task = { "duration": parse_duration("20m") };
		res = convert_time_seg(task, **args);
		self.assertEqual(len(res), 1);
		self.assertEqual(res[0].duration, util_dt_duration(task["duration"]));

		task = { "start": parse_time("09:00"), "end" : parse_time("10:00") };
		res = convert_time_seg(task, **args);
		self.assertEqual(len(res), 1);
		self.assertEqual(res[0].duration, util_duration("1h"));

		task = { "start_after" : parse_time("07:00am", start_time=args["start_time"]), 
		         "start_before" : parse_time("12:00pm", start_time=args["start_time"]),
		         "duration" : parse_duration("20m"), 
		         "alternative": parse_duration("1d") };
		         		         
		res = convert_time_seg(task, **args);
		self.assertEqual(len(res), 1)
		self.assertEqual(res[0].duration, util_dt_duration(task["duration"]));
		self.assertEqual(len(res[0].earliest_starts), len(res[0].latest_starts));
		self.assertEqual(len(res[0].earliest_starts), 3);

		self._check_start_end(res[0], 0, "07:00am 09/27/2014", "12:00pm 09/27/2014");
		self._check_start_end(res[0], 1, "07:00am 09/28/2014", "12:00pm 09/28/2014");
		self._check_start_end(res[0], 2, "07:00am 09/29/2014", "12:00pm 09/29/2014");

		task = { "start_after" : parse_time("21:00pm", start_time=args["start_time"]), 
		         "start_before" : parse_time("23:00pm", start_time=args["start_time"]),
		         "duration" : parse_duration("20m"), 
		         "alternative": parse_duration("1d") };

		res = convert_time_seg(task, **args);
		self.assertEqual(len(res), 1)
		self.assertEqual(res[0].duration, util_dt_duration(task["duration"]));
		self.assertEqual(len(res[0].earliest_starts), len(res[0].latest_starts));
		self.assertEqual(len(res[0].earliest_starts), 4);

		self._check_start_end(res[0], 0, "22:00pm 09/26/2014", "23:00pm 09/26/2014");
		self._check_start_end(res[0], 1, "21:00pm 09/27/2014", "23:00pm 09/27/2014");
		self._check_start_end(res[0], 2, "21:00pm 09/28/2014", "23:00pm 09/28/2014");
		self._check_start_end(res[0], 3, "21:00pm 09/29/2014", "22:00pm 09/29/2014");

		task = { "start" : parse_time("21:50", start_time=args["start_time"]), 
		         "start_tol" : parse_duration("15m"),
		         "duration" : parse_duration("45m"), 
		         "rep": parse_duration("1d") };

		res = convert_time_seg(task, **args);
		self.assertEqual(len(res), 4)
		for sub_task in res:
			self.assertEqual(sub_task.duration, util_duration("45m"));
			self.assertEqual(len(sub_task.earliest_starts), len(sub_task.latest_starts));
			self.assertEqual(len(sub_task.earliest_starts), 1);

		self._check_start_end(res[0], 0, "22:00pm 09/26/2014", "22:05pm 09/26/2014");
		self._check_start_end(res[1], 0, "21:35pm 09/27/2014", "22:05pm 09/27/2014");
		self._check_start_end(res[2], 0, "21:35pm 09/28/2014", "22:05pm 09/28/2014");
		self._check_start_end(res[3], 0, "21:35pm 09/29/2014", "22:00pm 09/29/2014");

		task = { "start" : parse_time("21:50", start_time=args["start_time"]), 
		         "start_tol" : parse_duration("15m"),
		         "duration" : parse_duration("45m"), 
		         "rep": parse_duration("1d"),
		         "alternative" : parse_duration("12h") };

		res = convert_time_seg(task, **args);
		self.assertEqual(len(res), 4)
		for sub_task in res:
			self.assertEqual(sub_task.duration, util_duration("45m"));
			self.assertEqual(len(sub_task.earliest_starts), len(sub_task.latest_starts));

		self.assertEqual(len(res[0].earliest_starts), 2);
		self._check_start_end(res[0], 0, "22:00 09/26/2014", "22:05 09/26/2014");
		self._check_start_end(res[0], 1, "9:35 09/27/2014", "10:05 09/27/2014");

		self.assertEqual(len(res[1].earliest_starts), 2);
		self._check_start_end(res[1], 0, "21:35 09/27/2014", "22:05 09/27/2014");
		self._check_start_end(res[1], 1, "9:35 09/28/2014", "10:05 09/28/2014");

		self.assertEqual(len(res[2].earliest_starts), 2);
		self._check_start_end(res[2], 0, "21:35 09/28/2014", "22:05 09/28/2014");
		self._check_start_end(res[2], 1, "9:35 09/29/2014", "10:05 09/29/2014");

		self.assertEqual(len(res[3].earliest_starts), 1);
		self._check_start_end(res[3], 0, "21:35 09/29/2014", "22:00 09/29/2014");

#class ScheduleLibTest(unittest.TestCase)

if __name__ == '__main__':
	unittest.main()