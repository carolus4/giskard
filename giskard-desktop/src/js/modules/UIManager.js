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
        
        // Update view title
        const titles = {
            giskard: 'Giskard',
            today: 'Today'
        };
        
        const titleElement = document.getElementById('view-title');
        if (titleElement) {
            titleElement.textContent = titles[view] || view;
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
        
        // Update sidebar counts
        this._updateCountElement('today-count', this.counts.today);
        
        this.updateTaskCount();
    }

    /**
     * Update individual count element
     */
    _updateCountElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.textContent = value;
        
        // Show count only if value > 0
        if (value > 0) {
            element.classList.add('show');
        } else {
            element.classList.remove('show');
        }
    }

    /**
     * Update task count in header
     */
    updateTaskCount() {
        const taskCountEl = document.getElementById('task-count');
        
        if (taskCountEl) {
            if (this.currentView === 'giskard') {
                taskCountEl.textContent = 'AI Productivity Coach';
            } else {
                const count = this._getTaskCountForView(this.currentView);
                taskCountEl.textContent = `${count} task${count !== 1 ? 's' : ''}`;
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
        const todayDateElement = document.getElementById('today-date');
        if (todayDateElement) {
            todayDateElement.textContent = dateStr;
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
