#include "schedule_lib.h"

#include <queue>
#include <vector>
#include <utility>
#include <string>
#include <map>
#include <iostream>
#include <limits>
#include <time.h>
#include <set>

using namespace std;
using namespace schedule;

/////////////////////////////////Heap////////////////////////////////////////////
template <typename Key, typename T>
class Heap {
private:
	struct HeapSlot {
		Key key;
		T content;
		// The pointer will maintain its location in the heap.
		int *backIndexPtr;
		HeapSlot() {
		}
		HeapSlot(const Key &k, const T &c, int *const ptr) 
			:key(k), content(c), backIndexPtr(ptr) {
		}
	};
	std::vector<HeapSlot> m_heap;
	int m_heapSize;

	void GenerateZeroPos() {
		// Always the first element.
		m_heap[0].key = -std::numeric_limits<Key>::max();
	}

	inline bool set_back_ptr(int index, int val) {
		int *back_ptr = m_heap[index].backIndexPtr;
		if (back_ptr != nullptr) {
			*back_ptr = val;
			return true;
		} else return false;
	}

public:
	Heap() {
		//
		m_heap.push_back(HeapSlot());
		m_heapSize = 0;
		GenerateZeroPos();
	}

	int GetSize() const { return m_heapSize; }

	void SiftUp(int index) {
		assert(index > 0);
		assert(index <= m_heapSize);
		while (m_heap[index].key < m_heap[index >> 1].key) {
			set_back_ptr(index >> 1, index);
			swap(m_heap[index], m_heap[index >> 1]);
			index >>= 1;
		}
		set_back_ptr(index, index);
	}
	void SiftDown(int index) {
		assert(index > 0);
		assert(index <= m_heapSize);
		while (2*index <= m_heapSize) {
			int nextIndex = index << 1;
			if (   (nextIndex + 1 <= m_heapSize) 
		    	&& (m_heap[nextIndex + 1].key < m_heap[nextIndex].key) ) 
				nextIndex ++;
			if (m_heap[nextIndex].key < m_heap[index].key) {
				set_back_ptr(nextIndex, index);
				swap(m_heap[nextIndex], m_heap[index]);
			}
			else break;
			index = nextIndex;
		}
		set_back_ptr(index, index);
	}
	void MakeHeap(const std::vector<Key> &keys, const std::vector<T> &contents, const std::vector<int *> &backIndexPointers) {
		assert(keys.size() == contents.size());
		m_heapSize = keys.size();
		m_heap.assign(m_heapSize + 1, HeapSlot());

		GenerateZeroPos();
		for (int i = 1; i <= m_heapSize; i ++) {
			m_heap[i].key = keys[i - 1];
			m_heap[i].content = contents[i - 1];
			m_heap[i].backIndexPtr = backIndexPointers[i - 1];
			*(m_heap[i].backIndexPtr) = i;
		}
		for (int i = m_heapSize >> 1; i >= 1; i --) {
			SiftDown(i);
		}
	}
	void Insert(const Key &key, const T &content, int *const backPtr) {
		m_heapSize++;
		m_heap.push_back(HeapSlot(key, content, backPtr));
		SiftUp(m_heapSize);
	}
	bool Delete(int index) {
		// Set the key to be the smallest.
		if (m_heapSize == 0)
			return false;		
		m_heap[index].key = -std::numeric_limits<Key>::max() / 2;
		SiftUp(index);
		// Then delete it from the top
		return DeleteMin(nullptr, nullptr);
	}

	bool IsEmpty()const {
		return m_heapSize < 1;
	}
	Key &GetKey(int index) {
		assert(index > 0 && index <= m_heapSize);
		return m_heap[index].key;
	}
	T &GetContent(int index) {
		assert(index > 0 && index <= m_heapSize);
		return m_heap[index].content;
	}

	// Get the minimal element and delete it.
	bool DeleteMin(Key* key, T* content) {
		if (m_heapSize == 0)
			return false;
		if (key != nullptr) *key = m_heap[1].key;
		if (content != nullptr) *content = m_heap[1].content;

		set_back_ptr(1, -1);
		if (m_heapSize > 1) {
			set_back_ptr(m_heapSize, 1);
			swap(m_heap[1], m_heap[m_heapSize]);
		}
		m_heapSize --;
		typename std::vector<HeapSlot>::iterator it = m_heap.end();
		--it;
		m_heap.erase(it);
		if (m_heapSize >= 1)
			SiftDown(1);
		return true;
	}
	bool CheckIndices(int &errValue)const {
		for (int i = 1; i <= m_heapSize; i++) {
			if ( *(m_heap[i].backIndexPtr) != i ) {
				errValue = i;
				return false;
			}
		}
		return true;
	}
};

