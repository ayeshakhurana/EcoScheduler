# process_detector.py
import psutil
import json
import time
from collections import defaultdict
import joblib
import numpy as np

class SystemProcessDetector:
    def __init__(self):
        self.process_history = defaultdict(list)
        self.energy_classifier = None
        self.load_ml_model()
        
    def load_ml_model(self):
        """Load the trained ML model for energy classification"""
        try:
            if os.path.exists("rf_joblib.pkl"):
                self.energy_classifier = joblib.load("rf_joblib.pkl")
                print("Loaded ML model for energy classification")
            else:
                print("No ML model found, using rule-based classification")
        except Exception as e:
            print(f"Error loading ML model: {e}")
    
    def get_system_processes(self):
        """Get currently running processes with their resource usage"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 'create_time']):
            try:
                proc_info = proc.info
                
                # Get additional process details
                proc_obj = psutil.Process(proc_info['pid'])
                
                # Get CPU and memory usage over a short interval
                cpu_percent = proc.cpu_percent(interval=0.1)
                memory_mb = proc.memory_info().rss / 1024 / 1024
                
                process_data = {
                    'name': proc_info['name'],
                    'pid': proc_info['pid'],
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'memory_percent': proc_info['memory_percent'],
                    'num_threads': proc_info['num_threads'],
                    'uptime_seconds': time.time() - proc_info['create_time'],
                    'executable_path': proc_obj.exe() if hasattr(proc_obj, 'exe') else '',
                    'cmdline': ' '.join(proc_obj.cmdline()) if hasattr(proc_obj, 'cmdline') else ''
                }
                
                processes.append(process_data)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return processes
    
    def classify_process_energy(self, process_data):
        """Classify process energy usage based on resource consumption"""
        
        # Rule-based classification (fallback)
        cpu_percent = process_data['cpu_percent']
        memory_mb = process_data['memory_mb']
        num_threads = process_data['num_threads']
        
        # Calculate energy score
        energy_score = 0
        
        # CPU usage weight (40%)
        if cpu_percent > 10:
            energy_score += 4
        elif cpu_percent > 5:
            energy_score += 3
        elif cpu_percent > 1:
            energy_score += 2
        else:
            energy_score += 1
            
        # Memory usage weight (30%)
        if memory_mb > 1000:  # > 1GB
            energy_score += 3
        elif memory_mb > 500:  # > 500MB
            energy_score += 2
        elif memory_mb > 100:  # > 100MB
            energy_score += 1
            
        # Thread count weight (20%)
        if num_threads > 20:
            energy_score += 3
        elif num_threads > 10:
            energy_score += 2
        elif num_threads > 5:
            energy_score += 1
            
        # Process name patterns (10%)
        high_energy_patterns = [
            'chrome', 'firefox', 'edge', 'code', 'devenv', 'gcc', 'clang', 
            'python', 'node', 'java', 'dotnet', 'docker', 'vmware', 'virtualbox',
            'photoshop', 'premiere', 'blender', 'maya', 'unity', 'unreal'
        ]
        
        medium_energy_patterns = [
            'explorer', 'winlogon', 'svchost', 'dwm', 'csrss', 'lsass',
            'steam', 'discord', 'slack', 'teams', 'zoom', 'skype'
        ]
        
        process_name = process_data['name'].lower()
        
        if any(pattern in process_name for pattern in high_energy_patterns):
            energy_score += 3
        elif any(pattern in process_name for pattern in medium_energy_patterns):
            energy_score += 2
            
        # ML-based classification (if model available)
        if self.energy_classifier:
            try:
                # Use memory_mb as feature (similar to duration in original model)
                ml_prediction = self.energy_classifier.predict([[memory_mb]])[0]
                ml_energy_score = {0: 1, 1: 2, 2: 3}[ml_prediction]
                energy_score = (energy_score + ml_energy_score) / 2
            except:
                pass  # Fallback to rule-based
                
        # Convert score to energy level
        if energy_score >= 8:
            return 'high'
        elif energy_score >= 5:
            return 'medium'
        else:
            return 'low'
    
    def detect_active_processes(self, min_cpu_threshold=0.1, min_memory_threshold=10):
        """Detect processes that are actively consuming resources"""
        processes = self.get_system_processes()
        active_processes = []
        
        for proc in processes:
            # Filter out system processes and low-usage processes
            if (proc['cpu_percent'] >= min_cpu_threshold or 
                proc['memory_mb'] >= min_memory_threshold):
                
                # Classify energy usage
                energy_level = self.classify_process_energy(proc)
                
                process_info = {
                    'name': proc['name'],
                    'pid': proc['pid'],
                    'cpu_percent': proc['cpu_percent'],
                    'memory_mb': proc['memory_mb'],
                    'energy_level': energy_level,
                    'uptime_seconds': proc['uptime_seconds'],
                    'cmdline': proc['cmdline']
                }
                
                active_processes.append(process_info)
                
        return active_processes
    
    def generate_task_list(self, output_file="tasks.txt"):
        """Generate tasks.txt file from detected processes"""
        active_processes = self.detect_active_processes()
        
        # Group similar processes and calculate average resource usage
        process_groups = defaultdict(list)
        for proc in active_processes:
            process_groups[proc['name']].append(proc)
            
        tasks = []
        for process_name, process_list in process_groups.items():
            # Calculate average metrics
            avg_cpu = sum(p['cpu_percent'] for p in process_list) / len(process_list)
            avg_memory = sum(p['memory_mb'] for p in process_list) / len(process_list)
            energy_level = process_list[0]['energy_level']  # All should be same
            
            # Estimate duration based on resource usage (simplified)
            if energy_level == 'high':
                estimated_duration = max(30, int(avg_memory / 10))  # 30+ seconds for high energy
            elif energy_level == 'medium':
                estimated_duration = max(10, int(avg_memory / 20))  # 10+ seconds for medium
            else:
                estimated_duration = max(5, int(avg_memory / 50))   # 5+ seconds for low
                
            # Cap duration at reasonable maximum
            estimated_duration = min(estimated_duration, 300)  # Max 5 minutes
            
            task_line = f"{process_name},{estimated_duration}"
            tasks.append(task_line)
            
        # Write to tasks.txt
        with open(output_file, "w") as f:
            for task in tasks:
                f.write(task + "\n")
                
        print(f"Generated {len(tasks)} tasks in {output_file}")
        return tasks
    
    def update_profiles_json(self, output_file="profiles.json"):
        """Update profiles.json with current process classifications"""
        active_processes = self.detect_active_processes()
        
        profiles = {}
        for proc in active_processes:
            profiles[proc['name']] = proc['energy_level']
            
        with open(output_file, "w") as f:
            json.dump(profiles, f, indent=2)
            
        print(f"Updated {len(profiles)} process profiles in {output_file}")
        return profiles

def main():
    """Main function to run process detection"""
    import os
    detector = SystemProcessDetector()
    
    print("Detecting system processes...")
    active_processes = detector.detect_active_processes()
    
    print(f"\nFound {len(active_processes)} active processes:")
    for proc in active_processes[:10]:  # Show first 10
        print(f"  {proc['name']} (PID: {proc['pid']}) - {proc['energy_level']} energy")
        print(f"    CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_mb']:.1f}MB")
    
    if len(active_processes) > 10:
        print(f"  ... and {len(active_processes) - 10} more processes")
    
    print("\nGenerating task list...")
    tasks = detector.generate_task_list()
    
    print("\nUpdating profiles...")
    profiles = detector.update_profiles_json()
    
    print(f"\nTask generation complete!")
    print(f"  - {len(tasks)} tasks written to tasks.txt")
    print(f"  - {len(profiles)} profiles written to profiles.json")

if __name__ == "__main__":
    import os
    main()
