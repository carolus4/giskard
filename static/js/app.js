// Mini Todo App - JavaScript
class TodoApp {
    constructor() {
        this.currentView = 'today';
        this.currentTaskData = null;
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
        this.lastTasksHash = '';
        this.isUserAction = false;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTasks(true); // Initial load with animation
        this.updateKeyboardShortcutDisplay();
        
        // Smart auto-refresh every 30 seconds - only if data changed
        setInterval(() => this.smartRefresh(), 30000);
    }

    updateKeyboardShortcutDisplay() {
        // Show appropriate shortcut for user's platform
        const shortcutSpan = document.querySelector('.keyboard-shortcut');
        if (shortcutSpan) {
            const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
            shortcutSpan.textContent = isMac ? '⌘↵' : 'Ctrl+↵';
        }
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
        
        // ESC to close modal, Cmd+Enter to save
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAddTaskModal();
                this.closeTaskDetail();
            }
            
            // Cmd+Enter or Ctrl+Enter to save task (only when detail modal is open)
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                const detailModal = document.getElementById('task-detail-modal');
                if (detailModal && detailModal.classList.contains('show')) {
                    e.preventDefault(); // Prevent any default behavior
                    
                    // Brief visual feedback on the save button
                    const saveBtn = document.getElementById('save-task-btn');
                    if (saveBtn) {
                        saveBtn.style.transform = 'scale(0.95)';
                        setTimeout(() => {
                            saveBtn.style.transform = '';
                        }, 150);
                    }
                    
                    this.saveTask(); // This will now close the popup automatically
                }
            }
        });

        // Task detail modal controls
        const detailClose = document.getElementById('detail-close-btn');
        const detailModal = document.getElementById('task-detail-modal');
        const saveTaskBtn = document.getElementById('save-task-btn');
        const progressBtn = document.getElementById('detail-progress-btn');
        const detailCheckbox = document.getElementById('detail-checkbox');
        
        detailClose.addEventListener('click', () => this.closeTaskDetail());
        detailModal.addEventListener('click', (e) => {
            if (e.target === detailModal) this.closeTaskDetail();
        });
        
        saveTaskBtn.addEventListener('click', () => this.saveTask());
        progressBtn.addEventListener('click', () => this.toggleTaskProgress());
        
        // Handle checkbox in detail modal
        detailCheckbox.addEventListener('change', (e) => {
            if (!this.currentTaskData) return;
            
            if (this.currentTaskData.status === 'done') {
                // Uncomplete the task
                e.target.checked = true; // Keep checked while processing
                this.uncompleteTask(this.currentTaskData.file_idx);
            } else if (e.target.checked) {
                // Complete the task
                this.markTaskDone(this.currentTaskData.id);
            }
            
            // Close detail modal after changing status
            setTimeout(() => {
                this.closeTaskDetail();
            }, 500);
        });
    }

    async loadTasks(allowAnimation = false) {
        try {
            const response = await fetch('/api/tasks');
            const data = await response.json();
            
            // Create hash of current data to detect changes
            const newHash = JSON.stringify(data);
            const dataChanged = newHash !== this.lastTasksHash;
            
            if (dataChanged || allowAnimation) {
                this.tasks = data.tasks;
                this.counts = data.counts;
                this.lastTasksHash = newHash;
                
                this.updateCounts();
                this.updateTodayDate(data.today_date);
                this.renderCurrentView(allowAnimation);
            }
            
        } catch (error) {
            console.error('Failed to load tasks:', error);
            this.showError('Failed to load tasks');
        }
    }

    async smartRefresh() {
        // Silent background refresh - no animations
        await this.loadTasks(false);
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

    renderCurrentView(allowAnimation = false) {
        switch (this.currentView) {
            case 'inbox':
                this.renderInboxView(allowAnimation);
                break;
            case 'today':
                this.renderTodayView(allowAnimation);
                break;
            case 'upcoming':
                this.renderUpcomingView(allowAnimation);
                break;
            case 'completed':
                this.renderCompletedView(allowAnimation);
                break;
        }
    }

    renderInboxView(allowAnimation = false) {
        const container = document.getElementById('inbox-tasks');
        container.innerHTML = '';
        
        // Show only active tasks (in progress + open)
        const allActiveTasks = [...this.tasks.in_progress, ...this.tasks.open];
        
        allActiveTasks.forEach(task => {
            const taskEl = this.createTaskElement(task, allowAnimation);
            container.appendChild(taskEl);
        });
    }

    renderTodayView(allowAnimation = false) {
        const todayContainer = document.getElementById('today-tasks');
        todayContainer.innerHTML = '';
        
        // Show in progress and open tasks
        const todayTasks = [...this.tasks.in_progress, ...this.tasks.open];
        
        todayTasks.forEach(task => {
            const taskEl = this.createTaskElement(task, allowAnimation);
            todayContainer.appendChild(taskEl);
        });
        
        // Hide overdue section for now (no due dates)
        document.getElementById('overdue-section').style.display = 'none';
    }

    renderUpcomingView(allowAnimation = false) {
        // Empty for now - no due dates
    }

    renderCompletedView(allowAnimation = false) {
        const container = document.getElementById('completed-tasks');
        container.innerHTML = '';
        
        this.tasks.done.forEach(task => {
            const taskEl = this.createTaskElement(task, allowAnimation);
            container.appendChild(taskEl);
        });
    }

    createTaskElement(task, allowAnimation = false) {
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
        
        // Description removed from task list - available in detail view only
        
        // Add status classes
        if (task.status === 'in_progress') {
            taskItem.classList.add('in-progress');
        } else if (task.status === 'done') {
            taskItem.classList.add('completed');
            checkbox.checked = true;
        }

        // Add animation class only when explicitly requested (new tasks)
        if (allowAnimation) {
            taskItem.classList.add('new-task');
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
            if (task.status === 'done') {
                // Uncomplete completed task
                e.target.checked = true; // Keep it visually checked while processing
                this.uncompleteTask(task.file_idx);
            } else if (e.target.checked) {
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

        // Make task clickable to open detail view
        taskItem.addEventListener('click', (e) => {
            // Don't open detail if clicking on checkbox or action buttons
            if (e.target.closest('.task-checkbox') || e.target.closest('.task-actions')) {
                return;
            }
            this.openTaskDetail(task.file_idx);
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
        const description = document.getElementById('modal-task-description');
        const title = input.value.trim();
        const desc = description.value.trim();
        
        if (!title) return;
        
        try {
            const response = await fetch('/api/tasks/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    title: title,
                    description: desc 
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.closeAddTaskModal();
                this.loadTasks(true); // Refresh with animation for new task
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
                this.loadTasks(); // Refresh without animation
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
                this.loadTasks(); // Refresh without animation
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
                this.loadTasks(); // Refresh without animation
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

    async uncompleteTask(fileIdx) {
        try {
            const response = await fetch('/api/tasks/uncomplete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ file_idx: fileIdx })
            });
            
            if (response.ok) {
                this.loadTasks(); // Refresh without animation
                this.showSuccess('Task uncompleted!');
            } else {
                const result = await response.json();
                this.showError(result.error || 'Failed to uncomplete task');
            }
            
        } catch (error) {
            console.error('Failed to uncomplete task:', error);
            this.showError('Failed to uncomplete task');
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    async openTaskDetail(fileIdx) {
        try {
            const response = await fetch(`/api/tasks/${fileIdx}/details`);
            const task = await response.json();
            
            if (response.ok) {
                this.showTaskDetail(task);
            } else {
                this.showError(task.error || 'Failed to load task details');
            }
            
        } catch (error) {
            console.error('Failed to load task details:', error);
            this.showError('Failed to load task details');
        }
    }

    showTaskDetail(task) {
        const modal = document.getElementById('task-detail-modal');
        const checkbox = document.getElementById('detail-checkbox');
        const titleRow = document.querySelector('.task-title-row');
        const progressBtn = document.getElementById('detail-progress-btn');
        
        // Populate task details
        document.getElementById('detail-title').value = task.title;
        document.getElementById('detail-description').value = task.description || '';
        
        // Set checkbox state
        checkbox.checked = task.status === 'done';
        if (task.status === 'done') {
            titleRow.classList.add('completed');
        } else {
            titleRow.classList.remove('completed');
        }
        
        // Set progress button state
        if (task.status === 'in_progress') {
            progressBtn.classList.add('in-progress');
            progressBtn.innerHTML = '<i class="fas fa-pause"></i><span>pause</span>';
        } else {
            progressBtn.classList.remove('in-progress');
            progressBtn.innerHTML = '<i class="fas fa-play"></i><span>start</span>';
        }
        
        // Show modal
        modal.classList.add('show');
        modal.dataset.fileIdx = task.file_idx;
        this.currentTaskData = task;
        
        // Update keyboard shortcut display when modal opens
        this.updateKeyboardShortcutDisplay();
    }

    closeTaskDetail() {
        const modal = document.getElementById('task-detail-modal');
        modal.classList.remove('show');
        this.currentTaskData = null;
    }

    async saveTask() {
        if (!this.currentTaskData) return;
        
        const title = document.getElementById('detail-title').value.trim();
        const description = document.getElementById('detail-description').value.trim();
        const fileIdx = this.currentTaskData.file_idx;
        
        if (!title) {
            this.showError('Task title cannot be empty');
            return;
        }
        
        try {
            const response = await fetch(`/api/tasks/${fileIdx}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: title,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Task saved!');
                this.loadTasks(); // Refresh the task list
                // Update current task data
                this.currentTaskData.title = title;
                this.currentTaskData.description = description;
                // Close the popup
                this.closeTaskDetail();
            } else {
                this.showError(data.error || 'Failed to save task');
            }
            
        } catch (error) {
            console.error('Failed to save task:', error);
            this.showError('Failed to save task');
        }
    }

    async toggleTaskProgress() {
        if (!this.currentTaskData) return;
        
        const task = this.currentTaskData;
        
        if (task.status === 'in_progress') {
            // Stop the task
            this.stopTask(task.id);
        } else {
            // Start the task
            this.startTask(task.id);
        }
        
        // Close the detail modal after changing status
        setTimeout(() => {
            this.closeTaskDetail();
        }, 500);
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
