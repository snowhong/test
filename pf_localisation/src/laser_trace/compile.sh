#!/bin/bash

g++ laser_trace.cpp -fPIC -O3  -msse4 -shared -I/usr/include/python2.7 -I/usr/local/lib -lboost_python -lpython2.7 -o laser_trace.so

