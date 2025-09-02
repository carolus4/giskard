/**
 * Mini Todo App - Modular JavaScript Application
 * Entry point that initializes and coordinates all modules
 */

import TaskManager from './modules/TaskManager.js';

/**
 * TodoApp - Main application class (simplified)
 */
class TodoApp {
    constructor() {
        this.taskManager = null;
        this._init();
    }

    /**
     * Initialize the application
     */
    async _init() {
        try {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                await new Promise(resolve => {
                    document.addEventListener('DOMContentLoaded', resolve);
                });
            }

            // Initialize the main task manager
            this.taskManager = new TaskManager();
            
            console.log('✅ Mini Todo App initialized with modular architecture');
            
        } catch (error) {
            console.error('❌ Failed to initialize Todo App:', error);
        }
    }

    /**
     * Get the task manager instance (for debugging/testing)
     */
    getTaskManager() {
        return this.taskManager;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TodoApp();
});

// Make app available globally for debugging
window.TodoApp = TodoApp;
