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
                console.log('Add task simple button clicked');
                this.showAddTask();
            });
        }

        const addTaskPlusBtn = document.getElementById('add-task-plus-btn');
        if (addTaskPlusBtn) {
            addTaskPlusBtn.addEventListener('click', (e) => {
                console.log('Add task plus button clicked');
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
        // This method is now mainly for general page events
        // Detail page events are bound in _bindDetailPageEvents()
    }

    /**
     * Bind detail page events when the detail page is loaded
     */
    _bindDetailPageEvents() {
        // Remove existing event listeners to avoid duplicates
        this._unbindDetailPageEvents();

        // Task detail page form
        const saveTaskBtn = document.getElementById('save-task-btn');
        const detailDeleteBtn = document.getElementById('detail-delete-btn');
        const detailProgressBtn = document.getElementById('detail-progress-btn');
        const detailCheckbox = document.getElementById('detail-checkbox');

        if (saveTaskBtn) {
            this._saveTaskHandler = () => {
                this._handleSaveTaskFromPage();
            };
            saveTaskBtn.addEventListener('click', this._saveTaskHandler);
        }

        if (detailDeleteBtn) {
            this._deleteTaskHandler = () => {
                this._handleDeleteTaskFromPage();
            };
            detailDeleteBtn.addEventListener('click', this._deleteTaskHandler);
        }

        if (detailProgressBtn) {
            this._progressHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Progress button clicked, currentTaskId:', this.currentTaskId);
                this._handleToggleProgressFromPage();
            };
            detailProgressBtn.addEventListener('click', this._progressHandler);
        }

        if (detailCheckbox) {
            this._checkboxHandler = (e) => {
                this._handleToggleCompletionFromPage(e.target.checked);
            };
            detailCheckbox.addEventListener('change', this._checkboxHandler);
        }

        // Auto-resize title textarea
        const titleTextarea = document.getElementById('detail-title');
        if (titleTextarea) {
            // Auto-resize function
            this._autoResizeTextarea = () => {
                // Reset height to auto to get natural height
                titleTextarea.style.height = 'auto';
                
                // Ensure the textarea has proper width for wrapping
                titleTextarea.style.width = '100%';
                titleTextarea.style.maxWidth = 'none';
                
                // Force text wrapping
                titleTextarea.style.whiteSpace = 'pre-wrap';
                titleTextarea.style.wordWrap = 'break-word';
                titleTextarea.style.overflowWrap = 'break-word';
                titleTextarea.style.wordBreak = 'break-word';
                
                // Force a reflow
                titleTextarea.offsetHeight;
                
                // Get the scroll height
                const scrollHeight = titleTextarea.scrollHeight;
                
                // Calculate lines
                const lines = titleTextarea.value.split('\n').length;
                
                // If still only 1 line, estimate height based on text length
                let newHeight = scrollHeight;
                if (lines === 1 && titleTextarea.value.length > 50) {
                    // Estimate height based on text length and width
                    const charsPerLine = Math.floor(titleTextarea.offsetWidth / 14); // Approximate chars per line
                    const estimatedLines = Math.ceil(titleTextarea.value.length / charsPerLine);
                    newHeight = Math.max(scrollHeight, estimatedLines * 1.2 * 28);
                }
                
                titleTextarea.style.height = newHeight + 'px';
                titleTextarea.style.minHeight = newHeight + 'px';
                titleTextarea.style.maxHeight = 'none';
            };
            
            // Bind multiple events to ensure it works
            titleTextarea.addEventListener('input', this._autoResizeTextarea);
            titleTextarea.addEventListener('paste', this._autoResizeTextarea);
            titleTextarea.addEventListener('keyup', this._autoResizeTextarea);
            
            // Also trigger on focus
            titleTextarea.addEventListener('focus', this._autoResizeTextarea);
            
            // Initial resize
            setTimeout(() => {
                console.log('Initial auto-resize');
                this._autoResizeTextarea();
            }, 100);
        } else {
            console.log('Textarea not found!');
        }

        // Keyboard shortcuts for task detail page
        this._keyboardHandler = (e) => {
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
        };
        document.addEventListener('keydown', this._keyboardHandler);
    }

    /**
     * Unbind detail page events to prevent duplicates
     */
    _unbindDetailPageEvents() {
        const saveTaskBtn = document.getElementById('save-task-btn');
        const detailDeleteBtn = document.getElementById('detail-delete-btn');
        const detailProgressBtn = document.getElementById('detail-progress-btn');
        const detailCheckbox = document.getElementById('detail-checkbox');

        if (saveTaskBtn && this._saveTaskHandler) {
            saveTaskBtn.removeEventListener('click', this._saveTaskHandler);
        }

        if (detailDeleteBtn && this._deleteTaskHandler) {
            detailDeleteBtn.removeEventListener('click', this._deleteTaskHandler);
        }

        if (detailProgressBtn && this._progressHandler) {
            detailProgressBtn.removeEventListener('click', this._progressHandler);
        }

        if (detailCheckbox && this._checkboxHandler) {
            detailCheckbox.removeEventListener('change', this._checkboxHandler);
        }

        // Clean up textarea auto-resize
        const titleTextarea = document.getElementById('detail-title');
        if (titleTextarea && this._autoResizeTextarea) {
            titleTextarea.removeEventListener('input', this._autoResizeTextarea);
            titleTextarea.removeEventListener('paste', this._autoResizeTextarea);
            titleTextarea.removeEventListener('keyup', this._autoResizeTextarea);
            titleTextarea.removeEventListener('focus', this._autoResizeTextarea);
        }

        if (this._keyboardHandler) {
            document.removeEventListener('keydown', this._keyboardHandler);
        }
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
        console.log('showAddTask called');
        this.showPage('task-detail', 'new');
        console.log('After showPage, currentTaskId:', this.currentTaskId);
        this._setupAddTaskMode();
        console.log('After _setupAddTaskMode');
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
        console.log('_setupAddTaskMode called');
        
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        const categoriesContainer = document.getElementById('task-categories-detail');
        const checkbox = document.getElementById('detail-checkbox');
        const progressBtn = document.getElementById('detail-progress-btn');
        const deleteBtn = document.getElementById('detail-delete-btn');
        const saveBtn = document.getElementById('save-task-btn');
        const titleHeader = document.querySelector('.task-title-header');

        console.log('Found elements:', {
            titleInput: !!titleInput,
            descriptionInput: !!descriptionInput,
            saveBtn: !!saveBtn,
            titleHeader: !!titleHeader
        });

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
            console.log('Save button updated:', saveBtn.textContent);
        } else {
            console.log('Save button not found!');
        }

        // Update title header styling
        if (titleHeader) {
            titleHeader.classList.remove('completed');
        }

        // Focus on title input
        setTimeout(() => {
            if (titleInput) {
                titleInput.focus();
                console.log('Focused on title input');
            } else {
                console.log('Title input not found for focus');
            }
        }, 100);
        
        // Bind detail page events for add mode
        console.log('Binding detail page events for add mode');
        this._bindDetailPageEvents();
    }

    /**
     * Handle saving task from page
     */
    async _handleSaveTaskFromPage() {
        const titleInput = document.getElementById('detail-title');
        const descriptionInput = document.getElementById('detail-description');
        
        console.log('_handleSaveTaskFromPage called', { 
            currentTaskId: this.currentTaskId, 
            titleValue: titleInput?.value,
            hasTitleInput: !!titleInput 
        });
        
        if (!titleInput || !titleInput.value.trim()) {
            console.log('No title input or empty title, returning');
            return;
        }

        // Parse the formatted title to extract project and title
        const parsedTitle = this._parseTaskTitle(titleInput.value.trim());
        
        // Check if we're in add mode or edit mode
        if (this.currentTaskId === 'new') {
            // Add mode
            const taskData = {
                title: parsedTitle.title,
                description: descriptionInput?.value.trim() || '',
                project: parsedTitle.project
            };

            console.log('Dispatching task:add-from-page event with data:', taskData);
            // Dispatch event to TaskManager
            document.dispatchEvent(new CustomEvent('task:add-from-page', {
                detail: taskData
            }));
        } else {
            // Edit mode
            const taskData = {
                fileIdx: this.currentTaskId,
                title: parsedTitle.title,
                description: descriptionInput?.value.trim() || '',
                project: parsedTitle.project
            };

            console.log('Dispatching task:save-from-page event with data:', taskData);
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
        if (this.currentTaskId === null || this.currentTaskId === undefined) return;

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:delete-from-page', {
            detail: { taskId: this.currentTaskId }
        }));
    }

    /**
     * Handle toggling progress from page
     */
    async _handleToggleProgressFromPage() {
        if (this.currentTaskId === null || this.currentTaskId === undefined) {
            return;
        }

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:toggle-progress-from-page', {
            detail: { taskId: this.currentTaskId }
        }));
    }

    /**
     * Handle toggling completion from page
     */
    async _handleToggleCompletionFromPage(checked) {
        if (this.currentTaskId === null || this.currentTaskId === undefined) {
            return;
        }

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

        if (titleInput) {
            // Show formatted title with project prefix
            const displayTitle = this._formatTaskTitle(taskData);
            titleInput.value = displayTitle;
            
            // Trigger auto-resize for the textarea with a small delay
            if (this._autoResizeTextarea) {
                setTimeout(() => {
                    this._autoResizeTextarea();
                }, 10);
            }
        }
        
        // Load categories
        if (categoriesContainer) {
            this._renderCategoriesInDetail(categoriesContainer, taskData.categories || []);
        }
        
        // Bind detail page events when elements are available
        this._bindDetailPageEvents();
        
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

    /**
     * Format task title with project prefix
     * @param {Object} task - Task object with title and project
     * @returns {string} Formatted title like "[Project] Title" or just "Title"
     */
    _formatTaskTitle(task) {
        const title = task.title || 'Untitled Task';
        const project = task.project;
        
        if (project && project.trim()) {
            return `[${project}] ${title}`;
        }
        
        return title;
    }

    /**
     * Parse formatted title back into project and title
     * @param {string} formattedTitle - Title in format "[Project] Title" or just "Title"
     * @returns {Object} Object with project and title properties
     */
    _parseTaskTitle(formattedTitle) {
        const projectPattern = /^\[([^\]]+)\]\s+(.+)$/;
        const match = formattedTitle.match(projectPattern);
        
        if (match) {
            return {
                project: match[1].trim(),
                title: match[2].trim()
            };
        }
        
        return {
            project: null,
            title: formattedTitle.trim()
        };
    }

}

export default PageManager;
