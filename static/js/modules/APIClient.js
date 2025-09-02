/**
 * APIClient - Centralized HTTP requests for the todo application
 */
class APIClient {
    constructor() {
        this.baseURL = '/api';
    }

    /**
     * Generic fetch wrapper with error handling
     */
    async _fetch(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return { success: true, data };
        } catch (error) {
            console.error(`API Error (${url}):`, error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get all tasks
     */
    async getTasks() {
        const result = await this._fetch(`${this.baseURL}/tasks`);
        return result;
    }

    /**
     * Add a new task
     */
    async addTask(title, description = '') {
        return await this._fetch(`${this.baseURL}/tasks/add`, {
            method: 'POST',
            body: JSON.stringify({ title, description })
        });
    }

    /**
     * Mark a task as done
     */
    async markTaskDone(taskId) {
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
