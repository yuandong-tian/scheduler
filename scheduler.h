#ifndef _SCHEDULE_LIB_H_
#define _SCHEDULE_LIB_H_

#include "task.pb.h"

bool make_schedule(const schedule::Tasks& tasks, schedule::Schedules* schedules);

#endif
