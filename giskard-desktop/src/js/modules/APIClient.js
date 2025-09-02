/**
 * APIClient - Centralized HTTP requests for the todo application
 * 
 * Provides a clean interface for all backend API interactions with
 * consistent error handling, request formatting, and response processing.
 * 
 * @class APIClient
 * @version 1.0.0
 * @author Mini Todo App
 * 
 * @example
 * const api = new APIClient();
 * const result = await api.getTasks();
 * if (result.success) {
 *   console.log(result.data.tasks);
 * }
 */
class APIClient {
    /**
     * Create an APIClient instance
     * @constructor
     */
    constructor() {
        /** @type {string} Base URL for all API endpoints */
        // Check if we're running in Tauri (desktop app) vs browser
        this.isTauri = window.__TAURI__ !== undefined;
        this.baseURL = this.isTauri ? 'http://localhost:5001/api' : '/api';
        
        // Debug Tauri detection
        console.log('🔍 Tauri detection:', {
            isTauri: this.isTauri,
            hasTauri: !!window.__TAURI__,
            hasInvoke: !!(window.__TAURI__?.invoke),
            baseURL: this.baseURL
        });
    }

    /**
     * Validate that an ID is a positive integer
     * 
     * @private
     * @param {any} id - The ID to validate
     * @param {string} [paramName='ID'] - Parameter name for error messages
     * @returns {{isValid: boolean, error?: string}} Validation result
     */
    _validateId(id, paramName = 'ID') {
        if (typeof id !== 'number' || !Number.isInteger(id) || id <= 0) {
            return {
                isValid: false,
                error: `${paramName} must be a positive integer, received: ${typeof id} ${id}`
            };
        }
        return { isValid: true };
    }

