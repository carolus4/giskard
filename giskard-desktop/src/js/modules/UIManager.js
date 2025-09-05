/**
 * UIManager - Handles view switching, DOM updates, and UI state management
 */
class UIManager {
    constructor() {
        this.currentView = 'today';
        this.counts = {
            today: 0
        };
        
        this._bindNavigation();
    }

    /**
     * Bind navigation events
     */
    _bindNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.switchView(view);
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
        
        const activeNavItem = document.querySelector(`[data-view="${view}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Update view title for each view's page header
        const titleElements = {
            giskard: document.getElementById('giskard-view-title'),
            today: document.getElementById('view-title')
        };
        
        const titles = {
            giskard: 'Giskard',
            today: 'Today' // Will be updated with date from API response
        };
        
        const subtitles = {
            giskard: 'AI Productivity Coach • llama3.1:8b',
            today: '0 tasks' // Will be updated with actual count
        };
        
        const titleElement = titleElements[view];
        if (titleElement) {
            // For today view, don't override if we already have a date set
            if (view === 'today' && titleElement.textContent.includes('Today -')) {
                // Keep the existing date format
            } else {
                titleElement.textContent = titles[view] || view;
            }
        }
        
        // Update subtitle for giskard view
        if (view === 'giskard') {
            const giskardSubtitle = document.getElementById('giskard-task-count');
            if (giskardSubtitle) {
                giskardSubtitle.textContent = subtitles.giskard;
            }
        }
        
        // Hide all views
        document.querySelectorAll('.view-container').forEach(container => {
            container.style.display = 'none';
        });
        
        // Show current view
        const currentViewElement = document.getElementById(`${view}-view`);
        if (currentViewElement) {
            currentViewElement.style.display = 'block';
        }
        
        this.currentView = view;
        this.updateTaskCount();
        
        // Emit view change event
        document.dispatchEvent(new CustomEvent('view:changed', { 
            detail: { view, previousView: this.currentView }
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
            today: document.getElementById('task-count')
        };
        
        const taskCountEl = taskCountElements[this.currentView];
        
        if (taskCountEl) {
            if (this.currentView === 'giskard') {
                taskCountEl.textContent = 'AI Productivity Coach • llama3.1:8b';
            } else {
                // Hide task count since it's not helpful
                taskCountEl.style.display = 'none';
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
