# energy_scheduler.py
# Advanced Energy-Based Task Scheduler with Gantt Chart Visualization
import json
import time
import threading
import psutil
from datetime import datetime, timedelta
from collections import defaultdict, deque
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates
    import matplotlib.patches as patches
    from matplotlib.patches import Rectangle
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Gantt chart generation will be skipped.")

class EnergyBasedScheduler:
    def __init__(self):
        self.tasks = []
        self.system_info = {}
        self.execution_log = []
        self.current_executing = {}
        self.completed_tasks = []
        self.deferred_tasks = []
        self.energy_capacity = 100  # Maximum energy units per time slot
        self.time_slots = []
        self.schedule_plan = []
        self.start_time = None
        
    def load_system_info(self):
        """Load current system information"""
        if os.path.exists("monitor.txt"):
            with open("monitor.txt", "r") as f:
                content = f.read()
                lines = content.replace('\\n', '\n').strip().split('\n')
                
                for line in lines:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        try:
                            if key == 'on_ac':
                                self.system_info[key] = value.lower() == 'true'
                            elif key in ['battery_percent', 'cpu_percent', 'load_factor', 'overall_factor']:
                                self.system_info[key] = float(value)
                            else:
                                self.system_info[key] = value
                        except:
                            self.system_info[key] = value
        
        # Set energy capacity based on system conditions
        self.adjust_energy_capacity()
    
    def adjust_energy_capacity(self):
        """Adjust energy capacity based on system conditions"""
        battery = self.system_info.get('battery_percent', 100)
        on_ac = self.system_info.get('on_ac', True)
        cpu_load = self.system_info.get('load_category', 'low')
        
        # Base capacity
        base_capacity = 100
        
        # Battery factor
        if not on_ac:
            if battery < 20:
                base_capacity *= 0.3
            elif battery < 30:
                base_capacity *= 0.5
            elif battery < 50:
                base_capacity *= 0.7
        
        # CPU load factor
        if cpu_load == 'high':
            base_capacity *= 0.6
        elif cpu_load == 'medium':
            base_capacity *= 0.8
        
        self.energy_capacity = max(20, int(base_capacity))
    
    def load_tasks_and_profiles(self):
        """Load tasks and their energy profiles"""
        self.tasks = []
        self.profiles = {}
        
        # Load tasks
        if os.path.exists("tasks.txt"):
            with open("tasks.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',')
                        if len(parts) >= 2:
                            name = parts[0]
                            duration = int(parts[1]) if parts[1].strip().isdigit() else 5
                            self.tasks.append({'name': name, 'duration': duration})
        
        # Load profiles
        if os.path.exists("profiles.json"):
            with open("profiles.json", "r") as f:
                self.profiles = json.load(f)
    
    def calculate_task_energy(self, task):
        """Calculate energy consumption for a task"""
        task_name = task['name']
        energy_level = self.profiles.get(task_name, 'medium')
        duration = task['duration']
        
        # Energy per second based on level
        energy_per_second = {'low': 5, 'medium': 15, 'high': 30}[energy_level]
        
        return {
            'total_energy': energy_per_second * duration,
            'energy_per_second': energy_per_second,
            'energy_level': energy_level,
            'duration': duration
        }
    
    def create_optimal_schedule(self):
        """Create optimal task schedule using energy-based bin packing"""
        # Calculate energy requirements for all tasks
        task_energy_data = []
        for task in self.tasks:
            energy_data = self.calculate_task_energy(task)
            task_energy_data.append({
                'task': task,
                'energy_data': energy_data,
                'priority': self.get_task_priority(task, energy_data)
            })
        
        # Sort by priority (high priority first, then by energy efficiency)
        task_energy_data.sort(key=lambda x: (-x['priority'], x['energy_data']['total_energy']))
        
        # Create time slots (each slot = 1 minute)
        time_slots = []
        current_time = datetime.now()
        
        # Group tasks into time slots based on energy capacity
        current_slot_energy = 0
        current_slot_tasks = []
        slot_start_time = current_time
        
        for item in task_energy_data:
            task = item['task']
            energy_data = item['energy_data']
            required_energy = energy_data['total_energy']
            
            # Check if task fits in current slot
            if current_slot_energy + required_energy <= self.energy_capacity:
                current_slot_tasks.append({
                    'task': task,
                    'energy_data': energy_data,
                    'start_time': slot_start_time + timedelta(seconds=current_slot_energy / energy_data['energy_per_second']),
                    'end_time': slot_start_time + timedelta(seconds=(current_slot_energy + required_energy) / energy_data['energy_per_second'])
                })
                current_slot_energy += required_energy
            else:
                # Current slot is full, start new slot
                if current_slot_tasks:
                    time_slots.append({
                        'start_time': slot_start_time,
                        'end_time': slot_start_time + timedelta(minutes=1),
                        'tasks': current_slot_tasks,
                        'total_energy': current_slot_energy
                    })
                
                # Start new slot
                current_slot_tasks = [{
                    'task': task,
                    'energy_data': energy_data,
                    'start_time': slot_start_time + timedelta(minutes=len(time_slots)),
                    'end_time': slot_start_time + timedelta(minutes=len(time_slots)) + timedelta(seconds=energy_data['duration'])
                }]
                current_slot_energy = required_energy
                slot_start_time = slot_start_time + timedelta(minutes=len(time_slots))
        
        # Add final slot
        if current_slot_tasks:
            time_slots.append({
                'start_time': slot_start_time,
                'end_time': slot_start_time + timedelta(minutes=1),
                'tasks': current_slot_tasks,
                'total_energy': current_slot_energy
            })
        
        self.time_slots = time_slots
        return time_slots
    
    def get_task_priority(self, task, energy_data):
        """Calculate task priority based on energy efficiency and system conditions"""
        base_priority = {'low': 3, 'medium': 2, 'high': 1}[energy_data['energy_level']]
        
        # Efficiency factor (lower energy per second = higher priority)
        efficiency_factor = max(1, 30 - energy_data['energy_per_second']) / 30
        
        # Duration factor (shorter tasks get slight priority boost)
        duration_factor = max(0.5, 10 - energy_data['duration']) / 10
        
        # System condition factor
        system_factor = 1.0
        battery = self.system_info.get('battery_percent', 100)
        on_ac = self.system_info.get('on_ac', True)
        
        if not on_ac and battery < 30:
            # Prioritize low-energy tasks when battery is low
            if energy_data['energy_level'] == 'low':
                system_factor = 1.5
            elif energy_data['energy_level'] == 'high':
                system_factor = 0.3
        
        return base_priority * efficiency_factor * duration_factor * system_factor
    
    def generate_schedule_text(self):
        """Generate text-based schedule visualization"""
        if not self.time_slots:
            return None
        
        schedule_text = []
        schedule_text.append("=" * 80)
        schedule_text.append("ENERGY-BASED TASK SCHEDULE")
        schedule_text.append("=" * 80)
        
        for slot_idx, slot in enumerate(self.time_slots):
            schedule_text.append(f"\nTime Slot {slot_idx + 1}: {slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}")
            schedule_text.append(f"Energy Usage: {slot['total_energy']}/{self.energy_capacity} units")
            
            for task_item in slot['tasks']:
                task = task_item['task']
                energy_data = task_item['energy_data']
                start_time = task_item['start_time']
                end_time = task_item['end_time']
                
                duration_min = (end_time - start_time).total_seconds() / 60
                schedule_text.append(f"  └─ {task['name']} ({energy_data['energy_level']}) - {duration_min:.1f}min")
        
        schedule_text.append("\n" + "=" * 80)
        
        # Save to file
        with open('schedule_text.txt', 'w') as f:
            f.write('\n'.join(schedule_text))
        
        print('\n'.join(schedule_text))
        return 'schedule_text.txt'

    def generate_gantt_chart(self, force_regenerate=False):
        """Generate Gantt chart visualization of the schedule"""
        if not self.time_slots:
            return None
        
        # Check if chart already exists and is recent (within 1 hour)
        chart_file = 'task_schedule_gantt.png'
        if not force_regenerate and os.path.exists(chart_file):
            import time
            file_age = time.time() - os.path.getmtime(chart_file)
            if file_age < 3600:  # Less than 1 hour old
                print(f"Using existing Gantt chart (created {file_age/60:.1f} minutes ago)")
                return chart_file
        
        if not MATPLOTLIB_AVAILABLE:
            print("Skipping Gantt chart generation - matplotlib not available")
            return self.generate_schedule_text()
        
        # Prepare data for Gantt chart
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Color mapping for energy levels
        energy_colors = {'low': '#4ade80', 'medium': '#f59e0b', 'high': '#ef4444'}
        
        # Track y positions for tasks
        y_pos = 0
        task_y_positions = {}
        
        # Plot each time slot
        for slot_idx, slot in enumerate(self.time_slots):
            slot_start = slot['start_time']
            slot_end = slot['end_time']
            
            # Plot tasks in this slot
            for task_item in slot['tasks']:
                task = task_item['task']
                energy_data = task_item['energy_data']
                start_time = task_item['start_time']
                end_time = task_item['end_time']
                
                # Get or assign y position for this task
                if task['name'] not in task_y_positions:
                    task_y_positions[task['name']] = y_pos
                    y_pos += 1
                
                y_pos_task = task_y_positions[task['name']]
                
                # Calculate duration in minutes for display
                duration_minutes = (end_time - start_time).total_seconds() / 60
                
                # Convert datetime to matplotlib date format
                start_date = matplotlib.dates.date2num(start_time)
                
                # Create rectangle for task
                rect = Rectangle(
                    (start_date, y_pos_task - 0.4),
                    duration_minutes,
                    0.8,
                    facecolor=energy_colors[energy_data['energy_level']],
                    edgecolor='black',
                    alpha=0.7
                )
                ax.add_patch(rect)
                
                # Add task label
                label_x = matplotlib.dates.date2num(start_time + timedelta(minutes=duration_minutes/2))
                ax.text(
                    label_x,
                    y_pos_task,
                    f"{task['name']}\n({energy_data['energy_level']})",
                    ha='center',
                    va='center',
                    fontsize=8,
                    weight='bold'
                )
        
        # Set up axes
        min_time = min(slot['start_time'] for slot in self.time_slots)
        max_time = max(slot['end_time'] for slot in self.time_slots)
        
        ax.set_xlim(matplotlib.dates.date2num(min_time), matplotlib.dates.date2num(max_time))
        ax.set_ylim(-0.5, len(task_y_positions))
        
        # Format x-axis for time
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Set y-axis labels
        ax.set_yticks(list(task_y_positions.values()))
        ax.set_yticklabels(list(task_y_positions.keys()))
        
        # Add labels and title
        ax.set_xlabel('Time', fontsize=12, weight='bold')
        ax.set_ylabel('Tasks', fontsize=12, weight='bold')
        ax.set_title('EcoScheduler - Energy-Based Task Schedule', fontsize=16, weight='bold')
        
        # Add legend
        legend_elements = [
            patches.Patch(color='#4ade80', label='Low Energy'),
            patches.Patch(color='#f59e0b', label='Medium Energy'),
            patches.Patch(color='#ef4444', label='High Energy')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Add energy capacity info
        ax.text(0.02, 0.98, f'Energy Capacity: {self.energy_capacity} units/min\nBattery: {self.system_info.get("battery_percent", 100)}%\nAC Power: {"Yes" if self.system_info.get("on_ac", True) else "No"}',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Generated new Gantt chart: {chart_file}")
        return chart_file
    
    def execute_schedule(self):
        """Execute the scheduled tasks"""
        self.start_time = datetime.now()
        
        # Track execution status
        execution_stats = {
            'completed': 0,
            'deferred': 0,
            'executing': 0,
            'total': len(self.tasks)
        }
        
        print("Starting Energy-Based Task Execution")
        print("=" * 60)
        
        for slot_idx, slot in enumerate(self.time_slots):
            print(f"\nTime Slot {slot_idx + 1}: {slot['start_time'].strftime('%H:%M')} - {slot['end_time'].strftime('%H:%M')}")
            print(f"   Energy Usage: {slot['total_energy']}/{self.energy_capacity} units")
            
            for task_item in slot['tasks']:
                task = task_item['task']
                energy_data = task_item['energy_data']
                
                # Check if task should be deferred based on current system conditions
                should_defer, defer_reason = self.should_defer_task(task, energy_data)
                
                if should_defer:
                    print(f"DEFERRED: {task['name']} - {defer_reason}")
                    self.deferred_tasks.append({
                        'task': task,
                        'energy_data': energy_data,
                        'defer_reason': defer_reason,
                        'defer_time': datetime.now()
                    })
                    execution_stats['deferred'] += 1
                else:
                    # Execute task
                    print(f"EXECUTING: {task['name']} ({energy_data['energy_level']}, {energy_data['total_energy']} units)")
                    
                    execution_start = datetime.now()
                    self.current_executing[task['name']] = {
                        'task': task,
                        'energy_data': energy_data,
                        'start_time': execution_start
                    }
                    execution_stats['executing'] += 1
                    
                    # Simulate task execution (replace with actual task execution)
                    time.sleep(min(energy_data['duration'], 2))  # Cap at 2 seconds for demo
                    
                    execution_end = datetime.now()
                    execution_time = (execution_end - execution_start).total_seconds()
                    
                    # Mark as completed
                    self.completed_tasks.append({
                        'task': task,
                        'energy_data': energy_data,
                        'start_time': execution_start,
                        'end_time': execution_end,
                        'actual_duration': execution_time
                    })
                    
                    # Remove from executing
                    del self.current_executing[task['name']]
                    execution_stats['executing'] -= 1
                    execution_stats['completed'] += 1
                    
                    print(f"COMPLETED: {task['name']} (took {execution_time:.1f}s)")
        
        return execution_stats
    
    def should_defer_task(self, task, energy_data):
        """Determine if a task should be deferred"""
        battery = self.system_info.get('battery_percent', 100)
        on_ac = self.system_info.get('on_ac', True)
        cpu_load = self.system_info.get('load_category', 'low')
        
        # Battery-based deferral
        if not on_ac and battery < 30 and energy_data['energy_level'] == 'high':
            return True, f"Battery low ({battery}%)"
        
        # CPU-based deferral
        if cpu_load == 'high' and energy_data['energy_level'] in ['high', 'medium']:
            return True, f"CPU overloaded ({cpu_load})"
        
        return False, None
    
    def generate_execution_report(self):
        """Generate detailed execution report"""
        total_energy_used = sum(item['energy_data']['total_energy'] for item in self.completed_tasks)
        total_energy_planned = sum(self.calculate_task_energy(task)['total_energy'] for task in self.tasks)
        
        report = {
            'execution_summary': {
                'total_tasks': len(self.tasks),
                'completed': len(self.completed_tasks),
                'deferred': len(self.deferred_tasks),
                'currently_executing': len(self.current_executing),
                'completion_rate': len(self.completed_tasks) / len(self.tasks) * 100 if self.tasks else 0
            },
            'energy_summary': {
                'total_energy_used': total_energy_used,
                'total_energy_planned': total_energy_planned,
                'energy_efficiency': total_energy_used / total_energy_planned * 100 if total_energy_planned else 0,
                'energy_capacity': self.energy_capacity
            },
            'system_conditions': self.system_info,
            'completed_tasks': self.completed_tasks,
            'deferred_tasks': self.deferred_tasks,
            'currently_executing': list(self.current_executing.values())
        }
        
        return report

def main():
    """Main execution function"""
    scheduler = EnergyBasedScheduler()
    
    # Load system info and tasks
    scheduler.load_system_info()
    scheduler.load_tasks_and_profiles()
    
    print(f"System Conditions:")
    print(f"   Battery: {scheduler.system_info.get('battery_percent', 100)}%")
    print(f"   AC Power: {'Yes' if scheduler.system_info.get('on_ac', True) else 'No'}")
    print(f"   Energy Capacity: {scheduler.energy_capacity} units/min")
    print(f"   Tasks to Schedule: {len(scheduler.tasks)}")
    print()
    
    # Create optimal schedule
    print("Creating optimal energy-based schedule...")
    time_slots = scheduler.create_optimal_schedule()
    print(f"   Created {len(time_slots)} time slots")
    
    # Generate Gantt chart
    print("Generating Gantt chart...")
    chart_file = scheduler.generate_gantt_chart()
    if chart_file:
        print(f"   Chart saved as: {chart_file}")
    
    # Execute schedule
    execution_stats = scheduler.execute_schedule()
    
    # Generate report
    report = scheduler.generate_execution_report()
    
    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total Tasks: {execution_stats['total']}")
    print(f"Completed: {execution_stats['completed']}")
    print(f"Deferred: {execution_stats['deferred']}")
    print(f"Currently Executing: {execution_stats['executing']}")
    print(f"Completion Rate: {report['execution_summary']['completion_rate']:.1f}%")
    print(f"Energy Used: {report['energy_summary']['total_energy_used']}/{report['energy_summary']['total_energy_planned']} units")
    print(f"Energy Efficiency: {report['energy_summary']['energy_efficiency']:.1f}%")
    
    # Save report
    with open('execution_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report saved as: execution_report.json")
    if chart_file:
        print(f"Chart saved as: {chart_file}")
    
    return report

if __name__ == "__main__":
    import os
    main()