void test_heap() {
	cout << "Testing heap" << endl;
	Heap<int, int> q;
	const int N = 100000;

	for (int i = 0; i < N; ++i)
		q.Insert(rand(), rand(), nullptr);

	vector<int> sorted_key;

	while (!q.IsEmpty()) {
		int key, val;
		q.DeleteMin(&key, &val);
		sorted_key.push_back(key);
	}

	// Check sorted
	for (int i = 1; i < N; ++i) {
		if (sorted_key[i - 1] > sorted_key[i]) {
			cout << "Heap output at " << i << " is not sorted!!";
		}
	}
	cout << "Done" << endl;
}

// Compact representation of schedule internal status.
struct ScheduleItem {
	int num_scheduled = 0;
	vector<time_t> end_timestamps;
	// The most recent ending timestamp.
	time_t end_timestamp = -1;
	int slot_index = -1;

	// Specify the number of tasks beforehand.
	// If a task is not scheduled, its end_timestamp is -1
	ScheduleItem() {
	}

	ScheduleItem(int N) : end_timestamps(N, -1) {
	}

	ScheduleItem next(int new_task, time_t end_timestamp) const {
		ScheduleItem new_item = *this;
		new_item.num_scheduled++;
		new_item.end_timestamps[new_task] = end_timestamp;
		new_item.end_timestamp = max(new_item.end_timestamp, end_timestamp);

		return new_item;
	}

	vector<int> GetOrder() const {
		vector<pair<time_t, int>> sort_pairs;
		for (int i = 0; i < end_timestamps.size(); ++i) {
			if (end_timestamps[i] > 0) {
				sort_pairs.emplace_back(make_pair(end_timestamps[i], i));
			}
		}

		sort(sort_pairs.begin(), sort_pairs.end());
		vector<int> order(sort_pairs.size());
		for (int i = 0; i < sort_pairs.size(); ++i) {
			order[i] = sort_pairs[i].second;
		}
		return order;
	}

	void PrintDebugInfo(const Tasks& tasks) const {
		for (int i = 0; i < end_timestamps.size(); ++i) {
			if (end_timestamps[i] < 0) continue;
			cout << "Task = " << tasks.tasks(i).id() << "  end = " << end_timestamps[i] << endl;
		}
	}

	friend bool operator<(const ScheduleItem& s1, const ScheduleItem& s2) {
		// Note since the priority queue in c++ always returns the greatest element, 
		// we reverse the definition of <.
		return s1.end_timestamp > s2.end_timestamp;
	}
};

typedef pair<float, ScheduleItem> SchedulePair;

time_t earliest_given_pre_req(time_t global_start_time, const Tasks& tasks,
	const ScheduleItem& completed, const vector<int>& pre_reqs) {

	// Find the earliest starting time.
	time_t start_time = completed.num_scheduled > 0 ? completed.end_timestamp : global_start_time;
	for (const int& pre_index : pre_reqs) {
		if (completed.end_timestamps[pre_index] < 0) return -1;
		start_time = max(start_time, completed.end_timestamps[pre_index] + tasks.tasks(pre_index).time().cool_down());
	}
	return start_time;
}

// Can the current task start with the given start_time (or later)
// If not, return -1, else return the earliest start time for the task.
time_t earliest_given_constraint(const Task& task, time_t start_time) {
	// Cannot miss the deadline.
	TimeSegment time = task.time();
	if (time.deadline() > 0 && start_time + time.duration() > time.deadline()) return -1;

	bool fit_in = false;
	for (int i = 0; i < time.earliest_starts_size(); ++i) {
		if (start_time <= time.latest_starts(i)) {
			start_time = max(start_time, (time_t)time.earliest_starts(i));
			fit_in = true;
			break;
		}
	}

	if (fit_in) return start_time;
	else return -1;
}

bool get_lb(const Tasks& tasks, const ScheduleItem& completed, float* score) {
	// Compute the heuristic function.
	time_t lower_bound = 0;
	for (int i = 0; i < tasks.tasks_size(); ++i) {
		if (completed.end_timestamps[i] >= 0) continue;
		const Task& task = tasks.tasks(i);

		time_t opt_start_time = earliest_given_constraint(task, completed.end_timestamp);
		// You can never start this job, set the score to be very low.
		if (opt_start_time < 0) {
			// Penalty for not achieving the goal.
			lower_bound += task.time().duration() * task.time().priority();
		} else {
			lower_bound += task.time().duration() + tasks.rest_time();
		}
	}

	*score = completed.end_timestamp + lower_bound;
	return true;
}

