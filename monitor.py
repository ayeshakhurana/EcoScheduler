# monitor.py
# Usage: python3 monitor.py
import json, time
import psutil

def main():
    info = {}
    try:
        batt = psutil.sensors_battery()
        if batt is not None:
            info['battery_percent'] = round(batt.percent,1)
            info['on_ac'] = batt.power_plugged
        else:
            info['battery_percent'] = 100.0
            info['on_ac'] = True
    except Exception as e:
        info['battery_percent'] = 100.0
        info['on_ac'] = True

    # CPU percent instantaneous (1s)
    info['cpu_percent'] = psutil.cpu_percent(interval=1)

    # Write monitor.txt for scheduler (simple key:value)
    with open("monitor.txt","w") as f:
        f.write(f"battery_percent:{info['battery_percent']}\\n")
        f.write(f"on_ac:{info['on_ac']}\\n")
        f.write(f"cpu_percent:{info['cpu_percent']}\\n")

    print("Wrote monitor.txt:", info)

if __name__ == "__main__":
    main()
