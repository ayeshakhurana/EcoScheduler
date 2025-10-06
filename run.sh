#!/usr/bin/env bash
set -e
echo "=== Build task_worker ==="
clang++ -std=c++17 -O2 -pthread task_worker.cpp -o task_worker
echo "=== Build scheduler ==="
clang++ -std=c++17 -O2 -pthread scheduler.cpp -o scheduler

echo
echo "=== Run monitor.py to capture system state ==="
python3 monitor.py

echo
echo "=== Train tiny ML and write profiles.json + tasks.txt ==="
python3 ml_trainer.py

echo
echo "=== Run scheduler (it will launch task_worker processes) ==="
./scheduler

echo
echo "=== Done ==="
