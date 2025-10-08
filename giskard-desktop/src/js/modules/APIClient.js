/**
 * APIClient - Clean REST API client for the database-backed system
 * 
 * Provides a clean interface for all backend API interactions with
 * the new SQLite-based task system using proper REST endpoints.
 * 
 * @class APIClient
 * @version 2.0.0
 * @author Giskard
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
        this.isTauri = false; // Temporarily disable Tauri commands to fix task loading
        this.baseURL = 'http://localhost:5001/api'; // Always use full URL for Tauri app
        
        // Debug Tauri detection
        console.log('🔍 APIClient Tauri detection:', {
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
                
                console.log('🦀 Using Tauri commands for API:', url, options);
                
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
                    
                } else if (url.includes('/api/tasks') && options.method === 'POST' && !url.includes('/')) {
                    try {
                        const body = JSON.parse(options.body);
                        const result = await invoke('api_create_task', {
                            title: body.title,
                            description: body.description || '',
                            project: body.project || null,
                            categories: body.categories ? body.categories.join(',') : null
                        });
                        const data = JSON.parse(result);
                        console.log('✅ Tauri createTask success:', data);
                        return { success: true, data };
                    } catch (error) {
                        console.error('❌ Tauri createTask failed:', error);
                        throw error; // Fall back to regular fetch
                    }
                } else if (url.includes('/api/tasks/') && url.includes('/status') && options.method === 'PATCH') {
                    try {
                        const body = JSON.parse(options.body);
                        const taskId = url.match(/\/api\/tasks\/(\d+)\/status/)[1];
                        const result = await invoke('api_update_task_status', {
                            task_id: parseInt(taskId),
                            status: body.status
                        });
                        const data = JSON.parse(result);
                        console.log('✅ Tauri updateTaskStatus success:', data);
                        return { success: true, data };
                    } catch (error) {
                        console.error('❌ Tauri updateTaskStatus failed:', error);
                        throw error; // Fall back to regular fetch
                    }
                }
                
                // For other endpoints, fall back to browser fetch for now
                console.log('⚠️  Endpoint not implemented in Tauri, using browser fetch');
            }

            // Fallback to regular fetch for browser or non-implemented endpoints
            console.log('🌐 Using browser fetch for API:', url);
            
            const config = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            };

            console.log('🔍 Fetch config:', config);
            const response = await fetch(url, config);
            console.log('📡 Response status:', response.status, response.statusText);
            
            const data = await response.json();
            console.log('📦 Response data keys:', Object.keys(data));

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
     * @param {string} [project=null] - Project name (optional)
     * @param {string[]} [categories=[]] - Categories array (optional)
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Creation result
     * @throws {Error} When title is invalid or too long
     * 
     * @example
     * const result = await api.createTask('Buy groceries', 'Milk, eggs, bread', 'Shopping', ['personal', 'shopping']);
     * if (result.success) {
     *   console.log('Task created successfully');
     * }
     */
    async createTask(title, description = '', project = null, categories = []) {
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
        
        return await this._fetch(`${this.baseURL}/tasks`, {
            method: 'POST',
            body: JSON.stringify({ 
                title: sanitizedTitle, 
                description: sanitizedDescription,
                project: project,
                categories: categories
            })
        });
    }

    /**
     * Get a specific task by ID
     * 
     * @param {number} taskId - The task ID
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Task data
     */
    async getTask(taskId) {
        const validation = this._validateId(taskId, 'Task ID');
        if (!validation.isValid) {
            return { success: false, error: validation.error };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/${taskId}`);
    }

    /**
     * Update a specific task
     * 
     * @param {number} taskId - The task ID
     * @param {Object} updates - Fields to update
     * @param {string} [updates.title] - New title
     * @param {string} [updates.description] - New description
     * @param {string} [updates.project] - New project
     * @param {string[]} [updates.categories] - New categories array
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Update result
     */
    async updateTask(taskId, updates) {
        const validation = this._validateId(taskId, 'Task ID');
        if (!validation.isValid) {
            return { success: false, error: validation.error };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    /**
     * Delete a specific task
     * 
     * @param {number} taskId - The task ID
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Deletion result
     */
    async deleteTask(taskId) {
        const validation = this._validateId(taskId, 'Task ID');
        if (!validation.isValid) {
            return { success: false, error: validation.error };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/${taskId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Update task status
     * 
     * @param {number} taskId - The task ID
     * @param {string} status - New status ('open', 'in_progress', 'done')
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Status update result
     */
    async updateTaskStatus(taskId, status) {
        const validation = this._validateId(taskId, 'Task ID');
        if (!validation.isValid) {
            return { success: false, error: validation.error };
        }
        
        if (!['open', 'in_progress', 'done'].includes(status)) {
            return { success: false, error: 'Status must be: open, in_progress, or done' };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/${taskId}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
    }

    /**
     * Reorder tasks by providing a list of task IDs in desired order
     * 
     * @param {number[]} taskIds - Array of task IDs in desired order
     * @returns {Promise<{success: boolean, data?: any, error?: string}>} Reorder result
     */
    async reorderTasks(taskIds) {
        if (!Array.isArray(taskIds)) {
            return { success: false, error: 'taskIds must be an array' };
        }
        
        return await this._fetch(`${this.baseURL}/tasks/reorder`, {
            method: 'POST',
            body: JSON.stringify({ task_ids: taskIds })
        });
    }

    // Legacy method aliases for backward compatibility during transition
    async addTask(title, description = '') {
        return this.createTask(title, description);
    }

    async markTaskDone(taskId) {
        return this.updateTaskStatus(taskId, 'done');
    }

    async startTask(taskId) {
        return this.updateTaskStatus(taskId, 'in_progress');
    }

    async stopTask(taskId) {
        return this.updateTaskStatus(taskId, 'open');
    }
}

export default APIClient;
