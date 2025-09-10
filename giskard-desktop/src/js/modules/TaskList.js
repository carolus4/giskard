/**
 * TaskList - Handles task rendering and basic task interactions
 */
class TaskList {
    constructor() {
        this.template = document.getElementById('task-template');
        if (!this.template) {
            console.warn('Task template not found');
        }
    }

    /**
     * Render tasks in a container
     */
    renderTasks(tasks, container, options = {}) {
        if (!container) {
            console.error('Container not provided for rendering tasks');
            return;
        }

        // Clear container
        container.innerHTML = '';

        // Render each task
        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task, options);
            if (taskElement) {
                container.appendChild(taskElement);
            }
        });
    }

    /**
     * Create a single task element
     */
    createTaskElement(task, options = {}) {
        if (!this.template) {
            console.error('Task template not available');
            return null;
        }

        const taskEl = this.template.content.cloneNode(true);
        
        const taskItem = taskEl.querySelector('.task-item');
        const checkbox = taskEl.querySelector('.task-check');
        const title = taskEl.querySelector('.task-title');
        const startBtn = taskEl.querySelector('.start-btn');
        const stopBtn = taskEl.querySelector('.stop-btn');
        
        if (!taskItem) {
            console.error('Invalid task template structure');
            return null;
        }

        // Set task data attributes
        taskItem.dataset.taskId = task.id || '';
        taskItem.dataset.fileIdx = task.file_idx !== undefined ? task.file_idx : '';
        taskItem.dataset.status = task.status || 'open';
        taskItem.dataset.order = task.order !== undefined ? task.order : (task.file_idx !== undefined ? task.file_idx : 0);
        
        // Set task content
        if (title) {
            title.textContent = task.title || 'Untitled Task';
        }
        
        // Add status classes
        if (task.status === 'in_progress') {
            taskItem.classList.add('in-progress');
        } else if (task.status === 'done') {
            taskItem.classList.add('completed');
            if (checkbox) checkbox.checked = true;
        }

        // Add animation class if requested
        if (options.allowAnimation) {
            taskItem.classList.add('new-task');
        }
        
        // Configure action buttons based on status
        this._configureActionButtons(task, startBtn, stopBtn);
        
        // Bind task events
        this._bindTaskEvents(taskItem, task, { checkbox, startBtn, stopBtn });
        
        return taskEl;
    }

    /**
     * Configure visibility of action buttons based on task status
     */
    _configureActionButtons(task, startBtn, stopBtn) {
        if (!startBtn || !stopBtn) return;

        if (task.status === 'done') {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'none';
        } else if (task.status === 'in_progress') {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
        } else {
            startBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
        }
    }

    /**
     * Bind events to task elements
     */
    _bindTaskEvents(taskItem, task, elements) {
        const { checkbox, startBtn, stopBtn } = elements;

        // Checkbox change event
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this._handleCheckboxChange(e, task);
            });
        }

        // Start button
        if (startBtn) {
            startBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._emitTaskEvent('task:start', task);
            });
        }

        // Stop button
        if (stopBtn) {
            stopBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._emitTaskEvent('task:stop', task);
            });
        }

        // Task click to open details
        taskItem.addEventListener('click', (e) => {
            // Don't open detail if clicking on interactive elements
            if (this._isInteractiveElement(e.target)) {
                return;
            }
            
            // Don't open detail if task is selected for drag
            if (taskItem.classList.contains('selected-for-move')) {
                return;
            }
            
            this._emitTaskEvent('task:detail', task);
        });
    }

    /**
     * Handle checkbox change events
     */
    _handleCheckboxChange(event, task) {
        if (task.status === 'done') {
            // Uncomplete completed task
            event.target.checked = true; // Keep visually checked while processing
            this._emitTaskEvent('task:uncomplete', task);
        } else if (event.target.checked) {
            // Complete open/in-progress task
            this._emitTaskEvent('task:complete', task);
        }
    }

    /**
     * Check if clicked element is interactive (should not trigger task detail)
     */
    _isInteractiveElement(target) {
        const interactiveSelectors = [
            '.task-checkbox',
            '.task-check',
            '.task-actions',
            '.task-action',
            '.start-btn',
            '.stop-btn',
            '.task-drag-handle'
        ];

        return interactiveSelectors.some(selector => 
            target.closest(selector) !== null
        );
    }

    /**
     * Emit task-related events
     */
    _emitTaskEvent(eventName, task, additionalData = {}) {
        const event = new CustomEvent(eventName, {
            detail: { task, ...additionalData },
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    /**
     * Update a specific task element
     */
    updateTaskElement(fileIdx, updatedTask) {
        const taskItem = document.querySelector(`[data-file-idx="${fileIdx}"]`);
        if (!taskItem) return;

        const title = taskItem.querySelector('.task-title');
        const checkbox = taskItem.querySelector('.task-check');
        const startBtn = taskItem.querySelector('.start-btn');
        const stopBtn = taskItem.querySelector('.stop-btn');

        // Update title
        if (title && updatedTask.title) {
            title.textContent = updatedTask.title;
        }

        // Update status
        if (updatedTask.status) {
            taskItem.dataset.status = updatedTask.status;
            
            // Remove existing status classes
            taskItem.classList.remove('in-progress', 'completed');
            
            // Add new status class
            if (updatedTask.status === 'in_progress') {
                taskItem.classList.add('in-progress');
            } else if (updatedTask.status === 'done') {
                taskItem.classList.add('completed');
                if (checkbox) checkbox.checked = true;
            } else {
                if (checkbox) checkbox.checked = false;
            }

            // Update action buttons
            this._configureActionButtons(updatedTask, startBtn, stopBtn);
        }
    }

    /**
     * Remove a task element
     */
    removeTaskElement(fileIdx) {
        const taskItem = document.querySelector(`[data-file-idx="${fileIdx}"]`);
        if (taskItem) {
            taskItem.remove();
        }
    }

    /**
     * Get all visible task elements
     */
    getAllTaskElements() {
        return Array.from(document.querySelectorAll('.task-item'));
    }

    /**
     * Get task element by file index
     */
    getTaskElement(fileIdx) {
        return document.querySelector(`[data-file-idx="${fileIdx}"]`);
    }

    /**
     * Add highlight animation to a task
     */
    highlightTask(fileIdx, duration = 2000) {
        const taskElement = this.getTaskElement(fileIdx);
        if (!taskElement) return;

        taskElement.classList.add('highlighted');
        
        setTimeout(() => {
            taskElement.classList.remove('highlighted');
        }, duration);
    }

    /**
     * Clear task selection states
     */
    clearTaskSelection() {
        document.querySelectorAll('.task-item.selected-for-move').forEach(item => {
            item.classList.remove('selected-for-move');
        });
    }

    /**
     * Get task data from DOM element
     */
    getTaskDataFromElement(element) {
        return {
            id: element.dataset.taskId,
            file_idx: element.dataset.fileIdx ? parseInt(element.dataset.fileIdx) : null,
            status: element.dataset.status,
            order: element.dataset.order ? parseInt(element.dataset.order) : null,
            title: element.querySelector('.task-title')?.textContent || ''
        };
    }
}

export default TaskList;
