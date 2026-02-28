#!/bin/bash

if [ ! -d "bin" ]; then
    # echo "no bin dir"
    mkdir bin
fi

if [ "$1" == "update" ]; then
    # echo "we should run the python parser"
    echo "generating the yaml file..."
    python3 generate_openapi.py
    echo "file generated!"
    echo
    if [ -f "openapi.yaml" ]; then
        mv ./openapi.yaml ./static/openapi.yaml
    fi
fi

echo "compiling cpp files..."
g++ -std=c++23 -DLINUX -pthread *.cpp -o ./bin/server -lsqlite3
echo "compilation done!"