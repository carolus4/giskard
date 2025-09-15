import APIClient from './APIClient.js';
import UIManager from './UIManager.js';
import TaskList from './TaskList.js';
import DragDropManager from './DragDropManager.js';
import PageManager from './PageManager.js';
import { ConfirmationModal } from './Modal.js';
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
        this.pageManager = new PageManager();
        
        // Initialize modals (only confirmation modal needed now)
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
        this._bindPageEvents();
        this._bindTaskEvents();
        this._bindKeyboardEvents();
        this._bindViewEvents();
    }

    /**
     * Bind page-related events
     */
    _bindPageEvents() {
        // Add task from page
        document.addEventListener('task:add-from-page', (e) => {
            this._handleAddTaskFromPage(e.detail);
        });

        // Save task from page
        document.addEventListener('task:save-from-page', (e) => {
            this._handleSaveTaskFromPage(e.detail);
        });

        // Delete task from page
        document.addEventListener('task:delete-from-page', (e) => {
            this._handleDeleteTaskFromPage(e.detail);
        });

        // Toggle progress from page
        document.addEventListener('task:toggle-progress-from-page', (e) => {
            this._handleToggleProgressFromPage(e.detail);
        });

        // Toggle completion from page
        document.addEventListener('task:toggle-completion-from-page', (e) => {
            this._handleToggleCompletionFromPage(e.detail);
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
                // Navigate back to task list from any page
                const currentPage = this.ui.getCurrentPage();
                if (currentPage === 'task-detail') {
                    this.pageManager.showPage('task-list');
                }
                this.taskList.clearTaskSelection();
            }
        });
    }

    /**
     * Bind view-related events
     */
    _bindViewEvents() {
        document.addEventListener('page:changed', (e) => {
            this._handlePageChanged(e.detail);
        });
    }

    /**
     * Load tasks from the server with retry logic
     */
    async loadTasks(allowAnimation = false, retryCount = 0) {
        try {
            const result = await this.api.getTasks();
            
            if (!result.success) {
                if (retryCount < 2) {
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
                this._renderCurrentView(allowAnimation);
                
                // Update today date after rendering to ensure it's not overridden
                this.ui.updateTodayDate(data.today_date);
                
                // Reinitialize drag drop after rendering
                setTimeout(() => {
                    const taskItems = document.querySelectorAll('.task-item');
                    
                    try {
                        this.dragDrop.initializeDragDrop();
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
        const currentPage = this.ui.getCurrentPage();
        
        switch (currentPage) {
            case 'task-list':
                this._renderTaskListView(allowAnimation);
                break;
            case 'chat':
                // Chat view doesn't need task rendering
                break;
        }
    }


    /**
     * Render task list view
     */
    _renderTaskListView(allowAnimation = false) {
        const container = document.getElementById('task-list-container');
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
     * Handle adding task from page
     */
    async _handleAddTaskFromPage(taskData) {
        if (!taskData.title.trim()) {
            Notification.error('Task title is required');
            return;
        }
        
        const result = await this.api.addTask(taskData.title, taskData.description);
        
        if (result.success) {
            this.pageManager.showPage('task-list');
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
            this.pageManager.showTaskDetail(task.file_idx);
            this.pageManager.loadTaskIntoDetailPage(result.data);
        } else {
            Notification.error(result.error || 'Failed to load task details');
        }
    }

    /**
     * Handle saving task from detail page
     */
    async _handleSaveTaskFromPage(taskData) {
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
            this.pageManager.showPage('task-list');
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
            return true;
        } else {
            Notification.error(result.error || 'Failed to complete task');
            return false;
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
            return true;
        } else {
            Notification.error(result.error || 'Failed to uncomplete task');
            return false;
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
            // Navigate back to task list since the task no longer exists
            this.pageManager.showPage('task-list');
            await this.loadTasks();
            Notification.success('Task deleted!');
        } else {
            Notification.error(result.error || 'Failed to delete task');
        }
    }

    /**
     * Handle deleting task from page
     */
    async _handleDeleteTaskFromPage({ taskId }) {
        // Get task data for confirmation
        const allTasks = [...this.tasks.in_progress, ...this.tasks.open, ...this.tasks.done];
        const task = allTasks.find(t => t.file_idx === taskId);
        
        if (!task) {
            Notification.error('Task not found');
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
        
        const result = await this.api.deleteTask(taskId);
        
        if (result.success) {
            // Navigate back to task list since the task no longer exists
            this.pageManager.showPage('task-list');
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
        const result = await this.api.reorderTasks(fileIdxSequence);
        
        if (result.success) {
            await this.loadTasks();
        } else {
            console.error('❌ Reorder failed:', result.error);
            Notification.error(result.error || 'Failed to reorder tasks');
        }
    }

    /**
     * Handle task progress toggle from detail page
     */
    async _handleToggleProgressFromPage({ taskId }) {
        // Get task data
        const allTasks = [...this.tasks.in_progress, ...this.tasks.open, ...this.tasks.done];
        const task = allTasks.find(t => t.file_idx === taskId);
        
        if (!task) {
            Notification.error('Task not found');
            return;
        }
        
        // First, save any changes made in the page (title, description)
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        
        if (titleInput && titleInput.value.trim()) {
            const taskData = {
                fileIdx: taskId,
                title: titleInput.value.trim(),
                description: descriptionInput?.value.trim() || ''
            };
            await this._handleSaveTaskFromPage(taskData);
        }
        
        // Then toggle the progress state
        if (task.status === 'in_progress') {
            await this._handleStopTask(task);
        } else {
            await this._handleStartTask(task);
        }
        
        // Update the progress button state in the detail page after data refresh
        setTimeout(() => {
            this._updateDetailPageProgressButton(taskId);
        }, 100);
    }

    /**
     * Handle task completion toggle from detail page
     */
    async _handleToggleCompletionFromPage({ taskId, checked }) {
        // Get task data
        const allTasks = [...this.tasks.in_progress, ...this.tasks.open, ...this.tasks.done];
        const task = allTasks.find(t => t.file_idx === taskId);
        
        if (!task) {
            Notification.error('Task not found');
            return;
        }
        
        // First, save any changes made in the page (title, description)
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        
        if (titleInput && titleInput.value.trim()) {
            const taskData = {
                fileIdx: taskId,
                title: titleInput.value.trim(),
                description: descriptionInput?.value.trim() || ''
            };
            await this._handleSaveTaskFromPage(taskData);
        }
        
        // Then toggle the completion state
        let success = false;
        if (task.status === 'done') {
            // Uncomplete the task
            success = await this._handleUncompleteTask(task);
        } else if (checked) {
            // Complete the task
            success = await this._handleCompleteTask(task);
        }
        
        // Close the detail page after successful completion/uncompletion
        if (success) {
            this.pageManager.showPage('task-list');
        }
    }

    /**
     * Handle new chat from sidebar
     */
    _handleNewChatFromSidebar() {
        // Switch to Giskard view first
        this.ui.switchView('giskard');
        
        // Then trigger new chat after a brief delay to ensure view is loaded
        setTimeout(() => {
            // Access the chat manager through the global app instance
            if (window.app && window.app.chatManager) {
                window.app.chatManager._handleNewChat();
            }
        }, 100);
    }

    /**
     * Update progress button state in detail page
     */
    _updateDetailPageProgressButton(taskId) {
        // Get updated task data
        const allTasks = [...this.tasks.in_progress, ...this.tasks.open, ...this.tasks.done];
        const task = allTasks.find(t => t.file_idx === taskId);
        
        if (!task) return;
        
        const progressBtn = document.getElementById('detail-progress-btn');
        if (!progressBtn) return;
        
        const isInProgress = task.status === 'in_progress';
        progressBtn.classList.toggle('in-progress', isInProgress);
        progressBtn.innerHTML = isInProgress 
            ? '<i class="fas fa-pause"></i><span>pause</span>'
            : '<i class="fas fa-play"></i><span>start</span>';
    }

    /**
     * Handle page changes
     */
    _handlePageChanged({ page }) {
        this._renderCurrentView();
    }
}

export default TaskManager;
