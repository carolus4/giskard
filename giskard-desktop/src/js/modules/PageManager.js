    /**
     * PageManager - Handles page navigation and routing
     */
class PageManager {
    constructor() {
        this.currentPage = 'task-list';
        this.currentTaskId = null;

        // Debouncing for task updates to avoid overwhelming classification queue
        this.updateTimeouts = new Map();
        this.pendingUpdates = new Map();

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
        const detailDeleteBtn = document.getElementById('detail-delete-btn');
        const detailProgressBtn = document.getElementById('detail-progress-btn');
        const statusSelector = document.getElementById('status-selector');
        const saveTaskBtn = document.getElementById('save-task-btn');

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


        // Status selector events
        if (statusSelector) {
            this._statusSelectorHandler = (e) => {
                const statusOption = e.target.closest('.status-option');
                if (statusOption) {
                    e.preventDefault();
                    e.stopPropagation();
                    const newStatus = statusOption.dataset.status;
                    console.log('Status selector clicked, newStatus:', newStatus);
                    this._handleStatusChangeFromPage(newStatus);
                }
            };
            statusSelector.addEventListener('click', this._statusSelectorHandler);
        }

        if (saveTaskBtn) {
            this._saveTaskHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Save task button clicked');
                this._handleSaveTaskFromPage();
            };
            saveTaskBtn.addEventListener('click', this._saveTaskHandler);
        }

        // Auto-resize title textarea
        const titleTextarea = document.getElementById('detail-title');
        if (titleTextarea) {
            // Auto-resize function
            this._autoResizeTextarea = () => {
                // Reset height to auto to get the natural scrollHeight
                titleTextarea.style.height = 'auto';

                // Get the scroll height (this is the height needed to show all content)
                const scrollHeight = titleTextarea.scrollHeight;

                // Set a reasonable minimum height (about 1.2 lines)
                const minHeight = 40; // 1.2 * 28px font size + padding

                // Set a reasonable maximum height (about 6 lines)
                const maxHeight = 200; // 6 * 28px font size + padding

                // Calculate the new height, constrained by min/max
                let newHeight = Math.max(minHeight, Math.min(scrollHeight, maxHeight));

                // Apply the new height
                titleTextarea.style.height = newHeight + 'px';
            };

            // Bind multiple events to ensure it works
            titleTextarea.addEventListener('input', this._autoResizeTextarea);
            titleTextarea.addEventListener('paste', this._autoResizeTextarea);
            titleTextarea.addEventListener('keyup', this._autoResizeTextarea);
            titleTextarea.addEventListener('keydown', this._autoResizeTextarea);

            // Also trigger on focus
            titleTextarea.addEventListener('focus', this._autoResizeTextarea);

            // Initial resize after a short delay to ensure DOM is ready
            setTimeout(() => {
                requestAnimationFrame(() => {
                    this._autoResizeTextarea();
                });
            }, 50);
        } else {
            console.log('Textarea not found!');
        }

        // Add real-time save handlers for automatic updates
        this._bindRealTimeSaveHandlers();

