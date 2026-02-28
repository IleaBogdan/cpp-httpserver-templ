@echo off

if not exist "bin" (
    mkdir bin
)

if "%1"=="update" (
    echo generating the yaml file...
    python generate_openapi.py
    echo file generated!
    echo.
    if exist "openapi.yaml" (
        move /Y openapi.yaml .\static\openapi.yaml
    )
)

echo compiling cpp files...
g++ -std=c++23 -I"C:\Program Files\Crow 1.3.1\include" -DWINDOWS -pthread *.cpp -o .\bin\server -lsqlite3 -lws2_32 -lmswsock
echo compilation done!