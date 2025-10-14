# monitor.py
# Enhanced EcoScheduler Monitor with Dynamic Adaptation
# Usage: python3 monitor.py
import json, time
import psutil

def get_temperature():
    """Get system temperature if available"""
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            # Get the first available temperature sensor
            for name, entries in temps.items():
                if entries:
                    return entries[0].current
        return None
    except:
        return None

def get_cpu_load_factors():
    """Calculate CPU load factors for dynamic adaptation"""
    try:
        # Get CPU usage over different intervals
        cpu_1s = psutil.cpu_percent(interval=0.1)
        cpu_5s = psutil.cpu_percent(interval=0.5)
        
        # Calculate load average (simplified)
        load_avg = (cpu_1s + cpu_5s) / 2
        
        # Determine load category
        if load_avg > 80:
            load_category = "high"
        elif load_avg > 50:
            load_category = "medium"
        else:
            load_category = "low"
            
        return {
            'cpu_percent': cpu_1s,
            'cpu_5s_avg': cpu_5s,
            'load_category': load_category,
            'load_factor': load_avg / 100.0
        }
    except:
        return {
            'cpu_percent': 0,
            'cpu_5s_avg': 0,
            'load_category': 'low',
            'load_factor': 0.0
        }

def calculate_adaptation_factors(info):
    """Calculate dynamic adaptation factors based on system conditions"""
    factors = {
        'battery_factor': 1.0,
        'cpu_factor': 1.0,
        'thermal_factor': 1.0,
        'power_factor': 1.0
    }
    
    # Battery factor (reduces priority when battery is low)
    if not info['on_ac']:
        if info['battery_percent'] < 20:
            factors['battery_factor'] = 0.3  # Severely reduce high-energy tasks
        elif info['battery_percent'] < 30:
            factors['battery_factor'] = 0.5  # Reduce high-energy tasks
        elif info['battery_percent'] < 50:
            factors['battery_factor'] = 0.7  # Slightly reduce high-energy tasks
    
    # CPU factor (reduces priority when CPU is overloaded)
    if info['load_category'] == 'high':
        factors['cpu_factor'] = 0.4  # Reduce all tasks when CPU overloaded
    elif info['load_category'] == 'medium':
        factors['cpu_factor'] = 0.7  # Slightly reduce high-energy tasks
    
    # Thermal factor (reduces priority when system is hot)
    if info.get('temperature'):
        if info['temperature'] > 80:  # Very hot
            factors['thermal_factor'] = 0.3
        elif info['temperature'] > 70:  # Hot
            factors['thermal_factor'] = 0.6
        elif info['temperature'] > 60:  # Warm
            factors['thermal_factor'] = 0.8
    
    # Power factor (boosts priority when on AC)
    if info['on_ac']:
        factors['power_factor'] = 1.2  # Boost priority when plugged in
    
    return factors

def main():
    info = {}
    
    # Get battery information
    try:
        batt = psutil.sensors_battery()
        if batt is not None:
            info['battery_percent'] = round(batt.percent, 1)
            info['on_ac'] = batt.power_plugged
        else:
            info['battery_percent'] = 100.0
            info['on_ac'] = True
    except Exception as e:
        info['battery_percent'] = 100.0
        info['on_ac'] = True

    # Get CPU load information
    cpu_info = get_cpu_load_factors()
    info.update(cpu_info)
    
    # Get temperature
    temp = get_temperature()
    if temp:
        info['temperature'] = round(temp, 1)
    
    # Calculate adaptation factors
    adaptation_factors = calculate_adaptation_factors(info)
    info['adaptation_factors'] = adaptation_factors
    
    # Calculate overall system stress level
    overall_factor = (
        adaptation_factors['battery_factor'] * 
        adaptation_factors['cpu_factor'] * 
        adaptation_factors['thermal_factor'] * 
        adaptation_factors['power_factor']
    )
    
    if overall_factor > 0.8:
        info['system_stress'] = 'low'
    elif overall_factor > 0.5:
        info['system_stress'] = 'medium'
    else:
        info['system_stress'] = 'high'
    
    info['overall_factor'] = round(overall_factor, 2)

    # Write monitor.txt for scheduler (simple key:value format)
    with open("monitor.txt", "w") as f:
        f.write(f"battery_percent:{info['battery_percent']}\\n")
        f.write(f"on_ac:{info['on_ac']}\\n")
        f.write(f"cpu_percent:{info['cpu_percent']}\\n")
        f.write(f"load_category:{info['load_category']}\\n")
        f.write(f"load_factor:{info['load_factor']}\\n")
        if 'temperature' in info:
            f.write(f"temperature:{info['temperature']}\\n")
        f.write(f"system_stress:{info['system_stress']}\\n")
        f.write(f"overall_factor:{info['overall_factor']}\\n")

    print("Wrote monitor.txt:", info)

if __name__ == "__main__":
    main()
