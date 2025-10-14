// EcoScheduler Dashboard JavaScript
class EcoSchedulerDashboard {
    constructor() {
        this.updateInterval = 5000; // 5 seconds
        this.init();
    }

    init() {
        this.loadInitialData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Refresh buttons
        document.getElementById('refresh-tasks')?.addEventListener('click', () => this.loadTasks());
        document.getElementById('refresh-logs')?.addEventListener('click', () => this.loadLogs());
        document.getElementById('refresh-schedule')?.addEventListener('click', () => this.loadScheduleStatus());
        
        // Process detection button
        document.getElementById('detect-processes')?.addEventListener('click', () => this.detectProcesses());
        
        // Energy scheduler button
        document.getElementById('run-energy-scheduler')?.addEventListener('click', () => this.runEnergyScheduler());
        
        // Gantt chart button
        document.getElementById('view-gantt')?.addEventListener('click', () => this.toggleGanttChart());
        
        // Log filter
        document.getElementById('log-filter')?.addEventListener('change', (e) => {
            this.filterLogs(e.target.value);
        });
    }

    async loadInitialData() {
        this.showLoading();
        try {
            await Promise.all([
                this.loadSystemStatus(),
                this.loadTasks(),
                this.loadLogs(),
                this.loadScheduleStatus()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading();
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/system-status');
            const data = await response.json();
            
            this.updateBatteryDisplay(data);
            this.updateCPUDisplay(data);
            this.updateTaskStats(data);
            this.updateActivityStats(data);
            this.updateHeader(data);
            
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }

    updateBatteryDisplay(data) {
        const batteryPercent = data.battery_percent || 0;
        const onAC = data.on_ac;
        
        // Update battery level
        const batteryFill = document.getElementById('battery-fill');
        const batteryPercentEl = document.getElementById('battery-percent');
        const batteryStatus = document.getElementById('battery-status');
        
        if (batteryFill) {
            batteryFill.style.width = `${batteryPercent}%`;
            
            // Change color based on battery level
            if (batteryPercent < 20) {
                batteryFill.style.background = '#ef4444';
            } else if (batteryPercent < 50) {
                batteryFill.style.background = '#f59e0b';
            } else {
                batteryFill.style.background = '#4ade80';
            }
        }
        
        if (batteryPercentEl) {
            batteryPercentEl.textContent = `${Math.round(batteryPercent)}%`;
        }
        
        if (batteryStatus) {
            batteryStatus.textContent = onAC ? 'Plugged In' : 'On Battery';
            batteryStatus.className = onAC ? 'battery-status' : 'battery-status low-battery';
        }
    }

    updateCPUDisplay(data) {
        const cpuPercent = data.cpu_percent || 0;
        const cpuGauge = document.getElementById('cpu-gauge');
        const cpuPercentEl = document.getElementById('cpu-percent');
        
        if (cpuGauge) {
            const degrees = (cpuPercent / 100) * 360;
            cpuGauge.style.background = `conic-gradient(#4ade80 0deg, #4ade80 ${degrees}deg, #e5e7eb ${degrees}deg)`;
        }
        
        if (cpuPercentEl) {
            cpuPercentEl.textContent = `${Math.round(cpuPercent)}%`;
        }
    }

    updateTaskStats(data) {
        const taskCount = data.total_tasks || 0;
        const energyBreakdown = data.energy_breakdown || { high: 0, medium: 0, low: 0 };
        
        const taskCountEl = document.getElementById('task-count');
        if (taskCountEl) {
            taskCountEl.textContent = taskCount;
        }
        
        // Update task breakdown with correct counts
        this.updateTaskBreakdown(energyBreakdown.high, energyBreakdown.medium, energyBreakdown.low);
    }

    updateTaskBreakdown(high, medium, low) {
        const breakdown = document.getElementById('task-breakdown');
        if (breakdown) {
            breakdown.innerHTML = `
                <div class="task-type">
                    <span class="task-dot high"></span>
                    <span>High Energy (${high})</span>
                </div>
                <div class="task-type">
                    <span class="task-dot medium"></span>
                    <span>Medium Energy (${medium})</span>
                </div>
                <div class="task-type">
                    <span class="task-dot low"></span>
                    <span>Low Energy (${low})</span>
                </div>
            `;
        }
    }

    updateActivityStats(data) {
        const recentLogs = data.recent_logs_count || 0;
        const totalTasks = data.total_tasks || 0;
        
        const recentLogsEl = document.getElementById('recent-logs');
        const totalTasksEl = document.getElementById('total-tasks');
        
        if (recentLogsEl) {
            recentLogsEl.textContent = recentLogs;
        }
        
        if (totalTasksEl) {
            totalTasksEl.textContent = totalTasks;
        }
    }

    updateHeader(data) {
        const systemStatus = document.getElementById('system-status');
        const lastUpdate = document.getElementById('last-update');
        
        if (systemStatus) {
            const batteryPercent = data.battery_percent || 0;
            const onAC = data.on_ac;
            
            if (batteryPercent < 20 && !onAC) {
                systemStatus.textContent = 'Low Battery';
                systemStatus.className = 'stat-value low-battery';
            } else {
                systemStatus.textContent = 'Normal';
                systemStatus.className = 'stat-value';
            }
        }
        
        if (lastUpdate) {
            lastUpdate.textContent = new Date().toLocaleTimeString();
        }
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            const taskGrid = document.getElementById('task-grid');
            
            if (taskGrid) {
                taskGrid.innerHTML = tasks.map(task => `
                    <div class="task-item">
                        <div class="task-name">${this.escapeHtml(task.name)}</div>
                        <div class="task-duration">Duration: ${task.duration}s</div>
                        <div class="task-energy ${this.getEnergyLevel(task.duration)}">
                            <i class="fas fa-bolt"></i>
                            ${this.getEnergyLevel(task.duration).toUpperCase()}
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    }

    getEnergyLevel(duration) {
        if (duration <= 2) return 'low';
        if (duration <= 6) return 'medium';
        return 'high';
    }

    async loadLogs() {
        try {
            const response = await fetch('/api/logs?limit=50');
            const logs = await response.json();
            this.displayLogs(logs);
        } catch (error) {
            console.error('Error loading logs:', error);
        }
    }

    displayLogs(logs) {
        const logsTable = document.getElementById('logs-table');
        
        if (logsTable) {
            if (logs.length === 0) {
                logsTable.innerHTML = `
                    <div style="padding: 2rem; text-align: center; color: #6b7280;">
                        <i class="fas fa-info-circle"></i>
                        <p>No logs available</p>
                    </div>
                `;
                return;
            }
            
            logsTable.innerHTML = logs.map(log => `
                <div class="log-entry">
                    <div class="log-timestamp">${this.formatTimestamp(log.timestamp)}</div>
                    <div class="log-task">${this.escapeHtml(log.task_name || 'System')}</div>
                    <div class="log-energy ${this.getLogEnergyLevel(log)}">
                        ${this.getLogEnergyLevel(log).toUpperCase()}
                    </div>
                    <div class="log-battery">
                        <i class="fas fa-battery-${this.getBatteryIcon(log.battery_percent)}"></i>
                        ${Math.round(log.battery_percent || 0)}%
                    </div>
                </div>
            `).join('');
        }
    }

    getLogEnergyLevel(log) {
        if (log.energy_level) {
            return log.energy_level;
        }
        
        // Fallback to duration-based classification
        const duration = log.duration || 5;
        return this.getEnergyLevel(duration);
    }

    getBatteryIcon(batteryPercent) {
        if (batteryPercent >= 75) return 'three-quarters';
        if (batteryPercent >= 50) return 'half';
        if (batteryPercent >= 25) return 'quarter';
        return 'empty';
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }

    filterLogs(filter) {
        const logEntries = document.querySelectorAll('.log-entry');
        
        logEntries.forEach(entry => {
            if (filter === 'all') {
                entry.style.display = 'grid';
            } else {
                const energyElement = entry.querySelector('.log-energy');
                const energyLevel = energyElement ? energyElement.textContent.toLowerCase().trim() : '';
                
                if (energyLevel === filter) {
                    entry.style.display = 'grid';
                } else {
                    entry.style.display = 'none';
                }
            }
        });
    }

    startAutoRefresh() {
        setInterval(() => {
            this.loadSystemStatus();
            this.loadLogs();
        }, this.updateInterval);
    }

    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('show');
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    }

    showError(message) {
        // Create a simple error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;
        
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    async detectProcesses() {
        const button = document.getElementById('detect-processes');
        const originalText = button.innerHTML;
        
        try {
            // Show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
            button.disabled = true;
            
            const response = await fetch('/api/detect-processes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Successfully detected ${result.tasks_count} processes!`, 'success');
                
                // Reload tasks and system status
                await this.loadTasks();
                await this.loadSystemStatus();
            } else {
                this.showNotification(`Error: ${result.message}`, 'error');
            }
            
        } catch (error) {
            console.error('Error detecting processes:', error);
            this.showNotification('Failed to detect processes', 'error');
        } finally {
            // Reset button
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        
        const colors = {
            success: '#4ade80',
            error: '#ef4444',
            info: '#3b82f6'
        };
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    async runEnergyScheduler() {
        const button = document.getElementById('run-energy-scheduler');
        const originalText = button.innerHTML;
        
        try {
            // Show loading state
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scheduling...';
            button.disabled = true;
            
            const response = await fetch('/api/run-energy-scheduler', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Task scheduling completed successfully!', 'success');
                
                // Reload schedule status and tasks
                await this.loadScheduleStatus();
                await this.loadTasks();
                
                // Show execution report if available
                if (result.execution_report) {
                    this.displayExecutionReport(result.execution_report);
                }
            } else {
                this.showNotification(`Scheduling failed: ${result.message}`, 'error');
            }
            
        } catch (error) {
            console.error('Error running energy scheduler:', error);
            this.showNotification('Failed to run energy scheduler', 'error');
        } finally {
            // Reset button
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    async loadScheduleStatus() {
        try {
            const response = await fetch('/api/schedule-status');
            const data = await response.json();
            
            const scheduleSummary = document.getElementById('schedule-summary');
            if (scheduleSummary) {
                if (data.has_schedule && data.execution_report) {
                    this.displayExecutionReport(data.execution_report);
                    
                    // Show/hide Gantt chart button based on availability
                    const viewGanttBtn = document.getElementById('view-gantt');
                    if (viewGanttBtn) {
                        viewGanttBtn.style.display = data.gantt_chart_available ? 'inline-flex' : 'none';
                    }
                } else {
                    scheduleSummary.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: #6b7280;">
                            <i class="fas fa-chart-gantt" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                            <p>No schedule available. Click "Schedule Tasks" to create an optimal task schedule.</p>
                        </div>
                    `;
                    
                    // Hide Gantt chart button if no schedule
                    const viewGanttBtn = document.getElementById('view-gantt');
                    if (viewGanttBtn) {
                        viewGanttBtn.style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error loading schedule status:', error);
        }
    }

    displayExecutionReport(report) {
        const scheduleSummary = document.getElementById('schedule-summary');
        if (!scheduleSummary) return;
        
        const execSummary = report.execution_summary;
        const energySummary = report.energy_summary;
        
        scheduleSummary.innerHTML = `
            <div class="schedule-stats">
                <div class="schedule-stat">
                    <span class="schedule-stat-value">${execSummary.total_tasks}</span>
                    <span class="schedule-stat-label">Total Tasks</span>
                </div>
                <div class="schedule-stat">
                    <span class="schedule-stat-value" style="color: #4ade80;">${execSummary.completed}</span>
                    <span class="schedule-stat-label">Completed</span>
                </div>
                <div class="schedule-stat">
                    <span class="schedule-stat-value" style="color: #f59e0b;">${execSummary.deferred}</span>
                    <span class="schedule-stat-label">Deferred</span>
                </div>
                <div class="schedule-stat">
                    <span class="schedule-stat-value" style="color: #3b82f6;">${execSummary.currently_executing}</span>
                    <span class="schedule-stat-label">Executing</span>
                </div>
                <div class="schedule-stat">
                    <span class="schedule-stat-value" style="color: #8b5cf6;">${execSummary.completion_rate.toFixed(1)}%</span>
                    <span class="schedule-stat-label">Completion Rate</span>
                </div>
                <div class="schedule-stat">
                    <span class="schedule-stat-value" style="color: #ef4444;">${energySummary.energy_efficiency.toFixed(1)}%</span>
                    <span class="schedule-stat-label">Energy Efficiency</span>
                </div>
            </div>
            
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.3); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">Energy Usage Summary</h4>
                <p style="margin: 0; color: #6b7280;">
                    Used: ${energySummary.total_energy_used}/${energySummary.total_energy_planned} energy units 
                    (Capacity: ${energySummary.energy_capacity} units/min)
                </p>
            </div>
        `;
    }

    toggleGanttChart() {
        const ganttContainer = document.getElementById('gantt-container');
        const viewButton = document.getElementById('view-gantt');
        
        if (ganttContainer.style.display === 'none') {
            // Show Gantt chart
            ganttContainer.style.display = 'block';
            viewButton.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Gantt Chart';
            
            // Load the chart image with cache busting
            const ganttImg = document.getElementById('gantt-chart');
            ganttImg.src = '/api/gantt-chart?' + new Date().getTime();
            
            // Show loading state
            ganttImg.style.display = 'none';
            const loadingDiv = document.createElement('div');
            loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading chart...';
            loadingDiv.style.cssText = 'text-align: center; padding: 2rem; color: #6b7280;';
            ganttContainer.appendChild(loadingDiv);
            
            // Show image when loaded
            ganttImg.onload = () => {
                loadingDiv.remove();
                ganttImg.style.display = 'block';
            };
            
            ganttImg.onerror = () => {
                loadingDiv.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Chart not available';
                loadingDiv.style.color = '#ef4444';
            };
        } else {
            // Hide Gantt chart
            ganttContainer.style.display = 'none';
            viewButton.innerHTML = '<i class="fas fa-image"></i> View Gantt Chart';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EcoSchedulerDashboard();
});

// Add some utility functions for better UX
window.addEventListener('beforeunload', () => {
    // Clean up any ongoing operations if needed
});

// Handle visibility change to pause/resume updates
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause updates here
    } else {
        // Page is visible, resume updates
    }
});