        // Keyboard shortcuts for task detail page
        this._keyboardHandler = (e) => {
            if (this.currentPage === 'task-detail') {
                // Cmd+Enter or Ctrl+Enter to save/create task (only in add mode)
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                    e.preventDefault();
                    // Only save if we're in add mode (not edit mode)
                    if (this.currentTaskId === 'new') {
                        this._handleSaveTaskFromPage();
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
        const detailDeleteBtn = document.getElementById('detail-delete-btn');
        const detailProgressBtn = document.getElementById('detail-progress-btn');
        const statusSelector = document.getElementById('status-selector');
        const saveTaskBtn = document.getElementById('save-task-btn');

        if (detailDeleteBtn && this._deleteTaskHandler) {
            detailDeleteBtn.removeEventListener('click', this._deleteTaskHandler);
        }

        if (detailProgressBtn && this._progressHandler) {
            detailProgressBtn.removeEventListener('click', this._progressHandler);
        }


        if (statusSelector && this._statusSelectorHandler) {
            statusSelector.removeEventListener('click', this._statusSelectorHandler);
        }

        if (saveTaskBtn && this._saveTaskHandler) {
            saveTaskBtn.removeEventListener('click', this._saveTaskHandler);
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
        // If leaving task detail page, flush any pending updates
        if (this.currentPage === 'task-detail' && pageName !== 'task-detail') {
            if (this.currentTaskId && this.currentTaskId !== 'new') {
                this._flushPendingUpdate(this.currentTaskId);
            }
        }

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
            // For task-detail page, keep "task-list" highlighted since it's conceptually part of tasks
            const sidebarPage = (pageName === 'task-detail') ? 'task-list' : pageName;
            this._updateSidebarActiveState(sidebarPage);

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
        const categoriesContainer = document.getElementById('task-categories-detail');
        const progressBtn = document.getElementById('detail-progress-btn');
        const deleteBtn = document.getElementById('detail-delete-btn');
        const saveBtn = document.getElementById('save-task-btn');
        const titleHeader = document.querySelector('.task-title-header');

        console.log('Found elements:', {
            titleInput: !!titleInput,
            saveBtn: !!saveBtn,
            titleHeader: !!titleHeader
        });

        // Clear all fields
        if (titleInput) {
            titleInput.value = '';
            // Trigger auto-resize for empty content
            if (this._autoResizeTextarea) {
                requestAnimationFrame(() => {
                    this._autoResizeTextarea();
                });
            }
        }
        if (categoriesContainer) categoriesContainer.innerHTML = '';
        
        // Initialize GitHub editor for new task (empty content)
        this._initializeGitHubEditor({ description: '' });

        // Hide elements not needed for add mode
        if (progressBtn) progressBtn.style.display = 'none';
        if (deleteBtn) deleteBtn.style.display = 'none';
        
        // Hide status selector in add mode
        const statusSelector = document.getElementById('status-selector');
        if (statusSelector) statusSelector.style.display = 'none';

        // Show save button in add mode
        if (saveBtn) {
            saveBtn.style.display = 'flex';
        }

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
     * Handle saving task from page (legacy method for external calls)
     * Since we no longer have a save button, this is mainly for programmatic saves
     */
    async _handleSaveTaskFromPage() {
        const titleInput = document.getElementById('detail-title');

        console.log('_handleSaveTaskFromPage called (programmatic save)', {
            currentTaskId: this.currentTaskId,
            titleValue: titleInput?.value,
            hasTitleInput: !!titleInput
        });

        if (!titleInput || !titleInput.value.trim()) {
            console.log('No title input or empty title, returning');
            return;
        }

        // Get the title directly (no project prefix parsing needed)
        const title = titleInput.value.trim();
        
        // Get description from GitHub editor
        const description = this.githubEditor ? this.githubEditor.getContent() : '';

        // Check if we're in add mode or edit mode
        if (this.currentTaskId === 'new') {
            // Add mode - immediate save (no debouncing for new tasks)
            const taskData = {
                title: title,
                description: description.trim(),
                project: null // Project will be handled separately in the future
            };

            console.log('Dispatching task:add-from-page event with data:', taskData);
            // Dispatch event to TaskManager
            document.dispatchEvent(new CustomEvent('task:add-from-page', {
                detail: taskData
            }));
        } else {
            // Edit mode - get original task data to compare
            const allTasks = [...(window.app?.taskManager?.tasks?.in_progress || []), 
                             ...(window.app?.taskManager?.tasks?.open || []), 
                             ...(window.app?.taskManager?.tasks?.done || [])];
            const originalTask = allTasks.find(t => t.id === this.currentTaskId);
            
            const taskData = {
                fileIdx: this.currentTaskId,
                title: title,
                description: description.trim()
            };

            // Force immediate save (this will trigger classification)
            await this._debouncedUpdateTask(this.currentTaskId, taskData, true);
        }
    }

    /**
     * Initialize GitHub-like editor for task descriptions
     */
    _initializeGitHubEditor(task) {
        const container = document.getElementById('github-editor-container');
        if (!container) {
            console.error('GitHub editor container not found');
            return;
        }

        // Destroy existing editor if it exists
        if (this.githubEditor) {
            this.githubEditor.destroy();
        }

        // Create new GitHub-like editor
        this.githubEditor = new GitHubLikeEditor('github-editor-container', {
            placeholder: 'Add description...',
            autosaveDelay: 1500
        });

        // Set initial content
        const description = task.description || '';
        this.githubEditor.setContent(description.replace(/\\n/g, '\n'));

        // Listen for save events
        container.addEventListener('github-editor-save', async (e) => {
            const content = e.detail.content;
            await this._debouncedUpdateTask(this.currentTaskId, {
                description: content
            });
        });
    }

    /**
     * Bind real-time save handlers for automatic updates
     */
    _bindRealTimeSaveHandlers() {
        // Only bind for edit mode (not add mode)
        if (this.currentTaskId === 'new') return;

        const titleInput = document.getElementById('detail-title');

        if (titleInput) {
            // Debounced save on title changes
            let titleTimeout;
            titleInput.addEventListener('input', () => {
                clearTimeout(titleTimeout);
                titleTimeout = setTimeout(async () => {
                    if (titleInput.value.trim()) {
                        const updateData = {
                            title: titleInput.value.trim()
                        };
                        
                        await this._debouncedUpdateTask(this.currentTaskId, updateData);
                    }
                }, 1000); // 1 second debounce for title changes
            });
        }

        // GitHub editor handles its own saving via events
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
     * Handle status change from status selector
     */
    async _handleStatusChangeFromPage(newStatus) {
        if (this.currentTaskId === null || this.currentTaskId === undefined) {
            return;
        }

        // Dispatch event to TaskManager
        document.dispatchEvent(new CustomEvent('task:change-status-from-page', {
            detail: { taskId: this.currentTaskId, status: newStatus }
        }));
    }


    /**
     * Update status selector to reflect current task status
     */
    _updateStatusSelector(currentStatus) {
        const statusSelector = document.getElementById('status-selector');
        if (!statusSelector) return;

        // Remove active class from all options
        const statusOptions = statusSelector.querySelectorAll('.status-option');
        statusOptions.forEach(option => {
            option.classList.remove('active');
        });

        // Add active class to current status
        const currentOption = statusSelector.querySelector(`[data-status="${currentStatus}"]`);
        if (currentOption) {
            currentOption.classList.add('active');
        }
    }

    /**
     * Load task data into detail page
     */
    loadTaskIntoDetailPage(taskData) {
        const titleInput = document.getElementById('detail-title');
        const categoriesContainer = document.getElementById('task-categories-detail');
        const titleHeader = document.querySelector('.task-title-header');
        const progressBtn = document.getElementById('detail-progress-btn');
        const deleteBtn = document.getElementById('detail-delete-btn');
        const saveBtn = document.getElementById('save-task-btn');

        // Extract task data from API response (nested under 'task' key)
        const task = taskData.task || taskData;

        if (titleInput) {
            // Show title without project prefix (project will be shown as badge)
            titleInput.value = task.title || 'Untitled Task';

            // Trigger auto-resize for the textarea immediately after setting value
            if (this._autoResizeTextarea) {
                // Use requestAnimationFrame to ensure the value is set before resizing
                requestAnimationFrame(() => {
                    this._autoResizeTextarea();
                });
            }
        }
        
        // Load categories and project
        if (categoriesContainer) {
            console.log('🔍 Categories debug:', {
                taskData: taskData,
                task: task,
                categories: task.categories,
                project: task.project,
                categoriesType: typeof task.categories,
                categoriesLength: task.categories?.length,
                container: categoriesContainer
            });
            this._renderCategoriesAndProjectInDetail(categoriesContainer, task.categories || [], task.project);
        } else {
            console.log('❌ Categories container not found!');
        }
        
        // Initialize GitHub-like editor
        this._initializeGitHubEditor(task);
        
        // Bind detail page events when elements are available
        this._bindDetailPageEvents();
        
        // Show all elements for edit mode
        if (progressBtn) {
            progressBtn.style.display = 'none'; // Hide old progress button
        }
        if (deleteBtn) {
            deleteBtn.style.display = 'block';
        }
        if (saveBtn) {
            // Hide save button in edit mode since saving is automatic
            saveBtn.style.display = 'none';
        }

        // Show status selector in edit mode
        const statusSelector = document.getElementById('status-selector');
        if (statusSelector) statusSelector.style.display = 'flex';

        // Update status selector
        this._updateStatusSelector(task.status);
        
        // Update title header styling
        if (titleHeader) {
            titleHeader.classList.toggle('completed', task.status === 'done');
        }

        // Update keyboard shortcut display (Cmd+Enter to go back to task list)
        this._updateKeyboardShortcut();

    }

    /**
     * Update keyboard shortcut display (no visual indicator needed since no save button)
     * Cmd+Enter/Ctrl+Enter still works to go back to task list
     */
    _updateKeyboardShortcut() {
        // Keyboard shortcut (Cmd+Enter/Ctrl+Enter) still works to navigate back to task list
        // No visual indicator needed since there's no save button to attach it to
        // The shortcut functionality is handled in the keyboard event handler above
    }

    /**
     * Render category badges with colored dots and project badges in task detail page
     */
    _renderCategoriesAndProjectInDetail(container, categories, project) {
        console.log('🎯 _renderCategoriesAndProjectInDetail called:', {
            container: container,
            categories: categories,
            project: project,
            categoriesType: typeof categories,
            categoriesLength: categories?.length
        });
        
        if (!container) {
            console.log('❌ Container not found in _renderCategoriesAndProjectInDetail');
            return;
        }
        
        // Clear existing categories
        container.innerHTML = '';
        
        // Add project badge if project exists
        if (project && project.trim()) {
            const projectBadge = document.createElement('span');
            projectBadge.className = 'project-badge';
            projectBadge.innerHTML = `<i class="fas fa-clipboard-list"></i>${project}`;
            container.appendChild(projectBadge);
            console.log('➕ Added project badge:', project);
        }
        
        // Add category badges with colored dots
        if (categories && categories.length > 0) {
            console.log('✅ Rendering categories:', categories);
            categories.forEach(category => {
                const badge = document.createElement('span');
                badge.className = `category-badge category-${category}`;
                badge.innerHTML = `<span class="category-dot"></span>${category}`;
                container.appendChild(badge);
                console.log('➕ Added category badge:', category);
            });
        } else {
            console.log('⚠️ No categories to render:', categories);
        }
    }


    /**
     * Debounced task update - saves changes but defers classification
     * @param {string} taskId - Task ID to update
     * @param {Object} taskData - Task data to save
     * @param {boolean} immediate - Whether to skip debouncing and save immediately
     */
    async _debouncedUpdateTask(taskId, taskData, immediate = false) {
        // Validate taskId before proceeding
        if (!taskId || taskId === 'new') {
            console.warn('⚠️ Skipping debounced update - invalid taskId:', taskId);
            return;
        }

        // Clear any existing timeout for this task
        if (this.updateTimeouts.has(taskId)) {
            clearTimeout(this.updateTimeouts.get(taskId));
            this.updateTimeouts.delete(taskId);
        }

        // Store the pending update
        this.pendingUpdates.set(taskId, {
            data: taskData,
            timestamp: Date.now()
        });

        if (immediate) {
            // Save immediately without debouncing
            await this._executeTaskUpdate(taskId, taskData);
        } else {
            // Set up debounced save (wait 2 seconds after last change)
            const timeoutId = setTimeout(async () => {
                this.updateTimeouts.delete(taskId);
                const pendingUpdate = this.pendingUpdates.get(taskId);

                if (pendingUpdate) {
                    this.pendingUpdates.delete(taskId);
                    await this._executeTaskUpdate(taskId, pendingUpdate.data);
                }
            }, 2000); // 2 second debounce delay

            this.updateTimeouts.set(taskId, timeoutId);
        }
    }

    /**
     * Execute the actual task update via API
     * @param {string} taskId - Task ID to update
     * @param {Object} taskData - Task data to save
     */
    async _executeTaskUpdate(taskId, taskData) {
        try {
            // Validate taskId before proceeding
            if (!taskId || taskId === 'new') {
                console.warn('⚠️ Skipping task update - invalid taskId:', taskId);
                return;
            }

            // Convert string taskId to number for API validation
            const numericTaskId = parseInt(taskId, 10);
            if (isNaN(numericTaskId) || numericTaskId <= 0) {
                console.error('❌ Invalid taskId format:', taskId);
                return;
            }

            // Use APIClient to update task immediately (for persistence)
            const apiClient = new (await import('./APIClient.js')).default();

            const result = await apiClient.updateTask(numericTaskId, {
                title: taskData.title,
                description: taskData.description,
                project: taskData.project,
                categories: taskData.categories,
                // Add a flag to indicate this is a debounced update that should defer classification
                _debounced: true
            });

            if (result.success) {
                console.log(`✅ Task ${taskId} updated (debounced - classification deferred)`);
                // Show subtle feedback that changes were saved
                this._showDebouncedSaveFeedback();
            } else {
                console.error('❌ Debounced task update failed:', result.error);
                // Still show error notification
                if (window.app?.notificationManager) {
                    window.app.notificationManager.error('Failed to save changes');
                }
            }
        } catch (error) {
            console.error('❌ Error in debounced task update:', error);
        }
    }

    /**
     * Show subtle feedback that changes were saved
     * Since there's no save button, we could add a subtle indicator elsewhere
     * or just rely on the console logging for now
     */
    _showDebouncedSaveFeedback() {
        // For now, just log the save (could add a subtle toast notification here later)
        console.log('💾 Changes auto-saved');
        // Could add a subtle visual indicator in the future, like:
        // - A small checkmark that appears briefly
        // - A subtle color change on the title input
        // - A small "Saved" indicator that fades in/out
    }

    /**
     * Force immediate save of pending changes (e.g., when navigating away)
     * @param {string} taskId - Task ID to save immediately
     */
    async _flushPendingUpdate(taskId) {
        if (this.updateTimeouts.has(taskId)) {
            clearTimeout(this.updateTimeouts.get(taskId));
            this.updateTimeouts.delete(taskId);
        }

        const pendingUpdate = this.pendingUpdates.get(taskId);
        if (pendingUpdate) {
            this.pendingUpdates.delete(taskId);
            await this._executeTaskUpdate(taskId, pendingUpdate.data);
        }
    }

    /**
     * Cancel all pending updates (e.g., when navigating away without saving)
     */
    _cancelAllPendingUpdates() {
        // Clear all timeouts
        for (const timeoutId of this.updateTimeouts.values()) {
            clearTimeout(timeoutId);
        }
        this.updateTimeouts.clear();
        this.pendingUpdates.clear();
    }

}

export default PageManager;
