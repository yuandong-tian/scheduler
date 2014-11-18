#!/bin/bash
./macro_scheduler.py ../../../daily_plan/plans/plans.org tmp.yaml
#./macro_scheduler.py sample_todo.org > tmp.yaml
./schedule.py tmp.yaml

