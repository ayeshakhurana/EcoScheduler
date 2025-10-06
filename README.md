# Eco-Aware Scheduler (user-space prototype)

## Setup
1. Install Python deps:
   `python3 -m pip install --user psutil scikit-learn joblib`
2. In terminal inside project folder:
   `chmod +x run.sh`
   `./run.sh`

## Files
- task_worker.cpp : simulated CPU-bound task
- scheduler.cpp   : user-space eco scheduler (reads monitor.txt, profiles.json, tasks.txt)
- monitor.py      : writes monitor.txt (battery, on_ac, cpu)
- ml_trainer.py   : trains small RF and emits profiles.json and tasks.txt
- run.sh          : builds & runs everything

## How it works
- `ml_trainer.py` builds a tiny RandomForest on synthetic data and labels demo tasks low/medium/high.
- `monitor.py` polls battery/cpu and writes `monitor.txt`.
- `scheduler` uses labels + battery to decide whether to defer high-energy tasks when battery < 30%.
- Tasks are simple CPU workers (`task_worker`) to demonstrate behavior.