bool make_schedule(const Tasks& tasks, Schedules* schedules) {
	// test_heap();
	const int N = tasks.tasks_size();
	vector<int> back_container(tasks.max_heap_size() + N, -1);
	set<int> unused_slot;
	for (int i = 0; i < tasks.max_heap_size() + N; ++i) {
		unused_slot.insert(i);
	}

	// Preprocessing
	map<string, int> id_to_index;
	for (int i = 0; i < N; ++i) {
		const Task& task = tasks.tasks(i);		
		id_to_index.insert(make_pair(task.id(), i));
	}

	vector<vector<int>> pre_reqs(N);
	for (int i = 0; i < N; ++i) {
		const Task& task = tasks.tasks(i);
		pre_reqs[i].resize(task.pre_req_ids_size());

		for (int j = 0; j < task.pre_req_ids_size(); ++j) {
			pre_reqs[i][j] = id_to_index[task.pre_req_ids(j)];
		}
	}

	ScheduleItem best_schedule(N);
	float best_score;

	int num_steps = 0;
	Heap<float, ScheduleItem> q;
	Heap<float, int> back_q;

	ScheduleItem completed(N);
	completed.slot_index = 0;
	q.Insert(0.0, completed, &back_container[0]);	
	back_q.Insert(0.0, 0, nullptr);
	unused_slot.erase(0);

	float score;
	while (!q.IsEmpty()) {
		q.DeleteMin(&score, &completed);
		unused_slot.insert(completed.slot_index);
		// cout << score << endl;
		// completed.PrintDebugInfo(tasks);
		// cout << endl;

		// const float score = q.top().first;
		// // One extra copy here.
		// ScheduleItem completed = q.top().second;
		// q.pop();
		num_steps++;

		if (completed.num_scheduled > best_schedule.num_scheduled) {
			best_schedule = completed;
			best_score = score;
		}

		if (best_schedule.num_scheduled == N) break;

		// Make 
		for (int i = 0; i < N; ++i) {
			// Else try scheduling it.
			if (completed.end_timestamps[i] >= 0) continue;

			time_t start_time = earliest_given_pre_req(tasks.global_start_time(), tasks, completed, pre_reqs[i]);

			if (start_time < 0) continue;
			start_time = earliest_given_constraint(tasks.tasks(i), start_time + tasks.rest_time());

			if (start_time < 0) continue;
			time_t end_time = start_time + tasks.tasks(i).time().duration();

			ScheduleItem next_item = completed.next(i, end_time);
			float next_score;
			if (get_lb(tasks, next_item, &next_score)) {
				int slot_index = *unused_slot.begin();
				next_item.slot_index = slot_index;
				q.Insert(next_score, next_item, &back_container[slot_index]);
				back_q.Insert(-next_score, slot_index, nullptr);
				unused_slot.erase(slot_index);
			}
		}

		// If queue is too large, remove the worst one.
		while (q.GetSize() > tasks.max_heap_size()) {
			while (true) {
				int slot_index;
				back_q.DeleteMin(nullptr, &slot_index);
				int heap_index = back_container[slot_index];
				if (heap_index >= 0) {
					// Remove
					q.Delete(heap_index);
					unused_slot.insert(slot_index);
					break;
				}
			}
		}
	}
	// Get the best schedule.
	vector<int> order = best_schedule.GetOrder();

	if (order.size() < N) {
		schedules->set_status(Schedules_FinalStatus_INCOMPLETE);
		for (int i = 0; i < N; ++i) {
  		    // Save incompleted tasks.
  		    if (best_schedule.end_timestamps[i] < 0) {
  		    	schedules->add_incomplete_tasks(tasks.tasks(i).id());
  		    }
		}
	} else {
		schedules->set_status(Schedules_FinalStatus_SUCCESS);		
	}
	schedules->set_search_steps(num_steps);
	schedules->set_total_duration(best_schedule.end_timestamp - tasks.global_start_time());

	schedules->clear_schedules();
	// From the order, construct the best schedule and get their start/end timestamp.
	int duration = 0;
	for (int i = 0; i < order.size(); ++i) {
		Schedule* schedule = schedules->add_schedules();

		const int task_index = order[i];
		const Task& task = tasks.tasks(task_index);

		schedule->set_id(task.id());
		schedule->set_end(best_schedule.end_timestamps[task_index]);		
		schedule->set_start(schedule->end() - task.time().duration());
		duration += task.time().duration();
	}

	schedules->set_used_duration(duration);

	return true;
}
