/**
 * Mini Todo App - Modular JavaScript Application
 * Entry point that initializes and coordinates all modules
 */

console.log('🚀 app.js loading...');

import TaskManager from './modules/TaskManager.js';
import ChatManager from './modules/ChatManager.js';

console.log('✅ TaskManager and ChatManager imported');

/**
 * TodoApp - Main application class (simplified)
 */
class TodoApp {
    constructor() {
        this.taskManager = null;
        this.chatManager = null;
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

            // Initialize managers
            this.taskManager = new TaskManager();
            this.chatManager = new ChatManager();
            
            console.log('✅ Giskard App initialized with task management and chat coaching');
            
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

    /**
     * Get the chat manager instance (for debugging/testing)
     */
    getChatManager() {
        return this.chatManager;
    }
}

console.log('📝 Setting up DOMContentLoaded listener...');

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOM loaded - initializing TodoApp...');
    window.__giskardApp = new TodoApp();
});

console.log('✅ app.js setup complete');

// Make app available globally for debugging
window.TodoApp = TodoApp;
// Global debug functions
window.debugChat = () => {
    if (window.__giskardApp?.chatManager) {
        window.__giskardApp.chatManager.debugChatState();
    } else {
        console.log('❌ ChatManager not found. App:', !!window.__giskardApp);
    }
};

window.clearChatStorage = () => {
    localStorage.removeItem('giscard_chat_history');
    console.log('🗑️ Chat storage cleared from localStorage');
};

window.checkChatStorage = () => {
    const stored = localStorage.getItem('giscard_chat_history');
    console.log('💾 Chat storage:', stored ? JSON.parse(stored) : 'empty');
};
