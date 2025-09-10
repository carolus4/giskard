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


        // Add task buttons
        const addTaskSimpleBtn = document.getElementById('add-task-simple-btn');
        if (addTaskSimpleBtn) {
            addTaskSimpleBtn.addEventListener('click', () => {
                this.showAddTask();
            });
        }

        const addTaskPlusBtn = document.getElementById('add-task-plus-btn');
        if (addTaskPlusBtn) {
            addTaskPlusBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showAddTask();
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
            detailProgressBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Progress button clicked, currentTaskId:', this.currentTaskId);
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
     * Show add task page (using task detail page)
     */
    showAddTask() {
        this.showPage('task-detail', 'new');
        this._setupAddTaskMode();
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
     * Setup add task mode in task detail page
     */
    _setupAddTaskMode() {
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        const categoriesContainer = document.getElementById('task-categories-detail');
        const checkbox = document.getElementById('detail-checkbox');
        const progressBtn = document.getElementById('detail-progress-btn');
        const deleteBtn = document.getElementById('detail-delete-btn');
        const saveBtn = document.getElementById('save-task-btn');
        const titleHeader = document.querySelector('.task-title-header');

        // Clear all fields
        if (titleInput) titleInput.value = '';
        if (descriptionInput) descriptionInput.value = '';
        if (categoriesContainer) categoriesContainer.innerHTML = '';
        if (checkbox) checkbox.checked = false;

        // Hide elements not needed for add mode
        if (checkbox) checkbox.style.display = 'none';
        if (progressBtn) progressBtn.style.display = 'none';
        if (deleteBtn) deleteBtn.style.display = 'none';

        // Update save button text
        if (saveBtn) {
            saveBtn.textContent = 'Add task';
            saveBtn.classList.remove('save-btn');
            saveBtn.classList.add('add-btn');
        }

        // Update title header styling
        if (titleHeader) {
            titleHeader.classList.remove('completed');
        }

        // Focus on title input
        setTimeout(() => {
            if (titleInput) titleInput.focus();
        }, 100);
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

        // Check if we're in add mode or edit mode
        if (this.currentTaskId === 'new') {
            // Add mode
            const taskData = {
                title: titleInput.value.trim(),
                description: descriptionInput?.value.trim() || ''
            };

            // Dispatch event to TaskManager
            document.dispatchEvent(new CustomEvent('task:add-from-page', {
                detail: taskData
            }));
        } else {
            // Edit mode
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
        console.log('_handleToggleProgressFromPage called, currentTaskId:', this.currentTaskId);
        if (!this.currentTaskId) {
            console.log('No currentTaskId, returning');
            return;
        }

        console.log('Dispatching task:toggle-progress-from-page event');
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
        const categoriesContainer = document.getElementById('task-categories-detail');
        const checkbox = document.getElementById('detail-checkbox');
        const titleHeader = document.querySelector('.task-title-header');
        const progressBtn = document.getElementById('detail-progress-btn');
        const deleteBtn = document.getElementById('detail-delete-btn');
        const saveBtn = document.getElementById('save-task-btn');

        if (titleInput) titleInput.value = taskData.title || '';
        
        // Load categories
        if (categoriesContainer) {
            this._renderCategoriesInDetail(categoriesContainer, taskData.categories || []);
        }
        
        if (descriptionInput) {
            // Unescape newlines for display in textarea
            const description = taskData.description || '';
            descriptionInput.value = description.replace(/\\n/g, '\n');
            
            // Add click handler to ensure textarea stays expanded
            descriptionInput.addEventListener('click', (e) => {
                e.stopPropagation();
                // Ensure textarea is focused and expanded
                descriptionInput.focus();
                descriptionInput.style.minHeight = '250px';
            });
            
            // Add focus handler to maintain expansion
            descriptionInput.addEventListener('focus', () => {
                descriptionInput.style.minHeight = '250px';
            });
            
            // Add blur handler to maintain expansion if there's content
            descriptionInput.addEventListener('blur', () => {
                // Only collapse if textarea is empty
                if (!descriptionInput.value.trim()) {
                    descriptionInput.style.minHeight = '200px';
                }
            });
        }
        
        // Show all elements for edit mode
        if (checkbox) {
            checkbox.style.display = 'block';
            checkbox.checked = taskData.status === 'done';
        }
        if (progressBtn) {
            progressBtn.style.display = 'block';
            const isInProgress = taskData.status === 'in_progress';
            progressBtn.classList.toggle('in-progress', isInProgress);
            progressBtn.innerHTML = isInProgress 
                ? '<i class="fas fa-pause"></i><span>pause</span>'
                : '<i class="fas fa-play"></i><span>start</span>';
        }
        if (deleteBtn) {
            deleteBtn.style.display = 'block';
        }
        if (saveBtn) {
            saveBtn.textContent = 'Save';
            saveBtn.classList.remove('add-btn');
            saveBtn.classList.add('save-btn');
        }
        
        // Update title header styling
        if (titleHeader) {
            titleHeader.classList.toggle('completed', taskData.status === 'done');
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
     * Render category badges in task detail page
     */
    _renderCategoriesInDetail(container, categories) {
        if (!container) return;
        
        // Clear existing categories
        container.innerHTML = '';
        
        if (!categories || categories.length === 0) {
            return;
        }
        
        categories.forEach(category => {
            const badge = document.createElement('span');
            badge.className = `category-badge-detail category-${category}`;
            badge.textContent = category;
            container.appendChild(badge);
        });
    }

}

export default PageManager;
