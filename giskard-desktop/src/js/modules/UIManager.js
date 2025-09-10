/**
 * UIManager - Handles view switching, DOM updates, and UI state management
 */
class UIManager {
    constructor() {
        this.currentView = 'task-list';
        this.counts = {
            today: 0,
            completed_today: 0
        };
        
        this._bindNavigation();
    }

    /**
     * Bind navigation events
     */
    _bindNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.switchView(page);
            });
        });
    }

    /**
     * Switch to a specific view
     */
    switchView(view) {
        if (this.currentView === view) return;

        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[data-page="${view}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Update view title for each view's page header
        const titleElements = {
            chat: document.getElementById('chat-page-title'),
            'task-list': document.getElementById('task-list-title')
        };
        
        const titles = {
            chat: 'Giskard',
            'task-list': 'Tasks'
        };
        
        const subtitles = {
            chat: 'AI Productivity Coach • llama3.1:8b',
            'task-list': '0 tasks' // Will be updated with actual count
        };
        
        const titleElement = titleElements[view];
        if (titleElement) {
            titleElement.textContent = titles[view] || view;
        }
        
        // Update subtitle for chat view
        if (view === 'chat') {
            const chatSubtitle = document.getElementById('chat-page-subtitle');
            if (chatSubtitle) {
                chatSubtitle.textContent = subtitles.chat;
            }
        }
        
        // Hide all views
        document.querySelectorAll('.page').forEach(container => {
            container.style.display = 'none';
        });
        
        // Show current view
        const currentViewElement = document.getElementById(`${view}-page`);
        if (currentViewElement) {
            currentViewElement.style.display = 'flex';
        }
        
        this.currentView = view;
        this.updateTaskCount();
        
        // Emit view change event
        document.dispatchEvent(new CustomEvent('page:changed', { 
            detail: { page: view, previousPage: this.currentView }
        }));
    }

    /**
     * Update task counts in sidebar and header
     */
    updateCounts(counts) {
        this.counts = { ...this.counts, ...counts };
        
        this.updateTaskCount();
    }

    /**
     * Update task count in header
     */
    updateTaskCount() {
        const taskCountElements = {
            giskard: document.getElementById('giskard-task-count'),
            'task-list': document.getElementById('task-count')
        };
        
        const taskCountEl = taskCountElements[this.currentView];
        
        if (taskCountEl) {
            if (this.currentView === 'giskard') {
                taskCountEl.textContent = 'AI Productivity Coach • llama3.1:8b';
            } else if (this.currentView === 'task-list') {
                const completedCount = this.counts.completed_today || 0;
                taskCountEl.textContent = `${completedCount} task${completedCount !== 1 ? 's' : ''} completed today`;
                taskCountEl.style.display = 'block';
            }
        }
    }

    /**
     * Get task count for specific view
     */
    _getTaskCountForView(view) {
        switch (view) {
            case 'giskard':
                return 0; // Chat view doesn't show task count
            case 'today':
                return this.counts.today;
            default:
                return 0;
        }
    }

    /**
     * Update today's date display
     */
    updateTodayDate(dateStr) {
        // Update the main content header title with the formatted date
        const titleElement = document.getElementById('view-title');
        if (titleElement && this.currentView === 'today') {
            titleElement.textContent = dateStr;
        }
    }

    /**
     * Clear a specific view container
     */
    clearView(view) {
        const containers = {
            giskard: '#giskard-view',
            today: '#today-tasks'
        };

        const selector = containers[view];
        if (selector) {
            const container = document.querySelector(selector);
            if (container) {
                container.innerHTML = '';
            }
        }
    }

    /**
     * Get view container element
     */
    getViewContainer(view) {
        const containers = {
            giskard: '#giskard-view',
            today: '#today-tasks'
        };

        const selector = containers[view];
        return selector ? document.querySelector(selector) : null;
    }

    /**
     * Show empty state for a view
     */
    showEmptyState(view, message = 'No tasks') {
        const container = this.getViewContainer(view);
        if (!container) return;

        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <p>${message}</p>
        `;
        
        container.innerHTML = '';
        container.appendChild(emptyState);
    }

    /**
     * Add loading state to view
     */
    setLoading(view, isLoading = true) {
        const container = this.getViewContainer(view);
        if (!container) return;

        if (isLoading) {
            container.classList.add('loading');
        } else {
            container.classList.remove('loading');
        }
    }

    /**
     * Highlight a specific task (e.g., after editing)
     */
    highlightTask(fileIdx, duration = 2000) {
        const taskElement = document.querySelector(`[data-file-idx="${fileIdx}"]`);
        if (!taskElement) return;

        taskElement.classList.add('highlighted');
        
        setTimeout(() => {
            taskElement.classList.remove('highlighted');
        }, duration);
    }

    /**
     * Scroll to a specific task
     */
    scrollToTask(fileIdx) {
        const taskElement = document.querySelector(`[data-file-idx="${fileIdx}"]`);
        if (!taskElement) return;

        taskElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }

    /**
     * Get current view name
     */
    getCurrentView() {
        return this.currentView;
    }

    /**
     * Get current page name (alias for getCurrentView)
     */
    getCurrentPage() {
        return this.currentView;
    }

    /**
     * Check if a specific view is active
     */
    isViewActive(view) {
        return this.currentView === view;
    }

    /**
     * Update keyboard shortcut displays based on platform
     */
    updateKeyboardShortcuts() {
        const shortcuts = document.querySelectorAll('.keyboard-shortcut');
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        
        shortcuts.forEach(shortcut => {
            const currentText = shortcut.textContent;
            if (currentText.includes('⌘') || currentText.includes('Ctrl')) {
                shortcut.textContent = isMac ? '⌘↵' : 'Ctrl+↵';
            }
        });
    }
}

export default UIManager;
