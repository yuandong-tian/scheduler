#!/bin/bash
./macro_scheduler.py sample_todo.org > tmp.yaml
./schedule.py tmp.yaml

