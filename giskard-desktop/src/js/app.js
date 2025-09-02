/**
 * Mini Todo App - Modular JavaScript Application
 * Entry point that initializes and coordinates all modules
 */

console.log('🚀 app.js loading...');

import TaskManager from './modules/TaskManager.js';

console.log('✅ TaskManager imported');

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

console.log('📝 Setting up DOMContentLoaded listener...');

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOM loaded - initializing TodoApp...');
    new TodoApp();
});

console.log('✅ app.js setup complete');

// Make app available globally for debugging
window.TodoApp = TodoApp;
