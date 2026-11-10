#!/usr/bin/env bash

# Clear any hidden, jammed port infrastructure locks
pkill -f "python3 -m http.server"
sleep 1

# Write data out to standard file before server launch
python3 core_engine.py > index.html

# Trigger stable local server ignition in background
nohup python3 -m http.server 8080 > logs/server.log 2>&1 &
sleep 1

# Print running process index and logs status
echo "Local network node server deployed."
cat logs/server.log
