OPT = -O3 -msse3

INCLUDES = -I/usr/local/include/google/protobuf
LIBS = 
CXX_FLAGS = -std=c++0x -lstdc++
PROTO_FLAGS = `pkg-config --cflags --libs protobuf`

GCC = gcc
PYTHON_FLAGS = -I/usr/include/python2.7/ -lpython2.7

schedule_pylib: *.cc *.h
	protoc --cpp_out=. --python_out=. task.proto
	#${GCC} ${OPT} -shared -Wl,-soname,schedule_pylib.so -o schedule_pylib.so -fPIC ${CXX_FLAGS} ${INCLUDES} ${LIBS} ${PROTO_FLAGS} ${PYTHON_FLAGS} task.pb.cc schedule_lib.cc schedule_py2.cc
	${GCC} ${OPT} -shared -o schedule_pylib.so -fPIC ${CXX_FLAGS} ${INCLUDES} ${LIBS} ${PROTO_FLAGS} ${PYTHON_FLAGS} task.pb.cc schedule_lib.cc schedule_py2.cc

test_schedule: *.cc *.h
	protoc --cpp_out=. task.proto
	${GCC} ${OPT} ${CXX_FLAGS} ${INCLUDES} ${LIBS} ${PROTO_FLAGS} task.pb.cc schedule_lib.cc schedule_test.cc -o test_schedule
