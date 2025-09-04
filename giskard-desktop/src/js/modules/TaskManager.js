import APIClient from './APIClient.js';
import UIManager from './UIManager.js';
import TaskList from './TaskList.js';
import DragDropManager from './DragDropManager.js';
import { AddTaskModal, TaskDetailModal, ConfirmationModal } from './Modal.js';
import Notification from './Notification.js';

/**
 * TaskManager - Core orchestrator for all task operations
 */
class TaskManager {
    constructor() {
        // Initialize core components
        this.api = new APIClient();
        this.ui = new UIManager();
        this.taskList = new TaskList();
        this.dragDrop = new DragDropManager();
        
        // Initialize modals
        this.addTaskModal = new AddTaskModal();
        this.taskDetailModal = new TaskDetailModal();
        this.confirmationModal = new ConfirmationModal();
        
        // Application state
        this.tasks = {
            in_progress: [],
            open: [],
            done: []
        };
        this.lastTasksHash = '';
        
        this._bindEvents();
        this._initialize();
    }

    /**
     * Initialize the application
     */
    async _initialize() {
        // Update keyboard shortcuts for user's platform
        this.ui.updateKeyboardShortcuts();
        
        // Initial load with animation
        await this.loadTasks(true);
        
        // Smart auto-refresh every 30 seconds - only if data changed
        setInterval(() => this._smartRefresh(), 30000);
    }

    /**
     * Bind all application events
     */
    _bindEvents() {
        this._bindModalEvents();
        this._bindTaskEvents();
        this._bindKeyboardEvents();
        this._bindViewEvents();
    }

    /**
     * Bind modal-related events
     */
    _bindModalEvents() {
        // Add task modal - sidebar button
        const modalBtn = document.getElementById('add-task-modal-btn');
        if (modalBtn) {
            modalBtn.addEventListener('click', () => this.addTaskModal.open());
        }

        // Add task modal - simple button in task list
        const simpleBtn = document.getElementById('add-task-simple-btn');
        if (simpleBtn) {
            simpleBtn.addEventListener('click', () => this.addTaskModal.open());
        }

        const modalAddBtn = document.getElementById('modal-add-btn');
        if (modalAddBtn) {
            modalAddBtn.addEventListener('click', () => this._handleAddTaskFromModal());
        }

        // Task detail modal events
        this.taskDetailModal.modal.addEventListener('task:save', (e) => {
            this._handleSaveTask(e.detail);
        });

        this.taskDetailModal.modal.addEventListener('task:toggle-progress', (e) => {
            this._handleToggleTaskProgress(e.detail.taskData);
        });

        this.taskDetailModal.modal.addEventListener('task:toggle-completion', (e) => {
            this._handleTaskCompletionToggle(e.detail);
        });
    }

    /**
     * Bind task-related events
     */
    _bindTaskEvents() {
        // Task interaction events
        document.addEventListener('task:detail', (e) => {
            this._handleOpenTaskDetail(e.detail.task);
        });

        document.addEventListener('task:start', (e) => {
            this._handleStartTask(e.detail.task);
        });

        document.addEventListener('task:stop', (e) => {
            this._handleStopTask(e.detail.task);
        });

        document.addEventListener('task:complete', (e) => {
            this._handleCompleteTask(e.detail.task);
        });

        document.addEventListener('task:uncomplete', (e) => {
            this._handleUncompleteTask(e.detail.task);
        });

        document.addEventListener('task:delete', (e) => {
            this._handleDeleteTask(e.detail.task);
        });

        document.addEventListener('task:reorder', (e) => {
            this._handleReorderTasks(e.detail.fileIdxSequence);
        });
    }

