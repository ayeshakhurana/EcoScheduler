# ml_trainer.py
from sklearn.ensemble import RandomForestClassifier
import joblib, json, os
import numpy as np

# ---------- Train small model (synthetic) ----------
X = [[s] for s in range(1,41)]
y = [0 if s <= 2 else 1 if s <= 6 else 2 for s in range(1,41)]  # 0=low,1=medium,2=high
clf = RandomForestClassifier(n_estimators=50, random_state=1)
clf.fit(X, y)
joblib.dump(clf, "rf_joblib.pkl")

# ---------- Read tasks.txt and predict ----------
profiles = {}
if os.path.exists("tasks.txt"):
    with open("tasks.txt") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(',')
            name = parts[0]
            secs = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 5
            pred = clf.predict([[secs]])[0]
            label = {0:"low", 1:"medium", 2:"high"}[int(pred)]
            profiles[name] = label

with open("profiles.json","w") as fo:
    json.dump(profiles, fo, indent=2)

print("WROTE profiles.json:", profiles)
