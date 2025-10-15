# enhanced_scheduler.py
# Enhanced EcoScheduler with Dynamic Priority Adaptation
import json
import time
import subprocess
import os
from datetime import datetime

class EnhancedEcoScheduler:
    def __init__(self):
        self.tasks = []
        self.system_info = {}
        self.adaptation_factors = {}
        
    def load_system_info(self):
        """Load system information from monitor.txt"""
        if not os.path.exists("monitor.txt"):
            return
            
        with open("monitor.txt", "r") as f:
            content = f.read()
            lines = content.replace('\\n', '\n').strip().split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.strip().split(':', 1)
                    try:
                        # Try to convert to appropriate type
                        if key in ['on_ac']:
                            self.system_info[key] = value.lower() == 'true'
                        elif key in ['battery_percent', 'cpu_percent', 'load_factor', 'temperature', 'overall_factor']:
                            self.system_info[key] = float(value)
                        else:
                            self.system_info[key] = value
                    except:
                        self.system_info[key] = value
    
    def load_tasks(self):
        """Load tasks from tasks.txt"""
        self.tasks = []
        if not os.path.exists("tasks.txt"):
            return
            
        with open("tasks.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        name = parts[0]
                        duration = int(parts[1]) if parts[1].strip().isdigit() else 5
                        self.tasks.append({'name': name, 'duration': duration})
    
    def load_profiles(self):
        """Load task energy profiles"""
        self.profiles = {}
        if os.path.exists("profiles.json"):
            with open("profiles.json", "r") as f:
                self.profiles = json.load(f)
    
    def calculate_dynamic_priority(self, task):
        """Calculate dynamic priority based on system conditions"""
        task_name = task['name']
        base_energy = self.profiles.get(task_name, 'medium')
        
        # Base priority scores
        base_priorities = {'low': 1, 'medium': 2, 'high': 3}
        base_priority = base_priorities.get(base_energy, 2)
        
        # Get system factors
        battery_factor = self.system_info.get('battery_factor', 1.0)
        cpu_factor = self.system_info.get('cpu_factor', 1.0)
        thermal_factor = self.system_info.get('thermal_factor', 1.0)
        power_factor = self.system_info.get('power_factor', 1.0)
        
        # Calculate adapted priority
        # Higher energy tasks are more affected by system conditions
        energy_multiplier = {'low': 1.0, 'medium': 1.2, 'high': 1.5}.get(base_energy, 1.0)
        
        adapted_priority = base_priority * (
            battery_factor * cpu_factor * thermal_factor * power_factor * energy_multiplier
        )
        
        return {
            'base_priority': base_priority,
            'adapted_priority': adapted_priority,
            'energy_level': base_energy,
            'factors': {
                'battery': battery_factor,
                'cpu': cpu_factor,
                'thermal': thermal_factor,
                'power': power_factor
            }
        }
    
    def should_defer_task(self, task, priority_info):
        """Determine if a task should be deferred based on system conditions"""
        energy_level = priority_info['energy_level']
        battery = self.system_info.get('battery_percent', 100)
        on_ac = self.system_info.get('on_ac', True)
        cpu_load = self.system_info.get('load_category', 'low')
        temperature = self.system_info.get('temperature', 0)
        system_stress = self.system_info.get('system_stress', 'low')
        
        defer_reasons = []
        
        # Battery-based deferral
        if not on_ac and battery < 20 and energy_level == 'high':
            defer_reasons.append(f"Battery critically low ({battery}%)")
        elif not on_ac and battery < 30 and energy_level == 'high':
            defer_reasons.append(f"Battery low ({battery}%)")
        
        # CPU-based deferral
        if cpu_load == 'high' and energy_level in ['high', 'medium']:
            defer_reasons.append(f"CPU overloaded ({cpu_load})")
        
        # Thermal-based deferral
        if temperature > 80 and energy_level == 'high':
            defer_reasons.append(f"System overheating ({temperature}°C)")
        elif temperature > 70 and energy_level in ['high', 'medium']:
            defer_reasons.append(f"System hot ({temperature}°C)")
        
        # System stress-based deferral
        if system_stress == 'high' and energy_level == 'high':
            defer_reasons.append(f"High system stress ({system_stress})")
        
        return len(defer_reasons) > 0, defer_reasons
    
    def execute_task(self, task):
        """Execute a task (simulated)"""
        duration = task['duration']
        print(f"🔹 Executing {task['name']} ({duration}s)")
        
        # Simulate task execution
        try:
            sleep_cap_seconds = float(os.getenv('EXEC_SLEEP_CAP_SECONDS', '2'))
        except ValueError:
            sleep_cap_seconds = 2.0
        time.sleep(min(duration, sleep_cap_seconds))
        
        return True
    
    def log_task_result(self, task, action, priority_info, defer_reasons=None):
        """Log task execution result"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'task': task['name'],
            'action': action,
            'energy_level': priority_info['energy_level'],
            'base_priority': priority_info['base_priority'],
            'adapted_priority': round(priority_info['adapted_priority'], 2),
            'battery_percent': self.system_info.get('battery_percent', 100),
            'on_ac': self.system_info.get('on_ac', True),
            'cpu_load': self.system_info.get('load_category', 'low'),
            'temperature': self.system_info.get('temperature', 0),
            'system_stress': self.system_info.get('system_stress', 'low'),
            'defer_reasons': defer_reasons or []
        }
        
        # Log to file
        with open("enhanced_log.txt", "a") as f:
            if defer_reasons:
                f.write(f"{timestamp}: {task['name']} - DEFERRED ({', '.join(defer_reasons)})\n")
            else:
                f.write(f"{timestamp}: {task['name']} - EXECUTED ({priority_info['energy_level']}, priority: {priority_info['adapted_priority']:.2f})\n")
        
        return log_entry
    
    def run_scheduler(self):
        """Run the enhanced scheduler"""
        print("🌿 Enhanced EcoScheduler v4 — Dynamic Adaptation Enabled")
        print("=" * 60)
        
        # Load system information
        self.load_system_info()
        print(f"📊 System Status:")
        print(f"   Battery: {self.system_info.get('battery_percent', 100)}% ({'AC' if self.system_info.get('on_ac', True) else 'Battery'})")
        print(f"   CPU Load: {self.system_info.get('cpu_percent', 0)}% ({self.system_info.get('load_category', 'low')})")
        print(f"   Temperature: {self.system_info.get('temperature', 'N/A')}°C")
        print(f"   System Stress: {self.system_info.get('system_stress', 'low')}")
        print(f"   Overall Factor: {self.system_info.get('overall_factor', 1.0)}")
        print()
        
        # Load tasks and profiles
        self.load_tasks()
        self.load_profiles()
        
        if not self.tasks:
            print("❌ No tasks found in tasks.txt")
            return
        
        # Calculate dynamic priorities for all tasks
        task_priorities = []
        for task in self.tasks:
            priority_info = self.calculate_dynamic_priority(task)
            task_priorities.append((task, priority_info))
        
        # Sort tasks by adapted priority (highest first)
        task_priorities.sort(key=lambda x: x[1]['adapted_priority'], reverse=True)
        
        print(f"📋 Loaded {len(self.tasks)} tasks with dynamic priorities:")
        for task, priority_info in task_priorities:
            energy = priority_info['energy_level']
            base_pri = priority_info['base_priority']
            adapted_pri = priority_info['adapted_priority']
            factors = priority_info['factors']
            
            print(f"   {task['name']}: {energy} energy (base: {base_pri}, adapted: {adapted_pri:.2f})")
            print(f"      Factors: Battery={factors['battery']:.2f}, CPU={factors['cpu']:.2f}, Thermal={factors['thermal']:.2f}, Power={factors['power']:.2f}")
        print()
        
        # Execute tasks
        executed_count = 0
        deferred_count = 0
        
        for task, priority_info in task_priorities:
            # Check if task should be deferred
            should_defer, defer_reasons = self.should_defer_task(task, priority_info)
            
            if should_defer:
                print(f"⚠️  DEFERRING {task['name']}: {', '.join(defer_reasons)}")
                self.log_task_result(task, 'deferred', priority_info, defer_reasons)
                deferred_count += 1
            else:
                # Execute task
                success = self.execute_task(task)
                if success:
                    self.log_task_result(task, 'executed', priority_info)
                    executed_count += 1
        
        print()
        print("=" * 60)
        print(f"✅ Scheduler run complete!")
        print(f"   Executed: {executed_count} tasks")
        print(f"   Deferred: {deferred_count} tasks")
        print(f"   Log written to: enhanced_log.txt")

if __name__ == "__main__":
    scheduler = EnhancedEcoScheduler()
    scheduler.run_scheduler()
