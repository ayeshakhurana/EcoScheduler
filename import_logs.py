# import_logs.py
import sqlite3, csv, os

db = "ecoscheduler.db"
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT,
  task TEXT,
  action TEXT,
  label TEXT,
  energy REAL,
  battery REAL,
  on_ac INTEGER
)
''')
conn.commit()

if not os.path.exists("logs.csv"):
    print("❌ No logs.csv found.")
    exit(1)

with open("logs.csv", newline='') as f:
    reader = csv.reader(f)
    next(reader, None)  # skip header
    for row in reader:
        if len(row) < 7: 
            continue
        timestamp, task, action, label, energy, battery, on_ac = row
        try:
            energy = float(energy.strip())
            battery = float(battery.strip())
            on_ac = int(on_ac.strip())
        except Exception as e:
            print(f"⚠️ Skipping row due to parse error: {row} ({e})")
            continue

        c.execute('INSERT INTO logs (timestamp,task,action,label,energy,battery,on_ac) VALUES (?,?,?,?,?,?,?)',
                  (timestamp.strip(), task.strip(), action.strip(), label.strip(), energy, battery, on_ac))

conn.commit()
conn.close()
print("✅ Imported logs.csv into ecoscheduler.db")
