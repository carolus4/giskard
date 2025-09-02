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

        // Modal controls
        const modalBtn = document.getElementById('add-task-modal-btn');
        const modal = document.getElementById('add-task-modal');
        const modalClose = document.getElementById('modal-close-btn');
        const modalCancel = document.getElementById('modal-cancel-btn');
        const modalAdd = document.getElementById('modal-add-btn');
        const modalInput = document.getElementById('modal-task-name');
        
        // Open modal
        modalBtn.addEventListener('click', () => this.openAddTaskModal());
        
        // Close modal
        modalClose.addEventListener('click', () => this.closeAddTaskModal());
        modalCancel.addEventListener('click', () => this.closeAddTaskModal());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeAddTaskModal();
        });
        
        // Add task from modal
        modalAdd.addEventListener('click', () => this.addTaskFromModal());
        modalInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addTaskFromModal();
        });
        
        // Enable/disable add button based on input
        modalInput.addEventListener('input', (e) => {
            modalAdd.disabled = !e.target.value.trim();
        });
        
        // ESC to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeAddTaskModal();
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
        // Update counts and show/hide based on value
        this.updateCountElement('inbox-count', this.counts.inbox);
        this.updateCountElement('today-count', this.counts.today);
        this.updateCountElement('upcoming-count', this.counts.upcoming);
        // Don't show completed count at all
        document.getElementById('completed-count').style.display = 'none';
        
        // Update task count in header
        const count = this.getTaskCountForView(this.currentView);
        const taskCountEl = document.getElementById('task-count');
        taskCountEl.textContent = `${count} task${count !== 1 ? 's' : ''}`;
    }

    updateCountElement(elementId, value) {
        const element = document.getElementById(elementId);
        element.textContent = value;
        
        // Show count only if value > 0
        if (value > 0) {
            element.classList.add('show');
        } else {
            element.classList.remove('show');
        }
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

    openAddTaskModal() {
        const modal = document.getElementById('add-task-modal');
        const input = document.getElementById('modal-task-name');
        const addBtn = document.getElementById('modal-add-btn');
        
        modal.classList.add('show');
        setTimeout(() => input.focus(), 300); // Focus after animation
        addBtn.disabled = true; // Start disabled
    }

    closeAddTaskModal() {
        const modal = document.getElementById('add-task-modal');
        const input = document.getElementById('modal-task-name');
        const description = document.getElementById('modal-task-description');
        
        modal.classList.remove('show');
        input.value = '';
        description.value = '';
    }

    async addTaskFromModal() {
        const input = document.getElementById('modal-task-name');
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
                this.closeAddTaskModal();
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
