# api.py
from flask import Flask, jsonify, render_template, request
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)

def fetch(q, args=()):
    conn = sqlite3.connect("ecoscheduler.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# Main dashboard route
@app.route("/")
def dashboard():
    return render_template('dashboard.html')

# API Routes
@app.route("/api/logs")
def logs():
    limit = request.args.get('limit', 200, type=int)
    return jsonify(fetch("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)))

@app.route("/api/system-status")
def system_status():
    status = {}
    
    # Read monitor.txt for current system status
    if os.path.exists("monitor.txt"):
        with open("monitor.txt", "r") as f:
            content = f.read()
            # Handle escaped newlines in the file
            lines = content.replace('\\n', '\n').strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.strip().split(':', 1)
                    if key == 'battery_percent':
                        try:
                            status['battery_percent'] = float(value)
                        except ValueError:
                            status['battery_percent'] = 100.0
                    elif key == 'on_ac':
                        status['on_ac'] = value.lower() == 'true'
                    elif key == 'cpu_percent':
                        try:
                            status['cpu_percent'] = float(value)
                        except ValueError:
                            status['cpu_percent'] = 0.0
    
    # Fallback: Get real-time system data if monitor.txt is outdated or incorrect
    import psutil
    import time
    
    # Get actual CPU usage (more accurate than monitor.txt)
    status['cpu_percent'] = psutil.cpu_percent(interval=0.1)
    
    # Get actual battery info
    try:
        battery = psutil.sensors_battery()
        if battery:
            status['battery_percent'] = battery.percent
            status['on_ac'] = battery.power_plugged
        else:
            # Default values if no battery info
            status['battery_percent'] = status.get('battery_percent', 100.0)
            status['on_ac'] = status.get('on_ac', True)
    except:
        # Keep monitor.txt values if psutil fails
        pass
    
    # Add enhanced monitoring data
    status['load_category'] = status.get('load_category', 'low')
    status['load_factor'] = status.get('load_factor', 0.0)
    status['temperature'] = status.get('temperature', 0)
    status['system_stress'] = status.get('system_stress', 'low')
    status['overall_factor'] = status.get('overall_factor', 1.0)
    
    # Add adaptation factors
    adaptation_factors = {}
    for key in ['battery_factor', 'cpu_factor', 'thermal_factor', 'power_factor']:
        if key in status:
            adaptation_factors[key] = status[key]
    status['adaptation_factors'] = adaptation_factors
    
    # Read profiles.json for task energy levels
    if os.path.exists("profiles.json"):
        with open("profiles.json", "r") as f:
            status['task_profiles'] = json.load(f)
    
    # Get recent logs count
    try:
        recent_logs = fetch("SELECT COUNT(*) as count FROM logs WHERE datetime(timestamp) > datetime('now', '-1 hour')")
        status['recent_logs_count'] = recent_logs[0]['count'] if recent_logs else 0
    except:
        status['recent_logs_count'] = 0
    
    # Count active tasks from profiles
    task_profiles = status.get('task_profiles', {})
    status['total_tasks'] = len(task_profiles)
    
    # Count by energy level
    high_count = sum(1 for level in task_profiles.values() if level == 'high')
    medium_count = sum(1 for level in task_profiles.values() if level == 'medium')
    low_count = sum(1 for level in task_profiles.values() if level == 'low')
    
    status['energy_breakdown'] = {
        'high': high_count,
        'medium': medium_count,
        'low': low_count
    }
    
    return jsonify(status)

@app.route("/api/tasks")
def get_tasks():
    if os.path.exists("tasks.txt"):
        tasks = []
        with open("tasks.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    tasks.append({
                        'name': parts[0],
                        'duration': int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 5
                    })
        return jsonify(tasks)
    return jsonify([])

@app.route("/api/task-stats")
def task_stats():
    # Get task statistics from logs
    stats = fetch("""
        SELECT task_name, 
               COUNT(*) as count,
               AVG(CASE WHEN energy_level = 'high' THEN 1 ELSE 0 END) as high_energy_ratio,
               AVG(CASE WHEN battery_percent < 30 THEN 1 ELSE 0 END) as low_battery_ratio
        FROM logs 
        WHERE task_name IS NOT NULL 
        GROUP BY task_name
        ORDER BY count DESC
    """)
    return jsonify(stats)

@app.route("/api/detect-processes", methods=['POST'])
def detect_processes():
    """Detect system processes and update tasks.txt and profiles.json"""
    try:
        from process_detector import SystemProcessDetector
        
        detector = SystemProcessDetector()
        
        # Generate new task list and profiles
        tasks = detector.generate_task_list()
        profiles = detector.update_profiles_json()
        
        return jsonify({
            'success': True,
            'message': f'Detected {len(tasks)} processes and updated task profiles',
            'tasks_count': len(tasks),
            'profiles_count': len(profiles)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error detecting processes: {str(e)}'
        }), 500

@app.route("/api/active-processes")
def get_active_processes():
    """Get currently active processes from the system"""
    try:
        from process_detector import SystemProcessDetector
        
        detector = SystemProcessDetector()
        active_processes = detector.detect_active_processes()
        
        return jsonify({
            'success': True,
            'processes': active_processes,
            'count': len(active_processes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting active processes: {str(e)}'
        }), 500

@app.route("/api/run-enhanced-scheduler", methods=['POST'])
def run_enhanced_scheduler():
    """Run the enhanced scheduler with dynamic adaptation"""
    try:
        import subprocess
        import os
        
        # Run the enhanced scheduler
        result = subprocess.run(['python', 'enhanced_scheduler.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Enhanced scheduler completed successfully',
                'output': result.stdout,
                'error': result.stderr
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Enhanced scheduler failed',
                'output': result.stdout,
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error running enhanced scheduler: {str(e)}'
        }), 500

@app.route("/api/run-energy-scheduler", methods=['POST'])
def run_energy_scheduler():
    """Run the energy-based scheduler with Gantt chart generation"""
    try:
        import subprocess
        import os
        import json
        
        # Run the energy scheduler
        result = subprocess.run(['python', 'energy_scheduler.py'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        # Load execution report if available
        execution_report = None
        if os.path.exists('execution_report.json'):
            with open('execution_report.json', 'r') as f:
                execution_report = json.load(f)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Energy scheduler completed successfully',
                'output': result.stdout,
                'error': result.stderr,
                'execution_report': execution_report,
                'gantt_chart': 'task_schedule_gantt.png' if os.path.exists('task_schedule_gantt.png') else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Energy scheduler failed',
                'output': result.stdout,
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error running energy scheduler: {str(e)}'
        }), 500

@app.route("/api/schedule-status")
def get_schedule_status():
    """Get current schedule and execution status"""
    try:
        # Check if execution report exists
        if os.path.exists('execution_report.json'):
            with open('execution_report.json', 'r') as f:
                report = json.load(f)
            
            return jsonify({
                'success': True,
                'has_schedule': True,
                'execution_report': report,
                'gantt_chart_available': os.path.exists('task_schedule_gantt.png')
            })
        else:
            return jsonify({
                'success': True,
                'has_schedule': False,
                'message': 'No schedule available. Run the energy scheduler first.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting schedule status: {str(e)}'
        }), 500

@app.route("/api/gantt-chart")
def get_gantt_chart():
    """Serve the Gantt chart image"""
    try:
        from flask import send_file
        if os.path.exists('task_schedule_gantt.png'):
            return send_file('task_schedule_gantt.png', mimetype='image/png')
        else:
            return jsonify({'error': 'Gantt chart not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
