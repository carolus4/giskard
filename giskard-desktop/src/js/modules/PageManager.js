/**
 * PageManager - Handles page navigation and routing
 */
class PageManager {
    constructor() {
        this.currentPage = 'task-list';
        this.currentTaskId = null;
        this._bindEvents();
        this._initialize();
    }

    /**
     * Initialize the page manager
     */
    _initialize() {
        // Show the default page
        this.showPage('task-list');
    }

    /**
     * Bind navigation events
     */
    _bindEvents() {
        // Sidebar navigation
        document.addEventListener('click', (e) => {
            const navItem = e.target.closest('.nav-item');
            if (navItem && navItem.dataset.page) {
                e.preventDefault();
                this.showPage(navItem.dataset.page);
            }
        });

        // Back buttons
        const backToTasksBtn = document.getElementById('back-to-tasks-btn');
        if (backToTasksBtn) {
            backToTasksBtn.addEventListener('click', () => {
                this.showPage('task-list');
            });
        }

        const backFromAddTaskBtn = document.getElementById('back-from-add-task-btn');
        if (backFromAddTaskBtn) {
            backFromAddTaskBtn.addEventListener('click', () => {
                this.showPage('task-list');
            });
        }

        // Add task buttons
        const addTaskSimpleBtn = document.getElementById('add-task-simple-btn');
        if (addTaskSimpleBtn) {
            addTaskSimpleBtn.addEventListener('click', () => {
                this.showPage('add-task');
            });
        }

        const addTaskPlusBtn = document.getElementById('add-task-plus-btn');
        if (addTaskPlusBtn) {
            addTaskPlusBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showPage('add-task');
            });
        }

        // New chat button
        const newChatBtn = document.getElementById('new-chat-btn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showPage('chat');
                // Trigger new chat after page loads
                setTimeout(() => {
                    if (window.__giskardApp?.chatManager) {
                        window.__giskardApp.chatManager._handleNewChat();
                    }
                }, 100);
            });
        }

        // Page-specific form handlers
        this._bindPageFormEvents();
    }

    /**
     * Bind form events for page-specific functionality
     */
    _bindPageFormEvents() {
        // Add task page form
        const pageAddBtn = document.getElementById('page-add-btn');
        const pageCancelBtn = document.getElementById('page-cancel-btn');
        const pageTaskName = document.getElementById('page-task-name');

        if (pageAddBtn) {
            pageAddBtn.addEventListener('click', () => {
                this._handleAddTaskFromPage();
            });
        }

        if (pageCancelBtn) {
            pageCancelBtn.addEventListener('click', () => {
                this.showPage('task-list');
            });
        }

        if (pageTaskName) {
            // Enable/disable add button based on title input
            pageTaskName.addEventListener('input', () => {
                if (pageAddBtn) {
                    pageAddBtn.disabled = !pageTaskName.value.trim();
                }
            });

            // Enter key to submit
            pageTaskName.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && pageAddBtn && !pageAddBtn.disabled) {
                    pageAddBtn.click();
                }
            });
        }

        // Task detail page form
        const saveTaskBtn = document.getElementById('save-task-btn');
        const detailDeleteBtn = document.getElementById('detail-delete-btn');
        const detailProgressBtn = document.getElementById('detail-progress-btn');
        const detailCheckbox = document.getElementById('detail-checkbox');

        if (saveTaskBtn) {
            saveTaskBtn.addEventListener('click', () => {
                this._handleSaveTaskFromPage();
            });
        }

        if (detailDeleteBtn) {
            detailDeleteBtn.addEventListener('click', () => {
                this._handleDeleteTaskFromPage();
            });
        }

        if (detailProgressBtn) {
            detailProgressBtn.addEventListener('click', () => {
                this._handleToggleProgressFromPage();
            });
        }

        if (detailCheckbox) {
            detailCheckbox.addEventListener('change', (e) => {
                this._handleToggleCompletionFromPage(e.target.checked);
            });
        }

        // Keyboard shortcuts for task detail page
        document.addEventListener('keydown', (e) => {
            if (this.currentPage === 'task-detail') {
                // Cmd+Enter or Ctrl+Enter to save
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                    e.preventDefault();
                    if (saveTaskBtn) {
                        // Visual feedback
                        saveTaskBtn.style.transform = 'scale(0.95)';
                        setTimeout(() => {
                            saveTaskBtn.style.transform = '';
                        }, 150);
                        saveTaskBtn.click();
                    }
                }
            }
        });
    }

    /**
     * Show a specific page
     */
    showPage(pageName, taskId = null) {
        // Hide all pages
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.style.display = 'none';
        });

        // Show the requested page
        const targetPage = document.getElementById(`${pageName}-page`);
        if (targetPage) {
            targetPage.style.display = 'flex';
            this.currentPage = pageName;
            this.currentTaskId = taskId;

            // Update sidebar active state
            this._updateSidebarActiveState(pageName);

            // Emit page change event
            document.dispatchEvent(new CustomEvent('page:changed', {
                detail: { page: pageName, taskId }
            }));

            // Focus on first input if available
            setTimeout(() => {
                const firstInput = targetPage.querySelector('input, textarea');
                if (firstInput) {
                    firstInput.focus();
                }
            }, 100);
        } else {
            console.error(`Page '${pageName}' not found`);
        }
    }

    /**
     * Show task detail page
     */
    showTaskDetail(taskId) {
        this.showPage('task-detail', taskId);
    }

    /**
     * Update sidebar active state
     */
    _updateSidebarActiveState(activePage) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === activePage) {
                item.classList.add('active');
            }
        });
    }

    /**
     * Get current page
     */
    getCurrentPage() {
        return this.currentPage;
    }

    /**
     * Get current task ID (if on task detail page)
     */
    getCurrentTaskId() {
        return this.currentTaskId;
    }

    /**
     * Handle adding task from page
     */
    async _handleAddTaskFromPage() {
        const titleInput = document.getElementById('page-task-name');
        const descriptionInput = document.getElementById('page-task-description');
        
        if (!titleInput || !titleInput.value.trim()) {
            return;
        }

        const taskData = {
            title: titleInput.value.trim(),
            description: descriptionInput?.value.trim() || ''
        };

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:add-from-page', {
            detail: taskData
        }));
    }

    /**
     * Handle saving task from page
     */
    async _handleSaveTaskFromPage() {
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        
        if (!titleInput || !titleInput.value.trim()) {
            return;
        }

        const taskData = {
            fileIdx: this.currentTaskId,
            title: titleInput.value.trim(),
            description: descriptionInput?.value.trim() || ''
        };

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:save-from-page', {
            detail: taskData
        }));
    }

    /**
     * Handle deleting task from page
     */
    async _handleDeleteTaskFromPage() {
        if (!this.currentTaskId) return;

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:delete-from-page', {
            detail: { taskId: this.currentTaskId }
        }));
    }

    /**
     * Handle toggling progress from page
     */
    async _handleToggleProgressFromPage() {
        if (!this.currentTaskId) return;

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:toggle-progress-from-page', {
            detail: { taskId: this.currentTaskId }
        }));
    }

    /**
     * Handle toggling completion from page
     */
    async _handleToggleCompletionFromPage(checked) {
        if (!this.currentTaskId) return;

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:toggle-completion-from-page', {
            detail: { taskId: this.currentTaskId, checked }
        }));
    }

    /**
     * Load task data into detail page
     */
    loadTaskIntoDetailPage(taskData) {
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        const checkbox = document.getElementById('detail-checkbox');
        const titleHeader = document.querySelector('.task-title-header');
        const progressBtn = document.getElementById('detail-progress-btn');

        if (titleInput) titleInput.value = taskData.title || '';
        if (descriptionInput) descriptionInput.value = taskData.description || '';
        
        // Set checkbox state
        if (checkbox) {
            checkbox.checked = taskData.status === 'done';
        }
        
        // Update title header styling
        if (titleHeader) {
            titleHeader.classList.toggle('completed', taskData.status === 'done');
        }

        // Update progress button
        if (progressBtn) {
            const isInProgress = taskData.status === 'in_progress';
            progressBtn.classList.toggle('in-progress', isInProgress);
            progressBtn.innerHTML = isInProgress 
                ? '<i class="fas fa-pause"></i><span>pause</span>'
                : '<i class="fas fa-play"></i><span>start</span>';
        }

        // Update keyboard shortcut display
        this._updateKeyboardShortcut();
    }

    /**
     * Update keyboard shortcut display
     */
    _updateKeyboardShortcut() {
        const shortcutSpan = document.querySelector('.keyboard-shortcut');
        if (shortcutSpan) {
            const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
            shortcutSpan.textContent = isMac ? '⌘↵' : 'Ctrl+↵';
        }
    }

    /**
     * Clear add task form
     */
    clearAddTaskForm() {
        const titleInput = document.getElementById('page-task-name');
        const descriptionInput = document.getElementById('page-task-description');
        const addBtn = document.getElementById('page-add-btn');

        if (titleInput) titleInput.value = '';
        if (descriptionInput) descriptionInput.value = '';
        if (addBtn) addBtn.disabled = true;
    }
}

export default PageManager;