    /**
     * Bind keyboard events
     */
    _bindKeyboardEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.addTaskModal.close();
                this.taskDetailModal.close();
                this.taskList.clearTaskSelection();
            }
        });
    }

    /**
     * Bind view-related events
     */
    _bindViewEvents() {
        document.addEventListener('view:changed', (e) => {
            this._handleViewChanged(e.detail);
        });
    }

    /**
     * Load tasks from the server with retry logic
     */
    async loadTasks(allowAnimation = false, retryCount = 0) {
        try {
            console.log(`🔄 Loading tasks (attempt ${retryCount + 1})...`);
            const result = await this.api.getTasks();
            
            if (!result.success) {
                if (retryCount < 2) {
                    console.log(`⏳ Retrying in ${(retryCount + 1) * 2}s...`);
                    setTimeout(() => {
                        this.loadTasks(allowAnimation, retryCount + 1);
                    }, (retryCount + 1) * 2000);
                    return;
                }
                Notification.error('Failed to load tasks after 3 attempts');
                return;
            }

            const data = result.data;
            
            // Create hash of current data to detect changes
            const newHash = JSON.stringify(data);
            const dataChanged = newHash !== this.lastTasksHash;
            
            if (dataChanged || allowAnimation) {
                this.tasks = data.tasks;
                this.lastTasksHash = newHash;
                
                // Update UI
                this.ui.updateCounts(data.counts);
                this.ui.updateTodayDate(data.today_date);
                this._renderCurrentView(allowAnimation);
                
                // Reinitialize drag drop after rendering
                setTimeout(() => {
                    const taskItems = document.querySelectorAll('.task-item');
                    console.log(`🔧 Reinitializing drag-drop for ${taskItems.length} tasks`);
                    
                    try {
                        this.dragDrop.initializeDragDrop();
                        console.log('✅ Drag-drop setup complete');
                    } catch (error) {
                        console.error('❌ Drag-drop failed:', error);
                    }
                }, 100);
            }
            
        } catch (error) {
            console.error('Failed to load tasks:', error);
            Notification.error('Failed to load tasks: ' + error.message);
        }
    }

    /**
     * Silent background refresh
     */
    async _smartRefresh() {
        await this.loadTasks(false);
    }

    /**
     * Render tasks for the current view
     */
    _renderCurrentView(allowAnimation = false) {
        const currentView = this.ui.getCurrentView();
        
        switch (currentView) {
            case 'inbox':
                this._renderInboxView(allowAnimation);
                break;
            case 'today':
                this._renderTodayView(allowAnimation);
                break;
            case 'upcoming':
                this._renderUpcomingView(allowAnimation);
                break;
            case 'completed':
                this._renderCompletedView(allowAnimation);
                break;
        }
    }

    /**
     * Render inbox view (all active tasks)
     */
    _renderInboxView(allowAnimation = false) {
        const container = this.ui.getViewContainer('inbox');
        if (!container) return;

        const allActiveTasks = [...this.tasks.in_progress, ...this.tasks.open];
        this.taskList.renderTasks(allActiveTasks, container, { allowAnimation });
    }

    /**
     * Render today view
     */
    _renderTodayView(allowAnimation = false) {
        const container = this.ui.getViewContainer('today');
        if (!container) return;

        const todayTasks = [...this.tasks.in_progress, ...this.tasks.open];
        this.taskList.renderTasks(todayTasks, container, { allowAnimation });
        
        // Hide overdue section for now (no due dates implemented)
        const overdueSection = document.getElementById('overdue-section');
        if (overdueSection) {
            overdueSection.style.display = 'none';
        }
    }

    /**
     * Render upcoming view (placeholder)
     */
    _renderUpcomingView(allowAnimation = false) {
        this.ui.showEmptyState('upcoming', 'No upcoming tasks');
    }

    /**
     * Render completed view
     */
    _renderCompletedView(allowAnimation = false) {
        const container = this.ui.getViewContainer('completed');
        if (!container) return;

        this.taskList.renderTasks(this.tasks.done, container, { allowAnimation });
    }

    /**
     * Handle adding task from modal
     */
    async _handleAddTaskFromModal() {
        const taskData = this.addTaskModal.getTaskData();
        
        if (!taskData.title.trim()) {
            Notification.error('Task title is required');
            return;
        }
        
        const result = await this.api.addTask(taskData.title, taskData.description);
        
        if (result.success) {
            this.addTaskModal.close();
            await this.loadTasks(true); // Refresh with animation for new task
            Notification.success('Task added!');
        } else {
            Notification.error(result.error || 'Failed to add task');
        }
    }

    /**
     * Handle opening task details
     */
    async _handleOpenTaskDetail(task) {
        const result = await this.api.getTaskDetails(task.file_idx);
        
        if (result.success) {
            this.taskDetailModal.showTask(result.data);
        } else {
            Notification.error(result.error || 'Failed to load task details');
        }
    }

    /**
     * Handle saving task from detail modal
     */
    async _handleSaveTask(taskData) {
        if (!taskData.title.trim()) {
            Notification.error('Task title cannot be empty');
            return;
        }
        
        const result = await this.api.updateTask(
            taskData.fileIdx,
            taskData.title,
            taskData.description
        );
        
        if (result.success) {
            Notification.success('Task saved!');
            await this.loadTasks();
            this.taskDetailModal.close();
        } else {
            Notification.error(result.error || 'Failed to save task');
        }
    }

    /**
     * Handle starting a task
     */
    async _handleStartTask(task) {
        const result = await this.api.startTask(task.id);
        
        if (result.success) {
            await this.loadTasks();
            Notification.success('Task started!');
        } else {
            Notification.error(result.error || 'Failed to start task');
        }
    }

    /**
     * Handle stopping a task
     */
    async _handleStopTask(task) {
        const result = await this.api.stopTask(task.id);
        
        if (result.success) {
            await this.loadTasks();
            Notification.success('Task stopped!');
        } else {
            Notification.error(result.error || 'Failed to stop task');
        }
    }

    /**
     * Handle completing a task
     */
    async _handleCompleteTask(task) {
        const result = await this.api.markTaskDone(task.id);
        
        if (result.success) {
            await this.loadTasks();
            Notification.success('Task completed!');
        } else {
            Notification.error(result.error || 'Failed to complete task');
        }
    }

    /**
     * Handle uncompleting a task
     */
    async _handleUncompleteTask(task) {
        const result = await this.api.uncompleteTask(task.file_idx);
        
        if (result.success) {
            await this.loadTasks();
            Notification.success('Task uncompleted!');
        } else {
            Notification.error(result.error || 'Failed to uncomplete task');
        }
    }

    /**
     * Handle deleting a task
     */
    async _handleDeleteTask(task) {
        if (!task) {
            return;
        }
        
        // Show custom confirmation dialog
        const confirmed = await this.confirmationModal.show(
            `Are you sure you want to delete "${task.title}"?`,
            'Confirm Deletion'
        );
        
        if (!confirmed) {
            return;
        }
        
        const result = await this.api.deleteTask(task.file_idx);
        
        if (result.success) {
            // Close the task detail modal since the task no longer exists
            this.taskDetailModal.close();
            await this.loadTasks();
            Notification.success('Task deleted!');
        } else {
            Notification.error(result.error || 'Failed to delete task');
        }
    }

    /**
     * Handle task reordering
     */
    async _handleReorderTasks(fileIdxSequence) {
        console.log('🔄 REORDERING with file index sequence:', fileIdxSequence);
        
        const result = await this.api.reorderTasks(fileIdxSequence);
        
        if (result.success) {
            console.log('✅ Tasks reordered successfully');
            await this.loadTasks();
        } else {
            console.error('❌ Reorder failed:', result.error);
            Notification.error(result.error || 'Failed to reorder tasks');
        }
    }

    /**
     * Handle task progress toggle from detail modal
     */
    async _handleToggleTaskProgress(taskData) {
        if (!taskData) return;
        
        if (taskData.status === 'in_progress') {
            await this._handleStopTask(taskData);
        } else {
            await this._handleStartTask(taskData);
        }
        
        // Close the detail modal after changing status
        setTimeout(() => {
            this.taskDetailModal.close();
        }, 500);
    }

    /**
     * Handle task completion toggle from detail modal
     */
    async _handleTaskCompletionToggle({ checked, taskData }) {
        if (!taskData) return;
        
        if (taskData.status === 'done') {
            // Uncomplete the task
            await this._handleUncompleteTask(taskData);
        } else if (checked) {
            // Complete the task
            await this._handleCompleteTask(taskData);
        }
        
        // Close detail modal after changing status
        setTimeout(() => {
            this.taskDetailModal.close();
        }, 500);
    }

    /**
     * Handle view changes
     */
    _handleViewChanged({ view }) {
        this._renderCurrentView();
    }
}

export default TaskManager;
