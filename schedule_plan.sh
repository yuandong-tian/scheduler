#!/bin/bash
if [ -z "$1" ] 
then
    filename=../../../daily_plan/plans/plans.org
else
    filename=$1
fi

./macro_scheduler.py $filename tmp.yaml
#./macro_scheduler.py sample_todo.org > tmp.yaml
./schedule.py tmp.yaml

