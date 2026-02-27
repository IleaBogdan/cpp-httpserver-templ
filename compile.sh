#!/bin/bash

if [ ! -d "bin" ]; then
    # echo "no bin dir"
    mkdir bin
fi

g++ -std=c++23 -pthread main.cpp -o ./bin/server
# If using SQLite:
# g++ -std=c++23 -pthread main.cpp -lsqlite3 -o myapp