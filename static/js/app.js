// Mini Todo App - JavaScript
class TodoApp {
    constructor() {
        this.currentView = 'today';
        this.tasks = {
            in_progress: [],
            open: [],
            done: []
        };
        this.counts = {
            inbox: 0,
            today: 0,
            upcoming: 0,
            completed: 0
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTasks();
        
        // Auto-refresh every 30 seconds
        setInterval(() => this.loadTasks(), 30000);
    }

    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.switchView(view);
            });
        });

        // Add task
        const addBtn = document.getElementById('add-task-btn');
        const input = document.getElementById('new-task-input');
        
        addBtn.addEventListener('click', () => this.addTask());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addTask();
        });
        
        // Show/hide add button based on input
        input.addEventListener('input', (e) => {
            const container = e.target.closest('.add-task-input');
            if (e.target.value.trim()) {
                container.classList.add('has-text');
            } else {
                container.classList.remove('has-text');
            }
        });
    }

    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            const data = await response.json();
            
            this.tasks = data.tasks;
            this.counts = data.counts;
            
            this.updateCounts();
            this.updateTodayDate(data.today_date);
            this.renderCurrentView();
            
        } catch (error) {
            console.error('Failed to load tasks:', error);
            this.showError('Failed to load tasks');
        }
    }

    updateCounts() {
        document.getElementById('inbox-count').textContent = this.counts.inbox;
        document.getElementById('today-count').textContent = this.counts.today;
        document.getElementById('upcoming-count').textContent = this.counts.upcoming;
        document.getElementById('completed-count').textContent = this.counts.completed;
        
        // Update task count in header
        const count = this.getTaskCountForView(this.currentView);
        const taskCountEl = document.getElementById('task-count');
        taskCountEl.textContent = `${count} task${count !== 1 ? 's' : ''}`;
    }

    updateTodayDate(dateStr) {
        document.getElementById('today-date').textContent = dateStr;
    }

    getTaskCountForView(view) {
        switch (view) {
            case 'inbox':
                return this.counts.inbox;
            case 'today':
                return this.counts.today;
            case 'upcoming':
                return this.counts.upcoming;
            case 'completed':
                return this.counts.completed;
            default:
                return 0;
        }
    }

    switchView(view) {
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`).classList.add('active');
        
        // Update view title
        const titles = {
            inbox: 'Inbox',
            today: 'Today',
            upcoming: 'Upcoming',
            completed: 'Completed'
        };
        document.getElementById('view-title').textContent = titles[view];
        
        // Hide all views
        document.querySelectorAll('.view-container').forEach(container => {
            container.style.display = 'none';
        });
        
        // Show current view
        document.getElementById(`${view}-view`).style.display = 'block';
        
        this.currentView = view;
        this.updateCounts();
        this.renderCurrentView();
    }

    renderCurrentView() {
        switch (this.currentView) {
            case 'inbox':
                this.renderInboxView();
                break;
            case 'today':
                this.renderTodayView();
                break;
            case 'upcoming':
                this.renderUpcomingView();
                break;
            case 'completed':
                this.renderCompletedView();
                break;
        }
    }

    renderInboxView() {
        const container = document.getElementById('inbox-tasks');
        container.innerHTML = '';
        
        // Show only active tasks (in progress + open)
        const allActiveTasks = [...this.tasks.in_progress, ...this.tasks.open];
        
        allActiveTasks.forEach(task => {
            const taskEl = this.createTaskElement(task);
            container.appendChild(taskEl);
        });
    }

    renderTodayView() {
        const todayContainer = document.getElementById('today-tasks');
        todayContainer.innerHTML = '';
        
        // Show in progress and open tasks
        const todayTasks = [...this.tasks.in_progress, ...this.tasks.open];
        
        todayTasks.forEach(task => {
            const taskEl = this.createTaskElement(task);
            todayContainer.appendChild(taskEl);
        });
        
        // Hide overdue section for now (no due dates)
        document.getElementById('overdue-section').style.display = 'none';
    }

    renderUpcomingView() {
        // Empty for now - no due dates
    }

    renderCompletedView() {
        const container = document.getElementById('completed-tasks');
        container.innerHTML = '';
        
        this.tasks.done.forEach(task => {
            const taskEl = this.createTaskElement(task);
            container.appendChild(taskEl);
        });
    }

    createTaskElement(task) {
        const template = document.getElementById('task-template');
        const taskEl = template.content.cloneNode(true);
        
        const taskItem = taskEl.querySelector('.task-item');
        const checkbox = taskEl.querySelector('.task-check');
        const title = taskEl.querySelector('.task-title');
        const startBtn = taskEl.querySelector('.start-btn');
        const stopBtn = taskEl.querySelector('.stop-btn');
        
        // Set task data
        taskItem.dataset.taskId = task.id || '';
        taskItem.dataset.status = task.status;
        title.textContent = task.title;
        
        // Add status classes
        if (task.status === 'in_progress') {
            taskItem.classList.add('in-progress');
        } else if (task.status === 'done') {
            taskItem.classList.add('completed');
            checkbox.checked = true;
        }
        
        // Show/hide action buttons based on status
        if (task.status === 'done') {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'none';
        } else if (task.status === 'in_progress') {
            startBtn.style.display = 'none';
        } else {
            stopBtn.style.display = 'none';
        }
        
        // Bind events
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked && task.status !== 'done') {
                this.markTaskDone(task.id);
            }
        });
        
        startBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.startTask(task.id);
        });
        
        stopBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.stopTask(task.id);
        });
        
        return taskEl;
    }

    async addTask() {
        const input = document.getElementById('new-task-input');
        const title = input.value.trim();
        
        if (!title) return;
        
        try {
            const response = await fetch('/api/tasks/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                input.value = '';
                input.closest('.add-task-input').classList.remove('has-text');
                this.loadTasks(); // Refresh
                this.showSuccess('Task added!');
            } else {
                this.showError(result.error || 'Failed to add task');
            }
            
        } catch (error) {
            console.error('Failed to add task:', error);
            this.showError('Failed to add task');
        }
    }

    async markTaskDone(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/done`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.loadTasks(); // Refresh
                this.showSuccess('Task completed!');
            } else {
                const result = await response.json();
                this.showError(result.error || 'Failed to complete task');
            }
            
        } catch (error) {
            console.error('Failed to complete task:', error);
            this.showError('Failed to complete task');
        }
    }

    async startTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/start`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.loadTasks(); // Refresh
                this.showSuccess('Task started!');
            } else {
                const result = await response.json();
                this.showError(result.error || 'Failed to start task');
            }
            
        } catch (error) {
            console.error('Failed to start task:', error);
            this.showError('Failed to start task');
        }
    }

    async stopTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.loadTasks(); // Refresh
                this.showSuccess('Task stopped!');
            } else {
                const result = await response.json();
                this.showError(result.error || 'Failed to stop task');
            }
            
        } catch (error) {
            console.error('Failed to stop task:', error);
            this.showError('Failed to stop task');
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: type === 'error' ? '#dc4c3e' : '#4caf50',
            color: '#fff',
            fontWeight: '500',
            fontSize: '14px',
            zIndex: '1000',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TodoApp();
});