    /**
     * Generic fetch wrapper with consistent error handling
     * 
     * @private
     * @param {string} url - The endpoint URL to fetch
     * @param {Object} [options={}] - Fetch options (method, headers, body, etc.)
     * @param {string} [options.method='GET'] - HTTP method
     * @param {Object} [options.headers={}] - Request headers
     * @param {string} [options.body] - Request body (JSON string)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Standardized response
     */
    async _fetch(url, options = {}) {
        try {
            console.log('🚀 API Request:', { url, options, isTauri: this.isTauri });
            
            // If running in Tauri, use Tauri commands (much more reliable!)
            if (this.isTauri && window.__TAURI__?.invoke) {
                const { invoke } = window.__TAURI__;
                
                console.log('🦀 Using Tauri commands for:', url, options);
                
                // Route to appropriate Tauri command  
                if (url.includes('/api/tasks') && (!options.method || options.method === 'GET')) {
                    try {
                        const result = await invoke('api_get_tasks');
                        const data = JSON.parse(result);
                        console.log('✅ Tauri getTasks success:', Object.keys(data));
                        return { success: true, data };
                    } catch (error) {
                        console.error('❌ Tauri getTasks failed:', error);
                        throw error; // Fall back to regular fetch
                    }
                    
                } else if (url.includes('/api/tasks/add') && options.method === 'POST') {
                    try {
                        const body = JSON.parse(options.body);
                        const result = await invoke('api_add_task', {
                            title: body.title,
                            description: body.description || ''
                        });
                        const data = JSON.parse(result);
                        console.log('✅ Tauri addTask success:', data);
                        return { success: true, data };
                    } catch (error) {
                        console.error('❌ Tauri addTask failed:', error);
                        throw error; // Fall back to regular fetch
                    }
                }
                
                // For other endpoints, fall back to browser fetch for now
                console.log('⚠️  Endpoint not implemented in Tauri, using browser fetch');
            }

            // Fallback to regular fetch for browser or non-implemented endpoints
            console.log('🌐 Using browser fetch:', url);
            
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            };

            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return { success: true, data };
        } catch (error) {
            console.error(`🔥 API Error (${url}):`, error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get all tasks with their current status and metadata
     * 
     * @returns {Promise<{success: boolean, data?: {tasks: Object, counts: Object, today_date: string}, error?: string}>} 
     *   Tasks data including in_progress, open, done arrays plus sidebar counts
     * 
     * @example
     * const result = await api.getTasks();
     * if (result.success) {
     *   const { in_progress, open, done } = result.data.tasks;
     * }
     */
    async getTasks() {
        const result = await this._fetch(`${this.baseURL}/tasks`);
        return result;
    }

    /**
     * Create a new task
     * 
     * @param {string} title - Task title (required)
     * @param {string} [description=''] - Task description (optional)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Creation result
     * @throws {Error} When title is invalid or too long
     * 
     * @example
     * const result = await api.addTask('Buy groceries', 'Milk, eggs, bread');
     * if (result.success) {
     *   console.log('Task created successfully');
     * }
     */
    async addTask(title, description = '') {
        // Input validation and sanitization
        if (typeof title !== 'string' || !title.trim()) {
            return { success: false, error: 'Task title is required and must be a non-empty string' };
        }
        
        if (typeof description !== 'string') {
            return { success: false, error: 'Description must be a string' };
        }
        
        // Sanitize inputs (trim whitespace, limit length)
        const sanitizedTitle = title.trim().substring(0, 500); // Max 500 chars
        const sanitizedDescription = description.trim().substring(0, 2000); // Max 2000 chars
        
        if (!sanitizedTitle) {
            return { success: false, error: 'Task title cannot be empty after trimming' };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/add`, {
            method: 'POST',
            body: JSON.stringify({ 
                title: sanitizedTitle, 
                description: sanitizedDescription 
            })
        });
    }

    /**
     * Mark a task as completed
     * 
     * @param {number} taskId - The UI task ID (sequential numbering)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Completion result
     * 
     * @example
     * const result = await api.markTaskDone(3);
     * if (result.success) {
     *   console.log('Task marked as done');
     * }
     */
    async markTaskDone(taskId) {
        // Validate task ID
        const validation = this._validateId(taskId, 'Task ID');
        if (!validation.isValid) {
            return { success: false, error: validation.error };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/${taskId}/done`, {
            method: 'POST'
        });
    }

    /**
     * Start a task (mark as in progress)
     */
    async startTask(taskId) {
        return await this._fetch(`${this.baseURL}/tasks/${taskId}/start`, {
            method: 'POST'
        });
    }

    /**
     * Stop a task (remove in progress status)
     */
    async stopTask(taskId) {
        return await this._fetch(`${this.baseURL}/tasks/${taskId}/stop`, {
            method: 'POST'
        });
    }

    /**
     * Uncomplete a completed task
     */
    async uncompleteTask(fileIdx) {
        return await this._fetch(`${this.baseURL}/tasks/uncomplete`, {
            method: 'POST',
            body: JSON.stringify({ file_idx: fileIdx })
        });
    }

    /**
     * Get detailed information for a specific task
     */
    async getTaskDetails(fileIdx) {
        return await this._fetch(`${this.baseURL}/tasks/${fileIdx}/details`);
    }

    /**
     * Update task title and description
     */
    async updateTask(fileIdx, title, description) {
        return await this._fetch(`${this.baseURL}/tasks/${fileIdx}/update`, {
            method: 'POST',
            body: JSON.stringify({ title, description })
        });
    }

    /**
     * Update task description only (deprecated)
     */
    async updateTaskDescription(fileIdx, description) {
        return await this._fetch(`${this.baseURL}/tasks/${fileIdx}/update_description`, {
            method: 'POST',
            body: JSON.stringify({ description })
        });
    }

    /**
     * Reorder tasks using file index sequence
     */
    async reorderTasks(fileIdxSequence) {
        return await this._fetch(`${this.baseURL}/tasks/reorder-simple`, {
            method: 'POST',
            body: JSON.stringify({ file_idx_sequence: fileIdxSequence })
        });
    }

    /**
     * Legacy reorder method
     */
    async reorderTaskLegacy(taskOrder, targetOrder) {
        return await this._fetch(`${this.baseURL}/tasks/reorder`, {
            method: 'POST',
            body: JSON.stringify({ task_order: taskOrder, target_order: targetOrder })
        });
    }
}

export default APIClient;
